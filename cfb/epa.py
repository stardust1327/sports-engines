"""Expected points model fit on the play table, then EPA and success for every
scrimmage play. Garbage time is flagged so the ratings can skip it."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

PASS = {"Pass Reception", "Pass Incompletion", "Sack", "Passing Touchdown", "Pass Interception Return",
        "Interception", "Pass Completion", "Interception Return Touchdown"}
RUSH = {"Rush", "Rushing Touchdown"}
FUMB = {"Fumble Recovery (Own)", "Fumble Recovery (Opponent)", "Fumble", "Fumble Return Touchdown", "Safety"}


def _feat(dn, ds, yt, sh):
    return np.column_stack([dn, np.clip(ds, 1, 30), np.clip(yt, 1, 99), np.clip(sh, 0, 1800)])


def build(plays, games):
    p = plays.merge(games[["game_id", "season", "week", "home_id", "away_id", "neutral"]], on="game_id", how="inner")
    p = p.sort_values(["game_id", "seq"]).reset_index(drop=True)
    for c in ["home_score", "away_score"]:
        p[c] = pd.to_numeric(p[c], errors="coerce")
        p[c] = p.groupby("game_id")[c].ffill().fillna(0)
    p["prev_home"] = p.groupby("game_id")["home_score"].shift(1).fillna(0)
    p["prev_away"] = p.groupby("game_id")["away_score"].shift(1).fillna(0)
    p["dh"] = p["home_score"] - p["prev_home"]
    p["da"] = p["away_score"] - p["prev_away"]
    p["half"] = np.where(p["period"] <= 2, 1, np.where(p["period"] <= 4, 2, 3))
    p["secs_half"] = np.where(p["period"].isin([1, 3]), p["clock"].fillna(0) + 900, p["clock"].fillna(0)).clip(0, 1800)

    # scoring events (exactly one side scored); a 2-point jump right after a TD is the conversion
    ev = p[((p["dh"] > 0) ^ (p["da"] > 0))].copy()
    ev["delta"] = np.where(ev["dh"] > 0, ev["dh"], ev["da"])
    ev["scorer"] = np.where(ev["dh"] > 0, ev["home_id"], ev["away_id"])
    ev = ev[ev["delta"].isin([2, 3, 6, 7, 8])]
    ev["prev_delta"] = ev.groupby("game_id")["delta"].shift(1)
    ev["prev_scorer"] = ev.groupby("game_id")["scorer"].shift(1)
    ev["prev_seq"] = ev.groupby("game_id")["seq"].shift(1)
    conv = (ev["delta"] == 2) & (ev["prev_delta"] == 6) & (ev["prev_scorer"] == ev["scorer"]) & ((ev["seq"] - ev["prev_seq"]) <= 3)
    ev = ev[~conv]
    ev["value"] = np.where(ev["delta"] >= 6, 7.0, ev["delta"].astype(float))
    ev = ev[["game_id", "half", "seq", "scorer", "value"]].rename(columns={"seq": "ev_seq"})

    sc = p[(p["type"].isin(PASS | RUSH | FUMB)) & (p["s_down"].between(1, 4)) & (p["half"] <= 2)].copy()
    sc = sc[(sc["s_ytg"] > 0) & (sc["s_ytg"] < 100) & (sc["s_dist"] > 0)]
    sc["is_pass"] = sc["type"].isin(PASS) | (sc["type"].isin(FUMB) & sc["text"].str.contains(r"pass|sack", case=False, regex=True))
    sc["off"] = sc["s_team"]
    sc["def"] = np.where(sc["off"] == sc["home_id"], sc["away_id"], sc["home_id"])
    sc = sc[(sc["off"] == sc["home_id"]) | (sc["off"] == sc["away_id"])]

    # next score in the same half, from the offense's point of view
    sc = sc.sort_values(["game_id", "seq"])
    left = sc[["game_id", "seq", "half"]].sort_values("seq")
    nxt = pd.merge_asof(left, ev.sort_values("ev_seq"), left_on="seq", right_on="ev_seq", by=["game_id"], direction="forward")
    nxt.index = left.index
    sc["ns_scorer"], sc["ns_value"], sc["ns_half"] = nxt["scorer"], nxt["value"], nxt["half_y"]
    same_half = sc["ns_half"] == sc["half"]
    sc["next_score"] = np.where(same_half & sc["ns_scorer"].notna(),
                                np.where(sc["ns_scorer"] == sc["off"], sc["ns_value"], -sc["ns_value"]), 0.0)

    X = _feat(sc["s_down"], sc["s_dist"], sc["s_ytg"], sc["secs_half"])
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
                                          min_samples_leaf=300, random_state=0)
    model.fit(X, sc["next_score"].values)
    sc["ep_before"] = model.predict(X)

    # end state: ESPN's end fields, falling back to the next play's start
    p_next = p.groupby("game_id")[["s_down", "s_dist", "s_ytg", "s_team", "half"]].shift(-1)
    p_next.columns = ["n_down", "n_dist", "n_ytg", "n_team", "n_half"]
    sc = sc.join(p_next)
    e_ok = sc["e_down"].between(1, 4) & (sc["e_ytg"] > 0) & (sc["e_ytg"] < 100) & (sc["e_dist"] > 0) & (sc["e_team"] != "")
    e_down = np.where(e_ok, sc["e_down"], sc["n_down"])
    e_dist = np.where(e_ok, sc["e_dist"], sc["n_dist"])
    e_ytg = np.where(e_ok, sc["e_ytg"], sc["n_ytg"])
    e_team = np.where(e_ok, sc["e_team"], sc["n_team"])
    valid_end = (pd.Series(e_down).between(1, 4).values & (pd.Series(e_ytg).fillna(-1).values > 0)
                 & (pd.Series(e_ytg).fillna(999).values < 100))
    Xa = _feat(np.nan_to_num(e_down.astype(float), nan=1), np.nan_to_num(e_dist.astype(float), nan=10),
               np.nan_to_num(e_ytg.astype(float), nan=75), np.clip(sc["secs_half"].values - 25, 0, 1800))
    ep_end = model.predict(Xa)
    ep_after = np.where(valid_end, np.where(e_team == sc["off"].values, ep_end, -ep_end), 0.0)

    # scoring on the play itself overrides
    scored_home, scored_away = sc["dh"].values > 0, sc["da"].values > 0
    delta = np.where(scored_home, sc["dh"].values, np.where(scored_away, sc["da"].values, 0))
    scorer = np.where(scored_home, sc["home_id"].values, np.where(scored_away, sc["away_id"].values, ""))
    off_scored = scorer == sc["off"].values
    td, saf = delta >= 6, delta == 2
    ep_after = np.where(td & off_scored, 7.0, ep_after)
    ep_after = np.where(td & ~off_scored & (scorer != ""), -7.0, ep_after)
    ep_after = np.where(saf & ~off_scored & (scorer != ""), -2.0, ep_after)
    sc["epa"] = ep_after - sc["ep_before"].values

    yds = pd.to_numeric(sc["yards"], errors="coerce").fillna(0).values
    dist = sc["s_dist"].values
    need = np.where(sc["s_down"] == 1, 0.5 * dist, np.where(sc["s_down"] == 2, 0.7 * dist, dist))
    succ = ((yds >= need) | (td & off_scored)) & ~(sc["turnover"].values & ~off_scored)
    sc["success"] = succ.astype(float)

    margin = (sc["prev_home"] - sc["prev_away"]).abs()
    sc["garbage"] = (((sc["period"] == 2) & (margin > 38)) | ((sc["period"] == 3) & (margin > 28))
                     | ((sc["period"] == 4) & (margin > 22)))
    sc["home_off"] = (sc["off"] == sc["home_id"]) & (~sc["neutral"])
    keep = ["game_id", "season", "week", "off", "def", "home_off", "is_pass", "epa", "success", "garbage"]
    return sc[keep].reset_index(drop=True)
