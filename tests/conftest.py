"""Small saved slates in a temporary results/ folder, shaped like the engines' real files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

PICK_COLUMNS = [
    "game_id", "kickoff_utc", "state", "away_id", "home_id", "away_name", "home_name", "neutral", "venue",
    "home_plays", "away_plays", "net_epa", "net_sr", "is_home", "p_home", "pick", "pick_prob", "status", "reason",
    "kickoff",
]  # fmt: skip
CFB_GRADED_COLUMNS = [
    "game_id", "away", "home", "away_score", "home_score", "final", "status", "reason", "pick", "pick_prob", "result",
]  # fmt: skip

# (game_id, kickoff_utc, away, home, p_home, status, reason)
UPCOMING_CFB = [
    ("1", "2099-10-17T16:00Z", "Auburn", "Georgia", 0.92, "PICK", ""),
    ("2", "2099-10-17T16:00Z", "Miami", "Stanford", 0.09, "PICK", ""),  # Miami (away) 91%
    ("3", "2099-10-17T19:30Z", "Kansas", "Texas Tech", 0.81, "PICK", ""),
    ("4", "2099-10-17T19:30Z", "Utah", "Arizona", 0.25, "PICK", ""),  # Utah 75%
    ("5", "2099-10-17T23:00Z", "Rice", "Navy", 0.64, "PICK", ""),
    ("6", "2099-10-17T23:00Z", "Duke", "Wake Forest", 0.55, "PICK", ""),
    ("7", "2099-10-18T01:00Z", "Florida", "Texas", 0.83, "NO PICK", "Starting QB out (shoulder)"),
]
PAST_CFB = [
    ("11", "2026-10-10T16:00Z", "Ohio", "Toledo", 0.80, "PICK", ""),
    ("12", "2026-10-10T19:00Z", "Ball State", "Akron", 0.35, "PICK", ""),  # Ball State 65%
    ("13", "2026-10-10T22:00Z", "Kent State", "Buffalo", 0.58, "PICK", ""),
]
PAST_SCORES = {"11": (14, 31), "12": (10, 24), "13": (20, 17)}  # Toledo W, Ball State L, Buffalo L
NFL = [
    ("21", "2099-10-04T17:00Z", "Cardinals", "Rams", 0.75, "PICK", ""),
    ("22", "2099-10-04T20:25Z", "Bills", "Raiders", 0.32, "PICK", ""),  # Bills 68%
    ("23", "2099-10-05T00:20Z", "Ravens", "Steelers", 0.50, "NO PICK", "Starting QB unconfirmed"),
]


def _picks(rows):
    out = []
    for game_id, kickoff, away, home, p_home, status, reason in rows:
        pick, prob = (home, p_home) if p_home >= 0.5 else (away, 1 - p_home)
        out.append(
            {
                "game_id": game_id, "kickoff_utc": kickoff, "state": "pre", "away_id": "", "home_id": "",
                "away_name": away, "home_name": home, "neutral": "False", "venue": "", "home_plays": 300,
                "away_plays": 300, "net_epa": 0.1, "net_sr": 0.01, "is_home": 1.0, "p_home": p_home, "pick": pick,
                "pick_prob": prob, "status": status, "reason": reason, "kickoff": f"Sat {kickoff[11:16]}",
            }
        )  # fmt: skip
    return out


def _write(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def make_results(directory: Path, *, notes: bool = True) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / "cfb_2099-10-17_picks.csv", PICK_COLUMNS, _picks(UPCOMING_CFB))
    _write(directory / "cfb_2026-10-10_picks.csv", PICK_COLUMNS, _picks(PAST_CFB))
    graded = []
    for row in _picks(PAST_CFB):
        away_score, home_score = PAST_SCORES[row["game_id"]]
        winner = row["home_name"] if home_score > away_score else row["away_name"]
        graded.append(
            {
                "game_id": row["game_id"], "away": row["away_name"], "home": row["home_name"],
                "away_score": away_score, "home_score": home_score, "final": True, "status": row["status"],
                "reason": "", "pick": row["pick"], "pick_prob": row["pick_prob"],
                "result": "W" if winner == row["pick"] else "L",
            }
        )  # fmt: skip
    _write(directory / "cfb_2026-10-10_graded.csv", CFB_GRADED_COLUMNS, graded)
    _write(directory / "nfl_cfbmethod_2099_week03_picks.csv", PICK_COLUMNS, _picks(NFL))
    _write(directory / "nfl_cfbmethod-untuned_2099_week03_picks.csv", PICK_COLUMNS, _picks(NFL))  # a variant: ignored
    _write(directory / "prompt_cfb_2099-10-17_picks.csv", PICK_COLUMNS, _picks(UPCOMING_CFB))  # another model: ignored
    if notes:
        (directory / "team_notes.json").write_text(
            json.dumps(
                {
                    "expire_after_days": 21,
                    "kinds": {
                        "unreliable": {"label": "Unreliable", "default_points": -3.0},
                        "max_effort": {"label": "Max effort", "default_points": 1.5},
                    },
                    "events": [
                        {"set_at": "2099-09-30T12:00Z", "action": "set", "team": "Rams", "kind": "unreliable",
                         "points": -3.0, "owner_said": "test note"},
                    ],
                }
            )
        )  # fmt: skip
    return directory


@pytest.fixture
def results(tmp_path, monkeypatch) -> Path:
    directory = make_results(tmp_path / "results")
    monkeypatch.setenv("SPORTS_RESULTS_DIR", str(directory))
    return directory
