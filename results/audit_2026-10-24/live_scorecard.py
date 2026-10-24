"""Every logged, graded pick in 2026 for all four models, re-verified against ESPN finals."""
import glob, json, os, re, sys, time, urllib.request
import numpy as np, pandas as pd

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.dirname(os.path.abspath(__file__))

def espn_final(sport, gid):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/{sport}/summary?event={gid}"
    for i in range(4):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
            break
        except Exception:
            time.sleep(2 * (i + 1))
    c = d["header"]["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    return (c["status"]["type"]["state"], t["away"]["team"]["location"], t["home"]["team"]["location"],
            t["away"]["team"].get("name", ""), t["home"]["team"].get("name", ""),
            int(t["away"].get("score") or 0), int(t["home"].get("score") or 0))

rows = []
# college engine + framework, 10-13 on (graded files carry game_id)
for f in sorted(glob.glob(f"{R}/cfb_2026-*_graded.csv")) + sorted(glob.glob(f"{R}/prompt_cfb_2026-*_graded.csv")):
    d = pd.read_csv(f, dtype={"game_id": str})
    model = "college framework" if os.path.basename(f).startswith("prompt_") else "college engine"
    date = re.search(r"(\d{4}-\d\d-\d\d)", f).group(1)
    for r in d.itertuples():
        rows.append(dict(model=model, slate=date, sport="college-football", game_id=r.game_id, away=r.away, home=r.home,
                         status=r.status, pick=r.pick, pick_prob=r.pick_prob, logged_result=r.result))
# NFL engine + framework
for f in sorted(glob.glob(f"{R}/nfl_cfbmethod_2026_week*_graded.csv")) + sorted(glob.glob(f"{R}/prompt_nfl_2026_week*_graded.csv")):
    d = pd.read_csv(f, dtype={"game_id": str})
    model = "NFL framework" if os.path.basename(f).startswith("prompt_") else "NFL engine"
    wk = int(re.search(r"week(\d+)", f).group(1))
    for r in d.itertuples():
        rows.append(dict(model=model, slate=f"week {wk}", sport="nfl", game_id=r.game_id, away=r.away, home=r.home,
                         status=r.status, pick=r.pick, pick_prob=r.pick_prob, logged_result=r.result))
L = pd.DataFrame(rows)

# re-verify every pick against ESPN's final score
cache = {}
for gid, sport in L[["game_id", "sport"]].drop_duplicates().itertuples(index=False):
    cache[gid] = espn_final(sport, gid)
def regrade(r):
    if r.status != "PICK":
        return pd.Series({"espn_state": cache[r.game_id][0], "espn_away": cache[r.game_id][5], "espn_home": cache[r.game_id][6], "regraded": None})
    st, aloc, hloc, anick, hnick, a_sc, h_sc = cache[r.game_id]
    home_names, away_names = {hloc, hnick, r.home}, {aloc, anick, r.away}
    if r.pick in home_names and r.pick not in away_names:
        side = "home"
    elif r.pick in away_names and r.pick not in home_names:
        side = "away"
    else:
        side = "?"
    if st != "post":
        res = "pending"
    elif a_sc == h_sc:
        res = "T"
    else:
        res = "W" if (side == "home") == (h_sc > a_sc) else "L"
    return pd.Series({"espn_state": st, "espn_away": a_sc, "espn_home": h_sc, "regraded": res if side != "?" else "NAME?"})
L = pd.concat([L, L.apply(regrade, axis=1)], axis=1)
L.to_csv(f"{OUT}/live_picks_2026.csv", index=False)

# the 10-10 college engine slate (old format, no game ids)
old = pd.read_csv(f"{R}/cfb_2026-10-10.csv")
old = old[old.status == "PICK"]

P = L[L.status == "PICK"].copy()
mism = P[(P.logged_result.astype(str) != P.regraded.astype(str))]
print("re-grade mismatches:", len(mism))
if len(mism):
    print(mism[["model", "slate", "away", "home", "pick", "logged_result", "regraded", "espn_away", "espn_home"]].to_string())

def summ(df, label):
    g = df[df.regraded.isin(["W", "L", "T"])]
    w, l, t = (g.regraded == "W").sum(), (g.regraded == "L").sum(), (g.regraded == "T").sum()
    exp = g.pick_prob.sum(); var = (g.pick_prob * (1 - g.pick_prob)).sum()
    decided = g[g.regraded != "T"]
    brier = ((decided.pick_prob - (decided.regraded == "W")) ** 2).mean()
    return f"{label:34s} {w:3d}-{l:<3d}{'-'+str(t) if t else '  '}  {w/(w+l):.1%}  expected wins {exp:5.1f} (+/- {np.sqrt(var):.1f})  Brier {brier:.3f}"

print()
for m in ["college engine", "college framework", "NFL engine", "NFL framework"]:
    sub = P[P.model == m]
    print(summ(sub, m + " (all)"))
    for s in sub.slate.unique():
        print("   ", summ(sub[sub.slate == s], s))
w = (old.result == "W").sum(); l = (old.result == "L").sum()
print(f"\ncollege engine 2026-10-10 (old file): {w}-{l}, expected {old.win_prob.sum():.1f}")
