"""The team ratings behind a logged NFL week, for the dashboard's "why". It changes no pick.

  python3 nfl_ui/ratings.py --season 2026 --week 6
  python3 nfl_ui/ratings.py --season 2026 --week 6 --cache /tmp/nflcache

nfl_cfbmethod/run.py logs each game's edges (net_epa, net_sr) but not the team ratings they come from. This rebuilds
the ratings with the engine's own code, loaded unchanged the way run.py itself loads the college code: the same
downloads, plays, expected points model, approved NFL settings and cutoff (games finished before the first kickoff
still to be priced). It checks the ratings against the edges logged in results/nfl_cfbmethod_<season>_week<NN>_picks.csv
and saves results/nfl_cfbmethod_<season>_week<NN>_ratings.csv. It writes no pick and reads no betting line
(CLAUDE.md rules 1-5); nothing in cfb/ or nfl_cfbmethod/ is edited.

A week's picks file can hold games priced by different runs (a Tuesday run, then a Friday re-run merged in for the
games still to come). Each run's cutoff is the first kickoff it priced, and one more finished game refits the expected
points model a little, so by default this tries every kickoff time in the file, earliest first, and saves one set of
ratings per cutoff that reproduces a logged game no earlier cutoff did. The dashboard explains each game with the set
that reproduces it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "nfl_cfbmethod"
EXACT = 1e-9  # an edge rebuilt to within this is the logged edge


def load_engine():
    """nfl_cfbmethod/run.py as a module: its settings and the engine modules it imports (main() is not run)."""
    spec = importlib.util.spec_from_file_location("nfl_cfbmethod_run", ENGINE_DIR / "run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    return run


def picks_path(results: Path, season: int, week: int) -> Path:
    return results / f"nfl_cfbmethod_{season}_week{week:02d}_picks.csv"


def ratings_path(results: Path, season: int, week: int) -> Path:
    return results / f"nfl_cfbmethod_{season}_week{week:02d}_ratings.csv"


def finished_games(run, cache: str, season: int) -> list[tuple]:
    """Every final regular-season game the engine reads (run.py step 2), before any cutoff."""
    rows = []
    for s in range(run.CAL_START - 1, season + 1):
        rows += run.download.final_games(cache, s, refresh=(s == season))
    return rows


def scrimmage_plays(run, cache: str, rows: list[tuple], cutoff: str):
    """run.py steps 2-4 for games finished before `cutoff` (a kickoff_utc string): plays with EPA and success."""
    rows = [r for r in rows if r[3] < cutoff]
    _, errors = run.download.summaries(cache, [r[0] for r in rows])
    games, plays, _, perrs = run.parse.parse(os.path.join(cache, "summary"), rows)
    return run.engine.prepare(run.epa.build(plays, games)), len(rows), errors, perrs


def team_ratings(run, sc, season: int, week: int):
    """The engine's ratings for the week (nfl_engine.ratings with the approved settings): (EPA, success) dicts."""
    return run.nfl_engine.ratings(sc, season, week, run.NFL_ALPHA, run.NFL_RHO, run.HALF_LIFE)


def nicknames(cache: str, season: int) -> dict[str, str]:
    """ESPN team id -> nickname ("Broncos"), from the season's cached scoreboards (the names run.py uses)."""
    names = {}
    folder = Path(cache) / "scoreboard"
    for path in sorted(folder.glob(f"{season}_w*.json")):
        for event in json.loads(path.read_text()).get("events", []):
            for team in event["competitions"][0]["competitors"]:
                names[str(team["team"]["id"])] = team["team"]["name"]
    return names


def gaps(run, ratings, logged: pd.DataFrame) -> list[float]:
    """For every logged game with edges: the largest gap between its logged and rebuilt edges."""
    re_, rs = ratings
    out = []
    for row in logged.dropna(subset=["net_epa", "net_sr"]).itertuples():
        h, a = str(row.home_id), str(row.away_id)
        if h not in re_["off"] or a not in re_["off"]:
            out.append(float("inf"))
            continue
        out.append(max(abs(run.engine.net(re_, h, a) - row.net_epa), abs(run.engine.net(rs, h, a) - row.net_sr)))
    return out


def table(ratings, names: dict[str, str], cutoff: str, reproduced: int) -> pd.DataFrame:
    re_, rs = ratings
    rows = [
        {
            "cutoff_utc": cutoff,
            "team_id": tid,
            "team": names.get(tid, tid),
            "off_epa": re_["off"][tid],
            "def_epa": re_["def"][tid],
            "off_sr": rs["off"][tid],
            "def_sr": rs["def"][tid],
            "plays": int(re_["n"].get(tid, 0)),
            "games_reproduced": reproduced,
        }
        for tid in sorted(re_["off"], key=lambda t: names.get(t, t))
    ]
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument(
        "--cache", default=str(ENGINE_DIR / "cache"), help="the engine's download cache (shared with run.py)"
    )
    ap.add_argument("--results", default=str(REPO_ROOT / "results"))
    ap.add_argument("--cutoff", action="append", help="kickoff_utc to try (default: every kickoff in the picks file)")
    a = ap.parse_args(argv)
    results = Path(a.results)
    path = picks_path(results, a.season, a.week)
    if not path.exists():
        print(f"No logged picks for {a.season} week {a.week}: {path}")
        return 1
    logged = pd.read_csv(path, dtype={"game_id": str, "home_id": str, "away_id": str})
    priced = int(logged["net_epa"].notna().sum())
    cutoffs = a.cutoff or sorted(set(logged["kickoff_utc"]))
    run = load_engine()
    os.makedirs(a.cache, exist_ok=True)
    print(f"Rebuilding the engine's team ratings for {a.season} week {a.week} ({priced} logged edges to match)")
    rows = finished_games(run, a.cache, a.season)
    names = nicknames(a.cache, a.season)
    covered: set[int] = set()
    sets, seen = [], set()
    for cutoff in cutoffs:
        before = frozenset(r[0] for r in rows if r[3] < cutoff)
        if before in seen:  # same games as a cutoff already tried: same ratings
            continue
        seen.add(before)
        sc, n_games, errors, perrs = scrimmage_plays(run, a.cache, rows, cutoff)
        ratings = team_ratings(run, sc, a.season, a.week)
        g = gaps(run, ratings, logged)
        hits = {i for i, x in enumerate(g) if x < EXACT}
        print(
            f"  cutoff {cutoff}: {n_games} games, {len(hits)} of {priced} logged edges reproduced"
            + (f" ({len(errors)} downloads failed, {len(perrs)} games unparsed)" if errors or perrs else "")
        )
        if hits - covered or not sets:
            sets.append(table(ratings, names, cutoff, len(hits)))
            covered |= hits
        if len(covered) == priced:
            break
    target = ratings_path(results, a.season, a.week)
    pd.concat(sets, ignore_index=True).to_csv(target, index=False)
    print(
        f"Saved {target}: {len(sets)} set(s) of team ratings; {len(covered)} of {priced} logged games reproduced exactly"
    )
    if len(covered) < priced:
        print(
            "  Some logged edges weren't reproduced (ESPN may have revised a game file since the run); the dashboard"
            " shows the closest ratings for those games and says so."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
