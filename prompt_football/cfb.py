#!/usr/bin/env python3
"""Prompt Football, scored with real numbers (college football).

The college version of prompt_football/nfl.py, built at the owner's request on
2026-10-11. Same five criteria, same weights, same scaling, same week-by-week
replay and the same calibration. Every number comes from the ESPN play-by-play
the college engine already uses (cfb/download.py, cfb/parse.py, cfb/epa.py and
cfb/qbs.py are imported unchanged):

  1. Trench dominance   25%  sack rate per dropback and line yards per run,
                             offense vs defense
  2. Net efficiency     25%  EPA per play, offense vs defense
  3. Passing matchups   20%  the starting QB's EPA per dropback against what the
                             defense allows per dropback
  4. Situational        15%  home field and rest days, turned into points from
                             past results (2019 and 2021-2025)
  5. High leverage      15%  third-down conversion rate, red-zone touchdown rate
                             per trip, turnover margin per game

Where the college data forces a difference from the NFL version (nothing else
changes):
  - No QB-hit data in the college feed: pressure is sacks per dropback (NFL:
    sacks + QB hits).
  - No blitz charting: the passing matchup uses all dropbacks together. This is
    the NFL formula with one bucket instead of blitz / no blitz.
  - Scrambles are logged as runs, so they count in line yards, not dropbacks.
  - Overtime drives (college overtime starts at the 25) are left out of
    red-zone trips.
  - No weather in the college feed, so the predicted total has no wind term.
  - Home field and rest are fitted on conference games. Non-conference college
    games are mostly strong teams hosting weaker ones, which would count team
    strength as home field; conference schedules are balanced like the NFL's.
  - Weeks 4-15 (the college regular season, as in the college engine).
  - A team needs 150 non-garbage offensive plays this season (the college
    engine's rule), else no pick.

Each criterion is a home-minus-away matchup number, scaled so a typical game is
1, then weighted 25/25/20/15/15. A week-by-week replay of 2022-2025 (weeks 4-15,
every team rated only from its earlier games that season) turns the weighted
score into a win chance, a margin and a total. Final scores are only the target.
No betting lines, records or points scored go in.

This is separate from the locked engines in METHOD.md.

  python3 prompt_football/cfb.py --date 2026-10-13 --date 2026-10-14
  python3 prompt_football/cfb.py --date 2026-10-16 --nopick "Washington=starting QB unconfirmed"
  python3 prompt_football/cfb.py --date 2026-10-16 --starter "Washington=Demond Williams Jr."
"""
import argparse
import datetime
import json
import math
import os
import re
import sys
from multiprocessing import Pool
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFB = os.path.join(ROOT, "cfb")
sys.path.insert(0, CFB)

import download  # noqa: E402  (cfb/download.py)
import engine  # noqa: E402    (cfb/engine.py, for MIN_PLAYS only)
import epa  # noqa: E402       (cfb/epa.py, the college engine's expected points)
import parse  # noqa: E402     (cfb/parse.py)
import qbs  # noqa: E402       (cfb/qbs.py)

assert os.path.dirname(epa.__file__) == CFB and os.path.dirname(parse.__file__) == CFB

WEIGHTS = {"trench": 0.25, "net_eff": 0.25, "passing": 0.20, "situational": 0.15, "leverage": 0.15}
BT_SEASONS = [2022, 2023, 2024, 2025]
SIT_SEASONS = [2019, 2021, 2022, 2023, 2024, 2025]  # 2020 left out, as in the NFL version
BT_WEEKS = range(4, 16)
K = dict(play=100, db=100, run=60, third=30, rz=8, games=2)  # NFL values; db = the NFL's blitz 40 + no-blitz 60
INT_TYPES = {"Pass Interception Return", "Interception", "Interception Return Touchdown"}
FUM_LOST = {"Fumble Recovery (Opponent)", "Fumble Return Touchdown"}
OFF_TD = {"Passing Touchdown", "Rushing Touchdown"}
SUBS = ["tp", "tr", "ne", "pm", "h3", "hr", "ht"]
EASTERN = ZoneInfo("America/New_York")


def rms(x):
    return float(np.sqrt(np.mean(np.square(np.asarray(x, float)))))


def rate(s, n, lg, k):
    return (s + k * lg) / (n + k)


# ---------------------------------------------------------------- schedule

def scoreboard_games(cache, seasons, current):
    """Every final regular-season game on ESPN's FBS scoreboards (weeks 1-16)."""
    out = []
    for s in seasons:
        download.final_games(cache, s, refresh=(s == current))  # caches the weekly scoreboards
        for w in range(1, 17):
            path = os.path.join(cache, "scoreboard", f"{s}_w{w}.json")
            if not os.path.exists(path):
                continue
            for e in json.load(open(path)).get("events", []):
                if e["status"]["type"]["state"] != "post":
                    continue
                c = e["competitions"][0]
                t = {x["homeAway"]: x for x in c["competitors"]}
                out.append({"game_id": e["id"], "season": s, "week": w, "kickoff_utc": e["date"],
                            "home_id": str(t["home"]["team"]["id"]), "away_id": str(t["away"]["team"]["id"]),
                            "home_score": int(t["home"].get("score") or 0), "away_score": int(t["away"].get("score") or 0),
                            "neutral": bool(c.get("neutralSite", False)),
                            "conference": bool(c.get("conferenceCompetition", False))})
    return pd.DataFrame(out).drop_duplicates("game_id").reset_index(drop=True)


def rest_days(g):
    """Days since each team's previous game that season (US Eastern dates). NaN for a team's first game."""
    side = []
    for s in ("home", "away"):
        x = g[["game_id", "season", "kickoff_utc", f"{s}_id"]].rename(columns={f"{s}_id": "team"})
        side.append(x.assign(side=s))
    t = pd.concat(side, ignore_index=True)
    day = pd.to_datetime(t.kickoff_utc, utc=True).dt.tz_convert(EASTERN).dt.date
    t["day"] = [d.toordinal() for d in day]
    t = t.sort_values(["team", "season", "day"])
    t["rest"] = t.day - t.groupby(["team", "season"]).day.shift(1)
    r = t.pivot_table(index="game_id", columns="side", values="rest", aggfunc="first")
    return r.reindex(columns=["home", "away"])


def add_rest(g, history=None):
    """rest_diff = home rest minus away rest, a missing rest counted as 7, clipped to +-7 (as in the NFL version)."""
    allg = g if history is None else pd.concat([history, g], ignore_index=True)
    r = rest_days(allg.drop_duplicates("game_id"))
    g = g.copy()
    g["home_rest"] = g.game_id.map(r["home"])
    g["away_rest"] = g.game_id.map(r["away"])
    g["rest_diff"] = np.clip(g.home_rest.fillna(7) - g.away_rest.fillna(7), -7, 7).astype(float)
    return g


def sit_fit(sb, seasons):
    """Points for home field and per rest day, from conference games (no intercept, as in the NFL version)."""
    s = sb[sb.season.isin(seasons) & sb.conference]
    X = np.column_stack([np.where(s.neutral, 0.0, 1.0), s.rest_diff.to_numpy(float)])
    beta, *_ = np.linalg.lstsq(X, (s.home_score - s.away_score).to_numpy(float), rcond=None)
    return beta


# ------------------------------------------------------------------- plays

SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\.?$", re.I)
PASS_FROM = re.compile(r"pass from (.+?)(?:\s*\(|$)", re.I)
VERB = re.compile(r"\b(pass|sacked|sack)\b")


def last_name(n):
    n = SUFFIX.sub("", str(n).strip()).strip().rstrip(",")
    parts = n.split()
    return parts[-1].lower() if parts else ""


def name_passers(db, passers):
    """Name the passer on every dropback: the team's passer (box score) whose last name comes
    before 'pass'/'sacked' in the play text, else the one named after 'pass from', else that
    game's main passer (most attempts)."""
    pas = passers[passers.att.fillna(0) > 0].copy()
    pas["last"] = pas.name.map(last_name)
    pas = pas.sort_values("att", ascending=False)
    cands = {k: list(zip(v.name, v["last"])) for k, v in pas.groupby(["game_id", "team_id"], sort=False)}
    out = []
    for gid, tid, txt in zip(db.game_id.values, db.off.values, db.text.fillna("").values):
        c = cands.get((gid, tid), [])
        low = txt.lower()
        cut = VERB.search(low)
        head = low[:cut.start()] if cut else low
        hit = sorted((head.find(ln), nm) for nm, ln in c if ln and re.search(r"\b" + re.escape(ln) + r"\b", head))
        if not hit:
            m = PASS_FROM.search(txt)
            if m:
                tail = m.group(1).lower()
                hit = [(0, nm) for nm, ln in c if ln and re.search(r"\b" + re.escape(ln) + r"\b", tail)]
        out.append(hit[0][1] if hit else (c[0][0] if c else ""))
    return np.array(out, dtype=object)


def scrimmage(plays, games):
    """The college engine's scrimmage plays and EPA (cfb/epa.py, unchanged), with the play details
    the framework needs. epa.build returns plays sorted by game and sequence; the same filter is
    applied here and the two tables are checked to line up row for row."""
    e = epa.build(plays, games)
    p = plays.merge(games[["game_id", "season", "week", "date", "home_id", "away_id", "neutral"]], on="game_id", how="inner")
    p = p.sort_values(["game_id", "seq"]).reset_index(drop=True)
    half = np.where(p["period"] <= 2, 1, np.where(p["period"] <= 4, 2, 3))
    s = p[(p["type"].isin(epa.PASS | epa.RUSH | epa.FUMB)) & (p["s_down"].between(1, 4)) & (half <= 2)]
    s = s[(s["s_ytg"] > 0) & (s["s_ytg"] < 100) & (s["s_dist"] > 0)]
    s = s[(s["s_team"] == s["home_id"]) | (s["s_team"] == s["away_id"])]
    s = s.sort_values(["game_id", "seq"]).reset_index(drop=True)
    s["is_pass"] = s["type"].isin(epa.PASS) | (s["type"].isin(epa.FUMB) & s["text"].str.contains(r"pass|sack", case=False, regex=True))
    if not (len(s) == len(e) and (s.game_id.values == e.game_id.values).all() and (s.s_team.values == e.off.values).all()
            and (s.is_pass.values == e.is_pass.values).all() and (s.week.values == e.week.values).all()):
        raise SystemExit("play table and EPA table don't line up; stopping rather than guessing")
    s["off"], s["def"] = e["off"].values, e["def"].values
    s["epa"], s["garbage"] = e["epa"].values, e["garbage"].values
    txt = s["text"].fillna("")
    s["kneel"] = ~s.is_pass & txt.str.contains(r"\bkneel", case=False, regex=True)
    s["spike"] = s.is_pass & txt.str.contains(r"\bspiked?\b", case=False, regex=True)
    s["yds"] = pd.to_numeric(s["yards"], errors="coerce").fillna(0.0)
    s["sack"] = (s["type"] == "Sack") | (s["type"].isin(epa.FUMB) & txt.str.contains("sack", case=False))
    s["giveaway"] = s["type"].isin(INT_TYPES | FUM_LOST) | (s["turnover"].astype(bool) & s["type"].isin(epa.FUMB))
    s["off_td"] = s["type"].isin(OFF_TD)
    return s


def _drives_one(args):
    folder, gid = args
    try:
        d = json.load(open(os.path.join(folder, f"{gid}.json")))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for dv in (d.get("drives") or {}).get("previous") or []:
        team = str((dv.get("team") or {}).get("id", ""))
        pl = dv.get("plays") or []
        if not team or not pl:
            continue
        period = (pl[0].get("period") or {}).get("number") or 0
        ytg = [(p.get("start") or {}).get("yardsToEndzone") for p in pl
               if str(((p.get("start") or {}).get("team") or {}).get("id", "")) == team]
        ytg = [y for y in ytg if isinstance(y, (int, float)) and 0 < y < 100]
        res, disp = str(dv.get("result") or "").strip().upper(), str(dv.get("displayResult") or "").strip().lower()
        out.append({"game_id": gid, "team": team, "period": period, "min_ytg": min(ytg) if ytg else np.nan,
                    "td": float(res == "TD" or disp == "touchdown")})
    return out


def drives(summary_dir, game_ids):
    with Pool(max(1, min(4, os.cpu_count() or 1))) as pool:
        res = pool.map(_drives_one, [(summary_dir, g) for g in game_ids], chunksize=20)
    return pd.DataFrame([r for x in res for r in x])


def team_games(s, drv, passers):
    """Per team per game sums (offense o_*, defense d_*), plus quarterback rows."""
    np_ = s[~s.garbage].groupby(["game_id", "off"]).size().rename("o_np")  # the college engine's play count
    x = s[~s.garbage & ~s.kneel & ~s.spike]
    db = x.is_pass.to_numpy()
    run = ~db
    y = x.yds.to_numpy(float)
    ly = np.where(y < 0, 1.2 * y, np.where(y <= 4, y, np.where(y <= 10, 4 + 0.5 * (y - 4), 7.0)))
    third = x.s_down.eq(3).to_numpy()
    to = x.giveaway.to_numpy()
    conv = third & ~to & ((y >= x.s_dist.to_numpy(float)) | x.off_td.to_numpy())
    e = x.epa.to_numpy(float)
    v = pd.DataFrame({
        "season": x.season.to_numpy(), "week": x.week.to_numpy(), "date": x.date.to_numpy(),
        "game_id": x.game_id.to_numpy(), "off": x.off.to_numpy(), "def": x["def"].to_numpy(),
        "n": 1.0, "epa": e, "n_db": db * 1.0, "epa_db": np.where(db, e, 0.0), "press": (db & x.sack.to_numpy()) * 1.0,
        "n_run": run * 1.0, "ly": np.where(run, ly, 0.0),
        "n_3rd": third * 1.0, "c_3rd": (third & conv) * 1.0, "to": to * 1.0,
    })
    keys = ["season", "week", "date", "game_id"]
    num = [c for c in v.columns if c not in keys + ["off", "def"]]
    o = v.groupby(keys + ["off"])[num].sum().add_prefix("o_").reset_index().rename(columns={"off": "team"})
    d = v.groupby(keys + ["def"])[num].sum().add_prefix("d_").reset_index().rename(columns={"def": "team"})
    tg = o.merge(d, on=keys + ["team"], how="outer").fillna(0.0)

    # red-zone trips: regulation drives that reached the opponent's 20; touchdowns on those drives
    dr = drv[(drv.period <= 4) & (drv.min_ytg <= 20)]
    rz = dr.groupby(["game_id", "team"]).agg(rz=("td", "size"), rztd=("td", "sum")).reset_index()
    pair = tg[["game_id", "team"]]
    opp = pair.merge(pair, on="game_id", suffixes=("", "_opp"))
    opp = opp[opp.team != opp.team_opp]
    rz_o = rz.rename(columns={"rz": "o_rz", "rztd": "o_rztd"})
    rz_d = rz.rename(columns={"team": "team_opp", "rz": "d_rz", "rztd": "d_rztd"}).merge(
        opp, on=["game_id", "team_opp"])[["game_id", "team", "d_rz", "d_rztd"]]
    tg = tg.merge(rz_o, on=["game_id", "team"], how="left").merge(rz_d, on=["game_id", "team"], how="left")
    tg = tg.merge(np_.reset_index().rename(columns={"off": "team"}), on=["game_id", "team"], how="left").fillna(0.0)
    tg["games"] = 1.0

    # quarterbacks (dropbacks by the named passer, sacks included)
    q = x[db].copy()
    q["name"] = name_passers(q, passers)
    q = q[q.name != ""]
    qv = pd.DataFrame({"season": q.season.to_numpy(), "week": q.week.to_numpy(), "date": q.date.to_numpy(),
                       "game_id": q.game_id.to_numpy(), "team": q.off.to_numpy(),
                       "qb": (q.off + "|" + q.name).to_numpy(), "name": q.name.to_numpy(),
                       "n_db": 1.0, "epa_db": q.epa.to_numpy(float)})
    qg = qv.groupby(["season", "week", "date", "game_id", "team", "qb"]).agg(
        name=("name", "first"), n_db=("n_db", "sum"), epa_db=("epa_db", "sum")).reset_index()
    return tg, qg


def snapshot(tg, qg):
    """Team rates from the given games (one season, earlier games only), shrunk toward the league."""
    a = tg.groupby("team").sum(numeric_only=True)
    L = a.sum()
    lg = {"epa": L.o_epa / L.o_n, "db": L.o_epa_db / L.o_n_db, "press": L.o_press / L.o_n_db,
          "ly": L.o_ly / L.o_n_run, "third": L.o_c_3rd / L.o_n_3rd, "rz": L.o_rztd / L.o_rz,
          "to": L.o_to / L.games}
    T = pd.DataFrame(index=a.index)
    for side, pre in (("off", "o_"), ("def", "d_")):
        T[f"{side}_epa"] = rate(a[pre + "epa"], a[pre + "n"], lg["epa"], K["play"])
        T[f"{side}_db"] = rate(a[pre + "epa_db"], a[pre + "n_db"], lg["db"], K["db"])
        T[f"{side}_press"] = rate(a[pre + "press"], a[pre + "n_db"], lg["press"], K["db"])
        T[f"{side}_ly"] = rate(a[pre + "ly"], a[pre + "n_run"], lg["ly"], K["run"])
        T[f"{side}_3rd"] = rate(a[pre + "c_3rd"], a[pre + "n_3rd"], lg["third"], K["third"])
        T[f"{side}_rz"] = rate(a[pre + "rztd"], a[pre + "rz"], lg["rz"], K["rz"])
        T[f"{side}_to"] = rate(a[pre + "to"], a.games, lg["to"], K["games"])
    T["n_plays"] = a.o_np
    raw = pd.DataFrame(index=a.index)          # unshrunk, for display
    raw["games"] = a.games
    with np.errstate(divide="ignore", invalid="ignore"):
        for side, pre in (("off", "o_"), ("def", "d_")):
            raw[f"{side}_epa"] = a[pre + "epa"] / a[pre + "n"]
            raw[f"{side}_db"] = a[pre + "epa_db"] / a[pre + "n_db"]
            raw[f"{side}_press"] = a[pre + "press"] / a[pre + "n_db"]
            raw[f"{side}_ly"] = a[pre + "ly"] / a[pre + "n_run"]
            raw[f"{side}_3rd"] = a[pre + "c_3rd"] / a[pre + "n_3rd"]
            raw[f"{side}_rz"] = a[pre + "rztd"] / a[pre + "rz"]
            raw[f"{side}_rz_trips"] = a[pre + "rz"]
    raw["giveaways"] = a.o_to
    raw["takeaways"] = a.d_to
    raw["to_margin_pg"] = (a.d_to - a.o_to) / a.games
    q = qg.groupby("qb").agg(name=("name", "last"), team=("team", "last"), n_db=("n_db", "sum"), epa_db=("epa_db", "sum"))
    q["db"] = rate(q.epa_db, q.n_db, lg["db"], K["db"])
    return T, raw, q, lg


def matchup(T, q, lg, h, a, qb_h, qb_a):
    H, A = T.loc[h], T.loc[a]

    def qb_rate(qb):           # unknown or brand-new QB -> league average
        return q.at[qb, "db"] if qb is not None and qb in q.index else lg["db"]

    eh = qb_rate(qb_h) + A.def_db - lg["db"]
    ea = qb_rate(qb_a) + H.def_db - lg["db"]
    return {
        "tp": (A.off_press - H.off_press) + (H.def_press - A.def_press),
        "tr": (H.off_ly - A.off_ly) + (A.def_ly - H.def_ly),
        "ne": (H.off_epa - A.off_epa) + (A.def_epa - H.def_epa),
        "pm": eh - ea, "pass_exp_home": eh, "pass_exp_away": ea,
        "h3": (H.off_3rd - A.off_3rd) + (A.def_3rd - H.def_3rd),
        "hr": (H.off_rz - A.off_rz) + (A.def_rz - H.def_rz),
        "ht": (H.def_to - H.off_to) - (A.def_to - A.off_to),
        "epa_sum": (H.off_epa + A.def_epa) + (A.off_epa + H.def_epa) - 2 * lg["epa"],
    }


def enough(T, *teams):
    return all(t in T.index and T.at[t, "n_plays"] >= engine.MIN_PLAYS for t in teams)


def build_rows(tg, qg, sched, season, weeks):
    """Replay finished games week by week; each team rated only from its earlier games that season."""
    starters = qg.sort_values("n_db").groupby(["game_id", "team"]).tail(1).set_index(["game_id", "team"]).qb
    rows = []
    for wk in weeks:
        gw = sched[(sched.season == season) & (sched.week == wk)]
        if gw.empty:
            continue
        T, raw, q, lg = snapshot(tg[(tg.season == season) & (tg.week < wk)], qg[(qg.season == season) & (qg.week < wk)])
        for r in gw.itertuples():
            h, a = r.home_id, r.away_id
            if not enough(T, h, a):
                continue
            f = matchup(T, q, lg, h, a, starters.get((r.game_id, h)), starters.get((r.game_id, a)))
            f.update(season=season, week=wk, game_id=r.game_id, home_id=h, away_id=a, home_name=r.home_name,
                     away_name=r.away_name, result=float(r.home_score - r.away_score),
                     total=float(r.home_score + r.away_score), home_sit=0.0 if r.neutral else 1.0,
                     rest_diff=r.rest_diff, qb_home=starters.get((r.game_id, h)), qb_away=starters.get((r.game_id, a)))
            rows.append(f)
    return pd.DataFrame(rows)


# ------------------------------------------------------------ scoring/fit

def add_scores(df, scale):
    df = df.copy()
    df["trench_raw"] = df["tp"] / scale["tp"] + df["tr"] / scale["tr"]
    df["leverage_raw"] = df["h3"] / scale["h3"] + df["hr"] / scale["hr"] + df["ht"] / scale["ht"]
    df["z_trench"] = df["trench_raw"] / scale["trench_raw"]
    df["z_net_eff"] = df["ne"] / scale["ne"]
    df["z_passing"] = df["pm"] / scale["pm"]
    df["z_situational"] = df["sit"] / scale["sit"]
    df["z_leverage"] = df["leverage_raw"] / scale["leverage_raw"]
    df["S"] = sum(WEIGHTS[k] * df[f"z_{k}"] for k in WEIGHTS)
    return df


def fit_cal(d):
    d = d[d.result.notna() & (d.result != 0)]
    a = float((d.S * d.result).sum() / (d.S ** 2).sum())
    lr = LogisticRegression(fit_intercept=False, C=1e6).fit(d[["S"]], (d.result > 0).astype(int))
    X = np.column_stack([np.ones(len(d)), d.epa_sum])
    tb, *_ = np.linalg.lstsq(X, d.total.to_numpy(float), rcond=None)
    return a, lr, tb


def apply_cal(d, a, lr, tb):
    d = d.copy()
    d["p_home"] = lr.predict_proba(d[["S"]])[:, 1]
    d["margin_hat"] = a * d.S
    d["total_hat"] = tb[0] + tb[1] * d.epa_sum
    for k in WEIGHTS:
        d[f"pts_{k}"] = a * WEIGHTS[k] * d[f"z_{k}"]
    return d


def record(d, col="p_home"):
    d = d[d.result.notna() & (d.result != 0)]
    win = (d[col] >= 0.5) == (d.result > 0)
    return int(win.sum()), int((~win).sum())


def kickoff_local(k, tz):
    t = datetime.datetime.strptime(k, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc).astimezone(tz)
    return t.strftime("%a %I:%M %p").replace(" 0", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", action="append", required=True, help="YYYY-MM-DD (repeat for several days)")
    ap.add_argument("--cache", default=os.path.join(CFB, "cache"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    ap.add_argument("--tz", default="America/Phoenix")
    ap.add_argument("--starter", action="append", default=[], help='"Team=Full Name": overrides the expected starter')
    ap.add_argument("--nopick", action="append", default=[], help='"Team=reason"')
    args = ap.parse_args()
    dates = sorted(args.date)
    d0 = datetime.date.fromisoformat(dates[0])
    S = d0.year if d0.month >= 7 else d0.year - 1
    tz = ZoneInfo(args.tz)
    os.makedirs(args.cache, exist_ok=True)

    slates = {}
    for dt in dates:
        sl, wk = download.slate(args.cache, dt)
        slates[dt] = ([g for g in sl if g["state"] == "pre"], wk)
    first_kick = min((g["kickoff_utc"] for sl, _ in slates.values() for g in sl), default=None)
    if first_kick is None:
        print("No games left to price on those dates.")
        return

    print(f"[1/5] Schedules {min(SIT_SEASONS)}-{S} and play-by-play {BT_SEASONS[0]}-{S}")
    sb = scoreboard_games(args.cache, SIT_SEASONS + [S], S)
    sb = add_rest(sb)
    rows = []
    for s in BT_SEASONS + [S]:
        rows += download.final_games(args.cache, s, refresh=False)
    rows = [r for r in rows if r[3] < first_kick]
    fetched, errors = download.summaries(args.cache, [r[0] for r in rows])
    print(f"      {len(rows)} finished games ({fetched} newly downloaded, {len(errors)} failed)")
    games, plays, passers, perrs = parse.parse(os.path.join(args.cache, "summary"), rows)
    if perrs:
        print(f"      {len(perrs)} games could not be parsed, e.g. {perrs[:3]}")
    games = games.merge(sb[["game_id", "rest_diff"]], on="game_id", how="left")
    games["rest_diff"] = games.rest_diff.fillna(0.0)

    print("[2/5] Expected points (the college engine's model) and play details")
    s_ = scrimmage(plays, games)
    drv = drives(os.path.join(args.cache, "summary"), games.game_id.tolist())
    tg, qg = team_games(s_, drv, passers)

    print(f"[3/5] Replay {BT_SEASONS[0]}-{BT_SEASONS[-1]}, weeks {BT_WEEKS[0]}-{BT_WEEKS[-1]}")
    bt = []
    for s in BT_SEASONS:
        r = build_rows(tg, qg, games, s, BT_WEEKS)
        beta = sit_fit(sb, [x for x in SIT_SEASONS if x != s])
        r["sit"] = r[["home_sit", "rest_diff"]].to_numpy(float) @ beta
        bt.append(r)
    bt = pd.concat(bt, ignore_index=True)
    scale = {c: rms(bt[c]) for c in SUBS + ["sit"]}
    scale["trench_raw"] = rms(bt["tp"] / scale["tp"] + bt["tr"] / scale["tr"])
    scale["leverage_raw"] = rms(bt["h3"] / scale["h3"] + bt["hr"] / scale["hr"] + bt["ht"] / scale["ht"])
    bt = add_scores(bt, scale)
    out = []
    for s in BT_SEASONS:
        a, lr, tb = fit_cal(bt[bt.season != s])
        out.append(apply_cal(bt[bt.season == s], a, lr, tb))
    bt = pd.concat(out, ignore_index=True)
    a, lr, tb = fit_cal(bt)
    beta_all = sit_fit(sb, SIT_SEASONS)
    sb_all = sb[sb.season.isin(SIT_SEASONS)]
    beta_every = np.linalg.lstsq(np.column_stack([np.where(sb_all.neutral, 0.0, 1.0), sb_all.rest_diff]),
                                 (sb_all.home_score - sb_all.away_score).to_numpy(float), rcond=None)[0]

    print(f"      situational points (conference games 2019, 2021-25): home field {beta_all[0]:+.2f}, "
          f"per rest day {beta_all[1]:+.2f}  [all games, for comparison: home {beta_every[0]:+.2f}]")
    print(f"      margin = {a:.2f} x weighted score; total = {tb[0]:.1f} + {tb[1]:.1f} x EPA sum")
    w_, l_ = record(bt)
    br = ((bt.p_home - (bt.result > 0)) ** 2)[bt.result != 0].mean()
    print(f"      backtest (each season calibrated on the others): {w_}-{l_} ({w_ / (w_ + l_):.1%}), Brier {br:.4f}")
    bt["pick_p"] = np.maximum(bt.p_home, 1 - bt.p_home)
    for lo, hi, lab in ((0.7, 1.01, "70%+"), (0.6, 0.7, "60-70%"), (0.5, 0.6, "under 60%")):
        ww, ll = record(bt[(bt.pick_p >= lo) & (bt.pick_p < hi)])
        print(f"        {lab:>9}: {ww}-{ll} ({ww / max(ww + ll, 1):.1%})")
    for s in BT_SEASONS:
        ww, ll = record(bt[bt.season == s])
        print(f"        {s}: {ww}-{ll} ({ww / (ww + ll):.1%})")
    for lo, hi in ((4, 6), (7, 10), (11, 15)):
        ww, ll = record(bt[bt.week.between(lo, hi)])
        print(f"        weeks {lo}-{hi}: {ww}-{ll} ({ww / (ww + ll):.1%})")
    for k in WEIGHTS:
        x = bt[bt.result != 0]
        hit = ((x[f"z_{k}"] > 0) == (x.result > 0))[x[f"z_{k}"] != 0].mean()
        print(f"        {k:<12} alone picks {hit:.1%}; corr with margin {np.corrcoef(x[f'z_{k}'], x.result)[0, 1]:+.3f}")
    print(f"        total points: mean abs error {np.mean(np.abs(bt.total_hat - bt.total)):.1f}")
    os.makedirs(args.out, exist_ok=True)
    bt.to_csv(os.path.join(args.out, f"prompt_cfb_backtest_{BT_SEASONS[0]}_{BT_SEASONS[-1]}.csv"), index=False)

    print(f"[4/5] {S} so far (out of sample)")
    wk_now = min(w for _, w in slates.values() if w) if any(w for _, w in slates.values()) else 16
    cur = build_rows(tg, qg, games, S, range(4, wk_now))
    if len(cur):
        cur["sit"] = cur[["home_sit", "rest_diff"]].to_numpy(float) @ beta_all
        cur = apply_cal(add_scores(cur, scale), a, lr, tb)
        ww, ll = record(cur)
        print(f"      {S} weeks 4-{wk_now - 1}: {ww}-{ll} ({ww / max(ww + ll, 1):.1%})")
        cur.to_csv(os.path.join(args.out, f"prompt_cfb_{S}_out_of_sample.csv"), index=False)

    print("[5/5] Picks")
    nop = {}
    for item in args.nopick:
        t, _, why = item.partition("=")
        nop[t.strip().lower()] = why.strip() or "manual no-pick"
    over = {}
    for item in args.starter:
        t, _, nm = item.partition("=")
        over[t.strip().lower()] = nm.strip()
    finals = sb[sb.season == S]
    for dt in dates:
        sl, _ = slates[dt]
        if not sl:
            print(f"\n  {dt}: no games left to price")
            continue
        fk = min(g["kickoff_utc"] for g in sl)
        T, raw, q, lg = snapshot(tg[(tg.season == S) & (tg.date < fk)], qg[(qg.season == S) & (qg.date < fk)])
        sg = pd.DataFrame(sl)
        sg["season"] = S
        sg = add_rest(sg, finals)
        qrep = qbs.report(passers, games, S, sl)
        names = {}
        for g in sl:
            names[g["home_id"]], names[g["away_id"]] = g["home_name"], g["away_name"]
        last = dict(zip(qrep.team, qrep.get("last_starter", pd.Series(dtype=object))))
        starter = {}
        for tid, nm in names.items():
            who = over.get(nm.lower(), last.get(nm))
            starter[tid] = f"{tid}|{who}" if isinstance(who, str) and who else None
        recs = []
        for g in sg.itertuples():
            h, aw = g.home_id, g.away_id
            reason = nop.get(g.home_name.lower()) or nop.get(g.away_name.lower())
            short = [names[t] for t in (h, aw) if not enough(T, t)]
            if short and not reason:
                reason = "not enough play-by-play this season: " + ", ".join(short)
            rec = dict(game_id=g.game_id, date=dt, kickoff=kickoff_local(g.kickoff_utc, tz), away_name=g.away_name,
                       home_name=g.home_name, neutral=bool(g.neutral), home_rest=g.home_rest, away_rest=g.away_rest,
                       status="NO PICK" if reason else "PICK", reason=reason or "")
            if not short:
                f = matchup(T, q, lg, h, aw, starter.get(h), starter.get(aw))
                f.update(home_sit=0.0 if g.neutral else 1.0, rest_diff=g.rest_diff, result=np.nan, total=np.nan)
                f = pd.DataFrame([f])
                f["sit"] = f[["home_sit", "rest_diff"]].to_numpy(float) @ beta_all
                f = apply_cal(add_scores(f, scale), a, lr, tb).iloc[0]
                ph = float(f.p_home)
                pick_home = ph >= 0.5
                pp = ph if pick_home else 1 - ph
                hp, ap_ = (f.total_hat + f.margin_hat) / 2, (f.total_hat - f.margin_hat) / 2
                hs, as_ = int(math.floor(hp + 0.5)), int(math.floor(ap_ + 0.5))
                if pick_home and hs <= as_:
                    hs = as_ + 1
                if not pick_home and as_ <= hs:
                    as_ = hs + 1
                pk, opp = (g.home_name, g.away_name) if pick_home else (g.away_name, g.home_name)
                rec.update(pick="" if reason else pk, pick_prob=np.nan if reason else round(pp, 4),
                           confidence=np.nan if reason else int(math.floor(10 * pp + 0.5)),
                           score="" if reason else f"{pk} {max(hs, as_)} - {opp} {min(hs, as_)}",
                           p_home=round(ph, 4), margin_home=round(float(f.margin_hat), 2), total=round(float(f.total_hat), 1),
                           weighted_score=round(float(f.S), 3))
                for k in WEIGHTS:
                    rec[f"z_{k}"] = round(float(f[f"z_{k}"]), 3)
                    rec[f"pts_{k}"] = round(float(f[f"pts_{k}"]), 2)
            for side, t in (("home", h), ("away", aw)):
                qb = starter.get(t)
                rec[f"{side}_qb"] = qb.split("|", 1)[1] if qb else ""
                rec[f"{side}_qb_dropbacks"] = int(q.at[qb, "n_db"]) if qb in q.index else 0
                rec[f"{side}_qb_epa_db"] = round(q.at[qb, "epa_db"] / q.at[qb, "n_db"], 3) if qb in q.index else np.nan
                if t in raw.index:
                    for c in ["games", "off_epa", "def_epa", "off_press", "def_press", "off_ly", "def_ly", "def_db",
                              "off_3rd", "def_3rd", "off_rz", "def_rz", "off_rz_trips", "def_rz_trips", "giveaways",
                              "takeaways", "to_margin_pg"]:
                        rec[f"{side}_{c}"] = round(float(raw.at[t, c]), 4)
            recs.append(rec)
        res = pd.DataFrame(recs)
        for c in ("pick", "pick_prob", "confidence", "score"):
            if c not in res:
                res[c] = np.nan
        res = res.assign(_o=pd.to_numeric(res["pick_prob"], errors="coerce").fillna(0)).sort_values(
            ["status", "_o"], ascending=[False, False]).drop(columns="_o")
        path = os.path.join(args.out, f"prompt_cfb_{dt}_picks.csv")
        res.to_csv(path, index=False)
        print(f"\n  {dt} ({path}):")
        for r in res.itertuples():
            if r.status == "NO PICK":
                print(f"    NO PICK {r.away_name} at {r.home_name}: {r.reason}")
            else:
                pts = " ".join(f"{k[:5]} {getattr(r, f'pts_{k}'):+.1f}" for k in WEIGHTS)
                print(f"    {r.pick} {float(r.pick_prob):.1%} conf {int(r.confidence)}  {r.score}  ({r.away_name} at "
                      f"{r.home_name}, {r.kickoff})  home-pts: {pts}")
        print("    QBs used: " + "; ".join(f"{names[t]} {starter[t].split('|', 1)[1] if starter[t] else '(none)'}"
                                         for t in names))


if __name__ == "__main__":
    main()
