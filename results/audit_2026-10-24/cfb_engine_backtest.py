"""Multi-season backtest of the locked college engine (cfb/engine.py), run exactly
the way the live engine makes a pick, for 2021-2025.

For each test season S:
  - plays from S-2, S-1 and S (the engine's three-season window); the expected
    points model is fit on that window, as in cfb/run.py
  - calibration: the engine's own week-by-week replay of S-1 (each week predicted
    only from earlier plays, S-2 as the starting point), weeks 4-8 for test weeks
    up to 8 and all of weeks 4-15 after that (engine.calibrate)
  - test: every week 4-15 of S predicted only from plays before that week
    (engine.walk_forward), then scored with that calibration
Nothing in cfb/ is edited; this file only imports it. No betting lines anywhere.
"""
import os
import sys
import time

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "cfb"))
import download  # noqa: E402  cfb/download.py
import engine    # noqa: E402  cfb/engine.py
import epa       # noqa: E402  cfb/epa.py
import parse     # noqa: E402  cfb/parse.py

CACHE = os.path.join(REPO, "cfb", "cache")
OUT = os.path.dirname(os.path.abspath(__file__))
TEST = [2021, 2022, 2023, 2024, 2025]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def main():
    seasons = list(range(min(TEST) - 2, max(TEST) + 1))
    rows = []
    for s in seasons:
        rows += download.final_games(CACHE, s, refresh=False)
    fetched, errors = download.summaries(CACHE, [r[0] for r in rows])
    log(f"{len(rows)} finished games {seasons[0]}-{seasons[-1]} ({fetched} downloaded, {len(errors)} failed)")
    games, plays, _, perrs = parse.parse(os.path.join(CACHE, "summary"), rows)
    log(f"parsed {len(games)} games, {len(plays)} plays ({len(perrs)} parse errors)")
    games.to_csv(os.path.join(OUT, "cfb_games_2019_2025.csv"), index=False)

    out = []
    for S in TEST:
        win = games[games["season"].between(S - 2, S)]
        pl = plays[plays["game_id"].isin(win["game_id"])]
        sc = engine.prepare(epa.build(pl, win))
        prev = engine.walk_forward(sc, win, S - 1, range(4, 16))
        cal_early, n_early = engine.calibrate(prev, 8)
        cal_late, n_late = engine.calibrate(prev, 99)
        cur = engine.walk_forward(sc, win, S, range(4, 16))
        early = cur["week"] <= 8
        p = np.where(early, cal_early.predict_proba(cur[engine.FEATS])[:, 1],
                     cal_late.predict_proba(cur[engine.FEATS])[:, 1])
        cur["p_home"] = p
        cur["coef_early"] = str(np.round(cal_early.coef_[0], 3).tolist())
        cur["coef_late"] = str(np.round(cal_late.coef_[0], 3).tolist())
        won = ((cur["p_home"] > 0.5) == (cur["home_win"] == 1))
        log(f"{S}: {int(won.sum())}-{int((~won).sum())} ({won.mean():.1%}) on {len(cur)} games; "
            f"calibrated on {S - 1} ({n_early} early / {n_late} all games)")
        out.append(cur)
    bt = pd.concat(out, ignore_index=True)
    bt.to_csv(os.path.join(OUT, "cfb_engine_backtest_2021_2025.csv"), index=False)
    won = ((bt["p_home"] > 0.5) == (bt["home_win"] == 1))
    log(f"ALL: {int(won.sum())}-{int((~won).sum())} ({won.mean():.1%}) on {len(bt)} games")


if __name__ == "__main__":
    main()
