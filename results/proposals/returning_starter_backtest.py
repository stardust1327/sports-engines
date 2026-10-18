"""PROPOSAL BACKTEST (not part of the locked method; changes nothing in cfb/).

Question (owner, 2026-10-17): when a team's regular starting QB plays, does the
college engine pick more winners if games its backup started stop dragging the
team's offense rating down?

Live picks only exist when both teams' regular starters play (the QB rule makes
every other game a no-pick), so the backtest grades exactly those games: both
teams' main passer in the game is the team's season-to-date attempts leader.
"Backup games" are this season's earlier games whose main passer was someone
else. Variants, each re-fit week by week from plays before that week only:

  base   the locked engine (cfb/engine.py ratings, unchanged)
  drop   same, but each team's offensive plays from its backup games are left out
  flag   same plays, plus one league-wide "backup QB on the field" term in the
         ridge fit, so those plays are explained by the term instead of the rating

Seasons 2023-2025 (weeks 4-15) and 2026 so far (weeks 4-8), each with the season
before as the starting point. Win chances: each variant's own logistic
calibration, graded leave-one-week-out (as cfb/run.py grades its backtest).
One difference from live runs: expected points are fit once on 2022-2026 plays
(live runs fit on the three seasons in use); it is the same for all variants.

  python3 results/proposals/returning_starter_backtest.py [--cache cfb/cache]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression, Ridge

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "cfb"))
import download  # noqa: E402
import engine  # noqa: E402
import epa  # noqa: E402
import parse  # noqa: E402

FEATS = engine.FEATS


def fit_flag(plays, metric, prior, rho):
    """engine.fit plus one league-wide backup-QB column (same ridge, same prior)."""
    teams = sorted(set(plays["off"]) | set(plays["def"]))
    idx = {t: i for i, t in enumerate(teams)}
    n, m = len(teams), len(plays)
    oi = plays["off"].map(idx).values
    di = plays["def"].map(idx).values + n
    ho = plays["home_off"].values.astype(float)
    bk = plays["backup"].values.astype(float)
    X = sparse.csr_matrix((np.concatenate([np.ones(m), np.ones(m), ho, bk]),
                           (np.concatenate([np.arange(m)] * 4),
                            np.concatenate([oi, di, np.full(m, 2 * n), np.full(m, 2 * n + 1)]))),
                          shape=(m, 2 * n + 2))
    y = plays[metric].values.astype(float)
    po = np.array([rho * prior["off"].get(t, 0.0) for t in teams])
    pdf = np.array([rho * prior["def"].get(t, 0.0) for t in teams])
    y = y - po[oi] - pdf[di - n]
    r = Ridge(alpha=engine.ALPHA, fit_intercept=True).fit(X, y)
    return {"off": dict(zip(teams, r.coef_[:n] + po)), "def": dict(zip(teams, r.coef_[n:2 * n] + pdf)),
            "n": plays["off"].value_counts().to_dict(), "b": float(r.coef_[2 * n + 1])}


def main_passers(passers, games):
    q = passers.merge(games[["game_id", "season", "week", "date"]], on="game_id")
    q = q[q["att"].notna()].sort_values(["team_id", "date", "att"], ascending=[True, True, False])
    top = q.groupby(["team_id", "game_id"]).head(1)[["team_id", "game_id", "season", "week", "date", "name"]]
    return q, top


def run(sc, games, passers, season, weeks):
    q, top = main_passers(passers, games)
    prior_plays = sc[sc["season"] == season - 1]
    pe, ps = engine.fit(prior_plays, "epa_c"), engine.fit(prior_plays, "success")
    G = games[games["season"] == season]
    out = []
    for w in weeks:
        cur = sc[(sc["season"] == season) & (sc["week"] < w)].copy()
        if cur.empty:
            continue
        qs = q[(q["season"] == season) & (q["week"] < w)]
        leader = qs.groupby(["team_id", "name"])["att"].sum().reset_index().sort_values("att", ascending=False) \
            .groupby("team_id").head(1).set_index("team_id")["name"].to_dict()
        ts = top[(top["season"] == season) & (top["week"] < w)]
        bk_games = {(r.game_id, r.team_id) for r in ts.itertuples() if leader.get(r.team_id) != r.name}
        nbk = ts.assign(b=[(r.game_id, r.team_id) in bk_games for r in ts.itertuples()]).groupby("team_id")["b"].sum().to_dict()
        cur["backup"] = [(g, o) in bk_games for g, o in zip(cur["game_id"], cur["off"])]
        R = {"base": (engine.fit(cur, "epa_c", pe, engine.RHO), engine.fit(cur, "success", ps, engine.RHO))}
        kept = cur[~cur["backup"]]
        R["drop"] = (engine.fit(kept, "epa_c", pe, engine.RHO), engine.fit(kept, "success", ps, engine.RHO))
        R["flag"] = (fit_flag(cur, "epa_c", pe, engine.RHO), fit_flag(cur, "success", ps, engine.RHO))
        now = top[(top["season"] == season) & (top["week"] == w)].set_index(["game_id", "team_id"])["name"].to_dict()
        for x in G[G["week"] == w].itertuples():
            h, a = x.home_id, x.away_id
            if x.home_score == x.away_score:
                continue
            Re = R["base"][0]
            if Re["n"].get(h, 0) < engine.MIN_PLAYS or Re["n"].get(a, 0) < engine.MIN_PLAYS:
                continue
            # live rule: a pick only when both regular starters play
            if not all(t in leader and now.get((x.game_id, t)) == leader[t] for t in (h, a)):
                continue
            row = {"season": season, "week": w, "game_id": x.game_id, "home": x.home_name, "away": x.away_name,
                   "is_home": 0.0 if x.neutral else 1.0, "home_win": int(x.home_score > x.away_score),
                   "home_bk": int(nbk.get(h, 0)), "away_bk": int(nbk.get(a, 0))}
            ok = True
            for v, (E, S) in R.items():
                if h not in E["off"] or a not in E["off"]:
                    ok = False
                    break
                row[f"{v}_net_epa"], row[f"{v}_net_sr"] = engine.net(E, h, a), engine.net(S, h, a)
            row["flag_b_epa"] = R["flag"][0]["b"]
            if ok:
                out.append(row)
    return pd.DataFrame(out)


def lowo(df, v):
    X = df[[f"{v}_net_epa", f"{v}_net_sr", "is_home"]].values
    y = df["home_win"].values
    key = df["season"].astype(str) + "-" + df["week"].astype(str)
    p = np.zeros(len(df))
    for k in key.unique():
        te = (key == k).values
        lr = LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(X[~te], y[~te])
        p[te] = lr.predict_proba(X[te])[:, 1]
    return p


def summary(df, mask, label):
    y = df["home_win"].values[mask]
    lines = [f"{label}: {int(mask.sum())} games"]
    for v in ("base", "drop", "flag"):
        p = df[f"p_{v}"].values[mask]
        hit = ((p > .5) == (y == 1))
        lines.append(f"  {v:5s} {int(hit.sum())}-{int((~hit).sum())} ({hit.mean():.1%}), Brier {np.mean((p - y) ** 2):.4f}")
    for v in ("drop", "flag"):
        pb, pv = df["p_base"].values[mask], df[f"p_{v}"].values[mask]
        diff = (pb > .5) != (pv > .5)
        vw = ((pv > .5) == (y == 1)) & diff
        lines.append(f"  {v} vs base: {int(diff.sum())} picks differ; {v} right on {int(vw.sum())} of them")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(ROOT, "cfb", "cache"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "proposals"))
    a = ap.parse_args()
    rows = []
    for s in range(2022, 2027):
        rows += download.final_games(a.cache, s, refresh=(s == 2026))
    fetched, errors = download.summaries(a.cache, [r[0] for r in rows])
    print(f"{len(rows)} games ({fetched} downloaded, {len(errors)} failed)", flush=True)
    games, plays, passers, perrs = parse.parse(os.path.join(a.cache, "summary"), rows)
    print(f"parsed; {len(perrs)} parse errors", flush=True)
    sc = engine.prepare(epa.build(plays, games))
    print("EPA built", flush=True)
    parts = []
    for s, wk in [(2023, range(4, 16)), (2024, range(4, 16)), (2025, range(4, 16)), (2026, range(4, 9))]:
        d = run(sc, games, passers, s, wk)
        print(f"{s}: {len(d)} games with both regular starters", flush=True)
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    for v in ("base", "drop", "flag"):
        df[f"p_{v}"] = lowo(df, v)
    df.to_csv(os.path.join(a.out, "returning_starter_backtest_games.csv"), index=False)
    aff = ((df["home_bk"] > 0) | (df["away_bk"] > 0)).values
    rep = [summary(df, np.ones(len(df), bool), "All games with both regular starters"),
           summary(df, aff, "Affected games (a team's backup started earlier this season)"),
           summary(df, ~aff, "Unaffected games")]
    for s in sorted(df["season"].unique()):
        m = (df["season"] == s).values & aff
        rep.append(summary(df, m, f"{s} affected"))
    rep.append(f"League-wide backup-QB term (EPA per play, flag variant): median {df['flag_b_epa'].median():+.3f}")
    text = "\n\n".join(rep)
    open(os.path.join(a.out, "returning_starter_backtest.txt"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
