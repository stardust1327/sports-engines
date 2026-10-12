"""College: the engine vs the Prompt Football framework on the same games.

  python3 results/compare_cfb_engine_vs_framework.py --date 2026-10-13

Engine: rebuilt exactly as cfb/run.py builds it for that date (same seasons,
same code): its 2025 week-by-week backtest (leave-one-week-out calibration, the
numbers run.py prints) and this season so far (calibrated on 2025).
Framework: results/prompt_cfb_backtest_2022_2025.csv (2025 rows) and
results/prompt_cfb_2026_out_of_sample.csv, written by prompt_football/cfb.py.
Games are matched on season, week and teams. Saves
results/cfb_engine_vs_framework_same_games.csv.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "cfb"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import download  # noqa: E402
import engine  # noqa: E402
import epa  # noqa: E402
import parse  # noqa: E402
import run as cfb_run  # noqa: E402  (cfb/run.py, for its leave-one-week-out helper)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--cache", default=os.path.join(ROOT, "cfb", "cache"))
    a = ap.parse_args()
    season = int(a.date[:4])
    slate, week = download.slate(a.cache, a.date)
    first_kick = min(g["kickoff_utc"] for g in slate if g["state"] == "pre")
    rows = []
    for s in (season - 2, season - 1, season):
        rows += download.final_games(a.cache, s, refresh=False)
    rows = [r for r in rows if r[3] < first_kick]
    games, plays, passers, _ = parse.parse(os.path.join(a.cache, "summary"), rows)
    sc = engine.prepare(epa.build(plays, games))
    bt = engine.walk_forward(sc, games, season - 1, range(4, 16))
    bt["p_engine"] = cfb_run.lowo(bt)
    cal, _ = engine.calibrate(bt, week)
    cur = engine.walk_forward(sc, games, season, range(4, week or 4))
    cur["p_engine"] = cal.predict_proba(cur[engine.FEATS])[:, 1]
    eng = pd.concat([bt, cur], ignore_index=True)[["season", "week", "home", "away", "p_engine", "home_win"]]

    fw_bt = pd.read_csv(os.path.join(HERE, "prompt_cfb_backtest_2022_2025.csv"))
    fw_cur = pd.read_csv(os.path.join(HERE, f"prompt_cfb_{season}_out_of_sample.csv"))
    fw = pd.concat([fw_bt[fw_bt.season == season - 1], fw_cur], ignore_index=True)
    fw = fw[["season", "week", "home_name", "away_name", "p_home", "result"]].rename(
        columns={"home_name": "home", "away_name": "away", "p_home": "p_framework"})
    m = eng.merge(fw, on=["season", "week", "home", "away"], how="inner")
    assert ((m.result > 0).astype(int) == m.home_win).all(), "matched games disagree on the winner"
    out = os.path.join(HERE, "cfb_engine_vs_framework_same_games.csv")
    m.to_csv(out, index=False)

    for label, d in ((f"{season - 1} weeks 4-15", m[m.season == season - 1]), (f"{season} so far", m[m.season == season])):
        hw = d.home_win == 1
        e = (d.p_engine >= 0.5) == hw
        f = (d.p_framework >= 0.5) == hw
        agree = (d.p_engine >= 0.5) == (d.p_framework >= 0.5)
        print(f"{label}: {len(d)} games both rated")
        print(f"  engine    {e.sum()}-{(~e).sum()} ({e.mean():.1%}), Brier {((d.p_engine - hw) ** 2).mean():.4f}")
        print(f"  framework {f.sum()}-{(~f).sum()} ({f.mean():.1%}), Brier {((d.p_framework - hw) ** 2).mean():.4f}")
        print(f"  agree on {agree.sum()} games: {e[agree].sum()}-{(~e[agree]).sum()}; disagree on {(~agree).sum()}: "
              f"engine {e[~agree].sum()}-{(~e[~agree]).sum()}, framework {f[~agree].sum()}-{(~f[~agree]).sum()}")
    print(f"\nSaved {out} (engine games not matched: {len(eng) - len(m)}, framework games not matched: {len(fw) - len(m)})")


if __name__ == "__main__":
    main()
