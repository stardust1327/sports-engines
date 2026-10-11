"""Download nflverse play-by-play and the schedule file. Past seasons are cached;
the current season and the schedule are refreshed on every run."""
import os
import time
import urllib.request

BASE = "https://github.com/nflverse/nflverse-data/releases/download"


def fetch(url, path, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                raw = r.read()
            tmp = path + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(raw)
            os.replace(tmp, path)
            return
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def get(cache, season):
    """Play-by-play for season-4 through season (the backtest and QB history need them) plus games.csv."""
    os.makedirs(cache, exist_ok=True)
    for y in range(season - 4, season + 1):
        path = os.path.join(cache, f"pbp_{y}.parquet")
        if y == season or not os.path.exists(path):
            fetch(f"{BASE}/pbp/play_by_play_{y}.parquet", path)
    fetch(f"{BASE}/schedules/games.csv", os.path.join(cache, "games.csv"))
