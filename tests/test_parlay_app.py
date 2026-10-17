"""Tests for the parlay builder: reading the saved picks, the parlay math, and the Streamlit app."""

from __future__ import annotations

import datetime as dt
import itertools
import math
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from parlay_app import parlays as P
from parlay_app import slates as S
from parlay_app import ui as A
from tests.conftest import make_results, nfl_p_home

ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.timezone.utc)


def _leg(name: str, prob: float, n: int = 0) -> P.Leg:
    return P.Leg(f"cfb:{name}", name, f"Opp{name}", prob, "cfb", "Sat", f"2099-01-01T{n:02d}:00")


# --------------------------------------------------------------------------- #
# Slates
# --------------------------------------------------------------------------- #
def test_discovery_reads_only_the_official_engine_files(results):
    slates = S.discover_slates()
    assert [s.label for s in slates] == [
        "NFL · 2099 Week 3",
        "College · Sat Oct 17, 2099",
        "College · Sat Oct 10, 2026",
    ]
    assert [s.key for s in slates] == ["2099-W03", "2099-10-17", "2026-10-10"]
    assert slates[2].graded_path == results / "cfb_2026-10-10_graded.csv" and slates[1].graded_path is None


def test_default_slates(results):
    slates = S.discover_slates()
    assert S.default_slate(slates, "cfb", NOW).key == "2099-10-17"  # the next college day
    later = dt.datetime(2100, 1, 1, tzinfo=dt.timezone.utc)
    assert S.default_slate(slates, "cfb", later).key == "2099-10-17"  # none upcoming: the newest
    assert S.default_slate(slates, "nfl", NOW).key == "2099-W03"
    assert S.default_slate([], "nfl", NOW) is None


def test_college_games_keep_picks_no_picks_and_the_engine_numbers(results):
    slate = next(s for s in S.discover_slates() if s.key == "2099-10-17")
    games = S.load_games(slate)
    assert [g.game_id for g in games] == ["1", "2", "3", "4", "5", "6", "7"]
    miami = games[1]
    assert (miami.pick, miami.opponent, round(miami.win_prob, 2), miami.is_pick) == ("Miami", "Stanford", 0.91, True)
    no_pick = games[6]
    assert not no_pick.is_pick and no_pick.reason == "Starting QB out (shoulder)" and no_pick.pick is None
    assert not any(g.started(NOW) for g in games)


def test_graded_slates_report_results_for_the_official_pick(results):
    slate = next(s for s in S.discover_slates() if s.key == "2026-10-10")
    games = S.load_games(slate)
    assert [(g.pick, g.result) for g in games] == [("Toledo", "W"), ("Ball State", "L"), ("Buffalo", "L")]
    assert all(g.started(NOW) for g in games)
    assert A.record_by_tier(games) == [
        {"Tier": "70%+", "Won": 1, "Lost": 0, "Hit rate": "100%"},
        {"Tier": "60-70%", "Won": 0, "Lost": 1, "Hit rate": "0%"},
        {"Tier": "Under 60%", "Won": 0, "Lost": 1, "Hit rate": "0%"},
    ]


def test_nfl_official_picks_have_the_owners_team_notes_applied(results):
    slate = next(s for s in S.discover_slates() if s.sport == "nfl")
    rams = S.load_games(slate)[0]
    assert (rams.model_pick, rams.model_prob) == ("Rams", nfl_p_home("21"))
    assert rams.pick == "Rams" and rams.win_prob < rams.model_prob  # docked 3 points on the engine's own scale
    assert rams.note_pts_home == -3.0
    assert "Rams" in rams.note and "unreliable" in rams.note.lower()
    bills = S.load_games(slate)[1]
    assert (bills.pick, bills.win_prob, bills.note) == (bills.model_pick, bills.model_prob, "")


def test_nfl_without_a_notes_file_uses_the_model_alone(tmp_path, monkeypatch):
    directory = make_results(tmp_path / "results", notes=False)
    monkeypatch.setenv("SPORTS_RESULTS_DIR", str(directory))
    rams = S.load_games(next(s for s in S.discover_slates() if s.sport == "nfl"))[0]
    assert (rams.pick, rams.win_prob, rams.note, rams.note_pts_home) == ("Rams", nfl_p_home("21"), "", 0.0)


def test_tiers_match_the_engines_groups():
    assert [S.tier(p) for p in (0.7, 0.6999, 0.6, 0.5999)] == ["70%+", "60-70%", "60-70%", "Under 60%"]


# --------------------------------------------------------------------------- #
# Parlay math
# --------------------------------------------------------------------------- #
def test_parlay_chance_is_the_product_and_fair_odds_follow():
    legs = [_leg("A", 0.9), _leg("B", 0.8), _leg("C", 0.5)]
    assert P.parlay_prob(legs) == pytest.approx(0.36)
    assert P.fair_american(0.36) == "+178"
    assert P.fair_american(0.75) == "-300"
    assert P.fair_american(0.5) == "-100"
    assert P.fair_american(1.0) == "n/a"


def test_pick_legs_modes():
    legs = [_leg(n, p, i) for i, (n, p) in enumerate([("A", 0.91), ("B", 0.82), ("C", 0.74), ("D", 0.66), ("E", 0.55)])]
    assert [leg.team for leg in P.pick_legs(legs, 2, "highest")] == ["A", "B"]
    assert [leg.team for leg in P.pick_legs(legs, 2, "lowest")] == ["D", "E"]
    assert [leg.team for leg in P.pick_legs(legs, 5, "range", low=0.6, high=0.85)] == ["B", "C", "D"]
    assert [leg.team for leg in P.pick_legs(legs, 0, "teams", chosen=["cfb:E", "cfb:A"])] == ["A", "E"]
    with pytest.raises(ValueError):
        P.pick_legs(legs, 2, "random")


def _ids(parlay):
    return {leg.leg_id for leg in parlay}


@pytest.mark.parametrize(("max_uses", "max_shared"), [(1, 0), (2, 1), (3, 2), (10, 3)])
def test_recommendations_respect_the_redundancy_limits(max_uses, max_shared):
    legs = [_leg(f"T{i}", 0.95 - 0.01 * i, i) for i in range(30)]
    recs = P.recommend(legs, 10, 4, max_uses=max_uses, max_shared=max_shared)
    assert recs and all(len(p) == 4 for p in recs)
    counts = {}
    for parlay in recs:
        for leg in parlay:
            counts[leg.leg_id] = counts.get(leg.leg_id, 0) + 1
    assert max(counts.values()) <= max_uses
    for a, b in itertools.combinations(recs, 2):
        assert len(_ids(a) & _ids(b)) <= min(max_shared, 3)
    assert len({frozenset(_ids(p)) for p in recs}) == len(recs)  # no duplicates
    chances = [P.parlay_prob(p) for p in recs]
    assert chances[0] == pytest.approx(math.prod(0.95 - 0.01 * i for i in range(4)))  # the strongest comes first


def test_no_repeats_means_one_loss_sinks_at_most_one_parlay():
    legs = [_leg(f"T{i}", 0.9 - 0.01 * i, i) for i in range(12)]
    recs = P.recommend(legs, 10, 4, max_uses=1, max_shared=0)
    assert len(recs) == 3  # 12 legs make only 3 disjoint four-leg parlays: the rest are not padded with repeats
    assert all(e.parlays == 1 for e in P.exposure(recs))


def test_recommendations_skip_weak_legs_and_stop_when_nothing_fits():
    legs = [_leg("A", 0.9), _leg("B", 0.8), _leg("C", 0.6), _leg("D", 0.55)]
    recs = P.recommend(legs, 5, 2, max_uses=1, max_shared=0, min_prob=0.6)
    assert [[leg.team for leg in p] for p in recs] == [["A", "B"]]  # C alone can't fill a second parlay
    assert P.recommend(legs, 0, 2, max_uses=1, max_shared=0) == []
    assert P.recommend(legs, 3, 5, max_uses=1, max_shared=0) == []


def test_exposure_counts_how_many_parlays_each_pick_can_sink():
    a, b, c, d = _leg("A", 0.9), _leg("B", 0.8), _leg("C", 0.7), _leg("D", 0.6)
    exposure = P.exposure([(a, b), (a, c), (a, d), (b, c)])
    assert [(e.leg.team, e.parlays) for e in exposure] == [("A", 3), ("C", 2), ("B", 2), ("D", 1)]


def test_outlook_of_independent_parlays_matches_the_exact_answer():
    p1, p2 = (_leg("A", 0.9), _leg("B", 0.8)), (_leg("C", 0.7), _leg("D", 0.6))
    outlook = P.outlook([p1, p2])
    assert outlook.expected_wins == pytest.approx(0.72 + 0.42)
    assert outlook.any_wins == pytest.approx(1 - (1 - 0.72) * (1 - 0.42), abs=0.01)
    shared = P.outlook([(p1[0], p1[1]), (p1[0], p2[0])])  # both need A: they win and lose together more often
    assert shared.any_wins == pytest.approx(0.9 * (1 - 0.2 * 0.3), abs=0.01)
    assert P.outlook([]).any_wins == 0.0


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
def _run_app() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_game_rows_show_the_model_alone_beside_a_noted_pick(results):
    games = S.load_games(next(s for s in S.discover_slates() if s.sport == "nfl"))
    rows = A.game_rows(games)
    assert [r["Pick"] for r in rows] == ["Rams", "Bills", "Texans"]  # the no-pick is listed separately
    assert "model alone: Rams 74.1%" in rows[0]["Note"] and rows[1]["Note"] == ""
    assert "model alone: Jaguars 51.5%" in rows[2]["Note"]  # the Texans note flips this one


def test_app_renders_every_tab(results):
    at = _run_app()
    assert at.title[0].value == "Parlay Builder"
    assert [t.label for t in at.tabs] == ["Games", "Build a parlay", "Recommended parlays", "Track record"]
    assert [sb.value for sb in at.sidebar.selectbox] == ["College · Sat Oct 17, 2099", "NFL · 2099 Week 3"]
    assert len(at.dataframe) >= 2  # one games table per slate
    parlays = [m.value for m in at.markdown if m.value.startswith("**Parlay ")]
    assert parlays and "to win" in parlays[0]
    assert any(m.value.startswith("**Your parlay**") for m in at.markdown)
    assert any("If a pick loses" in m.value for m in at.markdown)


def test_app_with_no_saved_picks(tmp_path, monkeypatch):
    monkeypatch.setenv("SPORTS_RESULTS_DIR", str(tmp_path / "empty"))
    at = _run_app()
    assert "No saved picks" in at.info[0].value


def test_app_with_only_past_slates_offers_no_legs(results):
    for name in ("cfb_2099-10-17_picks.csv", "nfl_cfbmethod_2099_week03_picks.csv"):
        (results / name).unlink()
    at = _run_app()
    assert any("No games left to start" in i.value for i in at.info)


def test_importing_the_app_does_not_start_streamlit():
    code = "import sys, app; assert 'streamlit' not in sys.modules; print('ok')"
    done = subprocess.run(
        [sys.executable, "-c", code], check=False, cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 0 and done.stdout.strip() == "ok", done.stderr
