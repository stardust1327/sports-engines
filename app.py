"""Parlay builder: browse the college and NFL engines' picks and build parlays that don't all lose together.

    streamlit run app.py

Read-only. It reads the picks the engines save in results/ (or SPORTS_RESULTS_DIR) and never changes a pick, a rule or
a team note, and never uses a betting line (CLAUDE.md rules 1-6). The data layer is in parlay_app/.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Any

from parlay_app import parlays as P
from parlay_app import slates as S

REDUNDANCY = {
    # label: (max parlays per team, max legs any two parlays share)
    "None: every parlay uses different teams": (1, 0),
    "Low: a team in at most 2 parlays, any two share at most 1 leg": (2, 1),
    "Medium: a team in at most 3 parlays, any two share at most 2 legs": (3, 2),
}
DISCLAIMER = (
    "Win chances are the engines' own, from play-by-play only; no betting line is used. Legs are treated as "
    "independent. A sportsbook pays less than the fair odds shown, on every leg. Not betting advice."
)


def _pct(p: float) -> str:
    return f"{100 * p:.1f}%"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def game_rows(games: list[S.Game]) -> list[dict[str, Any]]:
    rows = []
    for g in games:
        if not g.is_pick:
            continue
        noted = g.note and g.model_pick is not None and (g.model_pick, g.model_prob) != (g.pick, g.win_prob)
        rows.append(
            {
                "Kickoff": g.kickoff_text,
                "Matchup": f"{g.away} @ {g.home}",
                "Pick": g.pick,
                "Win chance": round(100 * g.win_prob, 1),
                "Tier": S.tier(g.win_prob),
                "Note": (g.note + f" (model alone: {g.model_pick} {_pct(g.model_prob)})") if noted else g.note,
                "Result": g.result or ("Final" if g.final else ""),
            }
        )
    return rows


def record_by_tier(games: list[S.Game]) -> list[dict[str, Any]]:
    """W-L of graded official picks, by confidence tier."""
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for g in games:
        if g.result in ("W", "L"):
            tally[S.tier(g.win_prob)][0 if g.result == "W" else 1] += 1
    rows = []
    for name in ("70%+", "60-70%", "Under 60%"):
        won, lost = tally.get(name, [0, 0])
        if won + lost:
            rows.append({"Tier": name, "Won": won, "Lost": lost, "Hit rate": f"{won / (won + lost):.0%}"})
    return rows


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
def _render_parlay(st: Any, title: str, legs: list[P.Leg]) -> None:
    prob = P.parlay_prob(legs)
    with st.container(border=True):
        st.markdown(f"**{title}** · {len(legs)} legs · **{_pct(prob)} to win** · fair odds {P.fair_american(prob)}")
        st.markdown("\n".join(f"- {leg.tag}" for leg in legs))


def _render_games(st: Any, selected: list[tuple[S.Slate, list[S.Game]]], now: dt.datetime) -> None:
    for slate, games in selected:
        picks = [g for g in games if g.is_pick]
        upcoming = [g for g in picks if not g.started(now)]
        st.subheader(slate.label)
        st.caption(f"{len(picks)} picks ({len(upcoming)} not started yet) · {len(games) - len(picks)} no-picks")
        rows = game_rows(games)
        if rows:
            st.dataframe(
                rows,
                hide_index=True,
                width="stretch",
                column_config={
                    "Win chance": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)
                },
            )
        no_picks = [g for g in games if not g.is_pick]
        if no_picks:
            with st.expander(f"No pick ({len(no_picks)})"):
                st.markdown("\n".join(f"- **{g.away} @ {g.home}**: {g.reason or 'no reason saved'}" for g in no_picks))


def _render_builder(st: Any, legs: list[P.Leg]) -> None:
    st.caption("Choose how many legs and which picks to use. Only games that haven't started are offered.")
    mode_labels = {
        "Highest chances": "highest",
        "Lowest chances": "lowest",
        "Chance range": "range",
        "Pick teams": "teams",
    }
    mode = mode_labels[st.radio("Legs", list(mode_labels), horizontal=True, key="build_mode")]
    low, high, chosen, n_legs = 0.5, 1.0, [], 0
    if mode == "teams":
        by_id = {leg.leg_id: leg for leg in legs}
        chosen = st.multiselect("Teams", list(by_id), format_func=lambda i: by_id[i].tag, key="build_teams")
    else:
        n_legs = st.slider("Number of legs", 2, max(2, min(15, len(legs))), min(4, max(2, len(legs))), key="build_n")
        if mode == "range":
            low_pct, high_pct = st.slider("Win chance range (%)", 50, 100, (70, 85), key="build_range")
            low, high = low_pct / 100, high_pct / 100
    picked = P.pick_legs(legs, n_legs, mode, low=low, high=high, chosen=chosen)
    if not picked:
        st.info("No legs match. Pick some teams, or widen the range.")
        return
    if mode != "teams" and len(picked) < n_legs:
        st.warning(f"Only {len(picked)} legs match, so the parlay has {len(picked)} legs.")
    _render_parlay(st, "Your parlay", picked)


def _render_recommendations(st: Any, legs: list[P.Leg]) -> None:
    st.caption(
        "The strongest parlays that fit your redundancy limit, so one loss can't sink most of them. "
        "Only games that haven't started are used."
    )
    cols = st.columns(3)
    n_parlays = cols[0].number_input("Parlays", 1, 25, 10, key="rec_n")
    legs_per = cols[1].number_input("Legs per parlay", 2, 12, 4, key="rec_legs")
    min_pct = cols[2].slider("Only legs at least (%)", 50, 90, 50, key="rec_min")
    preset = st.selectbox("Redundancy", list(REDUNDANCY), index=1, key="rec_redundancy")
    max_uses, max_shared = REDUNDANCY[preset]
    with st.expander("Custom limits"):
        if st.toggle("Use custom limits", key="rec_custom"):
            max_uses = st.slider("A team can be in at most this many parlays", 1, 10, max_uses, key="rec_uses")
            max_shared = st.slider(
                "Any two parlays share at most this many legs",
                0,
                int(legs_per) - 1,
                min(max_shared, int(legs_per) - 1),
                key="rec_shared",
            )
    recs = P.recommend(
        legs, int(n_parlays), int(legs_per), max_uses=max_uses, max_shared=max_shared, min_prob=min_pct / 100
    )
    if not recs:
        st.info("No parlay fits these limits. Use fewer legs, loosen the redundancy, or add another slate.")
        return
    if len(recs) < n_parlays:
        st.warning(f"Only {len(recs)} parlays fit these limits. Loosen the redundancy or add another slate for more.")
    outlook = P.outlook(recs)
    worst = P.exposure(recs)[0].parlays
    riskiest = [e.leg.team for e in P.exposure(recs) if e.parlays == worst]
    m = st.columns(3)
    m[0].metric("Expected winning parlays", f"{outlook.expected_wins:.1f} of {len(recs)}")
    m[1].metric("Chance at least one wins", _pct(outlook.any_wins))
    m[2].metric(
        "Most parlays one loss can sink",
        f"{worst} of {len(recs)}",
        help="Picks in that many parlays: " + ", ".join(riskiest),
    )
    for n, parlay in enumerate(recs, start=1):
        _render_parlay(st, f"Parlay {n}", list(parlay))
    st.markdown("**If a pick loses**")
    st.dataframe(
        [
            {"Pick": e.leg.label, "Win chance": _pct(e.leg.prob), "Parlays that lose": f"{e.parlays} of {len(recs)}"}
            for e in P.exposure(recs)
        ],
        hide_index=True,
        width="stretch",
    )


def _render_record(st: Any, slates: list[S.Slate]) -> None:
    st.caption("Official picks graded so far, by confidence tier (every saved slate with results).")
    for sport in ("cfb", "nfl"):
        games = [g for s in slates if s.sport == sport and s.graded_path for g in S.load_games(s)]
        rows = record_by_tier(games)
        st.markdown(f"**{S.SPORT_NAMES[sport]}**")
        if rows:
            st.dataframe(rows, hide_index=True)
        else:
            st.caption("No graded games yet.")


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Parlay Builder", page_icon=":material/sports_football:", layout="wide")
    now = _now()
    slates = S.discover_slates()
    st.title("Parlay Builder")
    if not slates:
        st.info(f"No saved picks in `{S.results_dir()}`. Run the engines (see README) and reload.")
        return

    with st.sidebar:
        st.header("Games")
        chosen: list[S.Slate] = []
        for sport in ("cfb", "nfl"):
            options = [s for s in slates if s.sport == sport]
            if not options:
                continue
            default = S.default_slate(slates, sport, now)
            names = ["None"] + [s.label for s in options]
            picked = st.selectbox(
                S.SPORT_NAMES[sport], names, index=names.index(default.label) if default else 0, key=f"slate_{sport}"
            )
            chosen += [s for s in options if s.label == picked]
        st.caption("New picks appear here when the engines save them to results/.")

    selected = [(s, S.load_games(s)) for s in chosen]
    legs = P.legs_from(g for _, games in selected for g in games if not g.started(now))
    st.caption(
        f"{len(legs)} picks available for parlays from "
        + (", ".join(s.label for s, _ in selected) or "no slate")
        + ". "
        + DISCLAIMER
    )
    games_tab, build_tab, rec_tab, record_tab = st.tabs(
        ["Games", "Build a parlay", "Recommended parlays", "Track record"]
    )
    with games_tab:
        if selected:
            _render_games(st, selected, now)
        else:
            st.info("Choose a college day or an NFL week in the sidebar.")
    with build_tab:
        if legs:
            _render_builder(st, legs)
        else:
            st.info("No games left to start in the chosen slates. Choose an upcoming day or week.")
    with rec_tab:
        if legs:
            _render_recommendations(st, legs)
        else:
            st.info("No games left to start in the chosen slates. Choose an upcoming day or week.")
    with record_tab:
        _render_record(st, slates)


if __name__ == "__main__":
    main()
