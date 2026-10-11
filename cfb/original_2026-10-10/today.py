import json, sys, datetime
import pandas as pd
d = json.load(open(sys.argv[1]))
USER = [("Texas","Oklahoma"),("Stanford","Notre Dame"),("Ole Miss","Vanderbilt"),("UCLA","Oregon"),
        ("Houston","Kansas State"),("Duke","Georgia Tech"),("Virginia Tech","California"),("Illinois","Michigan State"),
        ("Charlotte","North Texas"),("Tulsa","Navy"),("Eastern Michigan","Akron"),("Buffalo","Toledo"),
        ("Central Michigan","Ohio"),("Kent State","Western Michigan"),("UConn","Temple"),("Maryland","Ohio State"),
        ("Tennessee","Arkansas"),("San Diego State","Oregon State"),("LSU","Kentucky"),("UAB","Memphis"),
        ("Nevada","UTEP"),("North Dakota State","UNLV"),("Coastal Carolina","Marshall")]
rows = []
for e in d["events"]:
    c = e["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    utc = datetime.datetime.strptime(e["date"], "%Y-%m-%dT%H:%MZ")
    if utc < datetime.datetime(2026, 10, 10, 19, 30):
        continue
    an, hn = t["away"]["team"]["location"], t["home"]["team"]["location"]
    rows.append({"game_id": e["id"], "kick_phx": (utc - datetime.timedelta(hours=7)).strftime("%I:%M %p").lstrip("0"),
                 "away_id": t["away"]["team"]["id"], "home_id": t["home"]["team"]["id"],
                 "away_name": an, "home_name": hn, "neutral": bool(c.get("neutralSite", False)),
                 "in_user_list": (an, hn) in USER, "venue": (c.get("venue") or {}).get("fullName", "")})
df = pd.DataFrame(rows)
df.to_csv(sys.argv[2], index=False)
print(df[["kick_phx","away_name","home_name","neutral","in_user_list","venue"]].to_string())
print("user games matched:", int(df.in_user_list.sum()), "of", len(USER))
