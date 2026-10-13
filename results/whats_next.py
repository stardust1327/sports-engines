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
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # for team_notes.py
NFL ="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={stype}&week={week}&limit=400"
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


def notes_status(season, week, notes):
    """'team notes: ...' for a logged NFL week: picks with a noted team, and whether they're graded."""
    import pandas as pd
    import team_notes
    path = os.path.join(HERE, f"nfl_cfbmethod_{season}_week{week:02d}_picks.csv")
    if not os.path.exists(path):
        return ""
    a = team_notes.apply(pd.read_csv(path, dtype={"game_id": str}), "engine", notes)
    noted = a[(a.status == "PICK") & (a.note_text.str.len() > 0)]
    if not len(noted):
        return "; team notes: no noted picks"
    g = os.path.join(HERE, team_notes.GRADED_NAME)
    done = os.path.exists(g) and len(pd.read_csv(g).query("season == @season and week == @week"))
    flips = int(noted.note_flips.sum())
    return (f"; team notes: {len(noted)} noted pick(s)" + (f", {flips} changed by a note" if flips else "")
            + f", graded {'yes' if done else 'no'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="YYYY-MM-DD (default: today, Pacific)")
    a = ap.parse_args()
    now = datetime.datetime.now(PT)
    today = datetime.date.fromisoformat(a.today) if a.today else now.date()
    season = today.year if today.month >= 7 else today.year - 1
    print(f"Today (Pacific): {today}  |  season {season}")

    # ---- the owner's team notes (CHECKINS.md "Team notes"); never add, change or remove one unasked
    import team_notes
    notes = team_notes.load()
    live = team_notes.current(notes)

    def until(e):
        end = team_notes.expires_at(notes, e)
        return f", runs out {team_notes.phx(end)}" if end else ""
    print("Team notes in force (the owner's, applied to both NFL models; CHECKINS.md 'Team notes'): "
          + ("; ".join(f"{team_notes.note_text(notes, e)} points (last read {team_notes.phx(e['_t'])}{until(e)})"
                       for e in live) or "none"))
    soon = [e for e in live if team_notes.expires_at(notes, e) is not None
            and team_notes.expires_at(notes, e) - now.astimezone(datetime.timezone.utc) < datetime.timedelta(days=8)]
    if soon:
        print("  Running out within 8 days (ask the owner whether to renew; never renew unasked): "
              + "; ".join(f"{e['team']} {team_notes.phx(team_notes.expires_at(notes, e))}" for e in soon))
    gone = team_notes.expired(notes)
    if gone:
        print("  Expired, no longer applied: " + "; ".join(
            f"{team_notes.note_text(notes, e)} (ran out {team_notes.phx(team_notes.expires_at(notes, e))})" for e in gone))

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
                  f"{exists(f'prompt_nfl_{season}_week{ww}_graded.csv')}{notes_status(season, w, notes)}")
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
