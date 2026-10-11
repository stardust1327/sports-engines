"""College football engine: opponent-adjusted EPA and success-rate ratings
(ridge regression on every non-garbage scrimmage play), shrunk toward last
season's ratings, with win probabilities calibrated on a walk-forward backtest
of the previous season.

Inputs are play-level EPA and success only. No betting lines, records, yards
or points scored go in; final scores are only the calibration target.
"""
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression, Ridge

ALPHA = 50.0      # ridge penalty, tuned on the 2025 backtest
RHO = 0.7         # weight on last season's ratings as the starting point
MIN_PLAYS = 150   # a team needs this many non-garbage offensive plays this season, else no pick
FEATS = ["net_epa", "net_sr", "is_home"]


def prepare(scrim):
    sc = scrim[~scrim["garbage"]].copy()
    sc["epa_c"] = sc["epa"].clip(-10, 10)
    return sc


def fit(plays, metric, prior=None, rho=0.0):
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
    r = Ridge(alpha=ALPHA, fit_intercept=True).fit(X, y)
    return {"off": dict(zip(teams, r.coef_[:n] + po)), "def": dict(zip(teams, r.coef_[n:2 * n] + pdf)),
            "n": plays["off"].value_counts().to_dict()}


def net(R, h, a):
    """Home team's edge per play: its offense plus what the opponent's defense allows, minus the reverse."""
    return (R["off"][h] + R["def"][a]) - (R["off"][a] + R["def"][h])


def ratings(sc, season, rho=RHO, week_before=None):
    prior_plays = sc[sc["season"] == season - 1]
    pe, ps = fit(prior_plays, "epa_c"), fit(prior_plays, "success")
    cur = sc[sc["season"] == season]
    if week_before is not None:
        cur = cur[cur["week"] < week_before]
    return fit(cur, "epa_c", pe, rho), fit(cur, "success", ps, rho)


def walk_forward(sc, games, season, weeks, rho=RHO):
    """Predict each week of a past season using only plays from earlier weeks."""
    out = []
    G = games[games["season"] == season]
    for w in weeks:
        if sc[(sc["season"] == season) & (sc["week"] < w)].empty:
            continue
        Re, Rs = ratings(sc, season, rho, week_before=w)
        for x in G[G["week"] == w].itertuples():
            h, a = x.home_id, x.away_id
            if Re["n"].get(h, 0) < MIN_PLAYS or Re["n"].get(a, 0) < MIN_PLAYS or x.home_score == x.away_score:
                continue
            out.append({"season": season, "week": w, "home": x.home_name, "away": x.away_name,
                        "net_epa": net(Re, h, a), "net_sr": net(Rs, h, a), "is_home": 0.0 if x.neutral else 1.0,
                        "home_win": int(x.home_score > x.away_score)})
    return pd.DataFrame(out)


def calibrate(bt, current_week):
    """Logistic calibration on the backtest; early-season weeks only while it's still early."""
    use = bt[bt["week"].between(4, 8)] if (current_week or 99) <= 8 else bt
    # no intercept: the features are home-relative, so a neutral-site game with no edge is 50/50
    cal = LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(use[FEATS], use["home_win"])
    return cal, len(use)


def predict(sc, season, slate, cal, rho=RHO):
    Re, Rs = ratings(sc, season, rho)
    rows = []
    for g in slate:
        h, a = g["home_id"], g["away_id"]
        nh, na = Re["n"].get(h, 0), Re["n"].get(a, 0)
        r = dict(g, home_plays=nh, away_plays=na)
        short = [nm for nm, c in [(g["home_name"], nh), (g["away_name"], na)] if c < MIN_PLAYS]
        if short:
            r.update(status="NO PICK", reason="not enough play-by-play this season: " + ", ".join(short))
            rows.append(r)
            continue
        f = {"net_epa": net(Re, h, a), "net_sr": net(Rs, h, a), "is_home": 0.0 if g["neutral"] else 1.0}
        ph = float(cal.predict_proba(pd.DataFrame([f])[FEATS])[:, 1][0])
        r.update(f)
        r.update(p_home=ph, pick=g["home_name"] if ph >= 0.5 else g["away_name"], pick_prob=max(ph, 1 - ph),
                 status="PICK", reason="")
        rows.append(r)
    return pd.DataFrame(rows)


def scores(y, p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return {"n": len(y), "hit": float(np.mean((p > 0.5) == (y == 1))), "brier": float(np.mean((p - y) ** 2))}
