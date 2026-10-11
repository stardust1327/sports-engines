"""NFL engine: quarterback-aware, opponent-adjusted efficiency ratings.

Pass plays: EPA by team pass offense + the QB who dropped back, against the
pass defense. Run plays: EPA by team rush offense against the rush defense.
Each season's ratings start from last season's (weighted by RHO) and update
with this season's plays. Win probabilities come from a logistic calibration
fit on a walk-forward backtest of the previous two seasons.

Inputs: play-level EPA (nflverse), home field and rest days. No betting lines,
records, yards or points scored; final scores are only the calibration target.
"""
import os

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression, Ridge

ALPHA = 1000       # ridge penalty, tuned on the 2024-25 backtest
RHO = 0.45         # weight on last season's ratings as the starting point
MIN_DROPBACKS = 100  # a starting QB needs this many dropbacks over the last three seasons, else no pick
PASS_COLS = ["posteam", "passer_id"]
FEATS = ["net_pe", "net_re", "is_home", "rest_diff"]
INTERNATIONAL = ("Tottenham", "Wembley", "Allianz", "Deutsche Bank Park", "Olympiastadion", "Croke", "Bernab",
                 "Maracan", "Azteca", "Banorte", "Stade de France", "Melbourne", "Arena Corinthians")
COLS = ["game_id", "season", "season_type", "week", "posteam", "defteam", "home_team", "away_team", "epa",
        "success", "qb_dropback", "rush", "passer_id", "passer", "qb_kneel", "qb_spike", "two_point_attempt", "wp"]


class Data:
    def __init__(self, cache, season):
        self.season = season
        pbp = pd.concat([pd.read_parquet(os.path.join(cache, f"pbp_{y}.parquet"), columns=COLS)
                         for y in range(season - 4, season + 1)], ignore_index=True)
        games = pd.read_csv(os.path.join(cache, "games.csv"))
        games = games[games["season"] >= season - 4].copy()
        games["neutral"] = games["location"].eq("Neutral")
        self.games = games
        pbp = pbp.merge(games[["game_id", "neutral", "gameday"]], on="game_id", how="left")
        base = pbp[pbp["epa"].notna() & pbp["posteam"].notna() & ((pbp["qb_dropback"] == 1) | (pbp["rush"] == 1))
                   & (pbp["qb_kneel"] != 1) & (pbp["qb_spike"] != 1) & (pbp["two_point_attempt"] != 1)].copy()
        base["home_off"] = ((base["posteam"] == base["home_team"]) & (~base["neutral"].fillna(False))).astype(float)
        base["epa_c"] = base["epa"].clip(-6, 6)
        # starting QB per team per game = most dropbacks in that game
        self.db = base[(base["qb_dropback"] == 1) & base["passer_id"].notna()]
        st = (self.db.groupby(["game_id", "posteam", "passer_id", "passer"]).size().reset_index(name="n")
              .sort_values("n", ascending=False).drop_duplicates(["game_id", "posteam"]))
        self.starters = st
        self.start_map = {(r.game_id, r.posteam): r.passer_id for r in st.itertuples()}
        play = base[(base["wp"] >= 0.05) & (base["wp"] <= 0.95)]  # skip garbage time
        self.P = play[(play["qb_dropback"] == 1) & play["passer_id"].notna()]
        self.R = play[(play["rush"] == 1) & (play["qb_dropback"] != 1)]

    def dropbacks_before(self, qb, season, before_date):
        d = self.db
        return int(((d["passer_id"] == qb) & (d["season"] >= season - 2) & (d["season_type"] == "REG")
                    & (d["gameday"] < before_date)).sum())


def fit(plays, offcols, metric, prior=None, rho=0.0):
    if isinstance(offcols, str):
        offcols = [offcols]
    keycols = [plays[c].map(lambda v, c=c: f"{c}:{v}") for c in offcols]
    offs = sorted(set().union(*[set(k.unique()) for k in keycols]))
    defs = sorted(plays["defteam"].unique())
    oi_map = {k: i for i, k in enumerate(offs)}
    di_map = {k: i for i, k in enumerate(defs)}
    no, nd, m = len(offs), len(defs), len(plays)
    rows, cols, vals = [], [], []
    for k in keycols:
        rows.append(np.arange(m)); cols.append(k.map(oi_map).values); vals.append(np.ones(m))
    di = plays["defteam"].map(di_map).values
    rows += [np.arange(m), np.arange(m)]
    cols += [no + di, np.full(m, no + nd)]
    vals += [np.ones(m), plays["home_off"].values]
    X = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(m, no + nd + 1))
    y = plays[metric].values.astype(float)
    po, pdf = np.zeros(no), np.zeros(nd)
    if prior is not None and rho > 0:
        po = np.array([rho * prior["off"].get(k, 0.0) for k in offs])
        pdf = np.array([rho * prior["def"].get(k, 0.0) for k in defs])
        y = y - sum(po[k.map(oi_map).values] for k in keycols) - pdf[di]
    r = Ridge(alpha=ALPHA, fit_intercept=True).fit(X, y)
    return {"off": dict(zip(offs, r.coef_[:no] + po)), "def": dict(zip(defs, r.coef_[no:no + nd] + pdf)),
            "prior": prior, "rho": rho}


def get(R, side, k):
    v = R[side].get(k)
    if v is None and R["prior"] is not None:
        v = R["rho"] * R["prior"][side].get(k, 0.0)
    return 0.0 if v is None else v


def ratings(data, season, before_date, rho=RHO):
    """Pass and rush EPA ratings using last season as the start and this season's plays before a date."""
    P, R = data.P, data.R
    prior_p = fit(P[P["season"] == season - 1], PASS_COLS, "epa_c")
    prior_r = fit(R[R["season"] == season - 1], "posteam", "epa_c")
    Ps = P[(P["season"] == season) & (P["season_type"] == "REG") & (P["gameday"] < before_date)]
    Rs = R[(R["season"] == season) & (R["season_type"] == "REG") & (R["gameday"] < before_date)]
    if len(Ps) < 200:
        pe = {"off": {k: rho * v for k, v in prior_p["off"].items()}, "def": {k: rho * v for k, v in prior_p["def"].items()},
              "prior": prior_p, "rho": rho}
        re = {"off": {k: rho * v for k, v in prior_r["off"].items()}, "def": {k: rho * v for k, v in prior_r["def"].items()},
              "prior": prior_r, "rho": rho}
    else:
        pe = fit(Ps, PASS_COLS, "epa_c", prior_p, rho)
        re = fit(Rs, "posteam", "epa_c", prior_r, rho)
    return {"pe": pe, "re": re}


def features(Rt, h, a, qh, qa, neutral, rest_h, rest_a):
    vh, va = {"posteam": h, "passer_id": qh}, {"posteam": a, "passer_id": qa}
    off_h = sum(get(Rt["pe"], "off", f"{c}:{vh[c]}") for c in PASS_COLS)
    off_a = sum(get(Rt["pe"], "off", f"{c}:{va[c]}") for c in PASS_COLS)
    return {
        "net_pe": (off_h + get(Rt["pe"], "def", a)) - (off_a + get(Rt["pe"], "def", h)),
        "net_re": (get(Rt["re"], "off", f"posteam:{h}") + get(Rt["re"], "def", a))
                  - (get(Rt["re"], "off", f"posteam:{a}") + get(Rt["re"], "def", h)),
        "is_home": 0.0 if neutral else 1.0,
        "rest_diff": float(np.clip((rest_h if rest_h == rest_h else 7) - (rest_a if rest_a == rest_a else 7), -7, 7)) / 7.0,
    }


def walk_forward(data, season, weeks=None):
    """Predict each regular-season week using only plays before it (starters known pregame)."""
    G = data.games[(data.games["season"] == season) & (data.games["game_type"] == "REG") & data.games["result"].notna()]
    rows = []
    for w in sorted(G["week"].unique()):
        if weeks is not None and w not in weeks:
            continue
        Gw = G[G["week"] == w]
        first_day = Gw["gameday"].min()
        Rt = ratings(data, season, first_day)
        for x in Gw.itertuples():
            if x.result == 0:
                continue
            qh, qa = data.start_map.get((x.game_id, x.home_team)), data.start_map.get((x.game_id, x.away_team))
            if qh is None or qa is None:
                continue
            if min(data.dropbacks_before(qh, season, first_day), data.dropbacks_before(qa, season, first_day)) < MIN_DROPBACKS:
                continue
            f = features(Rt, x.home_team, x.away_team, qh, qa, x.neutral, x.home_rest, x.away_rest)
            f.update({"season": season, "week": w, "game_id": x.game_id, "home_win": int(x.result > 0)})
            rows.append(f)
    return pd.DataFrame(rows)


def calibrate(bt):
    # no intercept: features are home-relative, so a neutral-site game with no edge is 50/50
    return LogisticRegression(C=1e6, max_iter=2000, fit_intercept=False).fit(bt[FEATS], bt["home_win"])


def lowo(bt):
    pr = np.zeros(len(bt))
    keys = bt["season"].astype(str) + "-" + bt["week"].astype(str)
    for k in keys.unique():
        tr, te = keys != k, keys == k
        pr[te.values] = calibrate(bt[tr]).predict_proba(bt.loc[te, FEATS])[:, 1]
    return pr


def is_neutral(row):
    return bool(row["location"] == "Neutral" or any(s in str(row.get("stadium", "")) for s in INTERNATIONAL))
