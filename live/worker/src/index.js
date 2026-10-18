// Live winner calls -> Discord (Cloudflare Worker, runs every minute).
//
// For every college (FBS) and NFL game in progress, reads ESPN's live win
// probability from the game feed and posts to Discord the first time one team
// reaches the threshold (98% by default; backtests in live/backtest_calls_*.txt).
// Also posts if a called team later drops below 50% ("call in doubt"), and the
// final score of every called game with whether the call was right.
// No betting lines or odds are read. Separate from the prediction engines.
//
// Watch my bets (owner's request, 2026-10-18): bets added on the /bets page
// (team to win + full payout) get their own alerts when that team's ESPN live
// win chance crosses a level (75%, 50%, 25%, 10% by default), with the fair
// value of the payout at that moment (win chance x payout) to compare with a
// cash-out offer. Only "team to win" bets; the sportsbook's odds are never read.
import { betsPage, handleBetsPost, watchBets, matchTeam } from "./bets.js";

const SPORTS = [
  { key: "college", path: "college-football", q: "?groups=80&limit=400" },
  { key: "nfl", path: "nfl", q: "" },
];
const BASE = "https://site.api.espn.com/apis/site/v2/sports/football/";
const BUDGET = 45; // Cloudflare free plan allows 50 outside requests per run
const KEEP_MS = 3 * 24 * 3600 * 1000;

function name(team, sport) {
  return sport === "college" ? team.location : team.shortDisplayName;
}

function clockText(status) {
  const p = status.period || 0;
  return (p > 4 ? "OT" : `Q${p}`) + " " + (status.displayClock || "");
}

function nowPT() {
  return new Date().toLocaleString("en-US", { timeZone: "America/Los_Angeles", month: "2-digit", day: "2-digit",
    year: "numeric", hour: "numeric", minute: "2-digit" }).replace(/\//g, ".");
}

function pct(p) {
  return (p * 100).toFixed(p >= 0.995 && p < 1 ? 1 : 0) + "%";
}

export async function run(env, io = {}) {
  const get = io.fetch || fetch;
  const log = io.log || console.log;
  let budget = BUDGET;
  const json = async (url) => {
    budget -= 1;
    const r = await get(url, { headers: { "User-Agent": "Mozilla/5.0" } });
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r.json();
  };
  const state = JSON.parse((await env.STATE.get("state")) || '{"games":{}}');
  const games = state.games;
  const msgs = [];
  let changed = false;
  const live = [];
  const seen = []; // every scoreboard event, for the bets watcher
  const bets = JSON.parse((await env.STATE.get("bets")) || "[]");

  for (const s of SPORTS) {
    let sb;
    try {
      sb = await json(BASE + s.path + "/scoreboard" + s.q);
    } catch (e) {
      log(`scoreboard ${s.key} failed: ${e.message}`);
      continue;
    }
    const th = parseFloat(env[s.key === "nfl" ? "THRESHOLD_NFL" : "THRESHOLD_COLLEGE"] || "0.98");
    for (const e of sb.events || []) {
      const c = e.competitions[0];
      const home = c.competitors.find((x) => x.homeAway === "home");
      const away = c.competitors.find((x) => x.homeAway === "away");
      const hn = name(home.team, s.key), an = name(away.team, s.key);
      const score = `${an} ${away.score}, ${hn} ${home.score}`;
      const st = e.status.type.state;
      const g = games[e.id];
      if (st === "post" && g && !g.final) {
        const hs = +home.score, as = +away.score;
        const winner = hs > as ? hn : as > hs ? an : "tie";
        g.final = score;
        g.result = winner === g.call ? "right" : winner === "tie" ? "tie" : "WRONG";
        changed = true;
        if ((env.SEND_FINALS || "true") === "true") msgs.push(`FINAL: ${score} (called ${g.call}: ${g.result})`);
      }
      seen.push({ s, e, home, away, hn, an, score });
      const forBet = bets.some((b) => !b.done && (!b.sport || b.sport === s.key) &&
        (matchTeam(b.team, home.team) || matchTeam(b.team, away.team)));
      if (st === "in") live.push({ s, e, hn, an, score, th, g, forBet });
    }
  }

  // uncalled games first, then re-check called ones for a collapse
  // games with one of your bets first, then uncalled games, then called ones (checked for a collapse)
  live.sort((x, y) => (y.forBet ? 1 : 0) - (x.forBet ? 1 : 0) || (x.g ? 1 : 0) - (y.g ? 1 : 0));
  const wpById = {};
  for (const x of live) {
    if (budget <= 0) {
      log("request budget used up; remaining games wait for the next minute");
      break;
    }
    let d;
    try {
      d = await json(`${BASE}${x.s.path}/summary?event=${x.e.id}`);
    } catch (err) {
      log(`summary ${x.e.id} failed: ${err.message}`);
      continue;
    }
    const wp = d.winprobability || [];
    if (!wp.length) continue;
    const ph = +wp[wp.length - 1].homeWinPercentage;
    wpById[x.e.id] = ph;
    const when = clockText(x.e.status);
    if (!x.g) {
      if (Math.max(ph, 1 - ph) < x.th) continue;
      const call = ph >= 0.5 ? x.hn : x.an, p = Math.max(ph, 1 - ph);
      games[x.e.id] = { sport: x.s.key, matchup: `${x.an} at ${x.hn}`, call, p, score: x.score, when,
        at: nowPT(), t: Date.now(), home: x.hn };
      changed = true;
      msgs.push(`CALL: ${call} wins (${pct(p)}). ${x.score}, ${when}`);
    } else if (!x.g.doubt) {
      const pc = x.g.call === x.g.home ? ph : 1 - ph;
      if (pc < 0.5) {
        x.g.doubt = { p: pc, score: x.score, when, at: nowPT() };
        changed = true;
        msgs.push(`CALL IN DOUBT: ${x.g.call} now ${pct(pc)}. ${x.score}, ${when}`);
      }
    }
  }

  const betMsgs = watchBets(bets, seen, wpById, { pct, clockText, nowPT });
  if (betMsgs.changed) await env.STATE.put("bets", JSON.stringify(bets.filter((b) => !b.drop)));
  msgs.unshift(...betMsgs.msgs);

  for (const [id, g] of Object.entries(games)) {
    if (Date.now() - (g.t || 0) > KEEP_MS) {
      delete games[id];
      changed = true;
    }
  }
  if (changed) await env.STATE.put("state", JSON.stringify(state));
  if (msgs.length) await post(env, msgs, get, log);
  return msgs;
}

async function post(env, msgs, get, log) {
  const url = env.DISCORD_WEBHOOK;
  if (!url) {
    msgs.forEach((m) => log("[no webhook set] " + m));
    return;
  }
  // Discord allows 2,000 characters per message
  let chunk = "";
  const send = async (text) => {
    const r = await get(url, { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ content: text }) });
    if (!r.ok) log(`Discord post failed: ${r.status}`);
  };
  for (const m of msgs) {
    if ((chunk + "\n" + m).length > 1900) {
      await send(chunk);
      chunk = "";
    }
    chunk = chunk ? chunk + "\n" + m : m;
  }
  if (chunk) await send(chunk);
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(env));
  },
  // GET /calls: the calls kept for the last 3 days, as JSON (for grading and the log)
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.pathname === "/bets") {
      if (!env.BETS_KEY || (u.searchParams.get("key") || "") !== env.BETS_KEY) {
        return new Response("Not allowed. Open /bets?key=<your BETS_KEY>.\n", { status: 403 });
      }
      if (req.method === "POST") await handleBetsPost(req, env);
      const bets = JSON.parse((await env.STATE.get("bets")) || "[]");
      return new Response(betsPage(bets, env.BETS_KEY), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (u.pathname === "/calls") {
      return new Response((await env.STATE.get("state")) || '{"games":{}}', {
        headers: { "content-type": "application/json" } });
    }
    return new Response("football-live-calls: running. GET /calls for the calls log.\n");
  },
};
