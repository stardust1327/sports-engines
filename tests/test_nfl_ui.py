"""Tests for the NFL engine page: reading a logged week, the "why" in points, the records, and the Streamlit page."""

from __future__ import annotations

import csv
import datetime as dt
import math
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from nfl_ui import view as V
from nfl_ui import week as W
from nfl_ui import why as Y
from parlay_app import slates as S
from tests.conftest import NFL_CUTOFF, NFL_FORMULA, NFL_RATINGS, nfl_p_home, write_nfl_ratings

ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 10, 16, 12, 0, tzinfo=dt.timezone.utc)


def _week() -> W.Week:
    return W.load_week(W.weeks()[0])


def _game(week: W.Week, game_id: str) -> W.WeekGame:
    return next(wg for wg in week.games if wg.game.game_id == game_id)


def _formula(week: W.Week) -> Y.Formula:
    return Y.formula([wg.numbers for wg in week.games if wg.numbers is not None])


# --------------------------------------------------------------------------- #
# Reading a week
# --------------------------------------------------------------------------- #
def test_a_week_has_the_engines_numbers_qbs_and_ratings(results):
    assert [s.label for s in W.weeks()] == ["NFL · 2099 Week 3"]
    week = _week()
    assert (week.season, week.week) == (2099, 3)
    assert [wg.game.game_id for wg in week.games] == ["21", "22", "23", "24"]  # kickoff order
    rams = _game(week, "21")
    assert (rams.home_id, rams.away_id, rams.venue, rams.neutral) == ("2", "1", "SoFi Stadium", False)
    assert rams.numbers.p_home == pytest.approx(nfl_p_home("21")) and rams.numbers.home_plays == 320
    assert _game(week, "24").neutral and _game(week, "24").numbers.is_home == 0.0
    assert _game(week, "23").numbers is not None and not _game(week, "23").game.is_pick  # QB no-pick keeps numbers
    ravens = week.qbs["Ravens"]
    assert ravens.flag == "CHANGE SPLIT" and ravens.starters == ("Lamar Jackson", "Tyler Huntley")
    (rs,) = week.rating_sets
    assert rs.cutoff_utc == NFL_CUTOFF and len(rs.teams) == 8
    assert sum(r.off_epa for r in rs.teams.values()) == pytest.approx(0.0, abs=1e-12)  # centered on the league
    assert rs.teams["3"].ranks["off_epa"] == 1 and rs.teams["5"].ranks["def_epa"] == 1  # Bills offense, Ravens defense


def test_a_week_without_qbs_or_ratings_still_loads(results):
    for suffix in ("qbs", "ratings"):
        (results / f"nfl_cfbmethod_2099_week03_{suffix}.csv").unlink()
    week = _week()
    assert week.qbs == {} and week.rating_sets == [] and week.latest_ratings is None
    assert week.ratings_for(week.games[0]) == (None, False)


def test_each_game_is_explained_with_the_ratings_that_rebuild_it(results):
    later = {tid: (oe + 0.01 * int(tid), de, os_, ds, n) for tid, (oe, de, os_, ds, n) in NFL_RATINGS.items()}
    path = results / "nfl_cfbmethod_2099_week03_ratings.csv"
    write_nfl_ratings(path, {NFL_CUTOFF: NFL_RATINGS, "2099-10-05T00:20Z": later})
    week = _week()
    assert [rs.cutoff_utc for rs in week.rating_sets] == [NFL_CUTOFF, "2099-10-05T00:20Z"]
    assert week.latest_ratings.cutoff_utc == "2099-10-05T00:20Z"
    rs, exact = week.ratings_for(_game(week, "22"))
    assert exact and rs.cutoff_utc == NFL_CUTOFF  # not the latest set: the one behind the logged pick
    write_nfl_ratings(path, {"2099-10-05T00:20Z": later})
    week = _week()
    assert week.ratings_for(_game(week, "22")) == (week.latest_ratings, False)


# --------------------------------------------------------------------------- #
# Why, in points
# --------------------------------------------------------------------------- #
def test_the_engines_calibration_is_recovered_from_its_logged_games(results):
    f = _formula(_week())
    assert (f.epa, f.sr, f.home) == pytest.approx(NFL_FORMULA, abs=1e-9)
    numbers = [wg.numbers for wg in _week().games]
    assert Y.formula(numbers[:2]) is None  # too few games to pin it down
    off = [W.EngineNumbers(n.net_epa, n.net_sr, n.is_home, min(0.99, n.p_home + 0.1), 300, 300) for n in numbers]
    assert Y.formula(numbers[:3] + off[3:]) is None  # numbers that don't fit one formula get no breakdown


def test_points_use_the_scale_the_team_notes_use():
    tn = S.team_notes_module(ROOT / "results")
    assert Y.PTS_PER_LOGIT == tn.ENGINE_PTS_PER_LOGIT
    assert Y.points(0.5) == 0.0 and Y.points(0.75) == pytest.approx(7.8 * math.log(3))


def test_reasons_add_up_to_the_logged_edge(results):
    week = _week()
    f = _formula(week)
    rams = Y.explain(_game(week, "21"), f, week.rating_sets[0].teams)
    assert (rams.pick, rams.opponent, rams.pick_is_home, rams.detailed) == ("Rams", "Cardinals", True, True)
    assert rams.model_points == pytest.approx(Y.points(nfl_p_home("21")))
    assert rams.note_points == 0.0 and rams.total_points == rams.model_points  # team notes are off (rule 6)
    assert sum(r.points for r in rams.reasons) == pytest.approx(rams.total_points)
    labels = {r.label for r in rams.reasons}
    assert labels == {"Rams offense", "Rams defense", "Cardinals offense", "Cardinals defense", "Rams home field"}
    bills = Y.explain(_game(week, "22"), f, week.rating_sets[0].teams)  # the away pick: signs flip
    assert (bills.pick, bills.pick_is_home) == ("Bills", False)
    assert bills.model_points == pytest.approx(-Y.points(nfl_p_home("22")))
    assert sum(r.points for r in bills.reasons) == pytest.approx(bills.total_points)
    home = next(r for r in bills.reasons if r.label == "Raiders home field")
    assert home.points == pytest.approx(-7.8 * NFL_FORMULA[2])  # home field helps the opponent
    offense = next(r for r in bills.reasons if r.label == "Bills offense")
    assert offense.detail.startswith("1st of 8 in expected points per play")
    assert V.edge_line(rams, _game(week, "21").game) == f"Engine edge: **Rams by {rams.model_points:.1f} points**"


def test_switched_off_team_notes_still_add_up_if_turned_back_on(results, monkeypatch):
    monkeypatch.setattr(S, "TEAM_NOTES_ON", True)
    week = _week()
    f, teams = _formula(week), week.rating_sets[0].teams
    rams = Y.explain(_game(week, "21"), f, teams)
    assert rams.note_points == -3.0 and rams.total_points == pytest.approx(rams.model_points - 3.0)
    assert sum(r.points for r in rams.reasons) == pytest.approx(rams.total_points)
    assert [r.label for r in rams.helping_opponent] == ["Your team note"]
    wg = _game(week, "24")
    flipped = Y.explain(wg, f, teams)
    assert (flipped.pick, wg.game.model_pick) == ("Texans", "Jaguars")  # the Texans' max-effort note flips it
    assert flipped.model_points < 0 < flipped.total_points and flipped.note_points == 1.5
    line = V.edge_line(flipped, wg.game)
    assert f"Texans by {flipped.total_points:.1f} points" in line and "flips the pick" in line and "Jaguars" in line


def test_without_team_ratings_the_edge_splits_into_the_three_logged_numbers(results):
    week = _week()
    why = Y.explain(_game(week, "21"), _formula(week), {})
    assert not why.detailed
    assert {r.label for r in why.reasons} == {"Expected points per play", "Success rate", "Rams home field"}
    assert sum(r.points for r in why.reasons) == pytest.approx(why.total_points)


def test_a_neutral_site_has_no_home_field(results):
    week = _week()
    wg = _game(week, "24")
    why = Y.explain(wg, _formula(week), week.rating_sets[0].teams)
    assert not any("home field" in r.label for r in why.reasons)
    assert (why.pick, wg.game.model_pick, wg.game.note) == ("Jaguars", "Jaguars", "")  # no note flips it: notes are off
    assert sum(r.points for r in why.reasons) == pytest.approx(why.model_points)


def test_no_pick_gets_no_reasons(results):
    week = _week()
    wg = _game(week, "23")
    assert Y.explain(wg, _formula(week), week.rating_sets[0].teams) is None
    assert V.headline(wg) == "**No pick:** Ravens at Steelers"


def test_power_ratings_differ_by_the_engines_edge(results):
    week = _week()
    f, teams = _formula(week), week.rating_sets[0].teams
    rams = Y.explain(_game(week, "21"), f, teams)
    assert Y.power(f, teams["2"]) - Y.power(f, teams["1"]) + f.home_points == pytest.approx(rams.model_points)
    rows = V.ratings_rows(f, week.rating_sets[0])
    assert [r["Rank"] for r in rows] == list(range(1, 9))
    assert rows[0]["Rating (pts)"] >= rows[-1]["Rating (pts)"]


def test_small_reasons_count_as_about_even():
    reasons = (Y.Reason("A offense", "", 2.0), Y.Reason("B defense", "", -0.29), Y.Reason("B offense", "", -1.0))
    why = Y.Why("A", "B", True, 0.71, 0.0, reasons, True)
    assert [r.label for r in why.helping_pick] == ["A offense"]
    assert [r.label for r in why.helping_opponent] == ["B offense"]
    assert [r.label for r in why.even] == ["B defense"]


# --------------------------------------------------------------------------- #
# Plain-English pieces and records
# --------------------------------------------------------------------------- #
def test_text_pieces(results):
    week = _week()
    rams = _game(week, "21")
    assert [V.tier(p) for p in (0.70, 0.6999, 0.5)] == ["Strongest (70%+)", "Lean (60-70%)", "Coin flip (under 60%)"]
    assert V.kickoff(rams.game.kickoff_utc) == "Sun Oct 4, 10:00 AM"  # Phoenix time
    assert V.headline(rams) == f"**Rams** over Cardinals · **{100 * nfl_p_home('21'):.1f}%** · Strongest (70%+)"
    assert "neutral site" in V.where(_game(week, "24")) and "Estadio Azteca" in V.where(_game(week, "24"))
    assert V.qb_line(_game(week, "23"), week.qbs) == (
        "QBs (last starters) · Ravens: Tyler Huntley (1 of 2 starts) · :orange[CHANGE SPLIT] · "
        "Steelers: Aaron Rodgers (2 of 2 starts)"
    )
    rows = V.qb_rows(week)
    assert rows[0]["Team"] == "Ravens" and rows[0]["Engine"] == "No pick: Starting QB unconfirmed"  # flagged first
    assert next(r for r in rows if r["Team"] == "Rams")["Engine"] == f"Pick: Rams {100 * nfl_p_home('21'):.1f}%"
    assert V.record(["W", "L", "W", ""]) == "2-1" and V.record(["W", "T"]) == "1-0-1" and V.record([]) == ""


def _graded_week(results: Path) -> None:
    """2099 week 2, before the team notes were set: a strongest pick, a lean and a coin flip, all final."""
    rows = [
        {"game_id": "11", "kickoff_utc": "2099-09-27T17:00Z", "away_id": "1", "home_id": "2", "away_name": "Cardinals",
         "home_name": "Rams", "neutral": "False", "venue": "", "net_epa": 0.1, "net_sr": 0.0, "is_home": 1.0,
         "p_home": 0.75, "pick": "Rams", "pick_prob": 0.75, "status": "PICK", "reason": "", "kickoff": "Sun"},
        {"game_id": "12", "kickoff_utc": "2099-09-27T20:00Z", "away_id": "3", "home_id": "4", "away_name": "Bills",
         "home_name": "Raiders", "neutral": "False", "venue": "", "net_epa": -0.1, "net_sr": 0.0, "is_home": 1.0,
         "p_home": 0.45, "pick": "Bills", "pick_prob": 0.55, "status": "PICK", "reason": "", "kickoff": "Sun"},
        {"game_id": "13", "kickoff_utc": "2099-09-28T00:20Z", "away_id": "5", "home_id": "6", "away_name": "Ravens",
         "home_name": "Steelers", "neutral": "False", "venue": "", "net_epa": -0.2, "net_sr": 0.0, "is_home": 1.0,
         "p_home": 0.35, "pick": "Ravens", "pick_prob": 0.65, "status": "PICK", "reason": "", "kickoff": "Sun"},
    ]  # fmt: skip
    scores = [
        {"game_id": "11", "away_score": 10, "home_score": 20},
        {"game_id": "12", "away_score": 17, "home_score": 24},
        {"game_id": "13", "away_score": 27, "home_score": 13},
    ]
    for name, data in (("picks", rows), ("graded", scores)):
        with (results / f"nfl_cfbmethod_2099_week02_{name}.csv").open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)


def test_record_rows_by_week_and_tier(results):
    _graded_week(results)
    graded = V.graded_games(W.weeks())
    assert [(s, w, g.pick, g.result) for s, w, g in graded] == [
        (2099, 2, "Rams", "W"),
        (2099, 2, "Bills", "L"),
        (2099, 2, "Ravens", "W"),
    ]
    rows = V.record_rows(graded)
    assert rows[0]["Week"] == "2099 Week 2" and rows[-1]["Week"] == "Season so far"
    assert rows[-1]["Official"] == "2-1" and "Model alone" not in rows[-1]  # the same picks while notes are off
    assert [rows[-1][t] for t in ("Strongest (70%+)", "Lean (60-70%)", "Coin flip (under 60%)")] == [
        "1-0",
        "1-0",
        "0-1",
    ]
    without_leans = V.record_rows([x for x in graded if x[2].pick != "Ravens"])
    assert without_leans[-1]["Lean (60-70%)"] == ""


def test_closing_check_matches_grade_py():
    card = [  # engine pick, closing line, result: like nfl_scorecard.csv
        {"status": "PICK", "p_home": "0.70", "market_p_home": "0.80", "home_win": "1"},
        {"status": "PICK", "p_home": "0.40", "market_p_home": "0.60", "home_win": "1"},
        {"status": "PICK", "p_home": "0.55", "market_p_home": "0.45", "home_win": "0.5"},
        {"status": "NO PICK", "p_home": "0.50", "market_p_home": "0.50", "home_win": "1"},
    ]
    check = V.closing_check(card)
    assert (check["games"], check["engine"], check["market"]) == (3, "1-1-1", "2-0-1")
    assert check["brier_engine"] == pytest.approx((0.3**2 + 0.6**2 + 0.05**2) / 3)
    assert check["brier_market"] == pytest.approx((0.2**2 + 0.4**2 + 0.05**2) / 3)
    assert check["underdog_picks"] == "0-1-1"
    assert V.closing_check([]) is None


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #
def _nfl_page() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.switch_page("nfl_ui/page.py")
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_nfl_page_renders_every_tab(results):
    at = _nfl_page()
    assert at.title[0].value == "NFL engine"
    assert [t.label for t in at.tabs] == ["Picks", "Team ratings", "QB check", "Track record", "How it works"]
    assert at.selectbox[0].value == "NFL · 2099 Week 3"
    md = [m.value for m in at.markdown]
    heads = [m.split("**")[1] for m in md if m.startswith("**") and " over " in m and " · **" in m]  # pick headlines
    assert heads == ["Rams", "Bills", "Jaguars"]  # still to play, in kickoff order; no team note moves a pick
    assert any(m.startswith("**Helping the Rams**") for m in md) and "**No pick:** Ravens at Steelers" in md
    assert not any("team note" in m.lower() for m in md)
    assert not any("Team-by-team ratings" in c.value for c in at.caption)  # every pick explained by unit
    assert len(at.dataframe) >= 3  # team ratings, QB check, backtest


def test_nfl_page_without_ratings_or_picks(results, tmp_path, monkeypatch):
    (results / "nfl_cfbmethod_2099_week03_ratings.csv").unlink()
    at = _nfl_page()
    assert any("aren't saved yet" in i.value for i in at.info)
    assert any("Team-by-team ratings" in c.value for c in at.caption)
    monkeypatch.setenv("SPORTS_RESULTS_DIR", str(tmp_path / "empty"))
    at = _nfl_page()
    assert any("No NFL picks saved" in i.value for i in at.info)


def test_importing_the_pages_does_not_start_streamlit():
    code = "import sys, app, nfl_ui.view, parlay_app.ui; assert 'streamlit' not in sys.modules; print('ok')"
    done = subprocess.run(
        [sys.executable, "-c", code], check=False, cwd=ROOT, capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 0 and done.stdout.strip() == "ok", done.stderr


# --------------------------------------------------------------------------- #
# nfl_ui/ratings.py with the engine's own code (offline, in a fresh process)
# --------------------------------------------------------------------------- #
RATINGS_CHECK = r"""
import numpy as np, pandas as pd
from nfl_ui import ratings as R

run = R.load_engine()  # nfl_cfbmethod/run.py, unchanged
rng = np.random.default_rng(0)
teams = [str(i) for i in range(1, 7)]
plays = []
for season in (2098, 2099):
    for week in range(1, 5):
        for g in range(3):
            home, away = teams[2 * g], teams[2 * g + 1]
            if week % 2:
                home, away = away, home
            for _ in range(120):
                off = home if rng.random() < 0.5 else away
                plays.append({"season": season, "week": week, "off": off, "def": away if off == home else home,
                              "home_off": off == home, "epa_c": rng.normal(0.05 * int(off), 1.0),
                              "success": float(rng.random() < 0.4 + 0.02 * int(off))})
sc = pd.DataFrame(plays)
ratings = R.team_ratings(run, sc, 2099, 4)
expected = run.nfl_engine.ratings(sc, 2099, 4, run.NFL_ALPHA, run.NFL_RHO, run.HALF_LIFE)
assert ratings[0]["off"] == expected[0]["off"] and ratings[1]["def"] == expected[1]["def"]
logged = pd.DataFrame([{"home_id": "1", "away_id": "2", "net_epa": run.engine.net(ratings[0], "1", "2"),
                        "net_sr": run.engine.net(ratings[1], "1", "2")},
                       {"home_id": "3", "away_id": "4", "net_epa": 0.5, "net_sr": 0.0}])
gaps = R.gaps(run, ratings, logged)
assert gaps[0] < R.EXACT < gaps[1], gaps
table = R.table(ratings, {"1": "Rams"}, "2099-10-04T17:00Z", 1)
assert list(table.columns) == ["cutoff_utc", "team_id", "team", "off_epa", "def_epa", "off_sr", "def_sr", "plays",
                               "games_reproduced"]
assert len(table) == 6 and "Rams" in set(table["team"]) and table["plays"].sum() == len(sc[(sc.season == 2099) & (sc.week < 4)])
print("ok", run.NFL_ALPHA, run.NFL_RHO, run.HALF_LIFE)
"""


def test_ratings_helper_uses_the_engines_own_ratings():
    done = subprocess.run(
        [sys.executable, "-c", RATINGS_CHECK], check=False, cwd=ROOT, capture_output=True, text=True, timeout=300
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["ok", "500", "0.3", "5"]  # the approved NFL settings, read from run.py


def test_ratings_helper_needs_a_logged_week(tmp_path):
    from nfl_ui import ratings as R

    assert R.main(["--season", "2099", "--week", "9", "--results", str(tmp_path)]) == 1
    assert R.picks_path(tmp_path, 2026, 6).name == "nfl_cfbmethod_2026_week06_picks.csv"
    assert R.ratings_path(tmp_path, 2026, 6).name == "nfl_cfbmethod_2026_week06_ratings.csv"
