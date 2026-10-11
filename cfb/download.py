"""Download ESPN college football scoreboards and game summaries (play-by-play)
into a local cache. Finished games are cached for good; the current season's
scoreboards are refreshed on every run."""
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_json(url, path=None, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                raw = r.read()
            data = json.loads(raw)
            if path:
                tmp = path + ".tmp"
                with open(tmp, "wb") as fh:
                    fh.write(raw)
                os.replace(tmp, path)
            return data
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def final_games(cache, season, refresh):
    """Final regular-season FBS games for a season: list of (game_id, season, week, kickoff_utc)."""
    folder = os.path.join(cache, "scoreboard")
    os.makedirs(folder, exist_ok=True)
    seen, out = set(), []
    for week in range(1, 17):
        path = os.path.join(folder, f"{season}_w{week}.json")
        if refresh or not os.path.exists(path):
            url = f"{BASE}/scoreboard?dates={season}&seasontype=2&week={week}&groups=80&limit=400"
            data = fetch_json(url, path)
        else:
            data = json.load(open(path))
        for e in data.get("events", []):
            if e["status"]["type"]["state"] == "post" and e["id"] not in seen:
                seen.add(e["id"])
                out.append((e["id"], season, week, e["date"]))
    return out


def summaries(cache, game_ids, workers=16):
    """Download play-by-play summaries not already cached. Returns (number fetched, errors)."""
    folder = os.path.join(cache, "summary")
    os.makedirs(folder, exist_ok=True)
    todo = [g for g in game_ids if not os.path.exists(os.path.join(folder, f"{g}.json"))]

    def one(gid):
        try:
            fetch_json(f"{BASE}/summary?event={gid}", os.path.join(folder, f"{gid}.json"))
            return None
        except Exception as ex:  # noqa: BLE001
            return f"{gid}: {ex}"

    with ThreadPoolExecutor(workers) as pool:
        errors = [e for e in pool.map(one, todo) if e]
    return len(todo), errors


def slate(cache, date):
    """Every FBS game on a date (YYYY-MM-DD), with status, teams and neutral-site flag."""
    data = fetch_json(f"{BASE}/scoreboard?dates={date.replace('-', '')}&groups=80&limit=400",
                      os.path.join(cache, f"slate_{date}.json"))
    games = []
    for e in data.get("events", []):
        c = e["competitions"][0]
        t = {x["homeAway"]: x for x in c["competitors"]}
        games.append({
            "game_id": e["id"], "kickoff_utc": e["date"], "state": e["status"]["type"]["state"],
            "away_id": str(t["away"]["team"]["id"]), "home_id": str(t["home"]["team"]["id"]),
            "away_name": t["away"]["team"]["location"], "home_name": t["home"]["team"]["location"],
            "neutral": bool(c.get("neutralSite", False)),
            "venue": (c.get("venue") or {}).get("fullName", ""),
        })
    week = (data.get("week") or {}).get("number")
    return games, week
