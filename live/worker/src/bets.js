// Watch my bets: alerts for the owner's own "team to win" bets.
//
// A bet is { id, sport, team, payout, stake?, levels?, added }. Every minute the
// worker finds the bet team's game on ESPN's scoreboard, reads ESPN's live win
// probability for it, and posts to Discord when the team's win chance crosses one
// of the levels (75%, 50%, 25%, 10% by default), up or down. A 2-point buffer
// keeps a team sitting on a line from sending an alert every minute. Each alert
// carries the fair value of the full payout at that moment (win chance x payout)
// so it can be compared with the app's cash-out offer. The sportsbook's odds are
// never read; the payout is the number the owner types in.

export const LEVELS = [0.75, 0.5, 0.25, 0.1];
const BUFFER = 0.02;
const KEEP_MS = 7 * 24 * 3600 * 1000; // a bet whose game never shows up is dropped after 7 days

export function matchTeam(text, team) {
  const t = String(text || "").trim().toLowerCase();
  if (!t || !team) return false;
  return [team.location, team.shortDisplayName, team.displayName, team.name, team.abbreviation]
    .some((x) => x && String(x).toLowerCase() === t);
}

function money(x) {
  return "$" + (x >= 10 ? Math.round(x).toString() : x.toFixed(2));
}

// which band p is in: 0 = above every level, 1 = below the first, ...; moves only past the buffer
function band(p, levels, prev) {
  if (prev === undefined || prev === null) return levels.filter((l) => p < l).length;
  let b = prev;
  while (b < levels.length && p < levels[b] - BUFFER) b++;
  while (b > 0 && p > levels[b - 1] + BUFFER) b--;
  return b;
}

export function watchBets(bets, seen, wpById, { pct, clockText, nowPT }) {
  const msgs = [];
  let changed = false;
  for (const b of bets) {
    if (b.done) {
      b.drop = true;
      changed = true;
      continue;
    }
    const x = seen.find((y) => (!b.sport || b.sport === y.s.key) &&
      (matchTeam(b.team, y.home.team) || matchTeam(b.team, y.away.team)));
    if (!x) {
      if (Date.now() - (b.added || 0) > KEEP_MS) {
        b.drop = true;
        changed = true;
      }
      continue;
    }
    const isHome = matchTeam(b.team, x.home.team);
    const mine = isHome ? x.hn : x.an, theirs = isHome ? x.an : x.hn;
    const st = x.e.status.type.state;
    const levels = (b.levels && b.levels.length ? b.levels : LEVELS).slice().sort((p, q) => q - p);

    if (st === "in") {
      const ph = wpById[x.e.id];
      if (ph === undefined) continue; // ESPN has no live number for this game (yet)
      const p = isHome ? ph : 1 - ph;
      const fair = p * b.payout;
      const when = clockText(x.e.status);
      const nb = band(p, levels, b.band);
      if (b.band === undefined || b.band === null) {
        msgs.push(`YOUR BET: watching ${mine} vs ${theirs}. ${mine} ${pct(p)} to win. ${x.score}, ${when}. ` +
          `Fair value of your ${money(b.payout)} payout: ${money(fair)}.`);
      } else if (nb !== b.band) {
        const line = nb > b.band ? `down to ${pct(p)} (below ${pct(levels[nb - 1])})`
          : `up to ${pct(p)} (above ${pct(levels[nb])})`;
        msgs.push(`YOUR BET: ${mine} ${line}. ${x.score}, ${when}. ` +
          `Fair value of your ${money(b.payout)} payout now: ${money(fair)}; compare with the cash-out offer.`);
      } else {
        continue; // no write: the free plan allows 1,000 storage writes a day
      }
      b.band = nb;
      b.gameId = x.e.id;
      b.last = { p, at: nowPT() };
      changed = true;
    } else if (st === "post" && b.gameId === x.e.id) {
      const hs = +x.home.score, as = +x.away.score;
      const ms = isHome ? hs : as, ts = isHome ? as : hs;
      const res = ms > ts ? `${mine} won: your ${money(b.payout)} payout hits` : ms < ts ? `${mine} lost` : "tie";
      msgs.push(`YOUR BET FINAL: ${x.score}. ${res}.`);
      b.done = true;
      changed = true;
    }
  }
  return { msgs, changed };
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export async function handleBetsPost(req, env) {
  const f = await req.formData();
  const bets = JSON.parse((await env.STATE.get("bets")) || "[]");
  if (f.get("action") === "delete") {
    const id = f.get("id");
    await env.STATE.put("bets", JSON.stringify(bets.filter((b) => b.id !== id)));
    return;
  }
  const team = String(f.get("team") || "").trim();
  const payout = parseFloat(String(f.get("payout") || "").replace(/[$,]/g, ""));
  if (!team || !(payout > 0)) return;
  const sport = f.get("sport") === "college" ? "college" : "nfl";
  const lv = String(f.get("levels") || "").split(/[ ,]+/).map(parseFloat).filter((x) => x > 0 && x < 100).map((x) => x / 100);
  bets.push({ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), sport, team, payout,
    levels: lv.length ? lv : undefined, added: Date.now() });
  await env.STATE.put("bets", JSON.stringify(bets));
}

export function betsPage(bets, key) {
  const rows = bets.filter((b) => !b.done).map((b) => `<tr><td>${esc(b.sport === "college" ? "College" : "NFL")}</td>
    <td>${esc(b.team)}</td><td>$${esc(b.payout)}</td>
    <td>${b.last ? esc((b.last.p * 100).toFixed(0) + "% at " + b.last.at + " (last alert)") : "waiting for kickoff"}</td>
    <td><form method="post" action="/bets?key=${encodeURIComponent(key)}"><input type="hidden" name="action" value="delete">
    <input type="hidden" name="id" value="${esc(b.id)}"><button>Remove</button></form></td></tr>`).join("");
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Watch my bets</title><style>
body{font:16px system-ui,sans-serif;margin:0;padding:16px;background:#f6f7f9;color:#1d2330;max-width:640px}
h1{font-size:22px;margin:0 0 4px}p{color:#5b6475;margin:4px 0 16px}
form.add{display:grid;gap:10px;background:#fff;padding:14px;border-radius:10px;border:1px solid #e3e6eb}
label{display:grid;gap:4px;font-size:14px;color:#5b6475}input,select{font:16px system-ui;padding:9px;border:1px solid #cfd4dc;border-radius:7px}
button{font:15px system-ui;padding:9px 14px;border:0;border-radius:7px;background:#1d2330;color:#fff}
table{width:100%;border-collapse:collapse;margin-top:18px;background:#fff;font-size:14px}td,th{padding:8px;border-bottom:1px solid #e3e6eb;text-align:left}
@media (prefers-color-scheme:dark){body{background:#14171c;color:#e6e8eb}form.add,table{background:#1d2128;border-color:#2c313a}
input,select{background:#14171c;color:#e6e8eb;border-color:#3a404b}button{background:#e6e8eb;color:#14171c}td,th{border-color:#2c313a}}
</style></head><body>
<h1>Watch my bets</h1>
<p>Team-to-win bets only. You get a Discord alert when the team's ESPN live win chance crosses 75%, 50%, 25% or 10%,
with the fair value of your payout (win chance × payout) to compare with the cash-out offer.</p>
<form class="add" method="post" action="/bets?key=${encodeURIComponent(key)}">
<label>League<select name="sport"><option value="nfl">NFL</option><option value="college">College</option></select></label>
<label>Team you bet on (e.g. Bears, or Ohio State)<input name="team" required></label>
<label>Full payout if it wins, stake included ($)<input name="payout" inputmode="decimal" required></label>
<label>Alert levels in % (optional, default 75 50 25 10)<input name="levels" placeholder="75 50 25 10"></label>
<button>Add bet</button></form>
<table><tr><th>League</th><th>Team</th><th>Payout</th><th>Last alert</th><th></th></tr>${rows ||
    '<tr><td colspan="5">No bets being watched.</td></tr>'}</table>
</body></html>`;
}
