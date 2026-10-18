// Local dry run: real ESPN data, in-memory state, no Discord (messages are printed).
import { run } from "./src/index.js";
const mem = new Map();
const env = { STATE: { get: async (k) => mem.get(k) ?? null, put: async (k, v) => mem.set(k, v) },
  THRESHOLD_COLLEGE: process.env.TH || "0.98", THRESHOLD_NFL: process.env.TH || "0.98", SEND_FINALS: "true" };
const a = await run(env);
console.log("run 1:", a.length, "messages");
const b = await run(env);
console.log("run 2 (same minute, should be 0 new):", b.length);
console.log(JSON.stringify(JSON.parse(mem.get("state") || "{}"), null, 1).slice(0, 1500));
