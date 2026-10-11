"""Quarterback history for every team on a slate, to flag starters that need a news check."""
import pandas as pd


def report(passers, games, season, slate):
    q = passers.merge(games[["game_id", "season", "date"]], on="game_id")
    q = q[(q["season"] == season) & q["att"].notna()].sort_values(["team_id", "date", "att"], ascending=[True, True, False])
    top = q.groupby(["team_id", "game_id"]).head(1)
    teams = {}
    for g in slate:
        teams[g["home_id"]] = g["home_name"]
        teams[g["away_id"]] = g["away_name"]
    rows = []
    for tid, name in teams.items():
        tg = top[top["team_id"] == tid].sort_values("date")
        allq = q[q["team_id"] == tid]
        if tg.empty:
            rows.append({"team": name, "games": 0, "flag": "NO DATA"})
            continue
        totals = allq.groupby("name")["att"].sum().sort_values(ascending=False)
        last = tg.iloc[-1]
        mains = tg["name"].tolist()
        flag = []
        if last["name"] != totals.index[0]:
            flag.append("CHANGE")       # last game's main passer isn't the season leader
        if last["att"] < 15:
            flag.append("LOW ATTEMPTS")  # last starter threw under 15 times (injury? run-heavy?)
        if len(set(mains)) > 1:
            flag.append("SPLIT")         # more than one QB has started
        rows.append({"team": name, "games": len(tg), "season_leader": totals.index[0], "season_att": int(totals.iloc[0]),
                     "last_game": str(last["date"])[:10], "last_starter": last["name"], "last_att": int(last["att"]),
                     "starters_by_game": " > ".join(mains), "flag": " ".join(flag)})
    return pd.DataFrame(rows)
