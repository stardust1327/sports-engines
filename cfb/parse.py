"""Turn cached ESPN game summaries into play, game and passer tables."""
import json
import os
from multiprocessing import Pool

import pandas as pd


def _clock_secs(txt):
    try:
        m, s = txt.split(":")
        return int(m) * 60 + int(float(s))
    except Exception:  # noqa: BLE001
        return None


def _parse_one(args):
    folder, gid, season, week, date = args
    try:
        d = json.load(open(os.path.join(folder, f"{gid}.json")))
        comp = d["header"]["competitions"][0]
    except Exception as ex:  # noqa: BLE001
        return None, [], [], f"{gid}: {ex}"
    teams = {c["homeAway"]: c for c in comp["competitors"]}
    home, away = teams.get("home"), teams.get("away")
    if not home or not away:
        return None, [], [], f"{gid}: no teams"
    game = {
        "game_id": gid, "season": int(season), "week": int(week), "date": date,
        "home_id": str(home["team"]["id"]), "away_id": str(away["team"]["id"]),
        "home_name": home["team"].get("location", home["team"].get("displayName", "")),
        "away_name": away["team"].get("location", away["team"].get("displayName", "")),
        "home_score": int(home.get("score") or 0), "away_score": int(away.get("score") or 0),
        "neutral": bool(comp.get("neutralSite", False)),
    }
    plays, seq = [], 0
    for dv in (d.get("drives") or {}).get("previous") or []:
        for p in dv.get("plays") or []:
            seq += 1
            st, en = p.get("start") or {}, p.get("end") or {}
            plays.append({
                "game_id": gid, "seq": seq,
                "type": (p.get("type") or {}).get("text", ""),
                "period": (p.get("period") or {}).get("number"),
                "clock": _clock_secs((p.get("clock") or {}).get("displayValue", "")),
                "away_score": p.get("awayScore"), "home_score": p.get("homeScore"),
                "yards": p.get("statYardage"),
                "turnover": bool(p.get("isTurnover", False)),
                "s_down": st.get("down"), "s_dist": st.get("distance"), "s_ytg": st.get("yardsToEndzone"),
                "s_team": str((st.get("team") or {}).get("id", "")),
                "e_down": en.get("down"), "e_dist": en.get("distance"), "e_ytg": en.get("yardsToEndzone"),
                "e_team": str((en.get("team") or {}).get("id", "")),
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
                stats, att = a.get("stats") or [], None
                if "C/ATT" in labels and len(stats) > labels.index("C/ATT"):
                    try:
                        att = int(stats[labels.index("C/ATT")].split("/")[1])
                    except Exception:  # noqa: BLE001
                        att = None
                ath = a.get("athlete") or {}
                passers.append({"game_id": gid, "team_id": tid, "name": ath.get("displayName", ""), "att": att})
    return game, plays, passers, None


def parse(summary_dir, rows, processes=None):
    """rows: iterable of (game_id, season, week, kickoff_utc). Returns games, plays, passers DataFrames."""
    args = [(summary_dir, *r) for r in rows]
    with Pool(processes or max(1, min(4, os.cpu_count() or 1))) as pool:
        res = pool.map(_parse_one, args, chunksize=20)
    games, plays, passers, errors = [], [], [], []
    for g, p, q, e in res:
        if e:
            errors.append(e)
        if g:
            games.append(g)
        plays.extend(p)
        passers.extend(q)
    return pd.DataFrame(games), pd.DataFrame(plays), pd.DataFrame(passers), errors
