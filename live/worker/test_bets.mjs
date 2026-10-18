// Offline test of watch-my-bets with a fake ESPN feed (no network, no Discord).
import worker, { run } from "./src/index.js";
const mem = new Map();
const env = { STATE: { get: async (k) => mem.get(k) ?? null, put: async (k, v) => mem.set(k, v) },
  THRESHOLD_COLLEGE: "0.98", THRESHOLD_NFL: "0.98", SEND_FINALS: "true", BETS_KEY: "k" };
let state = "in", ph = 0.40, hs = 7, as = 3;
const team = (loc, short, abbr) => ({ location: loc, shortDisplayName: short, displayName: `${loc} ${short}`, name: short, abbreviation: abbr });
const fake = async (url, opt) => {
  if (url.includes("discord")) return { ok: true };
  const nfl = url.includes("/nfl/");
  if (url.includes("scoreboard")) return { ok: true, json: async () => ({ events: nfl ? [{ id: "1",
    status: { period: 3, displayClock: "5:12", type: { state } },
    competitions: [{ competitors: [{ homeAway: "home", score: String(hs), team: team("Atlanta", "Falcons", "ATL") },
                                   { homeAway: "away", score: String(as), team: team("Chicago", "Bears", "CHI") }] }] }] : [] }) };
  if (url.includes("summary")) return { ok: true, json: async () => ({ winprobability: [{ homeWinPercentage: ph }] }) };
  throw new Error(url);
};
// add a bet through the page
const form = new URLSearchParams({ sport: "nfl", team: "bears", payout: "250" });
let r = await worker.fetch(new Request("https://x/bets?key=k", { method: "POST", body: form,
  headers: { "content-type": "application/x-www-form-urlencoded" } }), env);
console.log("page:", r.status, (await r.text()).includes("bears") ? "bet listed" : "MISSING");
console.log("no key:", (await worker.fetch(new Request("https://x/bets"), env)).status);
const step = async (label) => console.log(label, JSON.stringify(await run(env, { fetch: fake, log: () => {} })));
await step("start, Bears 60%:");
ph = 0.70; await step("Bears 30% (crossed 50, 25? no):");
ph = 0.76; await step("Bears 24% (below 25):");
ph = 0.74; await step("Bears 26% (inside buffer, expect none):");
ph = 0.80; await step("Bears 20% (same band, none):");
ph = 0.20; hs = 7; as = 21; await step("Bears 80% (up past 25, 50, 75):");
state = "post"; await step("final:");
await step("after final (none):");
console.log("bets left:", mem.get("bets"));
