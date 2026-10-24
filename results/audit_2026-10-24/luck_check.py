"""How unusual is the live record, judged by each model's own multi-season backtest?"""
import os

import numpy as np
import pandas as pd

A = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(0)


def tier(p):
    return np.where(p >= .7, "70%+", np.where(p >= .6, "60-70%", "under 60%"))


def load():
    out = {}
    n = pd.read_csv(f"{A}/nfl_engine_backtest_2016_2025.csv")
    n = n[n.season >= 2017].assign(p=lambda d: d.p_expanding)          # strict: calibrated on earlier seasons only
    out["NFL engine (2017-2025, strict)"] = n
    f = pd.read_csv(f"{A}/nfl_framework_backtest_pregame_qb.csv")
    f = f[f.result.notna() & (f.result != 0)].assign(p=lambda d: d.p_home, home_win=lambda d: (d.result > 0).astype(int))
    out["NFL framework (2022-2025, pregame QB)"] = f
    c = pd.read_csv(f"{A}/cfb_engine_backtest_2021_2025.csv").assign(p=lambda d: d.p_home)
    out["College engine (2021-2025, live-style)"] = c
    fp = f"{A}/cfb_framework_backtest_2021_2025_pregame_qb.csv"
    if os.path.exists(fp):
        cf = pd.read_csv(fp)
        cf = cf[cf.result.notna() & (cf.result != 0)].assign(p=lambda d: d.p_home, home_win=lambda d: (d.result > 0).astype(int))
        out["College framework (2021-2025, pregame QB)"] = cf
    return out


def main():
    bts = load()
    for name, d in bts.items():
        d = d.copy()
        d["fav"] = np.maximum(d.p, 1 - d.p)
        d["right"] = ((d.p > .5) == (d.home_win == 1)).astype(int)
        print(f"\n== {name}: {d.right.sum()}-{len(d) - d.right.sum()} ({d.right.mean():.1%}), {len(d)} games")
        print("   by season: " + ", ".join(f"{s} {g.right.mean():.1%}" for s, g in d.groupby("season")))
        e = d[d.week.between(4, 8)]
        print(f"   weeks 4-8 only: {e.right.mean():.1%} ({len(e)} games); weeks 9+: {d[d.week >= 9].right.mean():.1%}")
        # calibration: stated chance vs how often the pick won
        cal = d.groupby(tier(d.fav)).agg(games=("right", "size"), won=("right", "mean"), said=("fav", "mean"))
        print("   stated vs actual: " + "; ".join(f"{t} said {r.said:.0%}, won {r.won:.0%} ({r.games})"
                                                 for t, r in cal.loc[[x for x in ['70%+', '60-70%', 'under 60%'] if x in cal.index]].iterrows()))
        # weekly records
        wk = d.groupby(["season", "week"]).right.agg(["sum", "size"])
        wk["pct"] = wk["sum"] / wk["size"]
        print(f"   weeks: {len(wk)}; median week {wk.pct.median():.0%}; worst {wk.pct.min():.0%}; best {wk.pct.max():.0%}; "
              f"weeks at 50% or worse: {(wk.pct <= .5).mean():.0%}; at 45% or worse: {(wk.pct <= .45).mean():.0%}")
        # back-to-back weeks at 50% or worse, within a season
        bb = 0
        tot = 0
        for s, g in wk.groupby(level=0):
            v = (g.pct <= .5).values
            tot += max(len(v) - 1, 0)
            bb += int(np.sum(v[1:] & v[:-1]))
        print(f"   back-to-back weeks both at 50% or worse: {bb} of {tot} week pairs ({bb / tot:.0%})")


if __name__ == "__main__":
    main()
