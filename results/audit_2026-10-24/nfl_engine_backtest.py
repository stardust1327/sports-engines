"""Backtest of the locked NFL engine (nfl_cfbmethod, approved settings) on more
seasons and with stricter out-of-sample rules, plus a replay of 2026 to compare
with the picks that were actually logged.

  A. Reproduction: 2019-2025, leave-one-season-out calibration, expected points
     fit on 2018-2026 plays - exactly what nfl_cfbmethod/run.py prints.
  B. Extended: 2016-2025 (expected points fit on 2015-2026 plays). 2016-2018 were
     never used to choose the NFL settings (those were picked on 2019-2025), so
     they are a clean holdout. Calibration variants:
       - live calibration (fit on 2019-2025, what the live engine uses) on 2016-18
       - expanding window: each season calibrated only on the seasons before it
  C. 2026 replay: weeks 5-7 predicted with the live calibration, for a
     game-by-game comparison with the logged picks.
Nothing in cfb/ or nfl_cfbmethod/ is edited. No betting lines anywhere.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "cfb"))
sys.path.insert(0, os.path.join(REPO, "nfl_cfbmethod"))
import download    # noqa: E402  nfl_cfbmethod/download.py
import engine      # noqa: E402  cfb/engine.py
import epa         # noqa: E402  cfb/epa.py
import parse       # noqa: E402  cfb/parse.py
import nfl_engine  # noqa: E402  nfl_cfbmethod/nfl_engine.py

assert os.path.basename(os.path.dirname(download.__file__)) == "nfl_cfbmethod"
CACHE = os.path.join(REPO, "nfl_cfbmethod", "cache")
OUT = os.path.dirname(os.path.abspath(__file__))
ALPHA, RHO, HL = 500, 0.30, 5  # the approved settings, as in nfl_cfbmethod/run.py


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def cal_fit(bt):
    return LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(bt[engine.FEATS], bt["home_win"])


def rec(df, p="p_home"):
    won = ((df[p] > 0.5) == (df["home_win"] == 1))
    return f"{int(won.sum())}-{int((~won).sum())} ({won.mean():.1%})"


def main():
    rows = []
    for s in range(2015, 2027):
        rows += download.final_games(CACHE, s, refresh=(s == 2026))
    fetched, errors = download.summaries(CACHE, [r[0] for r in rows])
    log(f"{len(rows)} finished games 2015-2026 ({fetched} downloaded, {len(errors)} failed)")
    games, plays, _, perrs = parse.parse(os.path.join(CACHE, "summary"), rows)
    log(f"parsed {len(games)} games ({len(perrs)} parse errors); plays per season:",
        plays.merge(games[["game_id", "season"]]).groupby("season").size().to_dict())

    # ---- A. reproduction (EP on 2018-2026, as run.py)
    gA = games[games["season"] >= 2018]
    scA = engine.prepare(epa.build(plays[plays["game_id"].isin(gA["game_id"])], gA))
    btA = pd.concat([nfl_engine.walk_forward(scA, gA, s, range(4, 19), ALPHA, RHO, HL) for s in range(2019, 2026)],
                    ignore_index=True)
    pA = np.zeros(len(btA))
    for s in btA["season"].unique():
        tr, te = btA["season"] != s, btA["season"] == s
        pA[te.values] = cal_fit(btA[tr]).predict_proba(btA.loc[te, engine.FEATS])[:, 1]
    btA["p_home"] = pA
    log("A. reproduction 2019-2025 (leave-one-season-out):", rec(btA))
    btA.to_csv(os.path.join(OUT, "nfl_engine_backtest_2019_2025_repro.csv"), index=False)

    # ---- C. 2026 replay with the live calibration (fit on all of 2019-2025)
    cal_live = cal_fit(btA)
    cur = nfl_engine.walk_forward(scA, gA, 2026, range(4, 8), ALPHA, RHO, HL)
    cur["p_home"] = cal_live.predict_proba(cur[engine.FEATS])[:, 1]
    cur.to_csv(os.path.join(OUT, "nfl_engine_replay_2026.csv"), index=False)
    log("C. 2026 replay weeks 4-7 (live calibration):", rec(cur), "coef", np.round(cal_live.coef_[0], 3).tolist())

    # ---- B. extended 2016-2025 (EP on 2015-2026)
    scB = engine.prepare(epa.build(plays, games))
    btB = pd.concat([nfl_engine.walk_forward(scB, games, s, range(4, 19), ALPHA, RHO, HL) for s in range(2016, 2026)],
                    ignore_index=True)
    # live calibration (2019-2025) on the untouched 2016-2018 seasons
    cal_1925 = cal_fit(btB[btB["season"] >= 2019])
    btB["p_live_cal"] = cal_1925.predict_proba(btB[engine.FEATS])[:, 1]
    # expanding window: calibrate only on earlier seasons (2017 on)
    btB["p_expanding"] = np.nan
    for s in range(2017, 2026):
        tr = btB["season"] < s
        te = btB["season"] == s
        btB.loc[te, "p_expanding"] = cal_fit(btB[tr]).predict_proba(btB.loc[te, engine.FEATS])[:, 1]
    # leave-one-season-out over all ten
    btB["p_loso"] = np.nan
    for s in btB["season"].unique():
        tr, te = btB["season"] != s, btB["season"] == s
        btB.loc[te, "p_loso"] = cal_fit(btB[tr]).predict_proba(btB.loc[te, engine.FEATS])[:, 1]
    btB.to_csv(os.path.join(OUT, "nfl_engine_backtest_2016_2025.csv"), index=False)
    hold = btB[btB["season"] <= 2018]
    log("B. holdout 2016-2018 with the live calibration:", rec(hold, "p_live_cal"))
    log("B. expanding-window calibration 2017-2025:", rec(btB[btB["season"] >= 2017], "p_expanding"))
    log("B. leave-one-season-out 2016-2025:", rec(btB, "p_loso"))
    for s in range(2016, 2026):
        d = btB[btB["season"] == s]
        log(f"   {s}: loso {rec(d, 'p_loso')}" + (f" | expanding {rec(d, 'p_expanding')}" if s >= 2017 else ""))


if __name__ == "__main__":
    main()
