"""Score each model's out-of-sample picks against the betting market's moneylines (grading only;
lines never feed a prediction). Run after build_preds.py and fetch_odds.py; see README.md."""
import glob
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

ML = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = REPO + "/results/"


def implied(ml):
    ml = np.asarray(ml, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(ml > 0, 100 / (ml + 100), -ml / (-ml + 100))


def payout(ml):
    ml = np.asarray(ml, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(ml > 0, ml / 100, 100 / -ml)


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def odds_table(folder):
    rows = [json.load(open(f)) for f in glob.glob(folder + "/*.json")]
    return pd.DataFrame(rows).astype({"game_id": str})


def prep(d, hc="h_close", ac="a_close", ho="h_open", ao="a_open"):
    d = d.copy()
    d = d[d[hc].notna() & d[ac].notna() & d.p_home.notna()]
    d = d[d.home_win != 0.5]                                    # ties (NFL only) are pushes: left out
    ih, ia = implied(d[hc]), implied(d[ac])
    d["mkt"] = ih / (ih + ia)
    d["vig"] = ih + ia - 1
    d["pick_home"] = d.p_home >= 0.5
    d["won"] = d.pick_home == (d.home_win == 1)
    d["pick_ml"] = np.where(d.pick_home, d[hc], d[ac])
    d["profit"] = np.where(d.won, payout(d.pick_ml), -1.0)
    d["mkt_pick"] = np.where(d.pick_home, d.mkt, 1 - d.mkt)
    d["model_pick"] = np.where(d.pick_home, d.p_home, 1 - d.p_home)
    d["edge"] = d.model_pick - d.mkt_pick
    d["dog"] = d.mkt_pick < 0.5
    if ho in d and ao in d:
        ok = d[ho].notna() & d[ao].notna()
        ih0, ia0 = implied(d[ho].fillna(-110)), implied(d[ao].fillna(-110))
        d["mkt_open"] = np.where(ok, ih0 / (ih0 + ia0), np.nan)
        d["has_open"] = ok
        d["pick_ml_open"] = np.where(d.pick_home, d[ho], d[ao])
        d["profit_open"] = np.where(ok, np.where(d.won, payout(d.pick_ml_open.fillna(-110)), -1.0), np.nan)
        d["open_pick"] = np.where(d.pick_home, d.mkt_open, 1 - d.mkt_open)
        d["edge_open"] = d.model_pick - d.open_pick
        d["clv"] = d.mkt_pick - d.open_pick          # + means the market moved toward the pick after the open
    return d


def roi(x):
    x = np.asarray(x, float)
    if len(x) == 0:
        return "-"
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0
    return f"{m:+.1%} (95% range {m - 1.96 * se:+.1%} to {m + 1.96 * se:+.1%})"


def rec(won):
    won = np.asarray(won, bool)
    return f"{won.sum()}-{(~won).sum()}"


def blend_test(d):
    """Out-of-sample by season: does adding the model's number to the closing line's improve accuracy?"""
    y = (d.home_win == 1).astype(int).values
    X = np.column_stack([logit(d.mkt), logit(d.p_home)])
    seasons = d.season.values
    pb = np.zeros(len(d))
    for s in np.unique(seasons):
        tr, te = seasons != s, seasons == s
        if tr.sum() < 100:
            return None
        lr = LogisticRegression(C=1e6, max_iter=1000).fit(X[tr], y[tr])
        pb[te] = lr.predict_proba(X[te])[:, 1]
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(X, y)
    # standard error of the model's weight (inverse Fisher information)
    p = lr.predict_proba(X)[:, 1]
    Xi = np.column_stack([np.ones(len(X)), X])
    cov = np.linalg.inv((Xi * (p * (1 - p))[:, None]).T @ Xi)
    w, se = lr.coef_[0][1], np.sqrt(cov[2, 2])
    return {"brier_mkt": np.mean((d.mkt - y) ** 2), "brier_blend": np.mean((pb - y) ** 2),
            "w_model": w, "se_model": se, "w_mkt": lr.coef_[0][0]}


def report(name, d, show_open=True):
    y = (d.home_win == 1).values
    fav_won = (d.mkt >= 0.5) == y
    print(f"\n### {name}: {len(d)} games with closing lines, seasons {d.season.min()}-{d.season.max()}")
    print(f"  picks right: model {rec(d.won)} ({d.won.mean():.1%}) | closing-line favorite {rec(fav_won)} ({fav_won.mean():.1%})")
    print(f"  Brier (lower better): model {np.mean((d.p_home - y) ** 2):.4f} | closing line {np.mean((d.mkt - y) ** 2):.4f}")
    print(f"  bet every pick at the closing moneyline: {rec(d.won)}, {d.profit.sum():+.1f} units, ROI {roi(d.profit)}")
    dog = d[d.dog]
    print(f"  picks against the market favorite: {len(dog)} ({len(dog) / len(d):.0%}), {rec(dog.won)}, ROI {roi(dog.profit)}")
    fav = d[~d.dog]
    print(f"  picks agreeing with the market favorite: {len(fav)}, {rec(fav.won)}, ROI {roi(fav.profit)}")
    for t in (0.05, 0.10):
        v = d[d.edge >= t]
        print(f"  'value' picks (model {int(t * 100)}+ pts above the closing price): {len(v)}, {rec(v.won)}, ROI {roi(v.profit)}")
    for lo, hi, lab in ((0.7, 1.01, "70%+"), (0.6, 0.7, "60-70%"), (0.5, 0.6, "under 60%")):
        t = d[(d.model_pick >= lo) & (d.model_pick < hi)]
        print(f"    tier {lab:>9}: {len(t)} picks, {rec(t.won)} ({t.won.mean():.1%}), market favorite on them "
              f"{((t.mkt >= .5) == (t.home_win == 1)).mean():.1%}, ROI {roi(t.profit)}")
    b = blend_test(d)
    if b:
        print(f"  adds anything to the closing line? model weight {b['w_model']:+.2f} (se {b['se_model']:.2f}); "
              f"out-of-sample Brier: line alone {b['brier_mkt']:.4f}, line + model {b['brier_blend']:.4f}")
    if show_open and "has_open" in d and d.has_open.any():
        o = d[d.has_open]
        corr = np.corrcoef(o.p_home - o.mkt_open, o.mkt - o.mkt_open)[0, 1]
        v = o[o.edge_open >= 0.05]
        print(f"  with opening lines ({len(o)} games, {o.season.min()}-{o.season.max()}): bet every pick at the open: ROI {roi(o.profit_open)}")
        print(f"    value picks vs the open (5+ pts): {len(v)}, {rec(v.won)}, ROI at the open {roi(v.profit_open)}, "
              f"at the close {roi(v.profit)}")
        print(f"    line moved toward the pick (open to close): every pick {np.mean(o.clv > 0.005):.0%} moved toward, "
              f"{np.mean(o.clv < -0.005):.0%} away, avg {o.clv.mean():+.2%}; value picks avg {v.clv.mean():+.2%}")
        print(f"    does the model's disagreement with the open predict the line move? correlation {corr:+.3f}")
    return d


def main():
    # ---------------- NFL
    gm = pd.read_csv(REPO + "/prompt_football/cache/games.csv")
    gm = gm[(gm.game_type == "REG")]
    gm["espn_id"] = gm.espn.apply(lambda x: str(int(x)) if pd.notna(x) else None)
    no = odds_table(REPO + "/nfl_cfbmethod/cache/odds").rename(columns={"game_id": "espn_id"})
    # cross-check nflverse closing vs ESPN closing where both exist
    x = gm.merge(no, on="espn_id")
    x = x[x.home_moneyline.notna() & x.h_close.notna()]
    a = implied(x.home_moneyline) / (implied(x.home_moneyline) + implied(x.away_moneyline))
    b = implied(x.h_close) / (implied(x.h_close) + implied(x.a_close))
    print(f"NFL check: nflverse vs ESPN closing no-vig home chance, {len(x)} games: corr {np.corrcoef(a, b)[0, 1]:.3f}, "
          f"median gap {np.median(np.abs(a - b)):.3f}")

    e = pd.read_csv(ML + "/nfl_engine_preds.csv", dtype={"game_id": str}).rename(columns={"game_id": "espn_id"})
    e = e.merge(gm[["espn_id", "game_id", "home_moneyline", "away_moneyline"]], on="espn_id", how="left")
    print("NFL engine rows without an nflverse match:", e.game_id.isna().sum())
    e = e.merge(no[["espn_id", "h_open", "a_open"]], on="espn_id", how="left")
    e = e.rename(columns={"home_moneyline": "h_close", "away_moneyline": "a_close"})
    nfl_e = prep(e[e.set == "backtest"])
    report("NFL ENGINE backtest 2019-2025", nfl_e)

    f = pd.read_csv(R + "prompt_nfl_backtest_2022_2025.csv")
    f["home_win"] = np.where(f.result > 0, 1.0, np.where(f.result < 0, 0.0, 0.5))
    f = f.merge(gm[["game_id", "espn_id", "home_moneyline", "away_moneyline"]], on="game_id", how="left")
    f = f.merge(no[["espn_id", "h_open", "a_open"]], on="espn_id", how="left")
    f = f.rename(columns={"home_moneyline": "h_close", "away_moneyline": "a_close"})
    nfl_f = prep(f)
    report("NFL FRAMEWORK backtest 2022-2025", nfl_f)
    same = nfl_e.merge(nfl_f[["espn_id", "p_home"]], on="espn_id", suffixes=("", "_fw"))
    same_f = nfl_f[nfl_f.espn_id.isin(same.espn_id)]
    print(f"\n  same {len(same)} NFL games (2022-2025): engine ROI {roi(same.profit)}; framework ROI "
          f"{roi(same_f.profit)}")

    # ---------------- college
    co = odds_table(REPO + "/cfb/cache/odds")
    # 2022 has no opening/closing in ESPN's odds service for many games: fall back to the cached summary line
    fb = []
    for gid in co[co.h_close.isna()].game_id:
        try:
            d = json.load(open(f"{REPO}/cfb/cache/summary/{gid}.json"))
        except Exception:  # noqa: BLE001
            continue
        for pc in d.get("pickcenter") or []:
            h, a_ = (pc.get("homeTeamOdds") or {}).get("moneyLine"), (pc.get("awayTeamOdds") or {}).get("moneyLine")
            if h is not None and a_ is not None and abs(h) >= 100 and abs(a_) >= 100:
                fb.append((gid, float(h), float(a_), (pc.get("provider") or {}).get("name")))
                break
    fb = pd.DataFrame(fb, columns=["game_id", "fh", "fa", "fprov"])
    co = co.merge(fb, on="game_id", how="left")
    use_fb = co.h_close.isna() & co.fh.notna()
    co.loc[use_fb, "h_close"], co.loc[use_fb, "a_close"], co.loc[use_fb, "provider"] = co.fh, co.fa, co.fprov
    print(f"\ncollege closing lines from the summary fallback: {int(use_fb.sum())} games")

    ce = pd.read_csv(ML + "/cfb_engine_preds.csv", dtype={"game_id": str}).merge(co, on="game_id", how="left")
    cfb_e = prep(ce)
    report("COLLEGE ENGINE 2024-2026 (as it would have run)", cfb_e)
    for s in (2024, 2025, 2026):
        d = cfb_e[cfb_e.season == s]
        print(f"    {s}: {len(d)} games, picks {rec(d.won)}, favorite {((d.mkt >= .5) == (d.home_win == 1)).mean():.1%}, "
              f"ROI {roi(d.profit)}")

    cf = pd.read_csv(R + "prompt_cfb_backtest_2022_2025.csv", dtype={"game_id": str})
    c26 = pd.read_csv(R + "prompt_cfb_2026_out_of_sample.csv", dtype={"game_id": str})
    cf = pd.concat([cf.assign(set="backtest"), c26.assign(set="2026")], ignore_index=True)
    cf["home_win"] = np.where(cf.result > 0, 1.0, 0.0)
    cf = cf.merge(co, on="game_id", how="left")
    cfb_f = prep(cf)
    report("COLLEGE FRAMEWORK 2022-2026 (backtest + 2026 so far)", cfb_f)
    for s in sorted(cfb_f.season.unique()):
        d = cfb_f[cfb_f.season == s]
        print(f"    {s}: {len(d)} games, picks {rec(d.won)}, favorite {((d.mkt >= .5) == (d.home_win == 1)).mean():.1%}, "
              f"ROI {roi(d.profit)}")
    same = cfb_e.merge(cfb_f[["game_id"]], on="game_id")
    same_f = cfb_f[cfb_f.game_id.isin(same.game_id)]
    print(f"\n  same {len(same)} college games (2024-2026): engine {rec(same.won)} ROI {roi(same.profit)}; "
          f"framework {rec(same_f.won)} ROI {roi(same_f.profit)}")

    for name, d in (("nfl_engine", nfl_e), ("nfl_framework", nfl_f), ("cfb_engine", cfb_e), ("cfb_framework", cfb_f)):
        d.to_csv(f"{ML}/scored_{name}.csv", index=False)


if __name__ == "__main__":
    main()
