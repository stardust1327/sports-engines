import sys
import pandas as pd
q = pd.read_csv(sys.argv[1], dtype={"team_id": str, "athlete_id": str, "game_id": str})
t = pd.read_csv(sys.argv[2], dtype=str)
ids = {}
for _, r in t.iterrows():
    ids[r["home_id"]] = r["home_name"]; ids[r["away_id"]] = r["away_name"]
q = q[q["team_id"].isin(ids)]
q = q.sort_values(["team_id", "date", "att"], ascending=[True, True, False])
top = q.groupby(["team_id", "game_id"]).head(1)  # each game's main passer
rows = []
for tid, name in ids.items():
    tg = top[top.team_id == tid].sort_values("date")
    allq = q[q.team_id == tid]
    if tg.empty:
        rows.append({"team": name, "games": 0}); continue
    tot = allq.groupby("name")["att"].sum().sort_values(ascending=False)
    last = tg.iloc[-1]
    lastgame = allq[allq.game_id == last.game_id].sort_values("att", ascending=False)
    starters = tg["name"].tolist()
    rows.append({"team": name, "games": len(tg), "season_main": tot.index[0], "season_att": int(tot.iloc[0]),
                 "last_date": last.date[:10], "last_main": last["name"], "last_att": int(last.att),
                 "last_others": "; ".join(f"{a.name if False else a['name']} {int(a.att)}" for _, a in lastgame.iloc[1:3].iterrows()),
                 "game_mains": " > ".join(starters),
                 "flag": ("CHANGE" if last["name"] != tot.index[0] else "") + (" LOWATT" if last.att < 15 else "") + (" SPLIT" if len(set(starters)) > 1 else "")})
df = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(df.to_string())
df.to_csv(sys.argv[3], index=False)
