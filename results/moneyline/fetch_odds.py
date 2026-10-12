"""Opening and closing moneylines from ESPN's odds service, one sportsbook per game (the first one ESPN
lists that has a closing moneyline; live-odds feeds skipped). Cached per game. Grading only.

  python3 fetch_odds.py <sport: nfl|college-football> <cache dir> <file with one ESPN game id per line>
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://sports.core.api.espn.com/v2/sports/football/leagues/{sport}/events/{gid}/competitions/{gid}/odds"


def get(u):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                return {}
            if i == 3:
                raise
        except Exception:  # noqa: BLE001
            if i == 3:
                raise
        time.sleep(1.5 * (i + 1))


def american(x):
    if x is None:
        return None
    s = str(x).strip().upper()
    if s in ("EVEN", "EV", "PK"):
        return 100.0
    try:
        v = float(s.replace("+", ""))
    except ValueError:
        return None
    return v if abs(v) >= 100 else None


def ml(x, side, when):
    return american((((x.get(side) or {}).get(when) or {}).get("moneyLine") or {}).get("american"))


def one(sport, cache, gid):
    path = os.path.join(cache, f"{gid}.json")
    if os.path.exists(path):
        return "cached"
    lst = get(BASE.format(sport=sport, gid=gid))
    rec = {"game_id": gid, "provider": None, "h_open": None, "a_open": None, "h_close": None, "a_close": None,
           "open_provider": None}
    for it in lst.get("items", []):
        x = get(it["$ref"].replace("http://", "https://")) if "$ref" in it else it
        prov = (x.get("provider") or {}).get("name") or ""
        if "live" in prov.lower():
            continue
        hc, ac = ml(x, "homeTeamOdds", "close"), ml(x, "awayTeamOdds", "close")
        ho, ao = ml(x, "homeTeamOdds", "open"), ml(x, "awayTeamOdds", "open")
        if rec["open_provider"] is None and ho is not None and ao is not None:
            rec.update(open_provider=prov, h_open=ho, a_open=ao)
        if hc is not None and ac is not None:
            rec.update(provider=prov, h_close=hc, a_close=ac)
            if ho is not None and ao is not None:          # open and close from the same book when it has both
                rec.update(open_provider=prov, h_open=ho, a_open=ao)
            break
    tmp = path + ".tmp"
    json.dump(rec, open(tmp, "w"))
    os.replace(tmp, path)
    return "fetched"


def main():
    sport, cache, idfile = sys.argv[1:4]
    os.makedirs(cache, exist_ok=True)
    ids = sorted({x.strip() for x in open(idfile) if x.strip()})
    t = time.time()
    errs = []

    def safe(g):
        try:
            return one(sport, cache, g)
        except Exception as ex:  # noqa: BLE001
            errs.append(f"{g}: {ex}")
            return "error"

    with ThreadPoolExecutor(16) as p:
        res = list(p.map(safe, ids))
    print(f"{sport}: {len(ids)} games, {res.count('fetched')} fetched, {res.count('cached')} cached, "
          f"{len(errs)} errors, {time.time() - t:.0f}s", errs[:3])


if __name__ == "__main__":
    main()
