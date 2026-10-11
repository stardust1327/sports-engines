"""NFL-only additions to the college engine, approved by the owner on 2026-10-11.

The math is cfb/engine.py's (same plays, ratings, features and no-pick rule)
with two approved NFL options:

- the ridge penalty and last-season weight are passed in (NFL-tuned values),
- recency weighting: within the current season, each week's plays count half
  as much for every HALF_LIFE weeks they are older than the most recent week.

cfb/engine.py itself is not edited; MIN_PLAYS, FEATS and net() come from it.
"""
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge

import engine  # cfb/engine.py


def fit(plays, metric, alpha, prior=None, rho=0.0, weights=None):
    """cfb engine.fit with the penalty passed in and optional per-play weights."""
    teams = sorted(set(plays["off"]) | set(plays["def"]))
    idx = {t: i for i, t in enumerate(teams)}
    n, m = len(teams), len(plays)
    oi = plays["off"].map(idx).values
    di = plays["def"].map(idx).values + n
    ho = plays["home_off"].values.astype(float)
    X = sparse.csr_matrix((np.concatenate([np.ones(m), np.ones(m), ho]),
                           (np.concatenate([np.arange(m)] * 3), np.concatenate([oi, di, np.full(m, 2 * n)]))),
                          shape=(m, 2 * n + 1))
    y = plays[metric].values.astype(float)
    po, pdf = np.zeros(n), np.zeros(n)
    if prior is not None and rho > 0:
        po = np.array([rho * prior["off"].get(t, 0.0) for t in teams])
        pdf = np.array([rho * prior["def"].get(t, 0.0) for t in teams])
        y = y - po[oi] - pdf[di - n]
    r = Ridge(alpha=alpha, fit_intercept=True).fit(X, y, sample_weight=weights)
    return {"off": dict(zip(teams, r.coef_[:n] + po)), "def": dict(zip(teams, r.coef_[n:2 * n] + pdf)),
            "n": plays["off"].value_counts().to_dict()}


def recency_weights(plays, week_now, half_life):
    if not half_life:
        return None
    age = np.clip((week_now - 1) - plays["week"].values, 0, None)  # 0 = most recent week
    return 0.5 ** (age / half_life)


def priors(sc, season, alpha):
    last = sc[sc["season"] == season - 1]
    return fit(last, "epa_c", alpha), fit(last, "success", alpha)


def ratings(sc, season, week_now, alpha, rho, half_life, prior=None):
    """Ratings from this season's plays before week_now, starting from last season's."""
    pe, ps = prior or priors(sc, season, alpha)
    cur = sc[(sc["season"] == season) & (sc["week"] < week_now)]
    w = recency_weights(cur, week_now, half_life)
    return fit(cur, "epa_c", alpha, pe, rho, w), fit(cur, "success", alpha, ps, rho, w)


def walk_forward(sc, games, season, weeks, alpha, rho, half_life):
    """Same as cfb engine.walk_forward: each week predicted only from plays before it."""
    prior = priors(sc, season, alpha)
    G = games[games["season"] == season]
    out = []
    for w in weeks:
        if sc[(sc["season"] == season) & (sc["week"] < w)].empty:
            continue
        Re, Rs = ratings(sc, season, w, alpha, rho, half_life, prior)
        for x in G[G["week"] == w].itertuples():
            h, a = x.home_id, x.away_id
            if Re["n"].get(h, 0) < engine.MIN_PLAYS or Re["n"].get(a, 0) < engine.MIN_PLAYS or x.home_score == x.away_score:
                continue
            out.append({"season": season, "week": w, "game_id": x.game_id, "date": x.date, "home": x.home_name,
                        "away": x.away_name, "net_epa": engine.net(Re, h, a), "net_sr": engine.net(Rs, h, a),
                        "is_home": 0.0 if x.neutral else 1.0, "home_win": int(x.home_score > x.away_score)})
    return pd.DataFrame(out)


def predict(sc, season, week_now, slate, cal, alpha, rho, half_life):
    """Same as cfb engine.predict, with the NFL ratings above."""
    Re, Rs = ratings(sc, season, week_now, alpha, rho, half_life)
    rows = []
    for g in slate:
        h, a = g["home_id"], g["away_id"]
        nh, na = Re["n"].get(h, 0), Re["n"].get(a, 0)
        r = dict(g, home_plays=nh, away_plays=na)
        short = [nm for nm, c in [(g["home_name"], nh), (g["away_name"], na)] if c < engine.MIN_PLAYS]
        if short:
            r.update(status="NO PICK", reason="not enough play-by-play this season: " + ", ".join(short))
            rows.append(r)
            continue
        f = {"net_epa": engine.net(Re, h, a), "net_sr": engine.net(Rs, h, a), "is_home": 0.0 if g["neutral"] else 1.0}
        ph = float(cal.predict_proba(pd.DataFrame([f])[engine.FEATS])[:, 1][0])
        r.update(f)
        r.update(p_home=ph, pick=g["home_name"] if ph >= 0.5 else g["away_name"], pick_prob=max(ph, 1 - ph),
                 status="PICK", reason="")
        rows.append(r)
    return pd.DataFrame(rows)
