"""Parse ESPN college football game summaries into a play table, a game table,
and a per-game passer table.

Usage: python3 -I parse.py <summ_dir> <ids.csv> <out_dir>
"""
import json, os, sys, csv
from multiprocessing import Pool

SUMM, IDS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]


def clock_secs(txt):
    try:
        m, s = txt.split(":")
        return int(m) * 60 + int(float(s))
    except Exception:
        return None


def parse_one(args):
    gid, season, week, date = args
    try:
        d = json.load(open(os.path.join(SUMM, gid + ".json")))
    except Exception as ex:
        return None, [], [], f"{gid}: {ex}"
    try:
        comp = d["header"]["competitions"][0]
    except Exception as ex:
        return None, [], [], f"{gid}: no header {ex}"
    teams = {}
    for c in comp["competitors"]:
        teams[c["homeAway"]] = c
    home, away = teams.get("home"), teams.get("away")
    if not home or not away:
        return None, [], [], f"{gid}: no teams"
    hid, aid = str(home["team"]["id"]), str(away["team"]["id"])
    game = {
        "game_id": gid, "season": int(season), "week": int(week), "date": date,
        "home_id": hid, "away_id": aid,
        "home_abbr": home["team"].get("abbreviation", ""),
        "away_abbr": away["team"].get("abbreviation", ""),
        "home_name": home["team"].get("location", home["team"].get("displayName", "")),
        "away_name": away["team"].get("location", away["team"].get("displayName", "")),
        "home_score": int(home.get("score") or 0), "away_score": int(away.get("score") or 0),
        "neutral": bool(comp.get("neutralSite", False)),
        "conf_game": bool(comp.get("conferenceCompetition", False)),
    }
    plays = []
    drives = (d.get("drives") or {}).get("previous") or []
    seq = 0
    for dv in drives:
        dteam = str((dv.get("team") or {}).get("id", ""))
        dres = dv.get("result", "")
        for p in dv.get("plays") or []:
            seq += 1
            st = p.get("start") or {}
            en = p.get("end") or {}
            plays.append({
                "game_id": gid, "seq": seq, "drive_id": dv.get("id", ""),
                "drive_team": dteam, "drive_result": dres,
                "type": (p.get("type") or {}).get("text", ""),
                "period": (p.get("period") or {}).get("number"),
                "clock": clock_secs((p.get("clock") or {}).get("displayValue", "")),
                "away_score": p.get("awayScore"), "home_score": p.get("homeScore"),
                "scoring": bool(p.get("scoringPlay", False)),
                "yards": p.get("statYardage"),
                "turnover": bool(p.get("isTurnover", False)),
                "penalty": bool(p.get("isPenalty", False)),
                "s_down": st.get("down"), "s_dist": st.get("distance"),
                "s_ytg": st.get("yardsToEndzone"), "s_team": str((st.get("team") or {}).get("id", "")),
                "e_down": en.get("down"), "e_dist": en.get("distance"),
                "e_ytg": en.get("yardsToEndzone"), "e_team": str((en.get("team") or {}).get("id", "")),
                "text": (p.get("text") or "")[:160],
            })
    passers = []
    for tp in (d.get("boxscore") or {}).get("players") or []:
        tid = str((tp.get("team") or {}).get("id", ""))
        for cat in tp.get("statistics") or []:
            if cat.get("name") != "passing":
                continue
            labels = cat.get("labels") or []
            for a in cat.get("athletes") or []:
                stats = a.get("stats") or []
                att = None
                if "C/ATT" in labels and len(stats) > labels.index("C/ATT"):
                    try:
                        att = int(stats[labels.index("C/ATT")].split("/")[1])
                    except Exception:
                        att = None
                ath = a.get("athlete") or {}
                passers.append({"game_id": gid, "team_id": tid,
                                "athlete_id": str(ath.get("id", "")),
                                "name": ath.get("displayName", ""), "att": att})
    return game, plays, passers, None


def main():
    rows = [r for r in csv.reader(open(IDS))]
    with Pool(2) as pool:
        res = pool.map(parse_one, rows, chunksize=20)
    import pandas as pd
    games, plays, passers, errs = [], [], [], []
    for g, p, q, e in res:
        if e:
            errs.append(e)
        if g:
            games.append(g)
        plays.extend(p)
        passers.extend(q)
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(games).to_parquet(os.path.join(OUT, "games.parquet"), index=False)
    pd.DataFrame(plays).to_parquet(os.path.join(OUT, "plays.parquet"), index=False)
    pd.DataFrame(passers).to_parquet(os.path.join(OUT, "passers.parquet"), index=False)
    print("games", len(games), "plays", len(plays), "passer rows", len(passers), "errors", len(errs))
    for e in errs[:10]:
        print("ERR", e)


if __name__ == "__main__":
    main()
