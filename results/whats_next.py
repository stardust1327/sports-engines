"""What the scheduled check-ins should work on: the NFL week just played and the
next one, the college dates with games in the next 8 days, and which of them
already have logged picks or grades in results/.

  python3 results/whats_next.py
  python3 results/whats_next.py --today 2026-10-13      (pretend it's that day)

Reads ESPN's public scoreboards. All times Pacific.
"""
import argparse
import datetime
import json
import os
import time
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
NFL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={stype}&week={week}&limit=400"
CFB = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates={day}&groups=80&limit=400"
PT = ZoneInfo("America/Los_Angeles")


def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return json.load(r)
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
            time.sleep(2 * (i + 1))


def when(iso):
    t = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc).astimezone(PT)
    return t


def fmt(t):
    return t.strftime("%a %b %d %I:%M %p").replace(" 0", " ")


def nfl_weeks(season):
    """Regular-season weeks (seasontype 2), then playoffs (3), as (label, stype, week, events)."""
    out = []
    for stype, weeks in ((2, range(1, 19)), (3, range(1, 6))):
        for w in weeks:
            ev = get(NFL.format(season=season, stype=stype, week=w)).get("events", [])
            if ev:
                out.append((f"week {w}" if stype == 2 else f"playoff round {w}", stype, w, ev))
    return out


def exists(name):
    return "yes" if os.path.exists(os.path.join(HERE, name)) else "no"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="YYYY-MM-DD (default: today, Pacific)")
    a = ap.parse_args()
    now = datetime.datetime.now(PT)
    today = datetime.date.fromisoformat(a.today) if a.today else now.date()
    season = today.year if today.month >= 7 else today.year - 1
    print(f"Today (Pacific): {today}  |  season {season}")

    # ---- NFL
    weeks = nfl_weeks(season)
    nxt = prev = None
    for i, (label, stype, w, ev) in enumerate(weeks):
        if any(e["status"]["type"]["state"] != "post" for e in ev):
            nxt = (label, stype, w, ev)
            prev = weeks[i - 1] if i > 0 else None
            break
    if prev is None and nxt is None and weeks:
        prev = weeks[-1]
    for tag, wk in (("NFL last week", prev), ("NFL next week", nxt)):
        if not wk:
            print(f"{tag}: none")
            continue
        label, stype, w, ev = wk
        kicks = sorted(when(e["date"]) for e in ev)
        states = [e["status"]["type"]["state"] for e in ev]
        ww = f"{w:02d}"
        print(f"{tag}: {label} (season type {stype}), {len(ev)} games, {states.count('post')} final, "
              f"{states.count('in')} in progress, {states.count('pre')} not started")
        print(f"  kickoffs: {fmt(kicks[0])} to {fmt(kicks[-1])} PT")
        print(f"  game dates (Eastern, for nfl_cfbmethod/run.py --date): "
              + " ".join(sorted({datetime.datetime.strptime(e['date'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=datetime.timezone.utc)
                                 .astimezone(ZoneInfo('America/New_York')).date().isoformat() for e in ev})))
        if stype == 2:
            print(f"  logged: engine picks {exists(f'nfl_cfbmethod_{season}_week{ww}_picks.csv')}, framework picks "
                  f"{exists(f'prompt_nfl_{season}_week{ww}_picks.csv')}; graded: engine "
                  f"{exists(f'nfl_cfbmethod_{season}_week{ww}_graded.csv')}, framework "
                  f"{exists(f'prompt_nfl_{season}_week{ww}_graded.csv')}")
        for e in sorted(ev, key=lambda e: e["date"]):
            print(f"    {fmt(when(e['date']))}  {e['shortName']:<12} {e['status']['type']['state']}")

    # ---- college: the last 8 days (to grade) and the next 8 days (to pick)
    print("College, last 8 days (dates with logged picks):")
    for d in range(8, 0, -1):
        day = (today - datetime.timedelta(days=d)).isoformat()
        if os.path.exists(os.path.join(HERE, f"cfb_{day}_picks.csv")):
            print(f"  {day}: graded engine {exists(f'cfb_{day}_graded.csv')}, framework {exists(f'prompt_cfb_{day}_graded.csv')}")
    print("College, today and the next 7 days (FBS games not yet started):")
    for d in range(0, 8):
        day = today + datetime.timedelta(days=d)
        ev = get(CFB.format(day=day.strftime("%Y%m%d"))).get("events", [])
        pre = [e for e in ev if e["status"]["type"]["state"] == "pre"]
        if not ev:
            continue
        kicks = sorted(when(e["date"]) for e in pre) if pre else []
        span = f", kickoffs {fmt(kicks[0])} to {fmt(kicks[-1])} PT" if kicks else ""
        print(f"  {day.isoformat()}: {len(ev)} games, {len(pre)} not started{span}; logged: engine "
              f"{exists(f'cfb_{day.isoformat()}_picks.csv')}, framework {exists(f'prompt_cfb_{day.isoformat()}_picks.csv')}")


if __name__ == "__main__":
    main()
