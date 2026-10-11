import json, sys
d = json.load(open(sys.argv[1]))
res = {}
for e in d["events"]:
    c = e["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    a, h = t["away"], t["home"]
    st = e["status"]["type"]
    res[(a["team"]["location"], h["team"]["location"])] = (st["state"], st["shortDetail"], int(a.get("score") or 0), int(h.get("score") or 0))
def winner(k):
    s = res.get(k)
    if not s: return None, "NOT FOUND"
    state, det, sa, sh = s
    if state != "post": return None, f"{det} {sa}-{sh}"
    return (k[0] if sa > sh else k[1]), f"{k[0]} {sa}, {k[1]} {sh}"
# list pasted by the user (all 36 games)
pasted = [("Arizona","West Virginia","West Virginia"),("Texas A&M","Missouri","Texas A&M"),("Indiana","Nebraska","Indiana"),
 ("UCF","Oklahoma State","Oklahoma State"),("Sacramento State","Bowling Green","Bowling Green"),("North Carolina","Pittsburgh","Pittsburgh"),
 ("Tulane","Army","Army"),("Wake Forest","NC State","NC State"),("Ball State","Northwestern","Northwestern"),
 ("South Carolina","Florida","South Carolina"),("Old Dominion","App State","App State"),("Rice","East Carolina","East Carolina"),
 ("Miami (OH)","Massachusetts","Miami (OH)"),("Illinois","Michigan State","Illinois"),("Tulsa","Navy","Navy"),
 ("Ole Miss","Vanderbilt","Ole Miss"),("Virginia Tech","California","California"),("Buffalo","Toledo","Toledo"),
 ("UCLA","Oregon","Oregon"),("Eastern Michigan","Akron","Eastern Michigan"),("Central Michigan","Ohio","Ohio"),
 ("Duke","Georgia Tech","Georgia Tech"),("Kent State","Western Michigan","Western Michigan"),("Texas","Oklahoma","Texas"),
 ("Houston","Kansas State","Kansas State"),("Charlotte","North Texas","North Texas"),("Stanford","Notre Dame","Notre Dame"),
 ("UConn","Temple","UConn"),("Maryland","Ohio State","Ohio State"),("Tennessee","Arkansas","Tennessee"),
 ("San Diego State","Oregon State","Oregon State"),("North Dakota State","UNLV","UNLV"),("LSU","Kentucky","Kentucky"),
 ("UAB","Memphis","Memphis"),("Coastal Carolina","Marshall","Marshall"),("Nevada","UTEP","Nevada")]
# my engine's picks as sent (tier), 12:30 PM on
mine = [("Stanford","Notre Dame","Notre Dame","70+"),("Charlotte","North Texas","North Texas","70+"),("Buffalo","Toledo","Toledo","70+"),
 ("Maryland","Ohio State","Ohio State","70+"),("San Diego State","Oregon State","Oregon State","70+"),("UAB","Memphis","Memphis","70+"),
 ("Kent State","Western Michigan","Western Michigan","70+"),
 ("Central Michigan","Ohio","Ohio","60-70"),("Illinois","Michigan State","Michigan State","60-70"),("UConn","Temple","Temple","60-70"),
 ("LSU","Kentucky","LSU","60-70"),("Tulsa","Navy","Navy","60-70"),("Houston","Kansas State","Houston","60-70"),
 ("Texas","Oklahoma","Texas","60-70"),("Coastal Carolina","Marshall","Marshall","60-70"),
 ("Duke","Georgia Tech","Georgia Tech","flip"),("Eastern Michigan","Akron","Akron","flip"),("Nevada","UTEP","Nevada","flip"),
 ("North Dakota State","UNLV","North Dakota State","flip")]
nopick = [("UCLA","Oregon"),("Tennessee","Arkansas"),("Ole Miss","Vanderbilt"),("Virginia Tech","California")]
print("== PASTED LIST ==")
w = l = 0; late = {"w":0,"l":0}
late_keys = set((a,h) for a,h,_,_ in mine) | set(nopick)
for a,h,p in pasted:
    win, txt = winner((a,h))
    if win is None: print("  ??", a, "@", h, txt); continue
    ok = win == p; w += ok; l += (not ok)
    if (a,h) in late_keys: late["w" if ok else "l"] += 1
    print(f"  {'W' if ok else 'L'}  pick {p:18s} | {txt}")
print(f"PASTED: {w}-{l} overall | same 23 games as mine: {late['w']}-{late['l']}")
print("== MINE ==")
tiers = {}
for a,h,p,t in mine:
    win, txt = winner((a,h))
    if win is None: print("  ??", a, "@", h, txt); continue
    ok = win == p; tiers.setdefault(t,[0,0]); tiers[t][0 if ok else 1] += 1
    print(f"  {'W' if ok else 'L'}  [{t}] pick {p:18s} | {txt}")
print("MINE by tier:", tiers, "| total:", sum(v[0] for v in tiers.values()), "-", sum(v[1] for v in tiers.values()))
for a,h in nopick: print("  no-pick:", winner((a,h))[1])
print("== OTHER ==")
for k in [("USC","Penn State"),("Georgia","Alabama")]: print(" ", winner(k)[1])
print("parlay legs:", [winner(k)[1] for k in [("Maryland","Ohio State"),("UCLA","Oregon"),("Stanford","Notre Dame")]])
