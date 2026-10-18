"""Live winner calls (separate from the locked engines; feeds nothing back into them).

Checks every college (FBS) and NFL game in progress on ESPN, reads ESPN's own live
win probability from the game feed, and makes a "call" the first time one team
reaches the threshold (default 98%: right 97% of the time in the 2025 college
backtest, median 12 minutes left; see live/backtest_calls_cfb.txt). Each call is
made once and logged to results/live_calls_<date>.csv with the time, score and
win chance, so it can be graded after the game (--grade).

  python3 live/calls.py                 # check games in progress, print new calls
  python3 live/calls.py --threshold 0.95
  python3 live/calls.py --grade --date 2026-10-17

No betting lines or odds are read. ESPN's win probability is ESPN's own model.
"""
import argparse
import datetime
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
PT = ZoneInfo("America/Los_Angeles")
SPORTS = {"college": ("college-football", "&groups=80&limit=400"), "nfl": ("nfl", "")}
BASE = "https://site.api.espn.com/apis/site/v2/sports/football/{}"
COLS = ["sport", "game_id", "matchup", "called_at_pt", "period", "clock", "score", "call", "win_chance",
        "threshold", "final", "result"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def log_path(day):
    return os.path.join(RES, f"live_calls_{day}.csv")


def load(day):
    p = log_path(day)
    return pd.read_csv(p, dtype={"game_id": str}) if os.path.exists(p) else pd.DataFrame(columns=COLS)


def events(sport, day):
    path, extra = SPORTS[sport]
    return get(f"{BASE.format(path)}/scoreboard?dates={day.replace('-', '')}{extra}").get("events", [])


def teams(e):
    c = e["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    return t["home"], t["away"]


def check(threshold, day):
    log = load(day)
    done = set(log.game_id)
    new = []
    for sport in SPORTS:
        for e in events(sport, day):
            st = e["status"]["type"]["state"]
            if st != "in" or e["id"] in done:
                continue
            h, a = teams(e)
            hn, an = h["team"]["location"] if sport == "college" else h["team"]["shortDisplayName"], \
                a["team"]["location"] if sport == "college" else a["team"]["shortDisplayName"]
            try:
                d = get(f"{BASE.format(SPORTS[sport][0])}/summary?event={e['id']}")
            except Exception as ex:  # noqa: BLE001
                print(f"  could not read {an} at {hn}: {ex}")
                continue
            wp = d.get("winprobability") or []
            if not wp:
                continue
            ph = float(wp[-1]["homeWinPercentage"])
            if max(ph, 1 - ph) < threshold:
                continue
            call, p = (hn, ph) if ph >= 0.5 else (an, 1 - ph)
            stt = e["status"]
            new.append({"sport": sport, "game_id": e["id"], "matchup": f"{an} at {hn}",
                        "called_at_pt": datetime.datetime.now(PT).strftime("%m.%d.%Y %-I:%M %p"),
                        "period": stt.get("period"), "clock": stt.get("displayClock"),
                        "score": f"{an} {a.get('score')}, {hn} {h.get('score')}", "call": call,
                        "win_chance": round(p, 4), "threshold": threshold, "final": "", "result": ""})
    if new:
        log = pd.concat([log, pd.DataFrame(new)], ignore_index=True)
        os.makedirs(RES, exist_ok=True)
        log.to_csv(log_path(day), index=False)
    return new


def grade(day):
    log = load(day)
    if log.empty:
        print("no calls logged for", day)
        return
    finals = {}
    for sport in SPORTS:
        for e in events(sport, day):
            if e["status"]["type"]["state"] == "post":
                h, a = teams(e)
                hs, as_ = int(h.get("score") or 0), int(a.get("score") or 0)
                hn = h["team"]["location"] if sport == "college" else h["team"]["shortDisplayName"]
                an = a["team"]["location"] if sport == "college" else a["team"]["shortDisplayName"]
                finals[e["id"]] = (f"{an} {as_}, {hn} {hs}", hn if hs > as_ else an if as_ > hs else "tie")
    for i, r in log.iterrows():
        if r.game_id in finals:
            log.at[i, "final"], w = finals[r.game_id]
            log.at[i, "result"] = "W" if w == r.call else "T" if w == "tie" else "L"
    log.to_csv(log_path(day), index=False)
    g = log[log.result.isin(["W", "L"])]
    print(f"{day}: {int((g.result == 'W').sum())}-{int((g.result == 'L').sum())} on {len(g)} graded calls "
          f"({len(log) - len(g)} not final)")
    for r in log[log.result == "L"].itertuples():
        print(f"  wrong: {r.matchup}: called {r.call} {r.win_chance:.0%} at {r.score} (Q{r.period} {r.clock}); final {r.final}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=0.98)
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today, Pacific)")
    ap.add_argument("--grade", action="store_true")
    a = ap.parse_args()
    day = a.date or datetime.datetime.now(PT).date().isoformat()
    if a.grade:
        grade(day)
        return
    new = check(a.threshold, day)
    if not new:
        print("No new calls.")
    for r in new:
        print(f"CALL: {r['call']} wins ({r['win_chance']:.0%}) | {r['matchup']} | {r['score']} | "
              f"Q{r['period']} {r['clock']} | {r['sport']}")


if __name__ == "__main__":
    main()
