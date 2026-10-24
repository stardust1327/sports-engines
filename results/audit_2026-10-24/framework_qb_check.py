"""Does the frameworks' backtest know something a live pick can't?

Both framework backtests (prompt_football/nfl.py and cfb.py, build_rows) score the
passing matchup with the quarterback who threw the most passes IN THAT GAME,
which is only known after the game (a starter hurt in the 1st quarter, a surprise
start, a benching). A live pick has to use the expected starter. This replays
each framework's backtest twice, changing only that one input:
  actual  - the QB with the most dropbacks in the game (as the framework does)
  pregame - the team's starter in its previous game (what the live picks use)
and reports both, plus the games where the two are the same QB.
Everything else (data, ratings, scaling, calibration, seasons) is the framework's
own code, imported unchanged. The college framework is also run on 2021-2025.

  python3 framework_qb_check.py nfl
  python3 framework_qb_check.py cfb
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.dirname(os.path.abspath(__file__))


def load(name):
    spec = importlib.util.spec_from_file_location(f"fw_{name}", os.path.join(REPO, "prompt_football", f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m  # so multiprocessing can find its functions
    spec.loader.exec_module(m)
    return m


def starter_maps(qg, team_col):
    """actual: most dropbacks in the game; pregame: the same team's actual starter in its previous game."""
    act = qg.sort_values("n_db").groupby(["game_id", team_col]).tail(1)
    act = act[["season", "week", "game_id", team_col, "qb"]].sort_values(["season", team_col, "week"])
    act["pregame"] = act.groupby(["season", team_col])["qb"].shift(1)
    actual = act.set_index(["game_id", team_col])["qb"]
    pregame = act.set_index(["game_id", team_col])["pregame"]
    return actual, pregame


def summarize(label, bt, keep=None):
    d = bt[bt.result.notna() & (bt.result != 0)]
    if keep is not None:
        d = d[keep.reindex(d.index).fillna(False).astype(bool)]
    win = (d.p_home >= 0.5) == (d.result > 0)
    br = ((d.p_home - (d.result > 0)) ** 2).mean()
    by = " ".join(f"{s}:{((g.p_home >= .5) == (g.result > 0)).mean():.1%}" for s, g in d.groupby("season"))
    print(f"  {label:44s} {int(win.sum())}-{int((~win).sum())} ({win.mean():.1%}) Brier {br:.4f} | {by}")
    return win.mean()


def run_nfl():
    m = load("nfl")
    raw = os.path.join(REPO, "prompt_football", "cache")
    sched = m.schedule(raw, False)
    plays = m.load_plays(raw, m.BT_SEASONS, 2026, False)
    tg, qg = m.team_games(plays)
    actual, pregame = starter_maps(qg, "team")

    def rows(qmap, season):
        out = []
        for wk in m.BT_WEEKS:
            gw = sched[(sched.season == season) & (sched.week == wk)]
            if gw.empty:
                continue
            T, raw_, q, lg = m.snapshot(tg, qg, season, wk)
            for r in gw.itertuples():
                if r.home_team not in T.index or r.away_team not in T.index:
                    continue
                qh, qa = qmap.get((r.game_id, r.home_team)), qmap.get((r.game_id, r.away_team))
                qh = None if (qh is None or (isinstance(qh, float) and np.isnan(qh))) else qh
                qa = None if (qa is None or (isinstance(qa, float) and np.isnan(qa))) else qa
                f = m.matchup(T, q, lg, r.home_team, r.away_team, qh, qa)
                f.update(season=season, week=wk, game_id=r.game_id, home_team=r.home_team, away_team=r.away_team,
                         result=r.result, total=r.total, home_sit=r.home, rest_diff=r.rest_diff, wind_eff=r.wind_eff,
                         qb_home=qh, qb_away=qa,
                         same_qb=(qh == actual.get((r.game_id, r.home_team))) and (qa == actual.get((r.game_id, r.away_team))))
                out.append(f)
        return pd.DataFrame(out)

    res = {}
    for tag, qmap in (("actual", actual), ("pregame", pregame)):
        bt = []
        for s in m.BT_SEASONS:
            r = rows(qmap, s)
            beta = m.sit_fit(sched, [x for x in m.SIT_SEASONS if x != s])
            r["sit"] = r[["home_sit", "rest_diff"]].to_numpy(float) @ beta
            bt.append(r)
        bt = pd.concat(bt, ignore_index=True)
        scale = {c: m.rms(bt[c]) for c in m.SUBS + ["sit"]}
        scale["trench_raw"] = m.rms(bt["tp"] / scale["tp"] + bt["tr"] / scale["tr"])
        scale["leverage_raw"] = m.rms(bt["h3"] / scale["h3"] + bt["hr"] / scale["hr"] + bt["ht"] / scale["ht"])
        bt = m.add_scores(bt, scale)
        out = []
        for s in m.BT_SEASONS:
            a, lr, tb = m.fit_cal(bt[bt.season != s])
            out.append(m.apply_cal(bt[bt.season == s], a, lr, tb))
        res[tag] = pd.concat(out, ignore_index=True)
        res[tag].to_csv(os.path.join(OUT, f"nfl_framework_backtest_{tag}_qb.csv"), index=False)
    print("NFL framework, 2022-2025 weeks 4-18:")
    summarize("actual QB (as the framework's backtest)", res["actual"])
    summarize("pregame QB (last game's starter, as live)", res["pregame"])
    same = res["pregame"]["same_qb"]
    summarize("pregame QB, games where it was the QB who played", res["pregame"], same)
    summarize("pregame QB, games where the QB changed", res["pregame"], ~same.astype(bool))
    print(f"  games where the pregame QB wasn't the QB who played most: {(~same.astype(bool)).sum()} of {len(same)}")


def run_cfb(seasons):
    m = load("cfb")
    m.BT_SEASONS = seasons
    cache = os.path.join(REPO, "cfb", "cache")
    sb = m.add_rest(m.scoreboard_games(cache, m.SIT_SEASONS + [2026], 2026))
    rows_ = []
    for s in seasons:
        rows_ += m.download.final_games(cache, s, refresh=False)
    games, plays, passers, _ = m.parse.parse(os.path.join(cache, "summary"), rows_)
    games = games.merge(sb[["game_id", "rest_diff"]], on="game_id", how="left")
    games["rest_diff"] = games.rest_diff.fillna(0.0)
    s_ = m.scrimmage(plays, games)
    drv = m.drives(os.path.join(cache, "summary"), games.game_id.tolist())
    tg, qg = m.team_games(s_, drv, passers)
    actual, pregame = starter_maps(qg, "team")

    def rows(qmap, season):
        out = []
        for wk in m.BT_WEEKS:
            gw = games[(games.season == season) & (games.week == wk)]
            if gw.empty:
                continue
            T, raw_, q, lg = m.snapshot(tg[(tg.season == season) & (tg.week < wk)], qg[(qg.season == season) & (qg.week < wk)])
            for r in gw.itertuples():
                h, a = r.home_id, r.away_id
                if not m.enough(T, h, a):
                    continue
                qh, qa = qmap.get((r.game_id, h)), qmap.get((r.game_id, a))
                qh = None if (qh is None or (isinstance(qh, float) and np.isnan(qh))) else qh
                qa = None if (qa is None or (isinstance(qa, float) and np.isnan(qa))) else qa
                f = m.matchup(T, q, lg, h, a, qh, qa)
                f.update(season=season, week=wk, game_id=r.game_id, home_id=h, away_id=a, home_name=r.home_name,
                         away_name=r.away_name, result=float(r.home_score - r.away_score),
                         total=float(r.home_score + r.away_score), home_sit=0.0 if r.neutral else 1.0,
                         rest_diff=r.rest_diff, qb_home=qh, qb_away=qa,
                         same_qb=(qh == actual.get((r.game_id, h))) and (qa == actual.get((r.game_id, a))))
                out.append(f)
        return pd.DataFrame(out)

    res = {}
    for tag, qmap in (("actual", actual), ("pregame", pregame)):
        bt = []
        for s in seasons:
            r = rows(qmap, s)
            beta = m.sit_fit(sb, [x for x in m.SIT_SEASONS if x != s])
            r["sit"] = r[["home_sit", "rest_diff"]].to_numpy(float) @ beta
            bt.append(r)
        bt = pd.concat(bt, ignore_index=True)
        scale = {c: m.rms(bt[c]) for c in m.SUBS + ["sit"]}
        scale["trench_raw"] = m.rms(bt["tp"] / scale["tp"] + bt["tr"] / scale["tr"])
        scale["leverage_raw"] = m.rms(bt["h3"] / scale["h3"] + bt["hr"] / scale["hr"] + bt["ht"] / scale["ht"])
        bt = m.add_scores(bt, scale)
        out = []
        for s in seasons:
            a, lr, tb = m.fit_cal(bt[bt.season != s])
            out.append(m.apply_cal(bt[bt.season == s], a, lr, tb))
        res[tag] = pd.concat(out, ignore_index=True)
        res[tag].to_csv(os.path.join(OUT, f"cfb_framework_backtest_{seasons[0]}_{seasons[-1]}_{tag}_qb.csv"), index=False)
    print(f"College framework, {seasons[0]}-{seasons[-1]} weeks 4-15:")
    summarize("actual QB (as the framework's backtest)", res["actual"])
    summarize("pregame QB (last game's starter, as live)", res["pregame"])
    same = res["pregame"]["same_qb"]
    summarize("pregame QB, games where it was the QB who played", res["pregame"], same)
    summarize("pregame QB, games where the QB changed", res["pregame"], ~same.astype(bool))
    print(f"  games where the pregame QB wasn't the QB who played most: {(~same.astype(bool)).sum()} of {len(same)}")


if __name__ == "__main__":
    if sys.argv[1] == "nfl":
        run_nfl()
    else:
        run_cfb([2022, 2023, 2024, 2025])
        run_cfb([2021, 2022, 2023, 2024, 2025])
