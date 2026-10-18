"""Live winner calls from our own history: "teams in this spot won X% of the time".

The owner's idea (2026-10-18): look at the live score, quarter and clock, compare
with the same situation in thousands of past games, and call the winner when
history says it's nearly settled. Models (gradient boosting, the chance can only
rise with the lead, fit on past seasons, tested on a season it never saw):

  situation   score margin, time left, who has the ball, field position, down and
              distance (nothing else)
  +strength   the same plus the college engine's pregame win chance (play-by-play
              only), college only

Compared with ESPN's published live win probability on the same games.
College: train 2023-2024, test 2025 (weeks 4-15). NFL: train 2018-2024, test 2025.
No betting lines or odds go in.

  python3 live/backtest_situation.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import backtest_calls as bc  # noqa: E402  (college states, pregame, calls())

SIT = ["diff", "secs", "home_ball", "ytg_home", "down", "dist"]
STR = SIT + ["pre"]


def fit(tr, feats):
    mono = [1 if f in ("diff", "pre") else 0 for f in feats]
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=500,
                                          monotonic_cst=mono, random_state=0).fit(tr[feats], tr.home_win)


def report(te, cols, label):
    out = [f"{label}: {te.game_id.nunique()} test games"]
    for c in cols:
        out.append(f"{c}:")
        out.append(bc.calls(te, c))
    for per in (1, 2, 3):
        e = te[te.period <= per].groupby("game_id").last()
        out.append(f"end of Q{per}: " + "; ".join(
            f"{c} {((e[c] >= .5) == (e.home_win == 1)).mean():.1%}" for c in cols if e[c].notna().any()))
    return "\n".join(out)


def college():
    rows = []
    for s in range(2022, 2026):
        rows += bc.download.final_games(bc.CACHE, s, refresh=False)
    games, plays, _, _ = bc.parse.parse(bc.SUM, rows)
    sc = bc.engine.prepare(bc.epa.build(plays, games))
    pre = bc.pregame(sc, games)
    st = []
    for r in pre.itertuples():
        for x in bc.game_states(r.game_id):
            x.update(season=r.season, pre=r.pre, home_win=r.home_win)
            st.append(x)
    df = pd.DataFrame(st)
    df = df[df.period.between(1, 4) & df.secs.notna()].reset_index(drop=True)
    tr, te = df[df.season < 2025], df[df.season == 2025].copy()
    te["situation"] = fit(tr, SIT).predict_proba(te[SIT])[:, 1]
    te["strength"] = fit(tr, STR).predict_proba(te[STR])[:, 1]
    return report(te, ["situation", "strength", "espn"], "College 2025 weeks 4-15")


def nfl():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nfl_download", os.path.join(ROOT, "nfl_cfbmethod", "download.py"))
    nd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nd)
    cache = os.path.join(ROOT, "nfl_cfbmethod", "cache")
    rows = []
    for s in range(2018, 2026):
        rows += nd.final_games(cache, s, refresh=False)
    nd.summaries(cache, [r[0] for r in rows])
    bc.SUM = os.path.join(cache, "summary")
    st = []
    for gid, season, _, _ in rows:
        try:
            d = json.load(open(os.path.join(bc.SUM, f"{gid}.json")))
            t = {c["homeAway"]: c for c in d["header"]["competitions"][0]["competitors"]}
            hs, as_ = int(t["home"].get("score") or 0), int(t["away"].get("score") or 0)
            if hs == as_:
                continue
            for x in bc.game_states(gid):
                x.update(season=season, home_win=int(hs > as_))
                st.append(x)
        except Exception:  # noqa: BLE001
            continue
    df = pd.DataFrame(st)
    df = df[df.period.between(1, 4) & df.secs.notna()].reset_index(drop=True)
    tr, te = df[df.season < 2025], df[df.season == 2025].copy()
    te["situation"] = fit(tr, SIT).predict_proba(te[SIT])[:, 1]
    return report(te, ["situation", "espn"], "NFL 2025")


def main():
    txt = college() + "\n\n" + nfl()
    open(os.path.join(HERE, "backtest_situation.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
