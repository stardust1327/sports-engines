"""Proposal backtests for the college engine (nothing in cfb/ is changed).

Each variant changes one thing and is scored with the live protocol: for test
season S, calibrate on the replay of S-1 (weeks 4-8 while it's week 8 or
earlier, all weeks after), then predict every week 4-15 of S from earlier plays
only. One expected points model (2019-2025 plays) is shared by every variant, so
the comparison is like for like.

  base      the locked engine (ridge 50, 70% of last season, plays equal weight)
  cal2      calibration on the two previous seasons' replays instead of one
  rec5      recency: this season's plays count half as much every 5 weeks older
  rec10     same with a 10-week half-life
  fcs50     plays against FCS opponents count half
  split     separate pass and run EPA ratings as features (success unchanged)
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO, "cfb"))
sys.path.insert(1, os.path.join(REPO, "nfl_cfbmethod"))
import download    # noqa: E402  cfb/download.py
import engine      # noqa: E402  cfb/engine.py
import epa         # noqa: E402  cfb/epa.py
import parse       # noqa: E402  cfb/parse.py
import nfl_engine  # noqa: E402  its fit() is cfb's fit with optional weights

assert os.path.basename(os.path.dirname(download.__file__)) == "cfb"
CACHE = os.path.join(REPO, "cfb", "cache")
OUT = os.path.dirname(os.path.abspath(__file__))
ALPHA, RHO = engine.ALPHA, engine.RHO


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def replay(sc, games, fcs, S, hl=None, fcs_w=None, split=False):
    prior = sc[sc.season == S - 1]
    cur_all = sc[sc.season == S]

    def w_fcs(p):
        if fcs_w is None:
            return np.ones(len(p))
        off_bad = np.array([(s, t) in fcs for s, t in zip(p.season, p["off"])], dtype=bool)
        def_bad = np.array([(s, t) in fcs for s, t in zip(p.season, p["def"])], dtype=bool)
        return np.where(off_bad | def_bad, fcs_w, 1.0)

    wp = w_fcs(prior) if fcs_w is not None else None
    pe = nfl_engine.fit(prior, "epa_c", ALPHA, weights=wp)
    ps = nfl_engine.fit(prior, "success", ALPHA, weights=wp)
    if split:
        m = prior.is_pass.values.astype(bool)
        pp = nfl_engine.fit(prior[m], "epa_c", ALPHA, weights=None if wp is None else wp[m])
        pr = nfl_engine.fit(prior[~m], "epa_c", ALPHA, weights=None if wp is None else wp[~m])
    G = games[games.season == S]
    out = []
    for w in range(4, 16):
        cur = cur_all[cur_all.week < w]
        if cur.empty:
            continue
        wt = np.ones(len(cur))
        if hl:
            wt = wt * nfl_engine.recency_weights(cur, w, hl)
        if fcs_w is not None:
            wt = wt * w_fcs(cur)
        wt = None if (not hl and fcs_w is None) else wt
        Re = nfl_engine.fit(cur, "epa_c", ALPHA, pe, RHO, wt)
        Rs = nfl_engine.fit(cur, "success", ALPHA, ps, RHO, wt)
        if split:
            m = cur.is_pass.values.astype(bool)
            Rp = nfl_engine.fit(cur[m], "epa_c", ALPHA, pp, RHO, None if wt is None else wt[m])
            Rr = nfl_engine.fit(cur[~m], "epa_c", ALPHA, pr, RHO, None if wt is None else wt[~m])
        for x in G[G.week == w].itertuples():
            h, a = x.home_id, x.away_id
            if Re["n"].get(h, 0) < engine.MIN_PLAYS or Re["n"].get(a, 0) < engine.MIN_PLAYS or x.home_score == x.away_score:
                continue
            r = {"season": S, "week": w, "home": x.home_name, "away": x.away_name,
                 "net_epa": engine.net(Re, h, a), "net_sr": engine.net(Rs, h, a),
                 "is_home": 0.0 if x.neutral else 1.0, "home_win": int(x.home_score > x.away_score)}
            if split:
                r["net_pass"] = engine.net(Rp, h, a)
                r["net_run"] = engine.net(Rr, h, a)
            out.append(r)
    return pd.DataFrame(out)


def score(rp, feats, test, cal_seasons):
    res = []
    for S in test:
        cal_df = pd.concat([rp[s] for s in cal_seasons(S)], ignore_index=True)
        early = LogisticRegression(C=1e6, max_iter=2000, fit_intercept=False).fit(
            cal_df[cal_df.week.between(4, 8)][feats], cal_df[cal_df.week.between(4, 8)].home_win)
        late = LogisticRegression(C=1e6, max_iter=2000, fit_intercept=False).fit(cal_df[feats], cal_df.home_win)
        d = rp[S].copy()
        d["p"] = np.where(d.week <= 8, early.predict_proba(d[feats])[:, 1], late.predict_proba(d[feats])[:, 1])
        res.append(d)
    return pd.concat(res, ignore_index=True)


def summary(name, d):
    right = (d.p > .5) == (d.home_win == 1)
    brier = ((d.p - d.home_win) ** 2).mean()
    e = d.week <= 8
    by = " ".join(f"{s}:{((g.p > .5) == (g.home_win == 1)).mean():.1%}" for s, g in d.groupby("season"))
    return (f"{name:8s} {int(right.sum())}-{int((~right).sum())} ({right.mean():.2%})  wks4-8 {right[e].mean():.2%}  "
            f"wks9+ {right[~e].mean():.2%}  Brier {brier:.4f} | {by}")


def main():
    rows = []
    for s in range(2019, 2026):
        rows += download.final_games(CACHE, s, refresh=False)
    games, plays, _, _ = parse.parse(os.path.join(CACHE, "summary"), rows)
    sc = engine.prepare(epa.build(plays, games))
    n_games = pd.concat([games[["season", "home_id"]].rename(columns={"home_id": "t"}),
                         games[["season", "away_id"]].rename(columns={"away_id": "t"})]).value_counts()
    fcs = {k for k, v in n_games.items() if v < 6}
    log(f"data ready: {len(games)} games, {len(sc)} plays, {len(fcs)} FCS team-seasons")

    variants = {"base": {}, "rec5": {"hl": 5}, "rec10": {"hl": 10}, "fcs50": {"fcs_w": 0.5}, "split": {"split": True}}
    reps = {}
    for name, kw in variants.items():
        reps[name] = {S: replay(sc, games, fcs, S, **kw) for S in range(2020, 2026)}
        log(f"replays done: {name}")
    F = engine.FEATS
    one = lambda S: [S - 1]  # noqa: E731
    two = lambda S: [S - 1, S - 2]  # noqa: E731
    lines, keep = [], {}
    for name in variants:
        feats = F + (["net_pass", "net_run"] if name == "split" else [])
        d = score(reps[name], feats, range(2021, 2026), one)
        keep[name] = d
        lines.append(summary(name, d))
    d2 = score(reps["base"], F, range(2022, 2026), two)
    b2 = keep["base"][keep["base"].season >= 2022]
    lines.append("--- 2022-2025 only (two-season calibration needs 2020 and 2021 replays)")
    lines.append(summary("base", b2))
    lines.append(summary("cal2", d2))
    keep["cal2"] = d2
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(OUT, "cfb_engine_variants.txt"), "w").write(txt + "\n")
    pd.concat([v.assign(variant=k) for k, v in keep.items()]).to_csv(os.path.join(OUT, "cfb_engine_variants.csv"), index=False)


if __name__ == "__main__":
    main()
