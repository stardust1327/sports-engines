"""Why the NFL engine picks a team, in points, from its own logged numbers.

The engine's win chance is a logistic regression with no intercept on three numbers (METHOD.md section 5):

    log-odds(home wins) = a * net_epa + b * net_sr + c * is_home

The fitted a, b and c aren't saved, but every logged game satisfies this equation, so they are recovered exactly from
the week's picks file by least squares (a file merged from two runs fits to within a hair). Log-odds become points on
the engine's own scale: results/team_notes.py ENGINE_PTS_PER_LOGIT (7.8 points per unit, the slope of the final margin
on the engine's log-odds over its 2019-2025 backtest).

With the team ratings behind the week (nfl_ui/ratings.py), each game's edge splits further into the four units that
make it up, since net_epa = (home offense + away defense) - (away offense + home defense), and the same for success
rate. Nothing here changes a number: the logged win chance stays the authority, and the parts add up to it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from nfl_ui.week import EngineNumbers, Rating, WeekGame

PTS_PER_LOGIT = 7.8  # results/team_notes.py ENGINE_PTS_PER_LOGIT (tests check the two agree)
MAX_FIT_ERROR = 0.01  # log-odds; above this the week's numbers don't fit one formula, so no breakdown is shown
EVEN = 0.3  # points; a reason smaller than this is listed as about even rather than helping a side


@dataclass(frozen=True)
class Formula:
    epa: float  # log-odds per unit of net_epa
    sr: float  # log-odds per unit of net_sr
    home: float  # log-odds for home field

    @property
    def home_points(self) -> float:
        return PTS_PER_LOGIT * self.home


def formula(numbers: Sequence[EngineNumbers]) -> Formula | None:
    """The week's calibration, recovered from its logged games; None if it can't be pinned down."""
    if len(numbers) < 3:
        return None
    x = np.array([[n.net_epa, n.net_sr, n.is_home] for n in numbers], dtype=float)
    p = np.clip(np.array([n.p_home for n in numbers], dtype=float), 1e-12, 1 - 1e-12)
    y = np.log(p / (1 - p))
    if np.linalg.matrix_rank(x) < 3:
        return None
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    if float(np.abs(x @ coef - y).max()) > MAX_FIT_ERROR:
        return None
    return Formula(*(float(c) for c in coef))


def logit(p: float) -> float:
    return math.log(p / (1 - p))


def points(p: float) -> float:
    """A win chance as the engine's edge in points (positive favors that side)."""
    return PTS_PER_LOGIT * logit(p)


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@dataclass(frozen=True)
class Reason:
    label: str  # "Jaguars offense"
    detail: str  # "8th of 32 in value per play, 5th in success rate"
    points: float  # positive helps the pick, negative helps the opponent


@dataclass(frozen=True)
class Why:
    pick: str
    opponent: str
    pick_is_home: bool
    model_points: float  # the engine alone, from the pick's side (negative if the model alone favors the opponent)
    note_points: float  # the owner's team notes, from the pick's side (0 while they're off, since 2026-10-17)
    reasons: tuple[Reason, ...]  # biggest first, the team note included; they add up to total_points
    detailed: bool  # split by unit from the team ratings, or only into the three logged edges

    @property
    def total_points(self) -> float:
        return self.model_points + self.note_points

    @property
    def helping_pick(self) -> list[Reason]:
        return [r for r in self.reasons if r.points >= EVEN]

    @property
    def helping_opponent(self) -> list[Reason]:
        return [r for r in self.reasons if r.points <= -EVEN]

    @property
    def even(self) -> list[Reason]:
        """Units too close to average to help either side much."""
        return [r for r in self.reasons if abs(r.points) < EVEN]


def _unit(team: str, rating: Rating, unit: str, n_teams: int) -> tuple[str, str]:
    if unit == "off":
        detail = (
            f"{ordinal(rating.ranks['off_epa'])} of {n_teams} in expected points per play, "
            f"{ordinal(rating.ranks['off_sr'])} in success rate"
        )
        return f"{team} offense", detail
    detail = (
        f"{ordinal(rating.ranks['def_epa'])} of {n_teams} in expected points allowed per play, "
        f"{ordinal(rating.ranks['def_sr'])} in success rate allowed"
    )
    return f"{team} defense", detail


def unit_points(f: Formula, rating: Rating, unit: str) -> float:
    """What one unit adds to its own team's edge, in points (offense: what it gains; defense: what it stops)."""
    if unit == "off":
        return PTS_PER_LOGIT * (f.epa * rating.off_epa + f.sr * rating.off_sr)
    return -PTS_PER_LOGIT * (f.epa * rating.def_epa + f.sr * rating.def_sr)


def power(f: Formula, rating: Rating) -> float:
    """The team's rating in points against a league-average team on a neutral field. Two teams' powers differ by the
    engine's edge between them (plus home field), because each edge is offense and defense of one minus the other."""
    return unit_points(f, rating, "off") + unit_points(f, rating, "def")


def _home_reason(wg: WeekGame, f: Formula, sign: float) -> Reason | None:
    n = wg.numbers
    if not n.is_home:
        return None
    return Reason(f"{wg.game.home} home field", "", sign * f.home_points * n.is_home)


def explain(wg: WeekGame, f: Formula | None, ratings: dict[str, Rating]) -> Why | None:
    """Why the official pick (team notes applied), from the pick's side; None for a no-pick or without a formula."""
    g, n = wg.game, wg.numbers
    if not g.is_pick or n is None or f is None:
        return None
    pick_is_home = g.pick == g.home
    sign = 1.0 if pick_is_home else -1.0
    model = sign * points(n.p_home)
    note = sign * g.note_pts_home
    opponent = g.opponent
    home = _home_reason(wg, f, sign)
    pick_id, opp_id = (wg.home_id, wg.away_id) if pick_is_home else (wg.away_id, wg.home_id)
    if pick_id in ratings and opp_id in ratings:
        n_teams = len(ratings)
        reasons = []
        for team, tid, side in ((g.pick, pick_id, 1.0), (opponent, opp_id, -1.0)):
            for unit in ("off", "def"):
                label, detail = _unit(team, ratings[tid], unit, n_teams)
                reasons.append(Reason(label, detail, side * unit_points(f, ratings[tid], unit)))
        detailed = True
    else:
        reasons = [
            Reason(
                "Expected points per play", "offense and defense together", sign * PTS_PER_LOGIT * f.epa * n.net_epa
            ),
            Reason("Success rate", "offense and defense together", sign * PTS_PER_LOGIT * f.sr * n.net_sr),
        ]
        detailed = False
    if home:
        reasons.append(home)
    if note:
        reasons.append(Reason("Your team note", g.note, note))
    reasons.sort(key=lambda r: -abs(r.points))
    return Why(g.pick, opponent, pick_is_home, model, note, tuple(reasons), detailed)
