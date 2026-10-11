"""NFL picks with the college football method (METHOD.md) and the NFL settings
the owner approved on 2026-10-11.

  python3 nfl_cfbmethod/run.py --date 2026-10-11 --date 2026-10-12
  python3 nfl_cfbmethod/run.py --date 2026-10-11 --nopick "Ravens=Lamar Jackson out"

It imports the college engine's own code (cfb/parse.py, cfb/epa.py,
cfb/engine.py, cfb/qbs.py) without editing it. Same inputs, plays, expected
points, ratings, features and quarterback rule. Plumbing differs (ESPN's NFL
feed, weeks 1-18, team nicknames), plus the NFL settings the owner approved on
2026-10-11 (nfl_engine.py):

  - ridge penalty 500 instead of 50
  - last season weighted 30% instead of 70%
  - recency: within a season, plays count half as much for every 5 weeks older
  - win chances calibrated on every season's week-by-week replay since 2019
    (weeks 4-18, about 1,500 games) instead of last season's weeks 4-8

All were chosen on a 2019-2025 backtest (see METHOD.md). Quarterback
availability is checked by hand, as for college: rerun with --nopick for any
game whose regular starter is out or unconfirmed. Closing lines are never an
input; grade.py uses them only to grade picks after they lock.
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFB = os.path.join(ROOT, "cfb")
sys.path.insert(0, CFB)
sys.path.insert(0, HERE)  # NFL download.py first; everything else comes from cfb/

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

import download  # noqa: E402  (nfl_cfbmethod/download.py)
import engine  # noqa: E402    (cfb/engine.py)
import epa  # noqa: E402       (cfb/epa.py)
import parse  # noqa: E402     (cfb/parse.py)
import qbs  # noqa: E402       (cfb/qbs.py)
import nfl_engine  # noqa: E402  (nfl_cfbmethod/nfl_engine.py)

assert os.path.dirname(download.__file__) == HERE and os.path.dirname(engine.__file__) == CFB

# Approved NFL settings (owner, 2026-10-11). cfb/engine.py itself is not edited.
NFL_ALPHA = 500
NFL_RHO = 0.30
HALF_LIFE = 5      # weeks
CAL_START = 2019   # calibrate on every season from 2019 through last season


def calibrate(bt):
    return LogisticRegression(C=1e6, max_iter=1000, fit_intercept=False).fit(bt[engine.FEATS], bt["home_win"])


def leave_one_season_out(bt):
    p = np.zeros(len(bt))
    for s in bt["season"].unique():
        tr, te = bt["season"] != s, bt["season"] == s
        p[te.values] = calibrate(bt[tr]).predict_proba(bt.loc[te, engine.FEATS])[:, 1]
    return p


def tiers(p, won):
    fav = np.maximum(p, 1 - p)
    out = []
    for lo, hi, label in [(0.5, 0.6, "under 60%"), (0.6, 0.7, "60-70%"), (0.7, 1.01, "70%+")]:
        m = (fav >= lo) & (fav < hi)
        out.append(f"{label}: {int(won[m].sum())}-{int(m.sum() - won[m].sum())}")
    return " | ".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", action="append", required=True, help="YYYY-MM-DD; repeat for a Sunday + Monday slate")
    ap.add_argument("--cache", default=os.path.join(HERE, "cache"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--tz", default="America/Phoenix")
    ap.add_argument("--nopick", action="append", default=[], metavar="TEAM=REASON",
                    help='team nickname, e.g. "Ravens=Lamar Jackson out"')
    a = ap.parse_args()
    day = datetime.date.fromisoformat(a.date[0])
    season = day.year if day.month >= 7 else day.year - 1
    first_season = CAL_START - 1  # the oldest backtest season needs the season before it
    os.makedirs(a.cache, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)

    print(f"[1/6] Games on {', '.join(a.date)}")
    slate, week = [], None
    for d in a.date:
        g, w = download.slate(a.cache, d)
        slate += [x for x in g if x["state"] == "pre"]
        week = week or w
    if not slate:
        print("No games left to price.")
        return
    first_kick = min(g["kickoff_utc"] for g in slate)

    print(f"[2/6] Play-by-play for {first_season}-{season}")
    rows = []
    for s in range(first_season, season + 1):
        rows += download.final_games(a.cache, s, refresh=(s == season))
    rows = [r for r in rows if r[3] < first_kick]
    fetched, errors = download.summaries(a.cache, [r[0] for r in rows])
    print(f"      {len(rows)} finished games ({fetched} newly downloaded, {len(errors)} failed)")
    if errors:
        print("      failed:", errors[:5])

    print("[3/6] Parsing")
    games, plays, passers, perrs = parse.parse(os.path.join(a.cache, "summary"), rows)
    if perrs:
        print(f"      {len(perrs)} games could not be parsed, e.g. {perrs[:3]}")

    print("[4/6] Expected points and EPA")
    sc = engine.prepare(epa.build(plays, games))

    cal_seasons = list(range(CAL_START, season))
    print(f"[5/6] Backtest {cal_seasons[0]}-{cal_seasons[-1]} (weeks 4-18) to calibrate")
    bt = pd.concat([nfl_engine.walk_forward(sc, games, s, range(4, 19), NFL_ALPHA, NFL_RHO, HALF_LIFE)
                    for s in cal_seasons], ignore_index=True)
    cal = calibrate(bt)
    p = leave_one_season_out(bt)
    won = ((p > 0.5) == (bt["home_win"] == 1)).astype(int).values
    print(f"      calibrated on {len(bt)} games; coefficients {dict(zip(engine.FEATS, np.round(cal.coef_[0], 3)))}")
    print(f"      backtest (each season graded with the other seasons' calibration): {int(won.sum())}-{int(len(won) - won.sum())} | {tiers(p, won)}")
    print("        by season: " + ", ".join(f"{s} {int(won[(bt['season'] == s).values].sum())}-"
                                         f"{int((bt['season'] == s).sum() - won[(bt['season'] == s).values].sum())}"
                                         for s in cal_seasons))
    early = bt["week"].between(4, 8).values
    print(f"      weeks 4-8 only: {int(won[early].sum())}-{int(early.sum() - won[early].sum())} | {tiers(p[early], won[early])}")
    cur = nfl_engine.walk_forward(sc, games, season, range(4, (week or 4)), NFL_ALPHA, NFL_RHO, HALF_LIFE)
    if len(cur):
        p_cur = cal.predict_proba(cur[engine.FEATS])[:, 1]
        won_cur = ((p_cur > 0.5) == (cur["home_win"] == 1)).astype(int).values
        print(f"      {season} so far (out of sample): {int(won_cur.sum())}-{int(len(won_cur) - won_cur.sum())} | {tiers(p_cur, won_cur)}")

    print("[6/6] Picks")
    picks = nfl_engine.predict(sc, season, int(week), slate, cal, NFL_ALPHA, NFL_RHO, HALF_LIFE)
    for item in a.nopick:
        team, _, reason = item.partition("=")
        m = (picks["home_name"].str.lower() == team.strip().lower()) | (picks["away_name"].str.lower() == team.strip().lower())
        if not m.any():
            print(f"      warning: --nopick team '{team}' isn't on the slate")
        picks.loc[m, "status"] = "NO PICK"
        picks.loc[m, "reason"] = reason.strip() or "manual no-pick"
    tz = ZoneInfo(a.tz)
    picks["kickoff"] = [datetime.datetime.strptime(k, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc)
                        .astimezone(tz).strftime("%a %I:%M %p").replace(" 0", " ") for k in picks["kickoff_utc"]]
    tag = f"{season}_week{int(week):02d}" if week else a.date[0]
    path = os.path.join(a.out, f"nfl_cfbmethod_{tag}_picks.csv")
    picks.to_csv(path, index=False)
    qrep = qbs.report(passers, games, season, slate)
    qpath = os.path.join(a.out, f"nfl_cfbmethod_{tag}_qbs.csv")
    qrep.to_csv(qpath, index=False)

    made = picks[picks["status"] == "PICK"].sort_values("pick_prob", ascending=False)
    for lo, hi, label in [(0.7, 1.01, "Strongest (70%+)"), (0.6, 0.7, "Leans (60-70%)"), (0.0, 0.6, "Coin flips (under 60%)")]:
        sub = made[(made["pick_prob"] >= lo) & (made["pick_prob"] < hi)]
        if len(sub):
            print(f"\n  {label}")
            for r in sub.itertuples():
                opp = r.home_name if r.pick == r.away_name else r.away_name
                print(f"    {r.pick} over {opp}: {r.pick_prob:.1%}  ({r.kickoff}{', neutral site' if r.neutral else ''})")
    nop = picks[picks["status"] != "PICK"]
    if len(nop):
        print("\n  No pick")
        for r in nop.itertuples():
            print(f"    {r.away_name} at {r.home_name}: {r.reason}")
    print("\n  QB history (check every flagged team in the news; rerun with --nopick if the starter is out or unconfirmed):")
    for r in qrep.itertuples():
        print(f"    {r.team}: {r.flag or 'ok'} | starters {getattr(r, 'starters_by_game', '')}")
    print(f"\nSaved {path} and {qpath}")


if __name__ == "__main__":
    main()
