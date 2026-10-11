"""Run the NFL engine for one week.

  python3 nfl/run.py --season 2026 --week 6
  python3 nfl/run.py --season 2026 --week 6 --qb "SEA=Sam Darnold" --nopick "CHI=starter questionable"

Steps: download nflverse play-by-play (seasons season-4..season), backtest the
previous two seasons week by week to calibrate win probabilities, check this
season so far out of sample, then price the week's games that haven't been
played. Starting QBs come from nflverse's schedule file; check them against
the final injury reports and override with --qb TEAM=Full Name when they're
wrong. A starter with under 100 dropbacks over the last three seasons is an
automatic no-pick.
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

import download  # noqa: E402
import engine  # noqa: E402


def tiers(p, won):
    fav = np.maximum(p, 1 - p)
    out = []
    for lo, hi, label in [(0.5, 0.6, "under 60%"), (0.6, 0.7, "60-70%"), (0.7, 1.01, "70%+")]:
        m = (fav >= lo) & (fav < hi)
        out.append(f"{label}: {int(won[m].sum())}-{int(m.sum() - won[m].sum())}")
    return " | ".join(out)


def qb_lookup(data):
    """Full and short names -> nflverse player id, from the schedule file and play-by-play."""
    names = {}
    g = data.games
    for side in ("home", "away"):
        for n, i in zip(g[f"{side}_qb_name"], g[f"{side}_qb_id"]):
            if isinstance(n, str) and isinstance(i, str):
                names[n.lower()] = i
    for n, i in zip(data.db["passer"], data.db["passer_id"]):
        if isinstance(n, str):
            names.setdefault(n.lower(), i)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--cache", default=os.path.join(HERE, "cache"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--tz", default="America/Phoenix")
    ap.add_argument("--qb", action="append", default=[], metavar="TEAM=NAME",
                    help='override a starter, e.g. "SEA=Sam Darnold" (team abbreviations as nflverse uses them)')
    ap.add_argument("--nopick", action="append", default=[], metavar="TEAM=REASON")
    ap.add_argument("--neutral", action="append", default=[], metavar="GAME_ID", help="treat a game as neutral site")
    ap.add_argument("--skip-download", action="store_true")
    a = ap.parse_args()
    S, W = a.season, a.week
    os.makedirs(a.out, exist_ok=True)

    if not a.skip_download:
        print(f"[1/5] Downloading play-by-play {S - 4}-{S} and the schedule")
        download.get(a.cache, S)
    print("[2/5] Loading")
    data = engine.Data(a.cache, S)

    print(f"[3/5] Backtest {S - 2}-{S - 1} to calibrate")
    bt = pd.concat([engine.walk_forward(data, S - 2), engine.walk_forward(data, S - 1)], ignore_index=True)
    cal = engine.calibrate(bt)
    p_bt = engine.lowo(bt)
    won_bt = ((p_bt > 0.5) == (bt["home_win"] == 1)).astype(int).values
    print(f"      {len(bt)} games: {int(won_bt.sum())}-{int(len(won_bt) - won_bt.sum())} | {tiers(p_bt, won_bt)}")
    cur = engine.walk_forward(data, S, weeks=set(range(1, W)))
    if len(cur):
        p_cur = cal.predict_proba(cur[engine.FEATS])[:, 1]
        won_cur = ((p_cur > 0.5) == (cur["home_win"] == 1)).astype(int).values
        print(f"      {S} weeks 1-{W - 1} (out of sample): {int(won_cur.sum())}-{int(len(won_cur) - won_cur.sum())} | "
              f"{tiers(p_cur, won_cur)}")

    print(f"[4/5] Week {W} starters")
    G = data.games[(data.games["season"] == S) & (data.games["week"] == W) & data.games["result"].isna()].copy()
    if G.empty:
        print("No unplayed games that week.")
        return
    names = qb_lookup(data)
    overrides = {}
    for item in a.qb:
        team, _, nm = item.partition("=")
        pid = names.get(nm.strip().lower())
        if pid is None:
            sys.exit(f"Can't find a QB named '{nm}'. Use the full name as nflverse spells it (e.g. 'Sam Darnold').")
        overrides[team.strip().upper()] = (pid, nm.strip())
    last_start = {}
    st = data.starters.merge(data.games[["game_id", "season", "gameday"]], on="game_id")
    st = st[st["season"] == S].sort_values("gameday")
    for r in st.itertuples():
        last_start[r.posteam] = (r.passer_id, r.passer)
    rows = []
    for x in G.itertuples():
        for side, team in (("home", x.home_team), ("away", x.away_team)):
            qid, qname = getattr(x, f"{side}_qb_id"), getattr(x, f"{side}_qb_name")
            source = "schedule"
            if not isinstance(qid, str) and team in last_start:
                qid, qname = last_start[team]
                source = "last start"
            if team in overrides:
                qid, qname = overrides[team]
                source = "override"
            history = " > ".join(f"W{int(r.week)}:{r.passer}" for r in
                                 data.starters.merge(data.games[["game_id", "season", "week"]], on="game_id")
                                 .query("season == @S and posteam == @team").sort_values("week").itertuples())
            last = last_start.get(team, (None, ""))[0]
            rows.append({"game_id": x.game_id, "team": team, "qb_id": qid, "qb": qname, "source": source,
                         "dropbacks_3yr": data.dropbacks_before(qid, S, x.gameday) if isinstance(qid, str) else 0,
                         "differs_from_last_start": bool(last and qid != last), "history": history})
    qbs = pd.DataFrame(rows)

    print(f"[5/5] Picks for week {W}")
    Rt = engine.ratings(data, S, G["gameday"].min())
    tz = ZoneInfo(a.tz)
    picks = []
    for x in G.itertuples():
        hq = qbs[(qbs.game_id == x.game_id) & (qbs.team == x.home_team)].iloc[0]
        aq = qbs[(qbs.game_id == x.game_id) & (qbs.team == x.away_team)].iloc[0]
        neutral = engine.is_neutral(x._asdict()) or x.game_id in a.neutral
        f = engine.features(Rt, x.home_team, x.away_team, hq.qb_id, aq.qb_id, neutral, x.home_rest, x.away_rest)
        ph = float(cal.predict_proba(pd.DataFrame([f])[engine.FEATS])[:, 1][0])
        et = datetime.datetime.strptime(f"{x.gameday} {x.gametime}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/New_York"))
        status, reason = "PICK", ""
        short = [f"{q.qb} ({q.team}) has {q.dropbacks_3yr} dropbacks" for q in (hq, aq) if q.dropbacks_3yr < engine.MIN_DROPBACKS]
        if short:
            status, reason = "NO PICK", "; ".join(short) + f", under {engine.MIN_DROPBACKS}"
        for item in a.nopick:
            team, _, why = item.partition("=")
            if team.strip().upper() in (x.home_team, x.away_team):
                status, reason = "NO PICK", why.strip() or "manual no-pick"
        picks.append({"game_id": x.game_id, "kickoff": et.astimezone(tz).strftime("%a %I:%M %p").replace(" 0", " "),
                      "away": x.away_team, "home": x.home_team, "away_qb": aq.qb, "home_qb": hq.qb, "neutral": neutral,
                      **f, "p_home": ph, "pick": x.home_team if ph >= 0.5 else x.away_team,
                      "pick_prob": max(ph, 1 - ph), "status": status, "reason": reason})
    picks = pd.DataFrame(picks)
    path = os.path.join(a.out, f"nfl_{S}_week{W:02d}_picks.csv")
    picks.to_csv(path, index=False)
    qpath = os.path.join(a.out, f"nfl_{S}_week{W:02d}_qbs.csv")
    qbs.to_csv(qpath, index=False)

    made = picks[picks["status"] == "PICK"].sort_values("pick_prob", ascending=False)
    for lo, hi, label in [(0.6, 1.01, "Strongest (60%+)"), (0.55, 0.6, "Leans (55-60%)"), (0.0, 0.55, "Coin flips")]:
        sub = made[(made["pick_prob"] >= lo) & (made["pick_prob"] < hi)]
        if len(sub):
            print(f"\n  {label}")
            for r in sub.itertuples():
                opp = r.home if r.pick == r.away else r.away
                print(f"    {r.pick} over {opp}: {r.pick_prob:.0%}  ({r.kickoff}{', neutral site' if r.neutral else ''})")
    nop = picks[picks["status"] != "PICK"]
    if len(nop):
        print("\n  No pick")
        for r in nop.itertuples():
            print(f"    {r.away} at {r.home}: {r.reason}")
    check = qbs[qbs["differs_from_last_start"] | (qbs["source"] != "schedule")]
    print("\n  Starters used (check every one against the final injury report; flagged ones first):")
    for r in pd.concat([check, qbs.drop(check.index)]).itertuples():
        flag = " <- differs from last start" if r.differs_from_last_start else ""
        print(f"    {r.team}: {r.qb} [{r.source}, {r.dropbacks_3yr} dropbacks]{flag} | {r.history}")
    print(f"\nSaved {path} and {qpath}")


if __name__ == "__main__":
    main()
