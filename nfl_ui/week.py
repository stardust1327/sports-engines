"""One NFL week as the NFL engine page shows it, read from the files the engine and the check-ins save in results/.

- the engine's logged picks (nfl_cfbmethod_<season>_week<NN>_picks.csv) with its own numbers for each game, and the
  official picks from parlay_app.slates (the engine's own: the owner turned the team notes off on 2026-10-17,
  CLAUDE.md rule 6)
- the QB report saved with them (_qbs.csv)
- the team ratings behind the picks, when nfl_ui/ratings.py has saved them (_ratings.csv)
- final scores (_graded.csv), and the season's grades (nfl_scorecard.csv), whose closing lines are for grading only
  and never an input (rules 4 and 5)

Read-only: nothing here writes a file or changes a pick.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from parlay_app import slates as S

WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")


@dataclass(frozen=True)
class EngineNumbers:
    """The engine's own numbers for a game, as logged (the home team's point of view)."""

    net_epa: float  # home edge in expected points added per play: its offense plus what the opponent's defense allows
    net_sr: float  # the same edge in success rate
    is_home: float  # 1 = home field, 0 = neutral site
    p_home: float  # the engine's win chance for the home team, before team notes
    home_plays: int
    away_plays: int


@dataclass(frozen=True)
class QB:
    team: str
    games: int
    last_starter: str
    season_leader: str
    starters: tuple[str, ...]  # each game's starter, oldest first
    flag: str  # "" or cfb/qbs.py's flags: CHANGE, LOW ATTEMPTS, SPLIT, NO DATA


@dataclass(frozen=True)
class Rating:
    """A team's ratings from the engine, minus the league average (so 0 is an average unit)."""

    team: str
    off_epa: float  # expected points the offense adds per play (higher is better)
    def_epa: float  # expected points the defense allows per play (lower is better)
    off_sr: float  # offense success rate
    def_sr: float  # success rate the defense allows
    plays: int  # offensive plays this season the ratings use
    ranks: dict[str, int] = field(default_factory=dict, compare=False)  # 1 = best of the league


@dataclass(frozen=True)
class WeekGame:
    game: S.Game
    home_id: str
    away_id: str
    venue: str
    neutral: bool
    numbers: EngineNumbers | None  # None when a team had too few plays for the engine to price the game


@dataclass(frozen=True)
class RatingSet:
    """The league's ratings from one engine run, named by its cutoff (the first kickoff that run priced)."""

    cutoff_utc: str
    teams: dict[str, Rating]  # by ESPN team id


@dataclass
class Week:
    slate: S.Slate
    season: int
    week: int
    games: list[WeekGame]
    qbs: dict[str, QB]  # by team nickname
    rating_sets: list[RatingSet]  # earliest cutoff first; empty until nfl_ui/ratings.py has saved them

    @property
    def latest_ratings(self) -> RatingSet | None:
        return self.rating_sets[-1] if self.rating_sets else None

    def ratings_for(self, wg: WeekGame) -> tuple[RatingSet | None, bool]:
        """The ratings behind a logged game: the set that rebuilds its logged edges (exact), else the latest set."""
        for rs in self.rating_sets:
            if reproduces(wg, rs.teams):
                return rs, True
        return self.latest_ratings, False


def reproduces(wg: WeekGame, teams: dict[str, Rating], tolerance: float = 1e-9) -> bool:
    """Do these ratings rebuild the game's logged edges? (Centering on the league average cancels in an edge.)"""
    n, h, a = wg.numbers, teams.get(wg.home_id), teams.get(wg.away_id)
    if n is None or h is None or a is None:
        return False
    epa = (h.off_epa + a.def_epa) - (a.off_epa + h.def_epa)
    sr = (h.off_sr + a.def_sr) - (a.off_sr + h.def_sr)
    return abs(epa - n.net_epa) <= tolerance and abs(sr - n.net_sr) <= tolerance


def season_week(slate: S.Slate) -> tuple[int, int]:
    match = WEEK_RE.match(slate.key)
    if not match:
        raise ValueError(f"not an NFL week: {slate.key}")
    return int(match[1]), int(match[2])


def weeks(directory: Path | None = None) -> list[S.Slate]:
    """Every logged NFL week, newest first."""
    return [s for s in S.discover_slates(directory) if s.sport == "nfl"]


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "", "nan") else None
    except ValueError:
        return None


def _numbers(row: dict[str, str]) -> EngineNumbers | None:
    values = [_float(row.get(c)) for c in ("net_epa", "net_sr", "is_home", "p_home")]
    if any(v is None for v in values):
        return None
    plays = [int(_float(row.get(c)) or 0) for c in ("home_plays", "away_plays")]
    return EngineNumbers(*values, *plays)


def _qbs(path: Path) -> dict[str, QB]:
    out = {}
    for row in _rows(path):
        starters = tuple(s.strip() for s in (row.get("starters_by_game") or "").split(">") if s.strip())
        out[row["team"]] = QB(
            team=row["team"],
            games=int(_float(row.get("games")) or 0),
            last_starter=row.get("last_starter") or "",
            season_leader=row.get("season_leader") or "",
            starters=starters,
            flag=(row.get("flag") or "").strip(),
        )
    return out


RANKED = {"off_epa": True, "def_epa": False, "off_sr": True, "def_sr": False}  # column: higher is better


def _rating_set(cutoff: str, rows: list[dict[str, str]]) -> RatingSet:
    cols = list(RANKED)
    values = {r["team_id"]: {c: float(r[c]) for c in cols} for r in rows}
    means = {c: sum(v[c] for v in values.values()) / len(values) for c in cols}
    ranks: dict[str, dict[str, int]] = {tid: {} for tid in values}
    for c, higher in RANKED.items():
        order = sorted(values, key=lambda t: (-values[t][c] if higher else values[t][c], t))
        for n, tid in enumerate(order, start=1):
            ranks[tid][c] = n
    teams = {
        r["team_id"]: Rating(
            team=r["team"],
            **{c: values[r["team_id"]][c] - means[c] for c in cols},
            plays=int(_float(r.get("plays")) or 0),
            ranks=ranks[r["team_id"]],
        )
        for r in rows
    }
    return RatingSet(cutoff, teams)


def _ratings(path: Path) -> list[RatingSet]:
    by_cutoff: dict[str, list[dict[str, str]]] = {}
    for row in _rows(path):
        by_cutoff.setdefault(row["cutoff_utc"], []).append(row)
    return [_rating_set(c, rows) for c, rows in sorted(by_cutoff.items())]


def load_week(slate: S.Slate, directory: Path | None = None) -> Week:
    directory = directory or S.results_dir()
    season, week = season_week(slate)
    official = {g.game_id: g for g in S.load_games(slate, directory)}
    games = []
    for row in _rows(slate.picks_path):
        game = official[str(row["game_id"])]
        games.append(
            WeekGame(
                game=game,
                home_id=str(row.get("home_id") or ""),
                away_id=str(row.get("away_id") or ""),
                venue=(row.get("venue") or "").strip(),
                neutral=(row.get("neutral") or "").strip().lower() == "true",
                numbers=_numbers(row),
            )
        )
    games.sort(key=lambda w: (w.game.kickoff_utc, w.game.game_id))
    stem = slate.picks_path.name.removesuffix("_picks.csv")
    return Week(
        slate, season, week, games, _qbs(directory / f"{stem}_qbs.csv"), _ratings(directory / f"{stem}_ratings.csv")
    )


def scorecard(directory: Path | None = None) -> list[dict[str, str]]:
    """Every graded NFL engine pick so far (nfl_cfbmethod/grade.py), closing lines included for the check."""
    return _rows((directory or S.results_dir()) / "nfl_scorecard.csv")
