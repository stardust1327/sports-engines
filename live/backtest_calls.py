"""Live winner calls: backtest (separate from the locked engines; nothing in cfb/ changes).

Goal (owner, 2026-10-18): know who wins a game as early as possible before it ends.
A "call" is made the first moment a live win chance reaches a threshold (90%, 95%,
98%) for one team. For each source this measures how often the call is right and
how much game time is left when it's made.

Sources compared, college 2025 weeks 4-15 (trained on 2023-2024, never on 2025):
  score    the leader by 8+ points at the end of the 3rd quarter (no model)
  tracker  our own live model: the engine's pregame win chance (walk-forward,
           play-by-play only) plus score, time left, possession, field position,
           down and distance; gradient boosting fit on 2023-2024 plays
  espn     ESPN's own published live win probability, read from the same feed
No betting lines or odds go into the tracker.

  python3 live/backtest_calls.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cfb"))
import download  # noqa: E402
import engine  # noqa: E402
import epa  # noqa: E402
import parse  # noqa: E402

CACHE = os.path.join(ROOT, "cfb", "cache")
SUM = os.path.join(CACHE, "summary")
FEATS = ["diff", "secs", "pre", "pre_t", "diff_t", "home_ball", "ytg_home", "down", "dist"]


def secs_of(txt):
    try:
        m, s = txt.split(":")
        return int(m) * 60 + int(float(s))
    except Exception:  # noqa: BLE001
        return np.nan


def game_states(gid):
    d = json.load(open(os.path.join(SUM, f"{gid}.json")))
    comp = d["header"]["competitions"][0]
    t = {c["homeAway"]: c for c in comp["competitors"]}
    hid = str(t["home"]["team"]["id"])
    wp = {str(x["playId"]): x.get("homeWinPercentage") for x in (d.get("winprobability") or [])}
    rows, hs, as_ = [], 0, 0
    for dv in (d.get("drives") or {}).get("previous") or []:
        for p in dv.get("plays") or []:
            per = (p.get("period") or {}).get("number") or 0
            clk = secs_of((p.get("clock") or {}).get("displayValue", ""))
            st = p.get("start") or {}
            ytg = st.get("yardsToEndzone")
            team = str((st.get("team") or {}).get("id", ""))
            secs = (4 - per) * 900 + clk if per <= 4 else 0.0
            rows.append({"game_id": gid, "period": per, "secs": secs, "diff": hs - as_,
                         "home_ball": 1.0 if team == hid else (0.0 if team else 0.5),
                         "ytg_home": (ytg if team == hid else (100 - ytg if ytg is not None else np.nan))
                         if ytg is not None else np.nan,
                         "down": st.get("down") or 0, "dist": st.get("distance") or 0,
                         "espn": wp.get(str(p.get("id")))})
            hs = p.get("homeScore", hs) or hs
            as_ = p.get("awayScore", as_) or as_
    return rows


def pregame(sc, games):
    """Engine pregame log-odds per game (walk-forward; each season calibrated on the other seasons)."""
    out = []
    bts = {s: engine.walk_forward(sc, games, s, range(4, 16)) for s in (2023, 2024, 2025)}
    for s in (2023, 2024, 2025):
        cal, _ = engine.calibrate(pd.concat([bts[x] for x in bts if x != s]), 99)
        b = bts[s].copy()
        b["pre"] = cal.decision_function(b[engine.FEATS])
        out.append(b)
    b = pd.concat(out, ignore_index=True)
    key = games[["game_id", "season", "week", "home_name", "away_name"]]
    return b.merge(key, left_on=["season", "week", "home", "away"], right_on=["season", "week", "home_name", "away_name"])


def calls(df, col, ths=(0.90, 0.95, 0.98)):
    res = []
    for th in ths:
        n = right = 0
        left, q3 = [], 0
        for gid, g in df.groupby("game_id", sort=False):
            g = g.dropna(subset=[col])
            hit = g[(g[col] >= th) | (g[col] <= 1 - th)]
            if hit.empty:
                continue
            first = hit.iloc[0]
            n += 1
            right += int((first[col] >= 0.5) == (first["home_win"] == 1))
            left.append(first["secs"])
            q3 += int(first["secs"] >= 900)
        ng = df.game_id.nunique()
        res.append(f"  {th:.0%}: called {n} of {ng} games; right {right} ({right / max(n, 1):.1%}); "
                   f"median {np.median(left) / 60:.0f} min left; called before the 4th quarter: {q3 / ng:.0%}")
    return "\n".join(res)


def main():
    rows = []
    for s in range(2022, 2026):
        rows += download.final_games(CACHE, s, refresh=False)
    download.summaries(CACHE, [r[0] for r in rows])
    games, plays, passers, _ = parse.parse(SUM, rows)
    sc = engine.prepare(epa.build(plays, games))
    pre = pregame(sc, games)
    print(f"pregame win chances for {len(pre)} games", flush=True)
    st = []
    for r in pre.itertuples():
        for x in game_states(r.game_id):
            x.update(season=r.season, week=r.week, pre=r.pre, home_win=r.home_win)
            st.append(x)
    df = pd.DataFrame(st)
    df = df[df.period.between(1, 4) & df.secs.notna()].reset_index(drop=True)
    df["t"] = df.secs / 3600.0
    df["pre_t"] = df.pre * df.t
    df["diff_t"] = df["diff"] / np.sqrt(df.secs / 60 + 1)
    tr, te = df[df.season < 2025], df[df.season == 2025].copy()
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=31, min_samples_leaf=200,
                                       random_state=0).fit(tr[FEATS], tr.home_win)
    te["tracker"] = m.predict_proba(te[FEATS])[:, 1]
    te["pregame"] = 1 / (1 + np.exp(-te.pre))
    # score-only rule: lead of 8+ at the end of the 3rd quarter
    q3 = te[te.period <= 3].groupby("game_id").last()
    q3 = q3[q3["diff"].abs() >= 8]
    lines = [f"College 2025 weeks 4-15 (test): {te.game_id.nunique()} games, {len(te)} plays",
             f"score rule (8+ point lead after Q3): called {len(q3)} games, right "
             f"{((q3['diff'] > 0) == (q3.home_win == 1)).mean():.1%}, 15 min left"]
    for col in ("tracker", "espn"):
        lines.append(f"{col}:")
        lines.append(calls(te, col))
    for per in (1, 2, 3):
        e = te[te.period <= per].groupby("game_id").last()
        for col in ("pregame", "tracker", "espn"):
            x = e.dropna(subset=[col])
            acc = ((x[col] >= .5) == (x.home_win == 1)).mean()
            br = ((x[col] - x.home_win) ** 2).mean()
            lines.append(f"end of Q{per} ({col}): picks the winner {acc:.1%}, Brier {br:.3f} ({len(x)} games)")
    txt = "\n".join(lines)
    out = os.path.join(ROOT, "live")
    open(os.path.join(out, "backtest_calls_cfb.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
