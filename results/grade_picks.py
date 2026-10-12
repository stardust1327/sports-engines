"""Grade logged picks against ESPN final scores. A tie is graded T.

  python3 results/grade_picks.py results/prompt_nfl_2026_week06_picks.csv
  python3 results/grade_picks.py results/cfb_2026-10-17_picks.csv results/prompt_cfb_2026-10-17_picks.csv

For the framework's NFL files (prompt_nfl_*), the college engine's files
(cfb_<date>_picks.csv) and the framework's college files (prompt_cfb_*). The NFL
engine is graded with nfl_cfbmethod/grade.py instead (it also runs the
closing-line check), so this script refuses nfl_cfbmethod files.

Writes <name>_graded.csv next to each <name>_picks.csv and prints the record.
Games that aren't final are left ungraded (pending); run it again later.
"""
import json
import os
import sys
import time
import urllib.request

import pandas as pd

SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/{sport}/summary?event={gid}"


def final_score(sport, gid):
    url = SUMMARY.format(sport=sport, gid=gid)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                d = json.load(r)
            break
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(2 * (i + 1))
    c = d["header"]["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    state = c["status"]["type"]["state"]
    return state, int(t["away"].get("score") or 0), int(t["home"].get("score") or 0)


def record(results):
    w, l, t = (results == "W").sum(), (results == "L").sum(), (results == "T").sum()
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def grade(path):
    name = os.path.basename(path)
    if name.startswith("nfl_cfbmethod"):
        sys.exit(f"{name}: grade the NFL engine with nfl_cfbmethod/grade.py (it also runs the closing-line check)")
    if not name.endswith("_picks.csv"):
        sys.exit(f"{name}: expected a *_picks.csv file")
    sport = "nfl" if name.startswith("prompt_nfl") else "college-football"
    p = pd.read_csv(path, dtype={"game_id": str})
    rows = []
    for r in p.itertuples():
        state, a_sc, h_sc = final_score(sport, r.game_id)
        final = state == "post"
        res = ""
        if r.status == "PICK" and final:
            if a_sc == h_sc:
                res = "T"
            else:
                if r.pick == r.home_name:
                    side_won = h_sc > a_sc
                elif r.pick == r.away_name:
                    side_won = a_sc > h_sc
                else:
                    sys.exit(f"{name}: pick '{r.pick}' is neither team in {r.away_name} at {r.home_name}")
                res = "W" if side_won else "L"
        rows.append({"game_id": r.game_id, "away": r.away_name, "home": r.home_name,
                     "away_score": a_sc if final else None, "home_score": h_sc if final else None, "final": final,
                     "status": r.status, "reason": r.reason if isinstance(r.reason, str) else "",
                     "pick": r.pick if r.status == "PICK" else "", "pick_prob": r.pick_prob if r.status == "PICK" else None,
                     "result": res})
    g = pd.DataFrame(rows).astype({"away_score": "Int64", "home_score": "Int64"})
    out = os.path.join(os.path.dirname(path), name.replace("_picks.csv", "_graded.csv"))
    g.to_csv(out, index=False)
    made = g[g.status == "PICK"]
    pend = int((~made.final).sum())
    print(f"{name}: {record(made.result)}" + (f", {pend} not final yet" if pend else "")
          + f" (no picks: {(g.status != 'PICK').sum()}) -> {os.path.basename(out)}")
    return g


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        grade(path)


if __name__ == "__main__":
    main()
