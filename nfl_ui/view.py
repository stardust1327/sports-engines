"""NFL engine page: who the engine picks each week and why, the QB check, results and the owner's team notes.

Read-only (nfl_ui/week.py): it shows the files the engine and the check-ins save in results/ and never runs the engine,
changes a pick, a setting or a team note, or uses a betting line as an input (CLAUDE.md rules 1-6). The closing-line
check on the Track record tab is grading only, after the games, as nfl_cfbmethod/grade.py does it.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any
from zoneinfo import ZoneInfo

from nfl_ui import week as W
from nfl_ui import why as Y
from parlay_app import slates as S

PHX = ZoneInfo("America/Phoenix")  # the engine prints Phoenix times
TIERS = (("Strongest", 0.70, "70%+"), ("Lean", 0.60, "60-70%"), ("Coin flip", 0.0, "under 60%"))
TIER_COUNT = {
    "Strongest": ("strongest", "strongest"),
    "Lean": ("lean", "leans"),
    "Coin flip": ("coin flip", "coin flips"),
}
BACKTEST = [  # METHOD.md, "Backtest with these settings" (2019-2025, 1,522 games, weeks 4-18)
    {"Picks": "All", "Record": "963-559", "Hit rate": "63%"},
    {"Picks": "Strongest (70%+)", "Record": "271-93", "Hit rate": "74%"},
    {"Picks": "Lean (60-70%)", "Record": "305-161", "Hit rate": "65%"},
    {"Picks": "Coin flip (under 60%)", "Record": "387-305", "Hit rate": "56%"},
]
FLAGS = {
    "CHANGE": "last game's starter isn't the season leader in attempts",
    "SPLIT": "more than one QB has started",
    "LOW ATTEMPTS": "last starter threw fewer than 15 passes",
    "NO DATA": "no passing data this season",
}


def tier(prob: float) -> str:
    """'Strongest (70%+)', 'Lean (60-70%)' or 'Coin flip (under 60%)', the groups the engine prints."""
    for name, low, rng in TIERS:
        if prob >= low:
            return f"{name} ({rng})"
    raise ValueError(prob)


def kickoff(t: dt.datetime) -> str:
    """'Sun Oct 18, 6:30 AM' in Phoenix time."""
    local = t.astimezone(PHX)
    return f"{local:%a %b} {local.day}, {local:%I:%M %p}".replace(", 0", ", ")


def _pct(p: float) -> str:
    return f"{100 * p:.1f}%"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def record(results: list[str]) -> str:
    """'7-3', or '7-3-1' with a tie; '' with no decided games."""
    w, l, t = (sum(r == x for r in results) for x in "WLT")
    if not w + l + t:
        return ""
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


# --------------------------------------------------------------------------- #
# Plain-English pieces (no Streamlit here, so they can be tested directly)
# --------------------------------------------------------------------------- #
def headline(wg: W.WeekGame) -> str:
    g = wg.game
    if not g.is_pick:
        return f"**No pick:** {g.away} at {g.home}"
    text = f"**{g.pick}** over {g.opponent} · **{_pct(g.win_prob)}** · {tier(g.win_prob)}"
    return text + {"W": " · :green[**Won**]", "L": " · :red[**Lost**]", "T": " · **Tie**"}.get(g.result, "")


def where(wg: W.WeekGame) -> str:
    parts = [f"{kickoff(wg.game.kickoff_utc)} Phoenix time"]
    if wg.venue:
        parts.append(wg.venue)
    if wg.neutral:
        parts.append("neutral site (no home field)")
    return " · ".join(parts)


def edge_line(why: Y.Why, g: S.Game) -> str:
    """The engine's edge in points, and what the owner's team note did to it."""
    line = f"Engine edge: **{why.pick} by {why.total_points:.1f} points**"
    if not g.note:
        return line
    line += f" with your team note ({g.note})."
    if g.model_pick != g.pick:
        return line + f" Your note flips the pick: the model alone had the {g.model_pick} at {_pct(g.model_prob)}."
    return line + f" Model alone: {g.model_pick} {_pct(g.model_prob)}, by {abs(why.model_points):.1f}."


def reason_lines(reasons: list[Y.Reason]) -> str:
    if not reasons:
        return "- nothing"
    return "\n".join(f"- {r.label} **+{abs(r.points):.1f}**" + (f" · {r.detail}" if r.detail else "") for r in reasons)


def qb_line(wg: W.WeekGame, qbs: dict[str, W.QB]) -> str:
    parts = []
    for team in (wg.game.away, wg.game.home):
        q = qbs.get(team)
        if q is None:
            continue
        starts = sum(s == q.last_starter for s in q.starters)
        text = f"{team}: {q.last_starter or 'unknown'}" + (f" ({starts} of {q.games} starts)" if q.games else "")
        if q.flag:
            text += f" · :orange[{q.flag}]"
        parts.append(text)
    return "QBs (last starters) · " + " · ".join(parts) if parts else ""


def final_line(g: S.Game) -> str:
    if not g.final:
        return ""
    if g.home_score >= g.away_score:
        return f"Final: {g.home} {g.home_score}, {g.away} {g.away_score}"
    return f"Final: {g.away} {g.away_score}, {g.home} {g.home_score}"


def ratings_rows(f: Y.Formula | None, rs: W.RatingSet) -> list[dict[str, Any]]:
    """Every team in a ratings set, best first by the engine's rating in points (when the formula is known)."""
    rows = []
    for r in rs.teams.values():
        rows.append(
            {
                "Team": r.team,
                "Rating (pts)": round(Y.power(f, r), 1) if f else None,
                "Offense EPA/play": round(r.off_epa, 3),
                "Offense rank": r.ranks["off_epa"],
                "Defense EPA allowed": round(r.def_epa, 3),
                "Defense rank": r.ranks["def_epa"],
                "Offense success": round(100 * r.off_sr, 1),
                "Defense success allowed": round(100 * r.def_sr, 1),
                "Plays": r.plays,
            }
        )
    rows.sort(key=lambda x: (-(x["Rating (pts)"] or 0), x["Offense rank"]))
    for n, row in enumerate(rows, start=1):
        row["Rank"] = n
    return [{"Rank": row.pop("Rank"), **row} for row in rows]


def qb_rows(week: W.Week) -> list[dict[str, Any]]:
    opponent, status = {}, {}
    for wg in week.games:
        g = wg.game
        opponent[g.away], opponent[g.home] = f"at {g.home}", f"vs {g.away}"
        status[g.away] = status[g.home] = (
            f"Pick: {g.pick} {_pct(g.win_prob)}" if g.is_pick else f"No pick: {g.reason or 'no reason saved'}"
        )
    rows = [
        {
            "Team": q.team,
            "Game": opponent.get(q.team, ""),
            "Engine": status.get(q.team, ""),
            "Flag": q.flag,
            "Last starter": q.last_starter,
            "Season leader": q.season_leader,
            "Starters by game": " > ".join(q.starters),
        }
        for q in week.qbs.values()
    ]
    return sorted(rows, key=lambda r: (r["Flag"] == "", r["Team"]))


def graded_games(slates: list[S.Slate]) -> list[tuple[int, int, S.Game]]:
    """(season, week, game) for every NFL game with a final score, official pick first."""
    out = []
    for slate in slates:
        if slate.graded_path is None:
            continue
        season, week = W.season_week(slate)
        out += [(season, week, g) for g in S.load_games(slate) if g.is_pick and g.final]
    return out


def _model_result(g: S.Game) -> str:
    """W/L/T for the model-alone pick."""
    if g.model_pick is None or not g.final:
        return ""
    if g.home_score == g.away_score:
        return "T"
    return "W" if (g.home if g.home_score > g.away_score else g.away) == g.model_pick else "L"


def record_rows(graded: list[tuple[int, int, S.Game]]) -> list[dict[str, Any]]:
    """Official record by week and tier, with the model alone beside it."""
    by_week: dict[tuple[int, int], list[S.Game]] = defaultdict(list)
    for season, week, g in graded:
        by_week[(season, week)].append(g)
    rows = []
    for (season, week), games in sorted(by_week.items(), reverse=True) + [((0, 0), [g for *_, g in graded])]:
        row = {"Week": f"{season} Week {week}" if season else "Season so far"}
        row["Official"] = record([g.result for g in games])
        for name, low, rng in TIERS:
            high = min((lo for _, lo, _ in TIERS if lo > low), default=1.01)
            row[f"{name} ({rng})"] = record([g.result for g in games if low <= g.win_prob < high])
        row["Model alone"] = record([_model_result(g) for g in games])
        rows.append(row)
    return rows


def closing_check(card: list[dict[str, str]]) -> dict[str, Any] | None:
    """The engine against the closing line on its graded picks (nfl_cfbmethod/grade.py's check; grading only)."""
    rows = [r for r in card if r.get("status") == "PICK" and r.get("market_p_home") not in (None, "")]
    if not rows:
        return None
    y = [float(r["home_win"]) for r in rows]
    pe = [float(r["p_home"]) for r in rows]
    pm = [float(r["market_p_home"]) for r in rows]

    def res(p: float, yy: float) -> str:
        return "T" if yy == 0.5 else ("W" if (p > 0.5) == (yy == 1) else "L")

    engine = [res(p, yy) for p, yy in zip(pe, y)]
    market = [res(p, yy) for p, yy in zip(pm, y)]
    split = [res(p, yy) for p, q, yy in zip(pe, pm, y) if (p > 0.5) != (q > 0.5)]
    return {
        "games": len(rows),
        "engine": record(engine),
        "market": record(market),
        "brier_engine": sum((p - yy) ** 2 for p, yy in zip(pe, y)) / len(rows),
        "brier_market": sum((p - yy) ** 2 for p, yy in zip(pm, y)) / len(rows),
        "underdog_picks": record(split) if split else "",
    }


# --------------------------------------------------------------------------- #
# Streamlit
# --------------------------------------------------------------------------- #
def _game_card(st: Any, week: W.Week, wg: W.WeekGame, f: Y.Formula | None) -> None:
    g = wg.game
    with st.container(border=True):
        st.markdown(headline(wg))
        st.caption(where(wg))
        if not g.is_pick:
            st.markdown(f"Reason: {g.reason or 'no reason saved'}")
        else:
            rs, exact = week.ratings_for(wg)
            why = Y.explain(wg, f, rs.teams if rs else {})
            if why is None:
                st.markdown(f"The engine's win chance: {g.pick} {_pct(g.win_prob)}.")
            else:
                st.markdown(edge_line(why, g))
                left, right = st.columns(2)
                left.markdown(f"**Helping the {why.pick}**\n\n" + reason_lines(why.helping_pick))
                right.markdown(f"**Helping the {why.opponent}**\n\n" + reason_lines(why.helping_opponent))
                if why.even:
                    st.caption("About even: " + ", ".join(r.label for r in why.even))
                if why.detailed and not exact:
                    st.caption(
                        f"These team ratings are from a different engine run (cutoff {rs.cutoff_utc}) than this pick, "
                        f"so they add up to {sum(r.points for r in why.reasons):.1f} points, not the logged "
                        f"{why.total_points:.1f}."
                    )
                elif not why.detailed:
                    st.caption("Team-by-team ratings for this week aren't saved yet (nfl_ui/ratings.py).")
        for line in (qb_line(wg, week.qbs), final_line(g)):
            if line:
                st.caption(line)


def _picks_tab(st: Any, week: W.Week, f: Y.Formula | None, now: dt.datetime) -> None:
    picks = [wg for wg in week.games if wg.game.is_pick]
    upcoming = [wg for wg in picks if not wg.game.started(now)]
    played = [wg for wg in picks if wg.game.started(now)]
    no_picks = [wg for wg in week.games if not wg.game.is_pick]
    counts = defaultdict(int)
    for wg in picks:
        counts[tier(wg.game.win_prob).split(" (")[0]] += 1
    graded = [wg.game.result for wg in picks if wg.game.result]
    st.caption(
        f"{plural(len(picks), 'pick')} ({', '.join(f'{counts[n]} {TIER_COUNT[n][counts[n] != 1]}' for n, *_ in TIERS if counts[n])}), "
        f"{plural(len(no_picks), 'no-pick')}"
        + (f" · this week so far {record(graded)}" if graded else "")
        + ". Each pick lists what helps each team, in points on the engine's own scale, biggest first; "
        "the two lists' difference is the engine's edge."
    )
    if f is None:
        st.warning("This week's logged numbers don't fit the engine's formula, so the reasons aren't broken down.")
    sections = [("Still to play", upcoming), ("No pick", no_picks), ("Played", played)]
    for title, items in sections:
        if items:
            st.subheader(f"{title} ({len(items)})")
            for wg in items:
                _game_card(st, week, wg, f)


def _ratings_tab(st: Any, week: W.Week, f: Y.Formula | None) -> None:
    rs = week.latest_ratings
    if rs is None:
        st.info(
            "Team ratings for this week aren't saved yet. They're rebuilt with the engine's own code by "
            f"`python3 nfl_ui/ratings.py --season {week.season} --week {week.week}` (it changes no pick)."
        )
        return
    caption = (
        f"The engine's ratings from its run with cutoff {rs.cutoff_utc} (games finished before then), each minus the "
        "league average, so 0 is an average unit. Offense: expected points it gains per play and its success rate. "
        "Defense: what it allows (lower is better)."
    )
    if f:
        caption += (
            " Rating: points better than a league-average team on a neutral field; two teams' ratings differ by the "
            f"engine's edge between them, plus {f.home_points:.1f} for home field."
        )
    st.caption(caption)
    st.dataframe(
        ratings_rows(f, rs),
        hide_index=True,
        width="stretch",
        column_config={
            "Offense success": st.column_config.NumberColumn(format="%+.1f%%"),
            "Defense success allowed": st.column_config.NumberColumn(format="%+.1f%%"),
            "Offense EPA/play": st.column_config.NumberColumn(format="%+.3f"),
            "Defense EPA allowed": st.column_config.NumberColumn(format="%+.3f"),
            "Rating (pts)": st.column_config.NumberColumn(format="%+.1f"),
        },
    )


def _qb_tab(st: Any, week: W.Week) -> None:
    rows = qb_rows(week)
    if not rows:
        st.info("No QB report saved for this week.")
        return
    st.caption(
        "The engine can't read injury reports, so every flagged team (and every starter) is checked in the news before "
        "the picks stand. The regular starter out, or not confirmed, means no pick. Flags: "
        + "; ".join(f"{k}: {v}" for k, v in FLAGS.items())
        + "."
    )
    st.dataframe(rows, hide_index=True, width="stretch")


def _record_tab(st: Any, slates: list[S.Slate]) -> None:
    graded = graded_games(slates)
    st.markdown("**This season: official picks (with your team notes)**")
    if graded:
        st.dataframe(record_rows(graded), hide_index=True, width="stretch")
    else:
        st.caption("No graded games yet.")
    check = closing_check(W.scorecard())
    st.markdown("**Against the closing line (grading only)**")
    if check:
        st.markdown(
            f"- {check['games']} graded picks: engine {check['engine']}, closing-line favorite {check['market']}\n"
            f"- Accuracy of the win chances (Brier score, lower is better): engine {check['brier_engine']:.3f}, "
            f"closing line {check['brier_market']:.3f}"
            + (
                f"\n- When the engine picked the market's underdog: {check['underdog_picks']}"
                if check["underdog_picks"]
                else ""
            )
        )
        st.caption(
            "Closing lines are read only here, after the games, as nfl_cfbmethod/grade.py does; they never go into a "
            "pick. Graded on the model alone, without team notes."
        )
    else:
        st.caption("No graded weeks in nfl_scorecard.csv yet.")
    st.markdown("**Backtest, 2019-2025 (1,522 games, weeks 4-18)**")
    st.dataframe(BACKTEST, hide_index=True)
    st.caption("From METHOD.md. The closing line was still more accurate (Brier 0.2087 vs 0.2264).")


def _notes_tab(st: Any, now: dt.datetime) -> None:
    directory = S.results_dir()
    path = directory / "team_notes.json"
    if not path.exists():
        st.info("No team notes saved.")
        return
    tn = S.team_notes_module(directory)
    notes = tn.load(str(path))
    st.caption(
        "Your notes, from watching the games. They move a team's predicted margin in the official picks (the model-alone "
        "numbers stay beside them) and are graded on every pick involving the team. Only you add, renew or clear one."
    )
    live = tn.current(notes, now)
    st.markdown("**In force now**")
    if live:
        st.dataframe(
            [
                {
                    "Team": e["team"],
                    "Note": tn.note_text(notes, e, team=False),
                    "Set": tn.phx(e["_t"]),
                    "Runs out": tn.phx(tn.expires_at(notes, e)) if tn.expires_at(notes, e) else "",
                }
                for e in live
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("None.")
    st.markdown("**Scorecard (engine)**")
    rows = [r for r in tn.scorecard(str(directory), notes) if r["model"] == "engine"]
    shown = [
        {
            "Team": r["team"],
            "Note": r["label"],
            "Status": r["state"],
            "Games": r["s"]["games"],
            "Team record": r["s"]["record"],
            "Wins vs model alone": f"{r['s']['wins_vs']:+.1f} (luck ±{r['s']['luck_wins']:.1f})",
            "Points per game vs model alone": f"{r['s']['pts_vs']:+.1f} (luck ±{r['s']['luck_pts']:.1f})",
            "Verdict": r["s"]["status"],
        }
        for r in rows
        if r["s"]
    ]
    if shown:
        st.dataframe(shown, hide_index=True, width="stretch")
    else:
        st.caption("No graded games with a noted team yet.")
    st.markdown("**Every read you've given**")
    st.dataframe(
        [
            {
                "When": tn.phx(e["_t"]),
                "Team": e["team"],
                "Action": e["action"],
                "Note": tn.note_text(notes, e, team=False) if e["action"] == "set" else "",
                "Your words": e.get("owner_said", ""),
            }
            for e in reversed(notes["events"])
        ],
        hide_index=True,
        width="stretch",
    )


HOW_IT_WORKS = """
**What goes in:** ESPN play-by-play only, from 2018 on: every scrimmage play's expected points added (EPA: how much the
play changed the offense's expected points, from down, distance, field position and time) and whether it was a success
(half the distance on 1st down, 70% on 2nd, all of it on 3rd or 4th). Garbage time is thrown out. No betting lines,
records, yards, points scored or narrative.

**Team ratings:** every team gets an offense and a defense number for EPA and for success rate, adjusted for the
opponents it played. They start from 30% of last season's ratings, and this season's plays count half as much for
every 5 weeks they're older.

**Win chance:** three numbers per game: the home team's EPA edge and success edge (its offense plus what the opponent's
defense allows, minus the reverse) and home field (none at a neutral site). A logistic regression fit on every season's
week-by-week replay since 2019 turns them into a win chance. The pick is the team at 50% or more.

**Points:** the reasons on each pick are the same numbers in points, on the engine's own scale (7.8 points per unit of
log-odds, the one your team notes use), so they add up to the engine's edge.

**No pick:** a team with fewer than 150 plays this season, or a starting QB who is out or not confirmed. The reason is
always saved.

**How far to trust it:** only the strongest picks have held up well, and the closing line is still more accurate
(see Track record). A high win chance is not the same as a good bet. Not betting advice.
"""


def render() -> None:
    import streamlit as st

    now = _now()
    st.title("NFL engine")
    slates = W.weeks()
    if not slates:
        st.info(f"No NFL picks saved in `{S.results_dir()}` yet.")
        return
    labels = [s.label for s in slates]
    picked = st.columns([1, 2])[0].selectbox("Week", labels, index=0, key="nfl_week")
    slate = slates[labels.index(picked)]
    week = W.load_week(slate)
    f = Y.formula([wg.numbers for wg in week.games if wg.numbers is not None])
    picks_tab, ratings_tab, qb_tab, record_tab, notes_tab, how_tab = st.tabs(
        ["Picks", "Team ratings", "QB check", "Track record", "Team notes", "How it works"]
    )
    with picks_tab:
        _picks_tab(st, week, f, now)
    with ratings_tab:
        _ratings_tab(st, week, f)
    with qb_tab:
        _qb_tab(st, week)
    with record_tab:
        _record_tab(st, slates)
    with notes_tab:
        _notes_tab(st, now)
    with how_tab:
        st.markdown(HOW_IT_WORKS)
