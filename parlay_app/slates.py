"""The engines' saved picks, read as slates of games for the parlay builder.

Read-only. Picks come from the files the engines save in results/ (CLAUDE.md rule 5): college picks by date
(cfb_<date>_picks.csv) and NFL picks by week (nfl_cfbmethod_<season>_week<NN>_picks.csv). The owner turned the NFL
team notes off on 2026-10-17 (rule 6), so official picks are the engines' own; the code that applied them through
results/team_notes.py stays behind TEAM_NOTES_ON, switched off, the way results/make_report.py keeps it. Results come
from the matching *_graded.csv files; only their scores are read, never their betting lines (rules 4 and 5).
"""

from __future__ import annotations

import csv
import datetime as dt
import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc

CFB_RE = re.compile(r"^cfb_(\d{4}-\d{2}-\d{2})_picks\.csv$")
NFL_RE = re.compile(r"^nfl_cfbmethod_(\d{4})_week(\d{2})_picks\.csv$")
SPORT_NAMES = {"cfb": "College", "nfl": "NFL"}
TEAM_NOTES_ON = False  # turned off by the owner 2026-10-17 ("Turn it off and drop the page"); CLAUDE.md rule 6

Sport = Literal["cfb", "nfl"]


def results_dir() -> Path:
    """results/ in this repository, or SPORTS_RESULTS_DIR (tests, other checkouts)."""
    return Path(os.environ.get("SPORTS_RESULTS_DIR") or REPO_ROOT / "results")


@dataclass(frozen=True)
class Slate:
    sport: Sport
    key: str  # "2026-10-17" (college date) or "2026-W06" (NFL week)
    label: str  # "College · Sat Oct 17, 2026" or "NFL · 2026 Week 6"
    picks_path: Path
    graded_path: Path | None


@dataclass(frozen=True)
class Game:
    sport: Sport
    slate_key: str
    game_id: str
    kickoff_utc: dt.datetime
    kickoff_text: str  # as the engine printed it (its local time zone)
    away: str
    home: str
    status: str  # "PICK" or "NO PICK"
    reason: str  # why there is no pick
    pick: str | None  # official pick (the engine's own while TEAM_NOTES_ON is False)
    win_prob: float | None
    model_pick: str | None  # the model alone, before any team note
    model_prob: float | None
    note: str  # team notes in force for this game ('' while TEAM_NOTES_ON is False)
    away_score: int | None
    home_score: int | None

    @property
    def leg_id(self) -> str:
        return f"{self.sport}:{self.game_id}"

    @property
    def is_pick(self) -> bool:
        return self.status == "PICK" and self.pick is not None and self.win_prob is not None

    @property
    def opponent(self) -> str | None:
        if self.pick is None:
            return None
        return self.home if self.pick == self.away else self.away

    @property
    def final(self) -> bool:
        return self.away_score is not None and self.home_score is not None

    @property
    def result(self) -> str:
        """W, L or T for the official pick once the game is final, else ''."""
        if not self.is_pick or not self.final:
            return ""
        if self.away_score == self.home_score:
            return "T"
        winner = self.home if self.home_score > self.away_score else self.away
        return "W" if winner == self.pick else "L"

    def started(self, now: dt.datetime) -> bool:
        return self.final or self.kickoff_utc <= now


def tier(prob: float) -> str:
    """The engines' confidence groups (README: "How far to trust it")."""
    return "70%+" if prob >= 0.70 else "60-70%" if prob >= 0.60 else "Under 60%"


def discover_slates(directory: Path | None = None) -> list[Slate]:
    """Every saved college date and NFL week, newest first within each sport (NFL weeks first)."""
    directory = directory or results_dir()
    found: list[Slate] = []
    if not directory.is_dir():
        return found
    for path in directory.iterdir():
        if match := CFB_RE.match(path.name):
            day = dt.date.fromisoformat(match[1])
            graded = directory / f"cfb_{match[1]}_graded.csv"
            label = f"College · {day.strftime('%a %b')} {day.day}, {day.year}"
            found.append(Slate("cfb", match[1], label, path, graded if graded.exists() else None))
        elif match := NFL_RE.match(path.name):
            season, week = int(match[1]), int(match[2])
            graded = directory / f"nfl_cfbmethod_{season}_week{week:02d}_graded.csv"
            label = f"NFL · {season} Week {week}"
            found.append(Slate("nfl", f"{season}-W{week:02d}", label, path, graded if graded.exists() else None))
    return sorted(found, key=lambda s: (0 if s.sport == "nfl" else 1, _neg_key(s.key)))


def _neg_key(key: str) -> tuple[int, ...]:
    """Sort key that puts the newest date or week first."""
    return tuple(-int(part) for part in re.findall(r"\d+", key))


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "", "nan") else None
    except ValueError:
        return None


def _int(value: str | None) -> int | None:
    number = _float(value)
    return None if number is None else int(number)


def _kickoff(value: str) -> dt.datetime:
    return dt.datetime.strptime(value.strip(), "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _scores(slate: Slate) -> dict[str, tuple[int | None, int | None]]:
    if slate.graded_path is None:
        return {}
    scores = {}
    for row in _read_csv(slate.graded_path):
        away, home = _int(row.get("away_score")), _int(row.get("home_score"))
        if away is not None and home is not None:
            scores[str(row["game_id"])] = (away, home)
    return scores


def _team_notes_module(directory: Path):
    """results/team_notes.py, imported from its file (it lives next to the picks, not in a package)."""
    path = directory / "team_notes.py"
    if not path.exists():
        path = REPO_ROOT / "results" / "team_notes.py"
    spec = importlib.util.spec_from_file_location("team_notes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _noted_nfl_picks(slate: Slate, directory: Path) -> dict[str, dict[str, object]] | None:
    """{game_id: {pick, prob, note}} with the owner's team notes applied, or None when the notes are off or absent."""
    notes_path = directory / "team_notes.json"
    if not TEAM_NOTES_ON or not notes_path.exists():
        return None
    import pandas as pd

    team_notes = _team_notes_module(directory)
    noted = team_notes.apply(
        pd.read_csv(slate.picks_path, dtype={"game_id": str}), "engine", team_notes.load(notes_path)
    )
    out = {}
    for row in noted.to_dict("records"):
        pick = row["pick_noted"] if isinstance(row["pick_noted"], str) else None
        prob = None if pick is None else float(row["pick_prob_noted"])
        out[str(row["game_id"])] = {"pick": pick, "prob": prob, "note": row["note_text"] or ""}
    return out


def load_games(slate: Slate, directory: Path | None = None) -> list[Game]:
    """The slate's games in kickoff order, with official picks and any final scores."""
    directory = directory or results_dir()
    rows = _read_csv(slate.picks_path)
    scores = _scores(slate)
    noted = _noted_nfl_picks(slate, directory) if slate.sport == "nfl" else None
    games = []
    for row in rows:
        game_id = str(row["game_id"])
        status = (row.get("status") or "").strip().upper()
        model_pick = (row.get("pick") or None) if status == "PICK" else None
        model_prob = _float(row.get("pick_prob")) if model_pick else None
        pick, prob, note = model_pick, model_prob, ""
        if noted is not None and game_id in noted:
            note = str(noted[game_id]["note"])
            if status == "PICK" and noted[game_id]["pick"] is not None:
                pick, prob = noted[game_id]["pick"], noted[game_id]["prob"]
        away_score, home_score = scores.get(game_id, (None, None))
        games.append(
            Game(
                sport=slate.sport,
                slate_key=slate.key,
                game_id=game_id,
                kickoff_utc=_kickoff(row["kickoff_utc"]),
                kickoff_text=row.get("kickoff") or "",
                away=row["away_name"],
                home=row["home_name"],
                status=status,
                reason=(row.get("reason") or "").strip(),
                pick=pick,
                win_prob=prob,
                model_pick=model_pick,
                model_prob=model_prob,
                note=note,
                away_score=away_score,
                home_score=home_score,
            )
        )
    return sorted(games, key=lambda g: (g.kickoff_utc, g.game_id))


def default_slate(slates: list[Slate], sport: Sport, now: dt.datetime) -> Slate | None:
    """The sport's next slate (today or later for college, the latest NFL week), else its newest one."""
    mine = [s for s in slates if s.sport == sport]
    if not mine:
        return None
    if sport == "cfb":
        today = now.date().isoformat()
        upcoming = sorted((s for s in mine if s.key >= today), key=lambda s: s.key)
        if upcoming:
            return upcoming[0]
    return mine[0]  # newest first
