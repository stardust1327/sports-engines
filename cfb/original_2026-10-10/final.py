"""Final CFB engine: ratings from in-season play-level EPA and success rate,
shrunk toward last season's ratings, with win probabilities calibrated on a
walk-forward backtest of the previous season.

Usage:
  python3 -I final.py <data_dir> backtest            # 2025 walk-forward with 2024 prior
  python3 -I final.py <data_dir> predict <rho> <games.csv> <out.csv>
Inputs: play-level EPA and success only. No betting lines, records, yards or
points scored are used as inputs; final scores are only the calibration target.
"""
import sys, os
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge, LogisticRegression

D, MODE = sys.argv[1], sys.argv[2]
ALPHA = 50.0
MIN_PLAYS = 150
FEATS = ["net_epa", "net_sr", "is_home"]

sc = pd.read_parquet(os.path.join(D, "scrim.parquet"))
g = pd.read_parquet(os.path.join(D, "games.parquet"))
sc = sc[~sc["garbage"]].copy()
sc["epa_c"] = sc["epa"].clip(-10, 10)


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
    return (R["off"][h] + R["def"][a]) - (R["off"][a] + R["def"][h])


def walk(season, weeks, rho):
    S = sc[sc["season"] == season]
    P = sc[sc["season"] == season - 1]
    pe, ps = fit(P, "epa_c"), fit(P, "success")
    G = g[g["season"] == season]
    out = []
    for w in weeks:
        tr = S[S["week"] < w]
        if tr.empty:
            continue
        Re, Rs = fit(tr, "epa_c", pe, rho), fit(tr, "success", ps, rho)
        for _, x in G[G["week"] == w].iterrows():
            h, a = x["home_id"], x["away_id"]
            if Re["n"].get(h, 0) < MIN_PLAYS or Re["n"].get(a, 0) < MIN_PLAYS or x["home_score"] == x["away_score"]:
                continue
            out.append({"season": season, "week": w, "home": x["home_name"], "away": x["away_name"],
                        "net_epa": net(Re, h, a), "net_sr": net(Rs, h, a), "is_home": 0.0 if x["neutral"] else 1.0,
                        "home_win": int(x["home_score"] > x["away_score"])})
    return pd.DataFrame(out)


def score(y, p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return (len(y), np.mean((p > .5) == (y == 1)), np.mean((p - y) ** 2),
            -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def lowo(df):
    pr = np.zeros(len(df))
    for w in df["week"].unique():
        tr, te = df["week"] != w, df["week"] == w
        lr = LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(df.loc[tr, FEATS], df.loc[tr, "home_win"])
        pr[te.values] = lr.predict_proba(df.loc[te, FEATS])[:, 1]
    return pr


if MODE == "backtest":
    for rho in [0.0, 0.3, 0.5, 0.7]:
        bt = walk(2025, range(4, 16), rho)
        bt.to_csv(os.path.join(D, f"bt25_rho{rho}.csv"), index=False)
        pr = lowo(bt)
        y = bt["home_win"].values
        e = bt["week"].between(4, 8).values
        a_, e_ = score(y, pr), score(y[e], pr[e])
        print(f"rho={rho}: ALL n={a_[0]} hit={a_[1]:.3f} brier={a_[2]:.4f} ll={a_[3]:.4f} | "
              f"EARLY wk4-8 n={e_[0]} hit={e_[1]:.3f} brier={e_[2]:.4f} ll={e_[3]:.4f}")

elif MODE == "predict":
    rho = float(sys.argv[3])
    games = pd.read_csv(sys.argv[4], dtype=str)
    bt = pd.read_csv(os.path.join(D, f"bt25_rho{rho}.csv"))
    early = bt[bt["week"].between(4, 8)]
    cal = LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(early[FEATS], early["home_win"])
    print("calibration (2025 wk4-8, n=%d):" % len(early), dict(zip(FEATS, np.round(cal.coef_[0], 3))),
          "(no intercept: neutral games have no home edge)")
    # honest check on this season: 2026 weeks 4-6 with the 2025-fitted calibration
    b26 = walk(2026, range(4, 7), rho)
    p26 = cal.predict_proba(b26[FEATS])[:, 1]
    s = score(b26["home_win"].values, p26)
    print(f"2026 out-of-sample wk4-6: n={s[0]} hit={s[1]:.3f} brier={s[2]:.4f} ll={s[3]:.4f}")
    b26.assign(prob=p26).to_csv(os.path.join(D, "check26.csv"), index=False)
    # buckets for the 2025 early backtest (LOWO probabilities)
    pr = lowo(bt)
    bt["p"] = pr
    bt["fav_p"] = np.maximum(pr, 1 - pr)
    bt["fav_won"] = ((pr > .5) == (bt["home_win"] == 1)).astype(int)
    e = bt[bt["week"].between(4, 8)]
    print("2025 wk4-8 by confidence bucket (pred favorite prob -> actual win rate):")
    for lo, hi in [(.5, .6), (.6, .7), (.7, .8), (.8, .9), (.9, 1.01)]:
        sub = e[(e.fav_p >= lo) & (e.fav_p < hi)]
        if len(sub):
            print(f"  {lo:.0%}-{min(hi,1):.0%}: n={len(sub)} predicted {sub.fav_p.mean():.0%} actual {sub.fav_won.mean():.0%}")
    S26, S25 = sc[sc["season"] == 2026], sc[sc["season"] == 2025]
    pe, ps = fit(S25, "epa_c"), fit(S25, "success")
    Re, Rs = fit(S26, "epa_c", pe, rho), fit(S26, "success", ps, rho)
    rows = []
    for _, x in games.iterrows():
        h, a = x["home_id"], x["away_id"]
        nh, na = Re["n"].get(h, 0), Re["n"].get(a, 0)
        r = dict(x)
        r.update({"home_plays": nh, "away_plays": na})
        short = [nm for nm, c in [(x["home_name"], nh), (x["away_name"], na)] if c < MIN_PLAYS]
        if short:
            r["status"] = "NO PICK"
            r["reason"] = "not enough 2026 play-by-play: " + ", ".join(short)
            rows.append(r)
            continue
        f = {"net_epa": net(Re, h, a), "net_sr": net(Rs, h, a), "is_home": 0.0 if x["neutral"] == "True" else 1.0}
        ph = float(cal.predict_proba(pd.DataFrame([f])[FEATS])[:, 1][0])
        r.update(f)
        r.update({"p_home": ph, "pick": x["home_name"] if ph >= .5 else x["away_name"],
                  "pick_prob": max(ph, 1 - ph), "status": "PICK", "reason": "",
                  "h_off_epa": Re["off"][h], "h_def_epa": Re["def"][h], "a_off_epa": Re["off"][a], "a_def_epa": Re["def"][a],
                  "h_off_sr": Rs["off"][h], "h_def_sr": Rs["def"][h], "a_off_sr": Rs["off"][a], "a_def_sr": Rs["def"][a]})
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(sys.argv[5], index=False)
    pd.set_option("display.width", 220)
    print(out[["kick_phx", "away_name", "home_name", "status", "pick", "pick_prob", "net_epa", "net_sr", "away_plays", "home_plays"]].to_string())
