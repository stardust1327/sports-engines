"""Proposal backtests for the NFL engine and an engine+framework blend (nothing
in cfb/, nfl_cfbmethod/ or prompt_football/ is changed).

  base   the locked NFL engine (ridge 500, 30% of last season, 5-week half-life)
  split  separate pass and run EPA ratings as features (success unchanged)
Both scored 2016-2025 with each season calibrated on the other nine (as the
audit), and 2017-2025 with each season calibrated only on earlier seasons.

  blend  the engine's and the framework's win chances averaged (log-odds, equal
         weights, nothing fitted) on the 2022-2025 games both rated; the
         framework uses each team's previous starter at QB (audit file).
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO, "cfb"))
sys.path.insert(0, os.path.join(REPO, "nfl_cfbmethod"))
import download    # noqa: E402  nfl_cfbmethod/download.py
import engine      # noqa: E402  cfb/engine.py
import epa         # noqa: E402  cfb/epa.py
import parse       # noqa: E402  cfb/parse.py
import nfl_engine  # noqa: E402

assert os.path.basename(os.path.dirname(download.__file__)) == "nfl_cfbmethod"
CACHE = os.path.join(REPO, "nfl_cfbmethod", "cache")
OUT = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(REPO, "results", "audit_2026-10-24")
ALPHA, RHO, HL = 500, 0.30, 5


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def replay(sc, games, S, split=False):
    prior = sc[sc.season == S - 1]
    pe, ps = nfl_engine.fit(prior, "epa_c", ALPHA), nfl_engine.fit(prior, "success", ALPHA)
    if split:
        m = prior.is_pass.values.astype(bool)
        pp, pr = nfl_engine.fit(prior[m], "epa_c", ALPHA), nfl_engine.fit(prior[~m], "epa_c", ALPHA)
    G = games[games.season == S]
    out = []
    for w in range(4, 19):
        cur = sc[(sc.season == S) & (sc.week < w)]
        if cur.empty:
            continue
        wt = nfl_engine.recency_weights(cur, w, HL)
        Re = nfl_engine.fit(cur, "epa_c", ALPHA, pe, RHO, wt)
        Rs = nfl_engine.fit(cur, "success", ALPHA, ps, RHO, wt)
        if split:
            m = cur.is_pass.values.astype(bool)
            Rp = nfl_engine.fit(cur[m], "epa_c", ALPHA, pp, RHO, wt[m])
            Rr = nfl_engine.fit(cur[~m], "epa_c", ALPHA, pr, RHO, wt[~m])
        for x in G[G.week == w].itertuples():
            h, a = x.home_id, x.away_id
            if Re["n"].get(h, 0) < engine.MIN_PLAYS or Re["n"].get(a, 0) < engine.MIN_PLAYS or x.home_score == x.away_score:
                continue
            r = {"season": S, "week": w, "game_id": x.game_id, "home": x.home_name, "away": x.away_name,
                 "net_epa": engine.net(Re, h, a), "net_sr": engine.net(Rs, h, a),
                 "is_home": 0.0 if x.neutral else 1.0, "home_win": int(x.home_score > x.away_score)}
            if split:
                r["net_pass"], r["net_run"] = engine.net(Rp, h, a), engine.net(Rr, h, a)
            out.append(r)
    return pd.DataFrame(out)


def cal(d, feats):
    return LogisticRegression(C=1e6, max_iter=2000, fit_intercept=False).fit(d[feats], d.home_win)


def summary(name, d, p="p"):
    right = (d[p] > .5) == (d.home_win == 1)
    brier = ((d[p] - d.home_win) ** 2).mean()
    e = d.week <= 8
    return (f"{name:22s} {int(right.sum())}-{int((~right).sum())} ({right.mean():.2%})  wks4-8 {right[e].mean():.2%}  "
            f"wks9+ {right[~e].mean():.2%}  Brier {brier:.4f}")


def main():
    rows = []
    for s in range(2015, 2026):
        rows += download.final_games(CACHE, s, refresh=False)
    games, plays, _, _ = parse.parse(os.path.join(CACHE, "summary"), rows)
    sc = engine.prepare(epa.build(plays, games))
    log(f"data ready: {len(games)} games")
    res = {}
    for name, split in (("base", False), ("split", True)):
        bt = pd.concat([replay(sc, games, S, split) for S in range(2016, 2026)], ignore_index=True)
        feats = engine.FEATS + (["net_pass", "net_run"] if split else [])
        bt["p"] = np.nan
        bt["p_strict"] = np.nan
        for S in range(2016, 2026):
            te = bt.season == S
            bt.loc[te, "p"] = cal(bt[~te], feats).predict_proba(bt.loc[te, feats])[:, 1]
            if S >= 2017:
                bt.loc[te, "p_strict"] = cal(bt[bt.season < S], feats).predict_proba(bt.loc[te, feats])[:, 1]
        res[name] = bt
        log(f"replays done: {name}")
    lines = ["2016-2025, each season calibrated on the other nine:"]
    lines += [summary(n, res[n]) for n in res]
    lines += ["2017-2025, each season calibrated only on earlier seasons:"]
    lines += [summary(n, res[n][res[n].season >= 2017], "p_strict") for n in res]

    # blend with the framework on 2022-2025
    sched = pd.read_csv(os.path.join(REPO, "prompt_football", "cache", "games.csv"), usecols=["game_id", "espn"])
    fw = pd.read_csv(os.path.join(AUDIT, "nfl_framework_backtest_pregame_qb.csv"))
    fw = fw.merge(sched, on="game_id").rename(columns={"p_home": "p_fw"})
    fw["espn"] = fw.espn.astype("Int64").astype(str)
    eng = res["base"].copy()
    eng["espn"] = eng.game_id.astype(str)
    b = eng.merge(fw[["espn", "p_fw"]], on="espn")
    lo = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731
    b["p_blend"] = 1 / (1 + np.exp(-(0.5 * lo(b.p) + 0.5 * lo(b.p_fw))))
    lines += [f"2022-2025 games both rated ({len(b)}):"]
    lines += [summary("engine", b, "p"), summary("framework", b, "p_fw"), summary("blend (50/50)", b, "p_blend")]
    agree = (b.p > .5) == (b.p_fw > .5)
    for nm, sub in (("models agree", b[agree]), ("models split", b[~agree])):
        lines += [f"   {nm}: {len(sub)} games; engine right {((sub.p > .5) == (sub.home_win == 1)).mean():.1%}, "
                  f"framework right {((sub.p_fw > .5) == (sub.home_win == 1)).mean():.1%}"]
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(OUT, "nfl_engine_variants.txt"), "w").write(txt + "\n")
    b.to_csv(os.path.join(OUT, "nfl_blend_2022_2025.csv"), index=False)
    pd.concat([v.assign(variant=k) for k, v in res.items()]).to_csv(os.path.join(OUT, "nfl_engine_variants.csv"), index=False)


if __name__ == "__main__":
    main()
