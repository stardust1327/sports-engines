"""Live winner calls, NFL: how good are ESPN's live win-probability calls?

Same test as live/backtest_calls.py (college): a call is made the first moment
ESPN's live win probability reaches 90%, 95% or 98% for one team. Measured on the
NFL regular seasons 2023-2025 (every week). Ties count as a wrong call.

  python3 live/backtest_espn_nfl.py
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "nfl_cfbmethod"))
import download  # noqa: E402  (nfl_cfbmethod/download.py)

CACHE = os.path.join(ROOT, "nfl_cfbmethod", "cache")


def secs_of(txt):
    try:
        m, s = txt.split(":")
        return int(m) * 60 + int(float(s))
    except Exception:  # noqa: BLE001
        return np.nan


def series(gid):
    d = json.load(open(os.path.join(CACHE, "summary", f"{gid}.json")))
    comp = d["header"]["competitions"][0]
    t = {c["homeAway"]: c for c in comp["competitors"]}
    hs, as_ = int(t["home"].get("score") or 0), int(t["away"].get("score") or 0)
    wp = {str(x["playId"]): x.get("homeWinPercentage") for x in (d.get("winprobability") or [])}
    pts = []
    for dv in (d.get("drives") or {}).get("previous") or []:
        for p in dv.get("plays") or []:
            v = wp.get(str(p.get("id")))
            if v is None:
                continue
            per = (p.get("period") or {}).get("number") or 0
            clk = secs_of((p.get("clock") or {}).get("displayValue", ""))
            pts.append((per, (4 - per) * 900 + clk if per <= 4 else 0.0, float(v)))
    return pts, (1 if hs > as_ else 0 if as_ > hs else 0.5)


def main():
    rows = []
    for s in (2023, 2024, 2025):
        rows += download.final_games(CACHE, s, refresh=False)
    download.summaries(CACHE, [r[0] for r in rows])
    games = []
    for r in rows:
        try:
            pts, res = series(r[0])
        except Exception:  # noqa: BLE001
            continue
        if pts:
            games.append((r[1], pts, res))
    out = [f"NFL 2023-2025 regular season: {len(games)} games with ESPN live win probability "
           f"({sum(1 for g in games if g[2] == 0.5)} ties)"]
    for th in (0.90, 0.95, 0.98):
        n = right = q3 = 0
        left = []
        for _, pts, res in games:
            hit = [x for x in pts if x[2] >= th or x[2] <= 1 - th]
            if not hit:
                continue
            per, secs, p = hit[0]
            n += 1
            right += int(res != 0.5 and (p >= 0.5) == (res == 1))
            left.append(secs)
            q3 += int(per <= 3)
        out.append(f"  {th:.0%}: called {n} of {len(games)}; right {right} ({right / n:.1%}); "
                   f"median {np.nanmedian(left) / 60:.0f} min left; called before the 4th quarter: {q3 / len(games):.0%}")
    for per in (1, 2, 3):
        acc = []
        for _, pts, res in games:
            x = [p for p in pts if p[0] <= per]
            if x and res != 0.5:
                acc.append((x[-1][2] >= 0.5) == (res == 1))
        out.append(f"end of Q{per}: ESPN's favorite wins {np.mean(acc):.1%}")
    txt = "\n".join(out)
    open(os.path.join(ROOT, "live", "backtest_calls_nfl.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
