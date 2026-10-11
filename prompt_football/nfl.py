#!/usr/bin/env python3
"""Prompt Football, scored with real numbers (NFL).

The owner's "Prompt Football" framework, with every criterion measured from
nflverse play-by-play instead of judgment:

  1. Trench dominance   25%  pressure rate (sacks + QB hits per dropback) and
                             line yards per designed run, offense vs defense
  2. Net efficiency     25%  EPA per play, offense vs defense
  3. Passing matchups   20%  the starting QB's EPA per dropback against the
                             blitz (5+ rushers, FTN charting) and without it,
                             against what the defense allows in each, weighted
                             by how often that defense blitzes
  4. Situational        15%  home field and rest days, turned into points from
                             past results (2019 and 2021-2025; 2020 had no
                             crowds). Time zones and miles travelled were tested
                             too and showed no effect in those seasons (the
                             estimates even leaned toward the travelling team),
                             so they score zero. Weather moves the total, not
                             the side.
  5. High leverage      15%  third-down conversion rate, red-zone touchdown rate
                             per trip, turnover margin per game

Each criterion is a home-minus-away matchup number, scaled so a typical game is
1, then weighted 25/25/20/15/15. A week-by-week replay of 2022-2025 (weeks 4-18,
every team rated only from its earlier games that season) turns the weighted
score into a win chance, a margin and a total. Final scores are only the target.
No betting lines, records or points scored go in (the schedule's betting columns
are never read).

This is separate from the locked engines in METHOD.md; it was run at the
owner's request on 2026-10-11.

  python3 prompt_football/nfl.py --season 2026 --week 5 --raw prompt_football/cache \
      --qbs results/nfl_cfbmethod_2026_week05_qbs.csv --starter "WAS=Jayden Daniels" \
      --nopick "CHI=..." --wind JAX=6 --wind TEN=10
"""
import argparse
import math
import os
import urllib.request

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

WEIGHTS = {"trench": 0.25, "net_eff": 0.25, "passing": 0.20, "situational": 0.15, "leverage": 0.15}
BT_SEASONS = [2022, 2023, 2024, 2025]               # FTN blitz charting starts in 2022
SIT_SEASONS = [2019, 2021, 2022, 2023, 2024, 2025]  # 2020 had no crowds
BT_WEEKS = range(4, 19)
SIT_COLS = ["home", "rest_diff"]
K = dict(play=100, db=100, run=60, bl=40, nb=60, blrate=100, third=30, rz=8, games=2)

PBP = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.parquet"
FTN = "https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_{}.parquet"
SCHED = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
SCHED_COLS = ["game_id", "season", "game_type", "week", "gameday", "gametime", "away_team", "home_team",
              "away_score", "home_score", "location", "result", "total", "away_rest", "home_rest",
              "roof", "wind", "stadium", "espn"]

NICK = {"Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF", "Panthers": "CAR",
        "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE", "Cowboys": "DAL", "Broncos": "DEN",
        "Lions": "DET", "Packers": "GB", "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX",
        "Chiefs": "KC", "Raiders": "LV", "Chargers": "LAC", "Rams": "LA", "Dolphins": "MIA",
        "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG", "Jets": "NYJ",
        "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF", "Seahawks": "SEA", "Buccaneers": "TB",
        "Titans": "TEN", "Commanders": "WAS"}
ABBR_NICK = {v: k for k, v in NICK.items()}

# home stadium: lat, lon, hours from US Eastern (daylight time)
TEAM_LOC = {
    "ARI": (33.528, -112.263, -3), "ATL": (33.755, -84.401, 0), "BAL": (39.278, -76.623, 0),
    "BUF": (42.774, -78.787, 0), "CAR": (35.226, -80.853, 0), "CHI": (41.862, -87.617, -1),
    "CIN": (39.095, -84.516, 0), "CLE": (41.506, -81.700, 0), "DAL": (32.748, -97.093, -1),
    "DEN": (39.744, -105.020, -2), "DET": (42.340, -83.046, 0), "GB": (44.501, -88.062, -1),
    "HOU": (29.685, -95.411, -1), "IND": (39.760, -86.164, 0), "JAX": (30.324, -81.637, 0),
    "KC": (39.049, -94.484, -1), "LV": (36.091, -115.184, -3), "OAK": (37.751, -122.200, -3),
    "LAC": (33.953, -118.339, -3), "LA": (33.953, -118.339, -3), "MIA": (25.958, -80.239, 0),
    "MIN": (44.974, -93.258, -1), "NE": (42.091, -71.264, 0), "NO": (29.951, -90.081, -1),
    "NYG": (40.813, -74.074, 0), "NYJ": (40.813, -74.074, 0), "PHI": (39.901, -75.168, 0),
    "PIT": (40.447, -80.016, 0), "SF": (37.403, -121.970, -3), "SEA": (47.595, -122.332, -3),
    "TB": (27.976, -82.503, 0), "TEN": (36.166, -86.771, -1), "WAS": (38.908, -76.864, 0),
}
INTL = [  # stadium-name keywords -> lat, lon, hours from US Eastern
    (("tottenham",), (51.604, -0.066, 5)), (("wembley",), (51.556, -0.280, 5)),
    (("allianz", "bayern"), (48.219, 11.625, 6)), (("deutsche bank", "frankfurt"), (50.069, 8.645, 6)),
    (("azteca", "banorte"), (19.303, -99.150, -1)), (("corinthians",), (-23.545, -46.474, 1)),
    (("croke",), (53.361, -6.251, 5)), (("bernab",), (40.453, -3.688, 6)),
    (("olympiastadion", "berlin"), (52.515, 13.239, 6)), (("maracan",), (-22.912, -43.230, 1)),
    (("cricket", "melbourne"), (-37.820, 144.983, 14)), (("stade de france",), (48.924, 2.360, 6)),
]
# international games the schedule files under the home team's own stadium
VENUE_FIX = {
    (2025, 1, "LAC"): (-23.545, -46.474, 1), (2025, 4, "PIT"): (53.361, -6.251, 5),
    (2025, 5, "CLE"): (51.604, -0.066, 5), (2025, 6, "NYJ"): (51.604, -0.066, 5),
    (2025, 7, "JAX"): (51.556, -0.280, 5), (2025, 10, "IND"): (52.515, 13.239, 6),
    (2025, 11, "MIA"): (40.453, -3.688, 6),
}


def fetch(url, path, refresh=False):
    if os.path.exists(path) and not refresh:
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    urllib.request.urlretrieve(url, path + ".part")
    os.replace(path + ".part", path)
    return path


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def rms(x):
    return float(np.sqrt(np.mean(np.square(np.asarray(x, float)))))


def rate(s, n, lg, k):
    return (s + k * lg) / (n + k)


# ---------------------------------------------------------------- schedule

def schedule(raw, refresh):
    g = pd.read_csv(fetch(SCHED, f"{raw}/games.csv", refresh), usecols=SCHED_COLS)
    g = g[(g.game_type == "REG") & (g.season >= min(SIT_SEASONS))].reset_index(drop=True)
    usual = g[g.location == "Home"].groupby("stadium").home_team.agg(lambda s: s.value_counts().index[0])
    extra = []
    for r in g.itertuples():
        st = str(r.stadium).lower()
        venue, neutral = None, r.location == "Neutral"
        if (r.season, r.week, r.home_team) in VENUE_FIX:
            venue, neutral = VENUE_FIX[(r.season, r.week, r.home_team)], True
        else:
            for keys, loc in INTL:
                if any(k in st for k in keys):
                    venue, neutral = loc, True
                    break
        if venue is None:
            venue = TEAM_LOC[usual.get(r.stadium, r.home_team)]
        hl, al = TEAM_LOC[r.home_team], TEAM_LOC[r.away_team]
        h_tz, a_tz = abs(venue[2] - hl[2]), abs(venue[2] - al[2])
        h_mi, a_mi = miles(hl, venue), miles(al, venue)
        outdoor = str(r.roof) in ("outdoors", "open")
        extra.append(dict(neutral=neutral, home=0.0 if neutral else 1.0,
                          rest_diff=float(np.clip((r.home_rest if pd.notna(r.home_rest) else 7)
                                                  - (r.away_rest if pd.notna(r.away_rest) else 7), -7, 7)),
                          tz_home=h_tz, tz_away=a_tz, mi_home=h_mi, mi_away=a_mi,
                          tz_diff=a_tz - h_tz, dist_diff=(a_mi - h_mi) / 1000.0,
                          wind_eff=float(r.wind) if outdoor and pd.notna(r.wind) else 0.0))
    return pd.concat([g.reset_index(drop=True), pd.DataFrame(extra)], axis=1)


def sit_fit(sched, seasons):
    s = sched[sched.season.isin(seasons) & sched.result.notna()]
    X = s[SIT_COLS].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, s.result.to_numpy(float), rcond=None)
    return beta


# ------------------------------------------------------------------- plays

PCOLS = ["game_id", "season", "week", "season_type", "play_id", "posteam", "defteam", "play_type", "down",
         "yardline_100", "qtr", "score_differential", "epa", "qb_dropback", "qb_scramble", "sack", "qb_hit",
         "yards_gained", "third_down_converted", "third_down_failed", "interception", "fumble_lost",
         "fixed_drive", "fixed_drive_result", "two_point_attempt", "passer_id", "passer"]


def load_plays(raw, seasons, current, refresh):
    parts = []
    for y in seasons:
        fresh = refresh and y == current
        p = pd.read_parquet(fetch(PBP.format(y), f"{raw}/pbp_{y}.parquet", fresh), columns=PCOLS)
        p = p[p.season_type == "REG"]
        f = pd.read_parquet(fetch(FTN.format(y), f"{raw}/ftn_{y}.parquet", fresh),
                            columns=["nflverse_game_id", "nflverse_play_id", "n_pass_rushers"])
        f.columns = ["game_id", "play_id", "rushers"]
        f["play_id"] = pd.to_numeric(f.play_id, errors="coerce")
        p = p.assign(play_id=pd.to_numeric(p.play_id, errors="coerce"))
        p = p.merge(f.dropna().drop_duplicates(["game_id", "play_id"]), on=["game_id", "play_id"], how="left")
        parts.append(p)
    return pd.concat(parts, ignore_index=True)


def team_games(p):
    """Per team per game sums (offense o_*, defense d_*), plus quarterback rows."""
    scr = p[p.play_type.isin(["pass", "run"]) & p.down.between(1, 4) & (p.two_point_attempt.fillna(0) == 0)
            & (p.qtr <= 4) & p.epa.notna() & p.posteam.notna() & p.defteam.notna()].copy()
    m = scr.score_differential.abs()
    scr = scr[~(((scr.qtr == 2) & (m > 38)) | ((scr.qtr == 3) & (m > 28)) | ((scr.qtr == 4) & (m > 22)))]
    db = scr.qb_dropback.fillna(0).eq(1).to_numpy()
    run = (scr.play_type.eq("run") & scr.qb_scramble.fillna(0).eq(0)).to_numpy()
    y = scr.yards_gained.fillna(0).to_numpy(float)
    ly = np.where(y < 0, 1.2 * y, np.where(y <= 4, y, np.where(y <= 10, 4 + 0.5 * (y - 4), 7.0)))
    rush = scr.rushers.fillna(0).to_numpy(float)
    ch = db & (rush > 0)
    bl, nb = ch & (rush >= 5), ch & (rush < 5)
    third = (scr.down.eq(3) & (scr.third_down_converted.eq(1) | scr.third_down_failed.eq(1))).to_numpy()
    conv = scr.third_down_converted.eq(1).to_numpy()
    e = scr.epa.to_numpy(float)
    press = (scr.sack.eq(1) | scr.qb_hit.eq(1)).to_numpy()
    to = (scr.interception.eq(1) | scr.fumble_lost.eq(1)).to_numpy()
    v = pd.DataFrame({
        "season": scr.season.to_numpy(), "week": scr.week.to_numpy(), "game_id": scr.game_id.to_numpy(),
        "off": scr.posteam.to_numpy(), "def": scr.defteam.to_numpy(),
        "n": 1.0, "epa": e, "n_db": db * 1.0, "epa_db": np.where(db, e, 0.0), "press": (db & press) * 1.0,
        "n_run": run * 1.0, "ly": np.where(run, ly, 0.0),
        "n_ch": ch * 1.0, "n_bl": bl * 1.0, "epa_bl": np.where(bl, e, 0.0),
        "n_nb": nb * 1.0, "epa_nb": np.where(nb, e, 0.0),
        "n_3rd": third * 1.0, "c_3rd": (third & conv) * 1.0, "to": to * 1.0,
    })
    keys = ["season", "week", "game_id"]
    num = [c for c in v.columns if c not in keys + ["off", "def"]]
    o = v.groupby(keys + ["off"])[num].sum().add_prefix("o_").reset_index().rename(columns={"off": "team"})
    d = v.groupby(keys + ["def"])[num].sum().add_prefix("d_").reset_index().rename(columns={"def": "team"})
    tg = o.merge(d, on=keys + ["team"], how="outer").fillna(0.0)

    # red-zone trips: drives that reached the opponent's 20; touchdowns on those drives
    dr = p[p.posteam.notna() & p.fixed_drive.notna() & p.yardline_100.notna()].assign(
        td=lambda x: x.fixed_drive_result.eq("Touchdown") * 1.0)
    dr = dr.groupby(["game_id", "posteam", "fixed_drive"]).agg(yl=("yardline_100", "min"), td=("td", "max")).reset_index()
    dr = dr[dr.yl <= 20]
    rz = dr.groupby(["game_id", "posteam"]).agg(rz=("td", "size"), rztd=("td", "sum")).reset_index()
    pair = tg[["game_id", "team"]]
    opp = pair.merge(pair, on="game_id", suffixes=("", "_opp"))
    opp = opp[opp.team != opp.team_opp]
    rz_o = rz.rename(columns={"posteam": "team", "rz": "o_rz", "rztd": "o_rztd"})
    rz_d = rz.rename(columns={"posteam": "team_opp", "rz": "d_rz", "rztd": "d_rztd"}).merge(
        opp, on=["game_id", "team_opp"])[["game_id", "team", "d_rz", "d_rztd"]]
    tg = tg.merge(rz_o, on=["game_id", "team"], how="left").merge(rz_d, on=["game_id", "team"], how="left").fillna(0.0)
    tg["games"] = 1.0

    # quarterbacks (dropbacks by the passer, scrambles and sacks included)
    q = scr[db & scr.passer_id.notna().to_numpy()]
    qr = q.rushers.fillna(0).to_numpy(float)
    qbl, qnb = qr >= 5, (qr > 0) & (qr < 5)
    qe = q.epa.to_numpy(float)
    qv = pd.DataFrame({"season": q.season.to_numpy(), "week": q.week.to_numpy(), "game_id": q.game_id.to_numpy(),
                       "team": q.posteam.to_numpy(), "qb": q.passer_id.to_numpy(), "name": q.passer.to_numpy(),
                       "n_db": 1.0, "epa_db": qe, "n_bl": qbl * 1.0, "epa_bl": np.where(qbl, qe, 0.0),
                       "n_nb": qnb * 1.0, "epa_nb": np.where(qnb, qe, 0.0)})
    qg = qv.groupby(["season", "week", "game_id", "team", "qb"]).agg(
        name=("name", "first"), n_db=("n_db", "sum"), epa_db=("epa_db", "sum"), n_bl=("n_bl", "sum"),
        epa_bl=("epa_bl", "sum"), n_nb=("n_nb", "sum"), epa_nb=("epa_nb", "sum")).reset_index()
    return tg, qg


def snapshot(tg, qg, season, week):
    a = tg[(tg.season == season) & (tg.week < week)].groupby("team").sum(numeric_only=True)
    L = a.sum()
    lg = {"epa": L.o_epa / L.o_n, "db": L.o_epa_db / L.o_n_db, "press": L.o_press / L.o_n_db,
          "ly": L.o_ly / L.o_n_run, "bl": L.o_epa_bl / L.o_n_bl, "nb": L.o_epa_nb / L.o_n_nb,
          "blrate": L.o_n_bl / L.o_n_ch, "third": L.o_c_3rd / L.o_n_3rd, "rz": L.o_rztd / L.o_rz,
          "to": L.o_to / L.games}
    T = pd.DataFrame(index=a.index)
    for side, pre in (("off", "o_"), ("def", "d_")):
        T[f"{side}_epa"] = rate(a[pre + "epa"], a[pre + "n"], lg["epa"], K["play"])
        T[f"{side}_db"] = rate(a[pre + "epa_db"], a[pre + "n_db"], lg["db"], K["db"])
        T[f"{side}_press"] = rate(a[pre + "press"], a[pre + "n_db"], lg["press"], K["db"])
        T[f"{side}_ly"] = rate(a[pre + "ly"], a[pre + "n_run"], lg["ly"], K["run"])
        T[f"{side}_bl"] = rate(a[pre + "epa_bl"], a[pre + "n_bl"], lg["bl"], K["bl"])
        T[f"{side}_nb"] = rate(a[pre + "epa_nb"], a[pre + "n_nb"], lg["nb"], K["nb"])
        T[f"{side}_3rd"] = rate(a[pre + "c_3rd"], a[pre + "n_3rd"], lg["third"], K["third"])
        T[f"{side}_rz"] = rate(a[pre + "rztd"], a[pre + "rz"], lg["rz"], K["rz"])
        T[f"{side}_to"] = rate(a[pre + "to"], a.games, lg["to"], K["games"])
    T["def_blrate"] = rate(a.d_n_bl, a.d_n_ch, lg["blrate"], K["blrate"])
    raw = pd.DataFrame(index=a.index)          # unshrunk, for display
    raw["games"] = a.games
    for side, pre in (("off", "o_"), ("def", "d_")):
        raw[f"{side}_epa"] = a[pre + "epa"] / a[pre + "n"]
        raw[f"{side}_db"] = a[pre + "epa_db"] / a[pre + "n_db"]
        raw[f"{side}_press"] = a[pre + "press"] / a[pre + "n_db"]
        raw[f"{side}_ly"] = a[pre + "ly"] / a[pre + "n_run"]
        raw[f"{side}_bl"] = a[pre + "epa_bl"] / a[pre + "n_bl"]
        raw[f"{side}_3rd"] = a[pre + "c_3rd"] / a[pre + "n_3rd"]
        raw[f"{side}_rz"] = a[pre + "rztd"] / a[pre + "rz"]
        raw[f"{side}_rz_trips"] = a[pre + "rz"]
    raw["def_blrate"] = a.d_n_bl / a.d_n_ch
    raw["giveaways"] = a.o_to
    raw["takeaways"] = a.d_to
    raw["to_margin_pg"] = (a.d_to - a.o_to) / a.games
    q = qg[(qg.season == season) & (qg.week < week)].groupby("qb").agg(
        name=("name", "last"), team=("team", "last"), n_db=("n_db", "sum"), epa_db=("epa_db", "sum"),
        n_bl=("n_bl", "sum"), epa_bl=("epa_bl", "sum"), n_nb=("n_nb", "sum"), epa_nb=("epa_nb", "sum"))
    q["bl"] = rate(q.epa_bl, q.n_bl, lg["bl"], K["bl"])
    q["nb"] = rate(q.epa_nb, q.n_nb, lg["nb"], K["nb"])
    return T, raw, q, lg


def matchup(T, q, lg, h, a, qb_h, qb_a):
    H, A = T.loc[h], T.loc[a]

    def qb_rates(qb):          # unknown or brand-new QB -> league average
        if qb is not None and qb in q.index:
            return q.at[qb, "bl"], q.at[qb, "nb"]
        return lg["bl"], lg["nb"]

    hb, hn = qb_rates(qb_h)
    ab, an = qb_rates(qb_a)
    eh = A.def_blrate * (hb + A.def_bl - lg["bl"]) + (1 - A.def_blrate) * (hn + A.def_nb - lg["nb"])
    ea = H.def_blrate * (ab + H.def_bl - lg["bl"]) + (1 - H.def_blrate) * (an + H.def_nb - lg["nb"])
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


def find_qb(qg, season, team, full_name):
    last = full_name
    for suf in (" Jr.", " Sr.", " III", " II", " IV"):
        last = last.replace(suf, "")
    last = last.split()[-1].lower()
    c = qg[(qg.season == season) & (qg.team == team)].groupby("qb").agg(name=("name", "first"), n=("n_db", "sum"))
    c = c[c.name.str.lower().str.endswith(last)]
    return None if c.empty else c.n.idxmax()


def build_rows(tg, qg, sched, season, weeks, starters_by_team=None):
    starters = qg.sort_values("n_db").groupby(["game_id", "team"]).tail(1).set_index(["game_id", "team"]).qb
    rows = []
    for wk in weeks:
        gw = sched[(sched.season == season) & (sched.week == wk)]
        if gw.empty:
            continue
        T, raw, q, lg = snapshot(tg, qg, season, wk)
        for r in gw.itertuples():
            if r.home_team not in T.index or r.away_team not in T.index:
                continue
            if pd.notna(r.result) or not starters_by_team:
                qh, qa = starters.get((r.game_id, r.home_team)), starters.get((r.game_id, r.away_team))
            else:
                qh, qa = starters_by_team.get(r.home_team), starters_by_team.get(r.away_team)
            f = matchup(T, q, lg, r.home_team, r.away_team, qh, qa)
            f.update(season=season, week=wk, game_id=r.game_id, home_team=r.home_team, away_team=r.away_team,
                     result=r.result, total=r.total, home_sit=r.home, rest_diff=r.rest_diff, tz_diff=r.tz_diff,
                     dist_diff=r.dist_diff, wind_eff=r.wind_eff, qb_home=qh, qb_away=qa)
            rows.append(f)
    return pd.DataFrame(rows)


# ------------------------------------------------------------ scoring/fit

SUBS = ["tp", "tr", "ne", "pm", "h3", "hr", "ht"]


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
    X = np.column_stack([np.ones(len(d)), d.epa_sum, d.wind_eff])
    tb, *_ = np.linalg.lstsq(X, d.total.to_numpy(float), rcond=None)
    return a, lr, tb


def apply_cal(d, a, lr, tb):
    d = d.copy()
    d["p_home"] = lr.predict_proba(d[["S"]])[:, 1]
    d["margin_hat"] = a * d.S
    d["total_hat"] = tb[0] + tb[1] * d.epa_sum + tb[2] * d.wind_eff
    for k in WEIGHTS:
        d[f"pts_{k}"] = a * WEIGHTS[k] * d[f"z_{k}"]
    return d


def record(d, col="p_home"):
    d = d[d.result.notna() & (d.result != 0)]
    win = (d[col] >= 0.5) == (d.result > 0)
    return int(win.sum()), int((~win).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--raw", required=True, help="folder for nflverse files (downloaded if missing)")
    ap.add_argument("--qbs", help="engine _qbs.csv; each team's last starter is the expected starter")
    ap.add_argument("--starter", action="append", default=[], help='TEAM=Full Name, overrides --qbs')
    ap.add_argument("--nopick", action="append", default=[], help="TEAM=reason")
    ap.add_argument("--wind", action="append", default=[], help="HOMETEAM=mph forecast (outdoor games)")
    ap.add_argument("--engine-backtest", help="engine backtest csv (with closing lines) to compare against")
    ap.add_argument("--out", default="results")
    ap.add_argument("--refresh", action="store_true", help="re-download this season's files")
    args = ap.parse_args()
    S, W = args.season, args.week

    sched = schedule(args.raw, args.refresh)
    plays = load_plays(args.raw, BT_SEASONS + [S], S, args.refresh)
    tg, qg = team_games(plays)

    # backtest rows (each season's situational points fit on the other seasons)
    bt = []
    for s in BT_SEASONS:
        r = build_rows(tg, qg, sched, s, BT_WEEKS)
        beta = sit_fit(sched, [x for x in SIT_SEASONS if x != s])
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
    beta_all = sit_fit(sched, SIT_SEASONS)

    # this season: earlier weeks (out of sample) and this week
    starters = {}
    if args.qbs:
        for r in pd.read_csv(args.qbs).itertuples():
            if r.team in NICK and isinstance(r.last_starter, str):
                starters[NICK[r.team]] = r.last_starter
    for s_ in args.starter:
        t, n = s_.split("=", 1)
        starters[t.strip()] = n.strip()
    sid = {t: find_qb(qg, S, t, n) for t, n in starters.items()}
    print("Expected starters:", ", ".join(f"{t} {starters[t]}->{sid[t]}" for t in sorted(sid)))
    cur = build_rows(tg, qg, sched, S, range(4, W + 1), sid)
    cur["sit"] = cur[["home_sit", "rest_diff"]].to_numpy(float) @ beta_all
    winds = {w.split("=")[0]: float(w.split("=")[1]) for w in args.wind}
    cur.loc[cur.result.isna(), "wind_eff"] = cur.loc[cur.result.isna(), "home_team"].map(winds).fillna(0.0)
    cur = apply_cal(add_scores(cur, scale), a, lr, tb)

    # ---- report
    print(f"Situational points (2019, 2021-25): home field {beta_all[0]:+.2f}, per rest day {beta_all[1]:+.2f}")
    print(f"Margin = {a:.2f} x weighted score; total = {tb[0]:.1f} + {tb[1]:.1f} x EPA sum + {tb[2]:.2f} x wind")
    w_, l_ = record(bt)
    br = ((bt.p_home - (bt.result > 0)) ** 2)[bt.result != 0].mean()
    print(f"\nBacktest 2022-2025, weeks 4-18 (each season calibrated on the others): {w_}-{l_} "
          f"({w_ / (w_ + l_):.1%}), Brier {br:.4f}")
    bt["pick_p"] = np.maximum(bt.p_home, 1 - bt.p_home)
    for lo, hi, lab in ((0.7, 1.01, "70%+"), (0.6, 0.7, "60-70%"), (0.5, 0.6, "under 60%")):
        x = bt[(bt.pick_p >= lo) & (bt.pick_p < hi)]
        ww, ll = record(x)
        print(f"  {lab:>9}: {ww}-{ll} ({ww / max(ww + ll, 1):.1%})")
    for s in BT_SEASONS:
        ww, ll = record(bt[bt.season == s])
        print(f"  {s}: {ww}-{ll} ({ww / (ww + ll):.1%})")
    for lo, hi in ((4, 6), (7, 10), (11, 18)):
        ww, ll = record(bt[bt.week.between(lo, hi)])
        print(f"  weeks {lo}-{hi}: {ww}-{ll} ({ww / (ww + ll):.1%})")
    for k in WEIGHTS:            # each criterion on its own
        x = bt[bt.result != 0]
        hit = ((x[f"z_{k}"] > 0) == (x.result > 0))[x[f"z_{k}"] != 0].mean()
        print(f"  {k:<12} alone picks {hit:.1%}; corr with margin {np.corrcoef(x[f'z_{k}'], x.result)[0, 1]:+.3f}")
    tm = bt[bt.result.notna()]
    print(f"  total points: mean abs error {np.mean(np.abs(tm.total_hat - tm.total)):.1f}")

    if args.engine_backtest and os.path.exists(args.engine_backtest):
        e = pd.read_csv(args.engine_backtest)
        m = bt.merge(e[["season", "week", "home_team", "away_team", "p_home", "market_p_home"]],
                     on=["season", "week", "home_team", "away_team"], suffixes=("", "_engine"))
        m = m[m.result != 0]
        hw = m.result > 0
        pr = ((m.p_home >= 0.5) == hw)
        en = ((m.p_home_engine >= 0.5) == hw)
        mk = ((m.market_p_home >= 0.5) == hw)
        agree = (m.p_home >= 0.5) == (m.p_home_engine >= 0.5)
        print(f"\nSame {len(m)} games: prompt {pr.sum()}-{(~pr).sum()} ({pr.mean():.1%}), engine "
              f"{en.sum()}-{(~en).sum()} ({en.mean():.1%}), closing favorite {mk.sum()}-{(~mk).sum()} "
              f"({mk.mean():.1%}; grading only)")
        print(f"  agree {agree.sum()} games: {pr[agree].sum()}-{(~pr[agree]).sum()}; disagree "
              f"{(~agree).sum()}: prompt {pr[~agree].sum()}-{(~pr[~agree]).sum()}")
        for lo, hi in ((4, 6), (7, 10), (11, 18)):
            b = m.week.between(lo, hi)
            print(f"  weeks {lo}-{hi}: prompt {pr[b].mean():.1%}, engine {en[b].mean():.1%}, "
                  f"disagree {(~agree & b).sum()} games, prompt won {pr[~agree & b].sum()} of them")
        avg = ((m.p_home + m.p_home_engine) / 2 >= 0.5) == hw
        print(f"  average of the two: {avg.sum()}-{(~avg).sum()} ({avg.mean():.1%})")
        print(f"  Brier: prompt {((m.p_home - hw) ** 2).mean():.4f}, engine {((m.p_home_engine - hw) ** 2).mean():.4f},"
              f" closing line {((m.market_p_home - hw) ** 2).mean():.4f}")

    done = cur[cur.result.notna()]
    if len(done):
        ww, ll = record(done)
        print(f"\n{S} weeks 4-{W} games already played (out of sample): {ww}-{ll}")

    nop = {t.split("=", 1)[0].strip(): t.split("=", 1)[1].strip() for t in args.nopick}
    live = cur[cur.result.isna() & (cur.week == W)].copy()
    T, raw, q, lg = snapshot(tg, qg, S, W)
    sw = sched[(sched.season == S) & (sched.week == W)].set_index("game_id")
    recs = []
    for r in live.itertuples():
        g = sw.loc[r.game_id]
        h, aw = r.home_team, r.away_team
        reason = nop.get(h) or nop.get(aw)
        pick_home = r.p_home >= 0.5
        pick = h if pick_home else aw
        pp = r.p_home if pick_home else 1 - r.p_home
        hp, ap_ = (r.total_hat + r.margin_hat) / 2, (r.total_hat - r.margin_hat) / 2
        hs, as_ = int(math.floor(hp + 0.5)), int(math.floor(ap_ + 0.5))
        if pick_home and hs <= as_:
            hs = as_ + 1
        if not pick_home and as_ <= hs:
            as_ = hs + 1
        hh, mm = map(int, str(g.gametime).split(":"))
        nick = lambda t: ABBR_NICK.get(t, t)
        rec = dict(game_id=str(int(g.espn)) if pd.notna(g.espn) else r.game_id, nflverse_id=r.game_id,
                   away_name=nick(aw), home_name=nick(h), gameday=g.gameday, kickoff_et=g.gametime,
                   kickoff_phoenix=f"{(hh - 3) % 12 or 12}:{mm:02d} {'AM' if hh - 3 < 12 else 'PM'}",
                   away=aw, home=h, neutral=bool(g.neutral), status="NO PICK" if reason else "PICK",
                   reason=reason or "", pick="" if reason else nick(pick), pick_prob="" if reason else round(pp, 4),
                   confidence="" if reason else int(math.floor(10 * pp + 0.5)),
                   score="" if reason else (f"{nick(pick)} {max(hs, as_)} - {nick(aw if pick_home else h)} {min(hs, as_)}"),
                   p_home=round(r.p_home, 4), margin_home=round(r.margin_hat, 2), total=round(r.total_hat, 1),
                   weighted_score=round(r.S, 3))
        for k in WEIGHTS:
            rec[f"z_{k}"] = round(getattr(r, f"z_{k}"), 3)
            rec[f"pts_{k}"] = round(getattr(r, f"pts_{k}"), 2)
        for side, t, qb in (("home", h, r.qb_home), ("away", aw, r.qb_away)):
            R_ = raw.loc[t]
            rec[f"{side}_qb"] = q.at[qb, "name"] if qb in q.index else ""
            rec[f"{side}_qb_dropbacks"] = int(q.at[qb, "n_db"]) if qb in q.index else 0
            rec[f"{side}_qb_epa_db"] = round(q.at[qb, "epa_db"] / q.at[qb, "n_db"], 3) if qb in q.index else np.nan
            rec[f"{side}_qb_epa_vs_blitz"] = round(q.at[qb, "epa_bl"] / q.at[qb, "n_bl"], 3) if qb in q.index and q.at[qb, "n_bl"] else np.nan
            rec[f"{side}_qb_blitzed_dropbacks"] = int(q.at[qb, "n_bl"]) if qb in q.index else 0
            for c in ["games", "off_epa", "def_epa", "off_press", "def_press", "off_ly", "def_ly", "def_db",
                      "def_blrate", "def_bl", "off_3rd", "def_3rd", "off_rz", "def_rz", "off_rz_trips",
                      "def_rz_trips", "giveaways", "takeaways", "to_margin_pg"]:
                rec[f"{side}_{c}"] = round(float(R_[c]), 4)
        rec.update(rest_home=int(sw.loc[r.game_id].home_rest), rest_away=int(sw.loc[r.game_id].away_rest),
                   tz_home=g.tz_home, tz_away=g.tz_away, miles_home=round(g.mi_home),
                   miles_away=round(g.mi_away), wind=r.wind_eff)
        recs.append(rec)
    res = pd.DataFrame(recs)
    res = res.assign(_o=pd.to_numeric(res.pick_prob, errors="coerce").fillna(0)).sort_values(
        ["status", "_o"], ascending=[False, False]).drop(columns="_o")
    os.makedirs(args.out, exist_ok=True)
    path = f"{args.out}/prompt_nfl_{S}_week{W:02d}_picks.csv"
    res.to_csv(path, index=False)
    bt.to_csv(f"{args.out}/prompt_nfl_backtest_2022_2025.csv", index=False)
    print(f"\nWeek {W} ({path}):")
    for r in res.itertuples():
        if r.status == "NO PICK":
            print(f"  NO PICK {r.away} @ {r.home}: {r.reason}")
        else:
            pts = " ".join(f"{k[:5]} {getattr(r, f'pts_{k}'):+.1f}" for k in WEIGHTS)
            print(f"  {r.pick:<4} {float(r.pick_prob):.1%} conf {r.confidence}  {r.score:<16} ({r.away} @ {r.home}, "
                  f"{r.kickoff_phoenix})  home-pts: {pts}")


if __name__ == "__main__":
    main()
