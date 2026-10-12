"""Rebuild each model's out-of-sample predictions for past games (read-only use of the repo's code).

NFL engine:      2019-2025 weeks 4-18, each season calibrated on the others (as nfl_cfbmethod/run.py grades it),
                 plus 2026 weeks 4-5 (calibrated on 2019-2025, as run.py does).
College engine:  2024, 2025, 2026 (weeks 4-15 / so far), each calibrated on the previous season's replay exactly as
                 cfb/run.py + engine.calibrate do it (weeks 4-8 of last season while it's week 8 or earlier).
Framework rows come from the saved backtest files.
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.dirname(os.path.abspath(__file__))
which = sys.argv[1]

if which == "ids":
    # game ids for fetch_odds.py: every game a model rated, plus the Oct 10 slate (live picks)
    R = os.path.join(REPO, "results")
    ids = set(pd.read_csv(os.path.join(OUT, "cfb_engine_preds.csv"), dtype={"game_id": str}).game_id)
    ids |= set(pd.read_csv(os.path.join(R, "prompt_cfb_backtest_2022_2025.csv"), dtype={"game_id": str}).game_id)
    ids |= set(pd.read_csv(os.path.join(R, "prompt_cfb_2026_out_of_sample.csv"), dtype={"game_id": str}).game_id)
    g = pd.read_csv(os.path.join(OUT, "cfb_games.csv"), dtype={"game_id": str})
    ids |= set(g[g.date.str.startswith("2026-10-1")].game_id)
    open(os.path.join(OUT, "cfb_ids.txt"), "w").write("\n".join(sorted(ids)))
    e = pd.read_csv(os.path.join(OUT, "nfl_engine_preds.csv"), dtype={"game_id": str})
    gm = pd.read_csv(os.path.join(REPO, "prompt_football", "cache", "games.csv"))
    nids = set(e[e.season >= 2022].game_id) | set(gm[(gm.season >= 2022) & gm.espn.notna() & gm.result.notna()].espn.astype(int).astype(str))
    open(os.path.join(OUT, "nfl_ids.txt"), "w").write("\n".join(sorted(nids)))
    print("ids:", len(ids), "college,", len(nids), "NFL")
    sys.exit(0)

if which == "nfl":
    sys.path.insert(0, os.path.join(REPO, "nfl_cfbmethod"))
    sys.path.insert(1, os.path.join(REPO, "cfb"))
    import download, engine, epa, parse, nfl_engine  # noqa: E401
    import run as nflrun
    cache = os.path.join(REPO, "nfl_cfbmethod", "cache")
    rows = []
    for s in range(nflrun.CAL_START - 1, 2027):
        rows += download.final_games(cache, s, refresh=False)
    games, plays, passers, perrs = parse.parse(os.path.join(cache, "summary"), rows)
    print("parsed", len(games), "games; errors", len(perrs))
    sc = engine.prepare(epa.build(plays, games))
    cal_seasons = list(range(nflrun.CAL_START, 2026))
    bt = pd.concat([nfl_engine.walk_forward(sc, games, s, range(4, 19), nflrun.NFL_ALPHA, nflrun.NFL_RHO, nflrun.HALF_LIFE)
                    for s in cal_seasons], ignore_index=True)
    bt["p_home"] = nflrun.leave_one_season_out(bt)
    won = (bt.p_home > .5) == (bt.home_win == 1)
    print("NFL engine backtest:", len(bt), "games,", int(won.sum()), "-", int((~won).sum()))
    cal = nflrun.calibrate(bt)
    cur = nfl_engine.walk_forward(sc, games, 2026, range(4, 6), nflrun.NFL_ALPHA, nflrun.NFL_RHO, nflrun.HALF_LIFE)
    cur["p_home"] = cal.predict_proba(cur[engine.FEATS])[:, 1]
    won = (cur.p_home > .5) == (cur.home_win == 1)
    print("NFL engine 2026 weeks 4-5:", len(cur), "games,", int(won.sum()), "-", int((~won).sum()))
    out = pd.concat([bt.assign(set="backtest"), cur.assign(set="2026")], ignore_index=True)
    out.to_csv(os.path.join(OUT, "nfl_engine_preds.csv"), index=False)

elif which == "cfb":
    # exactly as cfb/run.py runs: for a target season S it loads S-2..S, fits expected points on those,
    # replays S-1 (weeks 4-15) to calibrate, and rates S's games from plays before each week
    sys.path.insert(0, os.path.join(REPO, "cfb"))
    import download, engine, epa, parse  # noqa: E401
    cache = os.path.join(REPO, "cfb", "cache")
    out, allgames = [], []
    for S in (2024, 2025, 2026):
        rows = []
        for s in (S - 2, S - 1, S):
            rows += download.final_games(cache, s, refresh=False)
        rows = [r for r in rows if r[3] < "2026-10-13T00:00Z"]  # 2026: through Saturday Oct 10, as the Oct 13 run saw it
        games, plays, passers, perrs = parse.parse(os.path.join(cache, "summary"), rows)
        sc = engine.prepare(epa.build(plays, games))
        prev = engine.walk_forward(sc, games, S - 1, range(4, 16))
        cur = engine.walk_forward(sc, games, S, range(4, 16) if S < 2026 else range(4, 7))
        cal_early, _ = engine.calibrate(prev, 4)   # weeks 4-8 of last season's replay (used through week 8)
        cal_late, _ = engine.calibrate(prev, 99)   # all of last season's replay (week 9 on)
        early = cur.week <= 8
        cur["p_home"] = np.nan
        cur.loc[early, "p_home"] = cal_early.predict_proba(cur.loc[early, engine.FEATS])[:, 1]
        if (~early).any():
            cur.loc[~early, "p_home"] = cal_late.predict_proba(cur.loc[~early, engine.FEATS])[:, 1]
        key = games[["game_id", "season", "week", "home_name", "away_name"]].rename(columns={"home_name": "home", "away_name": "away"})
        cur = cur.merge(key, on=["season", "week", "home", "away"], how="left")
        assert cur.game_id.notna().all(), "unmatched engine rows"
        won = (cur.p_home > .5) == (cur.home_win == 1)
        print(f"college engine {S}: {len(cur)} games, {int(won.sum())}-{int((~won).sum())} ({won.mean():.1%})")
        out.append(cur)
        allgames.append(games)
    pd.concat(out, ignore_index=True).to_csv(os.path.join(OUT, "cfb_engine_preds.csv"), index=False)
    pd.concat(allgames, ignore_index=True).drop_duplicates("game_id").to_csv(os.path.join(OUT, "cfb_games.csv"), index=False)
