"""Parlay math on the engines' win chances: build one parlay, recommend a set without redundancy, and show exposure.

A parlay wins only if every leg wins. Legs come from different games, so their chances are treated as independent and
a parlay's chance is the product of its legs' chances. No betting line or price is used anywhere (CLAUDE.md rule 4):
the "fair odds" shown are what the engines' own chance would pay with no sportsbook margin.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from parlay_app.slates import SPORT_NAMES, Game

Mode = str  # "highest", "lowest", "range" or "teams"


@dataclass(frozen=True)
class Leg:
    leg_id: str  # "<sport>:<game_id>"
    team: str
    opponent: str
    prob: float
    sport: str
    kickoff_text: str
    sort_time: str  # ISO kickoff, for stable ordering

    @property
    def label(self) -> str:
        return f"{self.team} over {self.opponent}"

    @property
    def tag(self) -> str:
        return f"{self.label} ({SPORT_NAMES[self.sport]}, {self.prob:.1%})"


def legs_from(games: Iterable[Game]) -> list[Leg]:
    """One leg per game with a pick: the engine's pick, at its win chance."""
    return [
        Leg(g.leg_id, g.pick, g.opponent, g.win_prob, g.sport, g.kickoff_text, g.kickoff_utc.isoformat())
        for g in games
        if g.is_pick
    ]


def _by_strength(legs: Iterable[Leg]) -> list[Leg]:
    return sorted(legs, key=lambda leg: (-leg.prob, leg.sort_time, leg.leg_id))


def parlay_prob(legs: Sequence[Leg]) -> float:
    return math.prod(leg.prob for leg in legs)


def fair_american(prob: float) -> str:
    """American odds that a fair bet at this chance would pay (no sportsbook margin)."""
    if not 0.0 < prob < 1.0:
        return "n/a"
    if prob >= 0.5:
        return f"-{round(100 * prob / (1 - prob))}"
    return f"+{round(100 * (1 - prob) / prob)}"


def pick_legs(
    legs: Sequence[Leg],
    n_legs: int,
    mode: Mode,
    *,
    low: float = 0.5,
    high: float = 1.0,
    chosen: Iterable[str] = (),
) -> list[Leg]:
    """Legs for one parlay: the n highest or lowest chances, the n strongest inside a chance range, or chosen legs."""
    if mode == "teams":
        wanted = set(chosen)
        return _by_strength(leg for leg in legs if leg.leg_id in wanted)
    if mode == "highest":
        pool = _by_strength(legs)
    elif mode == "lowest":
        pool = sorted(legs, key=lambda leg: (leg.prob, leg.sort_time, leg.leg_id))
    elif mode == "range":
        pool = _by_strength(leg for leg in legs if low <= leg.prob <= high)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return _by_strength(pool[: max(0, n_legs)])


def recommend(
    legs: Sequence[Leg],
    n_parlays: int,
    legs_per: int,
    *,
    max_uses: int,
    max_shared: int,
    min_prob: float = 0.5,
) -> list[tuple[Leg, ...]]:
    """Up to n_parlays parlays of legs_per legs each, strongest first, built greedily so that

    * no team appears in more than max_uses parlays (1 = every parlay uses different teams), and
    * no two parlays share more than max_shared legs (so a single loss can't sink a whole set of near-copies).

    Each parlay takes the strongest legs that still fit both limits. It stops early when no further parlay fits;
    the caller should say so rather than relax the limits silently.
    """
    if legs_per < 1 or n_parlays < 1:
        return []
    max_shared = min(max_shared, legs_per - 1)  # two parlays can never be identical
    pool = _by_strength(leg for leg in legs if leg.prob >= min_prob)
    uses: Counter[str] = Counter()
    chosen: list[tuple[Leg, ...]] = []
    for _ in range(n_parlays):
        current: list[Leg] = []
        ids: set[str] = set()
        for leg in pool:
            if uses[leg.leg_id] >= max_uses:
                continue
            trial = ids | {leg.leg_id}
            if any(len(trial & {other.leg_id for other in parlay}) > max_shared for parlay in chosen):
                continue
            current.append(leg)
            ids = trial
            if len(current) == legs_per:
                break
        if len(current) < legs_per:
            break
        chosen.append(tuple(current))
        uses.update(ids)
    return chosen


@dataclass(frozen=True)
class Exposure:
    leg: Leg
    parlays: int  # how many of the set's parlays lose if this leg loses


def exposure(parlays: Sequence[Sequence[Leg]]) -> list[Exposure]:
    """Every leg in the set and how many parlays depend on it, most-used first."""
    counts: Counter[str] = Counter(leg.leg_id for parlay in parlays for leg in parlay)
    legs = {leg.leg_id: leg for parlay in parlays for leg in parlay}
    return sorted(
        (Exposure(legs[i], n) for i, n in counts.items()),
        key=lambda e: (-e.parlays, e.leg.prob, e.leg.leg_id),
    )


@dataclass(frozen=True)
class SetOutlook:
    expected_wins: float  # average number of winning parlays
    any_wins: float  # chance that at least one parlay wins
    all_lose: float


def outlook(parlays: Sequence[Sequence[Leg]], *, sims: int = 40_000, seed: int = 7) -> SetOutlook:
    """How a set of parlays should do together. Shared legs make parlays win or lose together, so the chance that at
    least one wins is simulated (every leg independent, at its own chance); the expected count is exact."""
    if not parlays:
        return SetOutlook(0.0, 0.0, 1.0)
    expected = sum(parlay_prob(p) for p in parlays)
    legs = {leg.leg_id: leg for parlay in parlays for leg in parlay}
    order = list(legs)
    probs = np.array([legs[i].prob for i in order])
    wins = np.random.default_rng(seed).random((sims, len(order))) < probs
    column = {leg_id: j for j, leg_id in enumerate(order)}
    hits = np.zeros(sims, dtype=bool)
    for parlay in parlays:
        hits |= wins[:, [column[leg.leg_id] for leg in parlay]].all(axis=1)
    any_wins = float(hits.mean())
    return SetOutlook(expected, any_wins, 1.0 - any_wins)
