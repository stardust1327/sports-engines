"""Small saved slates in a temporary results/ folder, shaped like the engines' real files."""

from __future__ import annotations

import csv
import json
import math
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
# NFL week 3 of 2099, built the way the engine builds it: team ratings (as nfl_ui/ratings.py saves them) give each
# game's edges, and a known calibration turns the edges into the logged win chance.
NFL_TEAMS = {"1": "Cardinals", "2": "Rams", "3": "Bills", "4": "Raiders",
             "5": "Ravens", "6": "Steelers", "7": "Texans", "8": "Jaguars"}  # fmt: skip
NFL_RATINGS = {  # team id: (off_epa, def_epa, off_sr, def_sr, plays)
    "1": (-0.03, 0.02, -0.010, 0.005, 300), "2": (0.04, -0.01, 0.015, -0.005, 320),
    "3": (0.06, 0.02, 0.020, 0.010, 310), "4": (-0.04, 0.03, -0.015, 0.010, 290),
    "5": (0.02, -0.02, 0.005, -0.010, 305), "6": (0.00, 0.00, 0.000, 0.000, 300),
    "7": (0.01, -0.01, 0.000, -0.005, 295), "8": (0.02, -0.01, 0.002, -0.005, 315),
}  # fmt: skip
NFL_FORMULA = (2.5, 18.0, 0.17)  # log-odds per unit of net_epa, net_sr and home field
NFL_CUTOFF = "2099-10-04T17:00Z"
# (game_id, kickoff_utc, away id, home id, neutral, venue, status, reason)
NFL = [
    ("21", "2099-10-04T17:00Z", "1", "2", False, "SoFi Stadium", "PICK", ""),
    ("22", "2099-10-04T20:25Z", "3", "4", False, "Allegiant Stadium", "PICK", ""),
    ("23", "2099-10-05T00:20Z", "5", "6", False, "Acrisure Stadium", "NO PICK", "Starting QB unconfirmed"),
    ("24", "2099-10-05T01:00Z", "7", "8", True, "Estadio Azteca", "PICK", ""),
]
NFL_QBS = [  # team, last starter, starters by game, flag
    ("Cardinals", "Kyler Murray", "Kyler Murray > Kyler Murray", ""),
    ("Rams", "Matthew Stafford", "Matthew Stafford > Matthew Stafford", ""),
    ("Bills", "Josh Allen", "Josh Allen > Josh Allen", ""),
    ("Raiders", "Geno Smith", "Geno Smith > Geno Smith", ""),
    ("Ravens", "Tyler Huntley", "Lamar Jackson > Tyler Huntley", "CHANGE SPLIT"),
    ("Steelers", "Aaron Rodgers", "Aaron Rodgers > Aaron Rodgers", ""),
    ("Texans", "C.J. Stroud", "C.J. Stroud > C.J. Stroud", ""),
    ("Jaguars", "Trevor Lawrence", "Trevor Lawrence > Trevor Lawrence", ""),
]


def nfl_edges(away: str, home: str, ratings=None) -> tuple[float, float]:
    """The home team's EPA and success edges from team ratings (nfl_engine / cfb engine.net)."""
    r = ratings or NFL_RATINGS
    epa = (r[home][0] + r[away][1]) - (r[away][0] + r[home][1])
    sr = (r[home][2] + r[away][3]) - (r[away][2] + r[home][3])
    return epa, sr


def nfl_p_home(game_id: str) -> float:
    _, _, away, home, neutral, *_ = next(g for g in NFL if g[0] == game_id)
    epa, sr = nfl_edges(away, home)
    a, b, c = NFL_FORMULA
    return 1 / (1 + math.exp(-(a * epa + b * sr + c * (0.0 if neutral else 1.0))))


def _nfl_picks():
    out = []
    for game_id, kickoff, away, home, neutral, venue, status, reason in NFL:
        epa, sr = nfl_edges(away, home)
        p_home = nfl_p_home(game_id)
        pick, prob = (NFL_TEAMS[home], p_home) if p_home >= 0.5 else (NFL_TEAMS[away], 1 - p_home)
        out.append(
            {
                "game_id": game_id, "kickoff_utc": kickoff, "state": "pre", "away_id": away, "home_id": home,
                "away_name": NFL_TEAMS[away], "home_name": NFL_TEAMS[home], "neutral": str(neutral), "venue": venue,
                "home_plays": NFL_RATINGS[home][4], "away_plays": NFL_RATINGS[away][4], "net_epa": epa, "net_sr": sr,
                "is_home": 0.0 if neutral else 1.0, "p_home": p_home, "pick": pick, "pick_prob": prob,
                "status": status, "reason": reason, "kickoff": f"Sun {kickoff[11:16]}",
            }
        )  # fmt: skip
    return out


def write_nfl_ratings(path: Path, sets: dict[str, dict]) -> None:
    """A ratings file as nfl_ui/ratings.py saves it: {cutoff_utc: ratings like NFL_RATINGS}."""
    rows = []
    for cutoff, ratings in sets.items():
        for tid, (oe, de, os_, ds, plays) in ratings.items():
            rows.append({"cutoff_utc": cutoff, "team_id": tid, "team": NFL_TEAMS[tid], "off_epa": oe, "def_epa": de,
                         "off_sr": os_, "def_sr": ds, "plays": plays, "games_reproduced": 3})  # fmt: skip
    _write(path, list(rows[0]), rows)


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
    _write(directory / "nfl_cfbmethod_2099_week03_picks.csv", PICK_COLUMNS, _nfl_picks())
    _write(directory / "nfl_cfbmethod-untuned_2099_week03_picks.csv", PICK_COLUMNS, _nfl_picks())  # a variant: ignored
    qbs = [{"team": t, "games": 2, "season_leader": s.split(" > ")[0] if "CHANGE" in f else last, "season_att": 60,
            "last_game": "2099-09-27", "last_starter": last, "last_att": 30, "starters_by_game": s, "flag": f}
           for t, last, s, f in NFL_QBS]  # fmt: skip
    _write(directory / "nfl_cfbmethod_2099_week03_qbs.csv", list(qbs[0]), qbs)
    write_nfl_ratings(directory / "nfl_cfbmethod_2099_week03_ratings.csv", {NFL_CUTOFF: NFL_RATINGS})
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
                        {"set_at": "2099-09-30T13:00Z", "action": "set", "team": "Texans", "kind": "max_effort",
                         "points": 1.5, "owner_said": "they play hard"},
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
