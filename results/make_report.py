"""Build the picks/results PDF for any check-in: graded NFL weeks and college
dates, and new NFL and college picks, engine and framework side by side.

  python3 results/make_report.py --out results/report_2026-10-13.pdf \
      --nfl-graded 2026:5 --nfl-picks 2026:6 --cfb-picks 2026-10-13 --cfb-picks 2026-10-14
  python3 results/make_report.py --out results/report_2026-10-17.pdf \
      --cfb-graded 2026-10-13 --cfb-graded 2026-10-16 --cfb-picks 2026-10-17

Each section gets its own page, in this order: "What to act on" (when there are
picks: the engine's picks for games not yet started, grouped as act on / lean /
pass by their backtest hit rates; owner's request 2026-10-24, --no-glance leaves
it out), "Season so far" (with --season-summary 2026: every graded pick this
season, both sports and both models, by week and by win-chance tier next to the
backtests; owner's request 2026-10-31), NFL graded, college graded, NFL picks,
college picks, and (with any NFL
section, once the owner has set a team note) the team notes scorecard. Every
number is read from the logged files in results/:
  NFL graded   nfl_cfbmethod_<S>_week<WW>_picks.csv and _graded.csv (nfl_cfbmethod/grade.py),
               prompt_nfl_<S>_week<WW>_picks.csv and _graded.csv (results/grade_picks.py)
  college      cfb_<date>_picks.csv / _graded.csv, prompt_cfb_<date>_picks.csv / _graded.csv
  NFL picks    nfl_cfbmethod_<S>_week<WW>_picks.csv, prompt_nfl_<S>_week<WW>_picks.csv
  team notes   team_notes.json (the owner's notes) and team_notes_graded.csv (results/team_notes.py grade)
NFL pages apply the owner's team notes (team_notes.py): official picks and
records include them, and every noted game also shows the model-alone number.
Kickoff times are Phoenix, as the models write them.
"""
import argparse
import os
import sys
from xml.sax.saxutils import escape

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import team_notes  # noqa: E402  (results/team_notes.py)


def apply_notes(df, model):
    """The owner's team notes on top of a picks file; a no-op while TEAM_NOTES_ON is False."""
    return team_notes.apply(df, model, NOTES) if TEAM_NOTES_ON and df is not None else df
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
INK, MUTED, RULE = colors.HexColor("#1F2937"), colors.HexColor("#6B7280"), colors.HexColor("#D1D5DB")
AGREE, SPLIT, NOPICK = colors.HexColor("#E7F4EA"), colors.HexColor("#FDF1DC"), colors.HexColor("#EEEEEE")
RES_COLOR = {"W": "#15803D", "L": "#B91C1C", "T": "#6B7280"}
RES_WORD = {"W": "Win", "L": "Loss", "T": "Tie"}


def style(name, size, bold=False, color=INK, lead=None, align=0):
    return ParagraphStyle(name, fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                          leading=lead or size * 1.25, textColor=color, alignment=align)


S_TITLE, S_SUB, S_H = style("t", 18, True), style("s", 9.5, color=MUTED), style("h", 12, True)
S_CELL, S_CELLB, S_HEAD = style("c", 9), style("cb", 9, True), style("hd", 8.5, True, colors.white)
S_NOTE, S_BOX = style("n", 7.9, color=MUTED, lead=10), style("bx", 8.8, lead=11.4)
S_BIG, S_BIGL = style("bg", 20, True, align=1, lead=23), style("bl", 8.5, color=MUTED, align=1)
S_TCELL, S_TCELLB = style("tc", 8.2, lead=10), style("tcb", 8.2, True, lead=10)
S_SMALL = style("sm", 6.8, color=MUTED, lead=8.2)
FLIP = "#B45309"  # a pick your team note changed


def P(text, st):
    return Paragraph(text, st)


DIR = HERE  # --dir changes it (for tests)
TEAM_NOTES_ON = False  # turned off by the owner 2026-10-17 ("Turn it off and drop the page")
NOTES = None  # the owner's team notes (team_notes.json), loaded when the report has an NFL section


def path(name):
    return os.path.join(DIR, name)


def read(name, required=True):
    if not os.path.exists(path(name)):
        if required:
            raise SystemExit(f"missing {name}: run the model / grader first")
        return None
    return pd.read_csv(path(name), dtype={"game_id": str})


def rec(results):
    r = pd.Series(list(results)).fillna("")
    w, l, t = (r == "W").sum(), (r == "L").sum(), (r == "T").sum()
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def res_cell(r):
    r = r if isinstance(r, str) else ""
    return P(f'<font color="{RES_COLOR.get(r, "#6B7280")}"><b>{RES_WORD.get(r, "Pending")}</b></font>', S_CELL)


def table(rows, widths, bg, span_from=None):
    t = Table(rows, colWidths=[w * inch for w in widths], repeatRows=1)
    ts = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
          ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE)]
    for i, c, span in bg:
        if c is not None:
            ts.append(("BACKGROUND", (0, i), (-1, i), c))
        if span and span_from is not None:
            ts.append(("SPAN", (span_from, i), (-1, i)))
    t.setStyle(TableStyle(ts))
    return t


def boxes(cells, width):
    t = Table([cells], colWidths=[width * inch] * len(cells))
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
          ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    st += [("BOX", (i, 0), (i, 0), 0.6, RULE) for i in range(len(cells))]
    t.setStyle(TableStyle(st))
    return t


def big_numbers(items):
    t = Table([[P(v, S_BIG) for v, _ in items], [P(l, S_BIGL) for _, l in items]],
              colWidths=[10.0 / len(items) * inch] * len(items))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LINEAFTER", (0, 0), (-2, -1), 0.6, RULE),
                           ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 1), (-1, 1), 8)]))
    return t


PHX = "America/Phoenix"


def us_date(d):
    """A date as MM.DD.YYYY (the owner's format), e.g. 10.18.2026."""
    return pd.Timestamp(d).strftime("%m.%d.%Y")


def kick_dt(r):
    """Kickoff as a Phoenix timestamp (from kickoff_utc), or None."""
    k = getattr(r, "kickoff_utc", None)
    if not isinstance(k, str) or not k:
        return None
    return pd.Timestamp(k).tz_convert(PHX)


def kick_cell(r):
    """Kickoff cell: the model's day and time with the full date, e.g. 'Sun 10.18.2026 / 10:00 AM'."""
    t = kick_dt(r)
    if t is None:
        return P(escape(str(r.kickoff)), S_CELL)
    return P(f"{t.strftime('%a')} {us_date(t)}<br/>{t.strftime('%-I:%M %p')}", S_CELL)


def date_span(df):
    """'10.15.2026 to 10.19.2026' (or a single date) for the games in df, Phoenix dates."""
    ds = sorted({pd.Timestamp(k).tz_convert(PHX).normalize() for k in df.kickoff_utc.dropna()})
    if not ds:
        return ""
    return us_date(ds[0]) if len(ds) == 1 else f"{us_date(ds[0])} to {us_date(ds[-1])}"


def game_label(r, neutral_word, star=False):
    """'Away at Home'; with star=True, an asterisk after each team that has one of your team notes."""
    away = r.away_name + ("*" if star and truthy(getattr(r, "noted_away", False)) else "")
    home = r.home_name + ("*" if star and truthy(getattr(r, "noted_home", False)) else "")
    return f"{away} at {home}" + (f" ({neutral_word})" if bool(r.neutral) else "")


def pick_text(status, pick, prob):
    if status != "PICK":
        return "No pick"
    return f"{escape(str(pick))} {float(prob):.0%}"


def lean(p_home, away, home):
    """(team, win chance) the model leans to in a no-pick game, from its saved p_home; None if it has no number."""
    try:
        ph = float(p_home)
    except (TypeError, ValueError):
        return None
    if pd.isna(ph):
        return None
    return (home, ph) if ph >= 0.5 else (away, 1 - ph)


def lean_result(ln, away, home, a_sc, h_sc):
    if ln is None or pd.isna(h_sc) or pd.isna(a_sc):
        return ""
    w = home if h_sc > a_sc else away if a_sc > h_sc else "tie"
    return "T" if w == "tie" else "W" if w == ln[0] else "L"


def lean_words(e, f, e_res="", f_res=""):
    """'Off record: engine X 70% (right), framework Y 65% (wrong)' for a no-pick game."""
    parts = []
    for name, ln, res in (("engine", e, e_res), ("framework", f, f_res)):
        if ln is not None:
            parts.append(f"{name} {escape(str(ln[0]))} {ln[1]:.0%}" + (f" ({ {'W': 'right', 'L': 'wrong', 'T': 'tie'}[res]})" if res in ("W", "L", "T") else ""))
    return ("<i>Off record: " + ", ".join(parts) + "</i>") if parts else "<i>Off record: no number (not enough data)</i>"


def note_line(note, alone_pick, alone_prob, flipped, alone_result=None):
    """Small line under a pick for a game with one of your team notes ('' for other games)."""
    if not isinstance(note, str) or not note:
        return ""
    alone = f"model alone {escape(str(alone_pick))} {float(alone_prob):.0%}"
    if isinstance(alone_result, str) and alone_result in RES_WORD:
        alone += f" ({RES_WORD[alone_result].lower()})"
    if flipped:
        return f'<font color="{FLIP}"><b>Changed by your note</b> ({escape(note)}); {alone}</font>'
    return f"{escape(note)}; {alone}"


def pick_cell(main, st, extra=""):
    """A pick, with the small team-note line under it when there is one."""
    return [P(main, st), P(extra, S_SMALL)] if extra else P(main, st)


def truthy(x):
    return str(x).strip().lower() == "true"


# ------------------------------------------------------------------ graded

def graded_section(story, title, sub, eng, eng_g, frm, frm_g, neutral_word, market=None):
    """eng/frm: picks; eng_g/frm_g: graded files (result per game_id); frm may be None (not run).
    NFL picks come with the owner's team notes applied (team_notes.apply): then the picks
    and records shown are the noted (official) ones, with the model-alone ones beside them."""
    noted = "pick_noted" in eng.columns
    g_e = eng_g.set_index("game_id")
    m = eng.copy()
    m["e_result"] = m.game_id.map(g_e["result"])
    m["away_score"], m["home_score"] = m.game_id.map(g_e["away_score"]), m.game_id.map(g_e["home_score"])
    if frm is not None:
        f = frm.set_index("game_id")
        m["f_status"], m["f_pick"], m["f_prob"] = m.game_id.map(f["status"]), m.game_id.map(f["pick"]), m.game_id.map(f["pick_prob"])
        m["f_result"] = m.game_id.map(frm_g.set_index("game_id")["result"]) if frm_g is not None else ""
        m["f_p_home"] = m.game_id.map(f["p_home"]) if "p_home" in f.columns else None
    else:
        m["f_status"], m["f_pick"], m["f_prob"], m["f_result"] = "NOT RUN", "", None, ""
        m["f_p_home"] = None
    e_flips = f_flips = False
    if noted:
        def results(picks, statuses):
            return [team_notes.result_of(p, a, h, asc, hsc) if s == "PICK" else ""
                    for p, s, a, h, asc, hsc in zip(picks, statuses, m.away_name, m.home_name, m.away_score, m.home_score)]
        m["e_pick_alone"], m["e_prob_alone"], m["e_result_alone"] = m["pick"], m["pick_prob"], m["e_result"]
        m["pick"], m["pick_prob"] = m["pick_noted"], m["pick_prob_noted"]
        m["e_note"], m["e_flip"] = m["note_text"], m["note_flips"].map(truthy)
        m["e_result"] = results(m["pick"], m["status"])
        e_flips = bool(m.loc[m.status == "PICK", "e_flip"].any())
        if frm is not None and "pick_noted" in frm.columns:
            m["f_pick_alone"], m["f_prob_alone"], m["f_result_alone"] = m["f_pick"], m["f_prob"], m["f_result"]
            m["f_pick"], m["f_prob"] = m.game_id.map(f["pick_noted"]), m.game_id.map(f["pick_prob_noted"])
            m["f_note"], m["f_flip"] = m.game_id.map(f["note_text"]), m.game_id.map(f["note_flips"]).map(truthy)
            m["f_result"] = results(m["f_pick"], m["f_status"])
            f_flips = bool(m.loc[m.f_status == "PICK", "f_flip"].any())
    m = m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)
    both = m[(m.status == "PICK") & (m.f_status == "PICK")]
    split = both[both.pick != both.f_pick]
    items = [(rec(m[m.status == "PICK"].e_result), "Engine (official picks)")]
    if e_flips:
        items.append((rec(m[m.status == "PICK"].e_result_alone), "Engine alone, without your team notes"))
    if frm is not None:
        items.append((rec(m[m.f_status == "PICK"].f_result), "Framework (your Prompt Football)"))
        if f_flips:
            items.append((rec(m[m.f_status == "PICK"].f_result_alone), "Framework alone, without your team notes"))
        items.append((rec(split.f_result), f"Framework on the {len(split)} games where they split"))
    pend = m[((m.status == "PICK") | (m.f_status == "PICK")) & m.home_score.isna()]
    story += [P(title, S_TITLE), Spacer(1, 3), P(sub + (f" {len(pend)} game(s) not final yet." if len(pend) else ""), S_SUB),
              Spacer(1, 10), big_numbers(items), Spacer(1, 10)]
    rows, bg = [[P(h, S_HEAD) for h in ["Kickoff", "Game", "Final", "Engine pick", "", "Framework pick", ""]]], []
    any_note = False
    off_e, off_f = [], []
    for i, r in enumerate(m.itertuples(), start=1):
        final = "" if pd.isna(r.home_score) else f"{r.away_name} {int(r.away_score)}, {r.home_name} {int(r.home_score)}"
        if r.status != "PICK" and r.f_status != "PICK":
            why = r.reason if isinstance(r.reason, str) and r.reason else "no pick"
            le = lean(r.p_home, r.away_name, r.home_name)
            lf = lean(r.f_p_home, r.away_name, r.home_name) if r.f_status != "NOT RUN" else None
            re_ = lean_result(le, r.away_name, r.home_name, r.away_score, r.home_score)
            rf_ = lean_result(lf, r.away_name, r.home_name, r.away_score, r.home_score)
            off_e += [re_] if re_ else []
            off_f += [rf_] if rf_ else []
            rows.append([kick_cell(r), P(escape(game_label(r, neutral_word)), S_CELL), P(escape(final), S_CELL),
                         [P(f"No pick (both): {escape(why)}", S_CELL), P(lean_words(le, lf, re_, rf_), S_SMALL)],
                         "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        e_extra = f_extra = ""
        if noted and r.status == "PICK":
            e_extra = note_line(r.e_note, r.e_pick_alone, r.e_prob_alone, r.e_flip, r.e_result_alone if r.e_flip else None)
        if noted and r.f_status == "PICK" and hasattr(r, "f_note"):
            f_extra = note_line(r.f_note, r.f_pick_alone, r.f_prob_alone, r.f_flip, r.f_result_alone if r.f_flip else None)
        any_note = any_note or bool(e_extra or f_extra)
        rows.append([kick_cell(r), P(escape(game_label(r, neutral_word, star=noted)), S_CELL),
                     P(escape(final) or "Not final", S_CELL),
                     pick_cell(pick_text(r.status, r.pick, r.pick_prob), S_CELL, e_extra),
                     res_cell(r.e_result) if r.status == "PICK" else "",
                     pick_cell(pick_text(r.f_status, r.f_pick, r.f_prob), S_CELL, f_extra) if r.f_status != "NOT RUN"
                     else P("Not run", S_CELL),
                     res_cell(r.f_result) if r.f_status == "PICK" else ""])
        bg.append((i, SPLIT if (r.status == r.f_status == "PICK" and r.pick != r.f_pick) else None, False))
    widths = (1.0, 2.05, 1.75, 1.8, 0.75, 1.8, 0.75) if any_note else (1.0, 2.2, 2.3, 1.45, 0.75, 1.45, 0.75)
    story += [table(rows, widths, bg, span_from=3), Spacer(1, 5),
              P("Amber rows: the two models picked different teams. A tie is graded as a tie. Percentages are each "
                "model's win chance for its pick." + (notes_sentence(eng) if any_note else ""), S_NOTE)]
    if off_e or off_f:
        story += [Spacer(1, 8), boxes([
            P(f"<b>Off the record: no-pick games.</b> The team each model would have taken in the grey rows went: "
              f"engine {rec(off_e)}, framework {rec(off_f)}. These never count in either model's record; they're "
              f"shown so you can see whether holding these games back pays off "
              f"(running total: results/nopick_leans.py).", S_BOX)], 10.0)]
    if market is not None and len(market):
        g = market[(market.status == "PICK") & market.market_p_home.notna()]
        if len(g):
            y = g.home_win.astype(float)
            eb, mb = ((g.p_home - y) ** 2).mean(), ((g.market_p_home - y) ** 2).mean()
            fav = ["T" if yy == 0.5 else "W" if (pm > .5) == (yy == 1) else "L" for pm, yy in zip(g.market_p_home, y)]
            dog = g[(g.p_home > .5) != (g.market_p_home > .5)]
            story += [Spacer(1, 8), boxes([
                P(f"<b>Against the betting market (grading only, never an input).</b> The closing-line favorite went "
                  f"{rec(fav)} on the engine's {len(g)} graded games. Accuracy of the win chances (Brier, lower is "
                  f"better): engine {eb:.3f}, closing line {mb:.3f}. The engine picked against the market favorite "
                  f"{len(dog)} times and went {rec(dog.result)}.", S_BOX)], 10.0)]
    story.append(PageBreak())


def nfl_graded(story, season, week):
    ww = f"{week:02d}"
    eng = apply_notes(read(f"nfl_cfbmethod_{season}_week{ww}_picks.csv"), "engine")
    eng_g = read(f"nfl_cfbmethod_{season}_week{ww}_graded.csv")
    frm = read(f"prompt_nfl_{season}_week{ww}_picks.csv", required=False)
    frm = apply_notes(frm, "framework")
    frm_g = read(f"prompt_nfl_{season}_week{ww}_graded.csv", required=frm is not None)
    graded_section(story, f"NFL Week {week} graded ({date_span(eng)})", "Engine graded with nfl_cfbmethod/grade.py, framework with "
                   "results/grade_picks.py. All times Phoenix. No betting lines go into either model.",
                   eng, eng_g, frm, frm_g, "neutral site", market=eng_g)


def cfb_graded(story, dates):
    eng = pd.concat([read(f"cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    eng_g = pd.concat([read(f"cfb_{d}_graded.csv") for d in dates], ignore_index=True)
    fr = [read(f"prompt_cfb_{d}_picks.csv", required=False) for d in dates]
    frm = pd.concat([x for x in fr if x is not None], ignore_index=True) if any(x is not None for x in fr) else None
    fg = [read(f"prompt_cfb_{d}_graded.csv", required=False) for d in dates]
    frm_g = pd.concat([x for x in fg if x is not None], ignore_index=True) if any(x is not None for x in fg) else None
    label = us_date(dates[0]) if len(dates) == 1 else f"{us_date(dates[0])} to {us_date(dates[-1])}"
    graded_section(story, f"College football graded ({label})", "Both models graded with results/grade_picks.py. "
                   "All times Phoenix.", eng, eng_g, frm, frm_g, "neutral site")


# ------------------------------------------------------------------- picks

def picks_section(story, title, sub, eng, frm, neutral_word, note, box_cells):
    """NFL picks come with the owner's team notes applied (team_notes.apply): the picks shown
    are then the noted (official) ones, with the model-alone ones beside noted games."""
    noted = "pick_noted" in eng.columns and "pick_noted" in frm.columns
    extra = ["pick_noted", "pick_prob_noted", "score_noted", "note_text", "note_flips"] if noted else []
    cols = ["game_id", "status", "pick", "pick_prob", "score", "reason"] + (["p_home"] if "p_home" in frm.columns else [])
    m = eng.merge(frm[cols + extra], on="game_id", how="left", suffixes=("_e", "_f"))
    if "p_home_f" not in m.columns:
        m["p_home_e"], m["p_home_f"] = m.get("p_home"), None
    m["status_f"] = m.status_f.fillna("NOT RUN")
    if noted:
        for side in ("e", "f"):
            m[f"alone_pick_{side}"], m[f"alone_prob_{side}"] = m[f"pick_{side}"], m[f"pick_prob_{side}"]
            m[f"pick_{side}"], m[f"pick_prob_{side}"] = m[f"pick_noted_{side}"], m[f"pick_prob_noted_{side}"]
            m[f"flip_{side}"] = m[f"note_flips_{side}"].map(truthy)
        m["score"] = m["score_noted"]
    m = m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)
    rows, bg = [[P(h, S_HEAD) for h in ["Kickoff", "Game", "Engine (official)", "Framework", "Framework score", ""]]], []
    flips, any_note = 0, False
    for i, r in enumerate(m.itertuples(), start=1):
        if r.status_e != "PICK" and r.status_f != "PICK":
            why = r.reason_e if isinstance(r.reason_e, str) and r.reason_e else str(r.reason_f)
            le = lean(r.p_home_e, r.away_name, r.home_name)
            lf = lean(r.p_home_f, r.away_name, r.home_name) if r.status_f != "NOT RUN" else None
            rows.append([kick_cell(r), P(escape(game_label(r, neutral_word)), S_CELL),
                         [P(f"No pick (both): {escape(why)}", S_CELL), P(lean_words(le, lf), S_SMALL)], "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        same = r.status_e == r.status_f == "PICK" and r.pick_e == r.pick_f
        e_strong = r.status_e == "PICK" and r.pick_prob_e >= 0.7
        f_strong = r.status_f == "PICK" and float(r.pick_prob_f) >= 0.7
        e_extra = f_extra = ""
        if noted and r.status_e == "PICK":
            e_extra = note_line(r.note_text_e, r.alone_pick_e, r.alone_prob_e, r.flip_e)
            flips += int(bool(r.flip_e))
        if noted and r.status_f == "PICK":
            f_extra = note_line(r.note_text_f, r.alone_pick_f, r.alone_prob_f, r.flip_f)
            flips += int(bool(r.flip_f))
        any_note = any_note or bool(e_extra or f_extra)
        rows.append([kick_cell(r), P(escape(game_label(r, neutral_word, star=noted)), S_CELL),
                     pick_cell(pick_text(r.status_e, r.pick_e, r.pick_prob_e), S_CELLB if e_strong else S_CELL, e_extra),
                     pick_cell(pick_text(r.status_f, r.pick_f, r.pick_prob_f), S_CELLB if f_strong else S_CELL, f_extra)
                     if r.status_f != "NOT RUN" else P("Not run", S_CELL),
                     P(escape(str(r.score)) if isinstance(r.score, str) else "", S_CELL),
                     P("Agree" if same else "<b>Split</b>" if r.status_e == r.status_f == "PICK" else "", S_CELL)])
        bg.append((i, AGREE if same else SPLIT if r.status_e == r.status_f == "PICK" else NOPICK, False))
    if flips:
        note += f" Your team notes changed {flips} pick(s) on this page (marked \"Changed by your note\")."
    made = m[(m.status_e == "PICK") & (m.status_f == "PICK")]
    agree = (made.pick_e == made.pick_f).sum()
    story += [P(title, S_TITLE), Spacer(1, 3), P(sub, S_SUB), Spacer(1, 9),
              table(rows, (1.0, 2.15, 2.1, 2.1, 2.05, 0.6) if any_note else (1.05, 2.75, 1.75, 1.75, 2.1, 0.6), bg,
                    span_from=2), Spacer(1, 5),
              P(f"They agree on {agree} of {len(made)} picks (green) and split on {len(made) - agree} (amber). "
                f"Bold = 70%+. Grey = no pick; the italic \"off record\" line is the team each model would take "
                f"and its win chance, never counted in the record. {note}", S_NOTE)]
    if box_cells:
        story += [Spacer(1, 8), boxes(box_cells, 10.0 / len(box_cells))]
    story.append(PageBreak())


def notes_sentence(eng):
    """The team notes on this page's picks, for the line under the table ('' when there are none)."""
    t = eng.loc[(eng.status == "PICK") & (eng.note_text.astype(str).str.len() > 0), "note_text"]
    found = sorted({x.strip() for s in t for x in s.split(";")})
    if not found:
        return ""
    return (" <b>* Your team notes:</b> " + escape("; ".join(found)) + " points. A note moves that team's "
            "predicted margin by its points in both models; official picks include it, and the small line under "
            "a pick shows each model alone.")


# ------------------------------------------------------------ what to act on
# Owner's request (2026-10-24): every picks PDF opens with the engine's picks for
# games not yet started, grouped by how often that kind of pick has won. The
# hit rates are the engines' multi-season backtests (results/audit_2026-10-24:
# college 2021-2025, NFL 2016-2025) and the agree/split rates from
# results/proposals/improvement_tests_2026-10-24. This page only ranks picks;
# the official record still counts every pick (METHOD.md section 7).
HIT = {"nfl": {"act": "75%", "lean": "68%", "pass": "53-58%"},
       "cfb": {"act": "81%", "lean": "66%", "pass": "57-59%"}}


def glance_lists(eng, frm, now):
    """(act, lean, pass, no_pick) lines for engine picks whose kickoff is after `now`."""
    m = eng.merge(frm[["game_id", "status", "pick", "pick_prob"]], on="game_id", how="left", suffixes=("_e", "_f"))
    m = m[pd.to_datetime(m.kickoff_utc, utc=True) > now].sort_values(["kickoff_utc", "away_name"])
    act, lean_, pas, nop = [], [], [], []
    for r in m.itertuples():
        t = kick_dt(r)
        when = f"{t.strftime('%a %-I:%M %p')}" if t is not None else escape(str(r.kickoff))
        if r.status_e != "PICK":
            nop.append(f"{escape(r.away_name)} at {escape(r.home_name)}")
            continue
        opp = r.home_name if r.pick_e == r.away_name else r.away_name
        agree = r.status_f == "PICK" and r.pick_f == r.pick_e
        line = f"<b>{escape(str(r.pick_e))}</b> over {escape(opp)} {float(r.pick_prob_e):.0%} <font color='#6B7280'>{when}</font>"
        if float(r.pick_prob_e) >= 0.7:
            act.append(line + ("" if agree or r.status_f != "PICK" else f" <font color='{FLIP}'>(framework: {escape(str(r.pick_f))})</font>"))
        elif float(r.pick_prob_e) >= 0.6 and agree:
            lean_.append(line)
        else:
            pas.append(line + (f" <font color='{FLIP}'>(split)</font>" if r.status_f == "PICK" and not agree else ""))
    return act, lean_, pas, nop


def glance_page(story, sections, now):
    """sections: [(label, key 'nfl'/'cfb', engine picks, framework picks)]. Adds nothing if no game is upcoming."""
    blocks = []
    for label, key, eng, frm in sections:
        act, lean_, pas, nop = glance_lists(eng, frm, now)
        if not (act or lean_ or pas or nop):
            continue
        h = HIT[key]
        head = [P(f"Act on: 70%+ (has won {h['act']})", S_HEAD),
                P(f"Lean: 60-70%, both models agree (has won {h['lean']})", S_HEAD),
                P(f"Pass: under 60% or the models split (has won {h['pass']})", S_HEAD)]
        body = [P("<br/>".join(x) if x else "<i>none</i>", S_TCELL) for x in (act, lean_, pas)]
        t = Table([head, body], colWidths=[3.34 * inch] * 3)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BACKGROUND", (0, 1), (0, 1), AGREE), ("BACKGROUND", (2, 1), (2, 1), NOPICK),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LINEAFTER", (0, 0), (-2, -1), 0.6, RULE)]))
        blocks += [P(label, S_H), Spacer(1, 4), t, Spacer(1, 3),
                   P(("<b>No pick:</b> " + "; ".join(nop) + " (reasons on the detail pages).") if nop else "", S_NOTE),
                   Spacer(1, 10)]
    if not blocks:
        return
    stamp = pd.Timestamp(now).tz_convert(PHX)
    story += [P("What to act on", S_TITLE), Spacer(1, 3),
              P(f"The engine's (official) picks for games not started as of {us_date(stamp)} {stamp.strftime('%-I:%M %p')} "
                "Phoenix, grouped by how often that kind of pick has won in the multi-season backtests. The official "
                "record still counts every pick; this page only ranks them. Full details follow.", S_SUB),
              Spacer(1, 10)] + blocks + [
              P("Hit rates: engine picks in the 2021-2025 college and 2016-2025 NFL backtests "
                "(results/audit_2026-10-24); agree/split rates from results/proposals/improvement_tests_2026-10-24. "
                "When the models split, the engine has been right 57% of the time in college and 55% in the NFL.",
                S_NOTE), PageBreak()]


# ------------------------------------------------------------- season so far
# Owner's request (2026-10-31: "a pdf of results so far and upcoming
# predictions"): one page with every graded pick this season, both sports and
# both models, by week and by win-chance tier next to the multi-season
# backtests, plus the running off-the-record and live-call tallies. Read-only:
# it re-reads the logged picks and graded files in results/ and changes nothing.
# Backtest hit rates: README "How far to trust it" (results/audit_2026-10-24).
TIER_BACKTEST = {
    ("NFL", "engine"): {"70%+": "75.3%", "60-70%": "66.6%", "Under 60%": "52.6%", "All": "62.2% (wks 4-8: 61.1%)"},
    ("NFL", "framework"): {"70%+": "74.5%", "60-70%": "65.9%", "Under 60%": "52.1%", "All": "62.5% (wks 4-8: 57.1%)"},
    ("College", "engine"): {"70%+": "80.9%", "60-70%": "64.7%", "Under 60%": "56.6%", "All": "70.0% (wks 4-8: 67.3%)"},
    ("College", "framework"): {"70%+": "79.4%", "60-70%": "66.4%", "Under 60%": "53.6%", "All": "67.4% (wks 4-8: 64.4%)"},
}


def tier_of(p):
    return "70%+" if p >= 0.7 else "60-70%" if p >= 0.6 else "Under 60%"


def season_picks(season, now):
    """One row per model and game for every logged game that has kicked off by `now`:
    sport, model, slate (sort key, label), status, pick, win chance, result (W/L/T, '' = not final)."""
    import glob
    import re
    rows = []

    def add(sport, model, key, picks, graded, gfinal=None):
        res = graded.set_index("game_id")["result"] if graded is not None else pd.Series(dtype=object)
        for r in picks.itertuples():
            k = getattr(r, "kickoff_utc", None)
            if isinstance(k, str) and k and pd.Timestamp(k) > now:
                continue  # not started: it's on the picks pages
            out = res.get(r.game_id, "") if r.status == "PICK" else ""
            rows.append({"sport": sport, "model": model, "key": key, "game_id": r.game_id, "kickoff_utc": k,
                         "status": r.status, "pick": r.pick if r.status == "PICK" else "",
                         "prob": float(r.pick_prob) if r.status == "PICK" else None,
                         "result": out if isinstance(out, str) and out in ("W", "L", "T") else ""})

    for f in sorted(glob.glob(path(f"nfl_cfbmethod_{season}_week*_picks.csv"))):
        ww = re.search(r"week(\d+)_picks", f).group(1)
        eng = read(os.path.basename(f))
        add("NFL", "engine", int(ww), eng, read(f"nfl_cfbmethod_{season}_week{ww}_graded.csv", required=False))
        fr = read(f"prompt_nfl_{season}_week{ww}_picks.csv", required=False)
        if fr is not None:  # kickoff times from the engine's file (same games)
            fr = fr.assign(kickoff_utc=fr.game_id.map(eng.set_index("game_id")["kickoff_utc"]))
            add("NFL", "framework", int(ww), fr, read(f"prompt_nfl_{season}_week{ww}_graded.csv", required=False))
    for f in sorted(glob.glob(path(f"cfb_{season}-*_picks.csv"))):
        d = re.search(r"cfb_(\d{4}-\d\d-\d\d)_picks", f).group(1)
        ts = pd.Timestamp(d)
        sat = ts + pd.Timedelta(days=(5 - ts.weekday()) % 7)  # the Saturday that week's slate leads up to
        eng = read(os.path.basename(f))
        add("College", "engine", sat, eng, read(f"cfb_{d}_graded.csv", required=False))
        fr = read(f"prompt_cfb_{d}_picks.csv", required=False)
        if fr is not None:
            fr = fr.assign(kickoff_utc=fr.game_id.map(eng.set_index("game_id")["kickoff_utc"]))
            add("College", "framework", sat, fr, read(f"prompt_cfb_{d}_graded.csv", required=False))
    old = read(f"cfb_{season}-10-10.csv", required=False) if season == 2026 else None
    if old is not None:  # the first logged college slate (engine only, older file format without game ids)
        for i, r in enumerate(old.itertuples()):
            rows.append({"sport": "College", "model": "engine", "key": pd.Timestamp("2026-10-10"),
                         "game_id": f"2026-10-10-{i}", "kickoff_utc": None, "status": r.status,
                         "pick": r.pick if r.status == "PICK" else "", "prob": float(r.win_prob) if r.status == "PICK" else None,
                         "result": r.result if r.status == "PICK" and r.result in ("W", "L", "T") else ""})
    return pd.DataFrame(rows)


def rec_pct(results):
    r = pd.Series(list(results)).fillna("")
    w, l = int((r == "W").sum()), int((r == "L").sum())
    if not (w or l or (r == "T").any()):
        return "-"
    return f"{rec(r)} ({w / (w + l):.0%})" if w + l else rec(r)


def season_page(story, season, now):
    S = season_picks(season, now)
    if not len(S):
        return
    picks = S[S.status == "PICK"]
    graded = picks[picks.result != ""]
    stamp = pd.Timestamp(now).tz_convert(PHX)

    def g(sport, model):
        return graded[(graded.sport == sport) & (graded.model == model)]

    items = []
    for sport, model, label in (("NFL", "engine", "NFL engine (official)"), ("NFL", "framework", "NFL framework"),
                                ("College", "engine", "College engine (official)"),
                                ("College", "framework", "College framework")):
        x = g(sport, model)
        dec = x[x.result != "T"]
        pct = f"{(dec.result == 'W').mean():.1%}" if len(dec) else "-"
        items.append((rec(x.result), f"{label}<br/>{pct} right; expected {x.prob.sum():.1f} wins"))

    # by week / slate
    head = ["Slate (Phoenix dates)", "Engine (official)", "Framework", "Splits won: engine / framework",
            "Engine 70%+", "No picks", "Not final"]
    rows, bg = [[P(h, S_HEAD) for h in head]], []
    for sport in ("NFL", "College"):
        sub = S[S.sport == sport]
        for key in sorted(sub.key.unique()):
            s = sub[sub.key == key]
            e, f = s[s.model == "engine"], s[s.model == "framework"]
            ep, fp = e[e.status == "PICK"], f[f.status == "PICK"]
            both = ep.merge(fp[["game_id", "pick", "result"]], on="game_id", suffixes=("", "_f"))
            spl = both[both.pick != both.pick_f]
            ks = pd.to_datetime(e.kickoff_utc.dropna(), utc=True).dt.tz_convert(PHX).dt.normalize()
            span = (f"{us_date(ks.min())} to {us_date(ks.max())}" if len(ks) and ks.min() != ks.max()
                    else us_date(ks.min()) if len(ks) else us_date(key))
            name = f"NFL Week {key}" if sport == "NFL" else "College"
            if sport == "College" and not len(f):
                span += " (engine only)"
            pend = len(set(ep[ep.result == ""].game_id) | set(fp[fp.result == ""].game_id))
            rows.append([P(f"<b>{name}</b> {span}", S_TCELL), P(rec_pct(ep.result), S_TCELL),
                         P(rec_pct(fp.result) if len(f) else "not run", S_TCELL),
                         P(f"{(spl.result == 'W').sum()} / {(spl.result_f == 'W').sum()} of {len(spl)}" if len(spl) else "-", S_TCELL),
                         P(rec_pct(ep[ep.prob >= 0.7].result), S_TCELL),
                         P(str(int((e.status != "PICK").sum())), S_TCELL), P(str(pend) if pend else "", S_TCELL)])
            bg.append((len(rows) - 1, None, False))
        e, f = sub[(sub.model == "engine") & (sub.status == "PICK")], sub[(sub.model == "framework") & (sub.status == "PICK")]
        both = e.merge(f[["game_id", "pick", "result"]], on="game_id", suffixes=("", "_f"))
        spl = both[both.pick != both.pick_f]
        pend = len(set(e[e.result == ""].game_id) | set(f[f.result == ""].game_id))
        rows.append([P(f"<b>{sport} season</b>", S_TCELLB), P(f"<b>{rec_pct(e.result)}</b>", S_TCELL),
                     P(f"<b>{rec_pct(f.result)}</b>", S_TCELL),
                     P(f"<b>{(spl.result == 'W').sum()} / {(spl.result_f == 'W').sum()} of {len(spl)}</b>", S_TCELL),
                     P(f"<b>{rec_pct(e[e.prob >= 0.7].result)}</b>", S_TCELL),
                     P(f"<b>{int((sub[sub.model == 'engine'].status != 'PICK').sum())}</b>", S_TCELL),
                     P(f"<b>{pend}</b>" if pend else "", S_TCELL)])
        bg.append((len(rows) - 1, AGREE, False))
    t_week = table(rows, (2.45, 1.35, 1.35, 1.75, 1.25, 0.8, 0.8), bg)
    t_week.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))

    # by win-chance tier, next to the multi-season backtests
    cols = [("NFL", "engine"), ("NFL", "framework"), ("College", "engine"), ("College", "framework")]
    head = [P("Win chance of the pick", S_HEAD)]
    for sport, model in cols:
        head += [P(f"{sport} {model}: 2026", S_HEAD), P("backtest", S_HEAD)]
    trows = [head]
    for tier in ("70%+", "60-70%", "Under 60%", "All"):
        line = [P(f"<b>{tier}</b>" if tier != "All" else "<b>All picks</b>", S_TCELL)]
        for sport, model in cols:
            x = g(sport, model)
            x = x if tier == "All" else x[x.prob.map(tier_of) == tier]
            line += [P(rec_pct(x.result), S_TCELL), P(TIER_BACKTEST[(sport, model)][tier], S_SMALL)]
        trows.append(line)
    t_tier = Table(trows, colWidths=[1.0 * inch] + [1.15 * inch, 1.1 * inch] * 4, repeatRows=1)
    t_tier.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                                ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE), ("BACKGROUND", (0, 4), (-1, 4), AGREE)]))

    # side tallies
    cells = []
    try:
        import nopick_leans  # results/nopick_leans.py (off the record, never in a record)
        L = nopick_leans.rows()
        if len(L):
            parts = [f"{sp} engine {rec(L[(L.sport == sp) & (L.model == 'engine')].result)}, "
                     f"framework {rec(L[(L.sport == sp) & (L.model == 'framework')].result)}" for sp in ("College", "NFL")]
            cells.append(P("<b>Off the record (no-pick games, never in a record).</b> The team each model would "
                           "have taken went " + "; ".join(parts) + ".", S_BOX))
    except Exception:  # noqa: BLE001  (the tally is a side note; the page doesn't depend on it)
        pass
    card = read("nfl_scorecard.csv", required=False)
    if card is not None:
        c = card[(card.season == season) & (card.status == "PICK") & card.market_p_home.notna()]
        if len(c):
            y = c.home_win.astype(float)
            fav = ["T" if yy == 0.5 else "W" if (pm > .5) == (yy == 1) else "L" for pm, yy in zip(c.market_p_home, y)]
            cells.append(P(f"<b>NFL against the closing line (grading only, never an input).</b> Same {len(c)} games: "
                           f"engine {rec(c.result)}, closing-line favorite {rec(fav)}. Brier (lower is better): engine "
                           f"{((c.p_home - y) ** 2).mean():.3f}, closing line {((c.market_p_home - y) ** 2).mean():.3f}.", S_BOX))
    import glob
    lc = [pd.read_csv(x) for x in sorted(glob.glob(path(f"live_calls_{season}-*.csv")))]
    if lc:
        lc = pd.concat(lc, ignore_index=True)
        r = lc["result"].fillna("")
        cells.append(P(f"<b>Live winner calls (separate tool, not part of the picks).</b> Called at ESPN's 98% "
                       f"live win chance: {rec(r[r.isin(['W', 'L', 'T'])])}"
                       + (f", {int((~r.isin(['W', 'L', 'T'])).sum())} not final" if (~r.isin(['W', 'L', 'T'])).any() else "")
                       + ".", S_BOX))

    top = Table([[P(v, style("sbg", 17, True, align=1, lead=19)) for v, _ in items], [P(l, S_BIGL) for _, l in items]],
                colWidths=[10.0 / len(items) * inch] * len(items))
    top.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LINEAFTER", (0, 0), (-2, -1), 0.6, RULE),
                             ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                             ("BOTTOMPADDING", (0, 1), (-1, 1), 5)]))
    story += [P(f"Season so far ({season})", S_TITLE), Spacer(1, 3),
              P(f"Every logged pick graded against ESPN final scores, through {us_date(stamp)} "
                f"{stamp.strftime('%-I:%M %p')} Phoenix. The engine's picks are the official record; the framework "
                f"is the comparison. A tie counts as a tie; percentages leave ties out. Games not started yet are on "
                f"the picks pages.", S_SUB),
              Spacer(1, 6), top, Spacer(1, 7), P("By week", S_H), Spacer(1, 3), t_week, Spacer(1, 7),
              P("By the pick's win chance, next to the multi-season backtests", S_H), Spacer(1, 3), t_tier,
              Spacer(1, 3),
              P("Backtests: college 2021-2025 (engine and framework), NFL engine 2016-2025, NFL framework 2022-2025; "
                "every game predicted only from what was known before it (results/audit_2026-10-24). October (weeks "
                "4-8) is the hardest stretch of the year for every model. Expected wins: the sum of the win chances of "
                "the graded picks.", S_NOTE)]
    if cells:
        story += [Spacer(1, 6), boxes(cells, 10.0 / len(cells))]
    story.append(PageBreak())


def nfl_picks(story, season, week):
    ww = f"{week:02d}"
    eng = apply_notes(read(f"nfl_cfbmethod_{season}_week{ww}_picks.csv"), "engine")
    frm = apply_notes(read(f"prompt_nfl_{season}_week{ww}_picks.csv"), "framework")
    picks_section(story, f"NFL Week {week} picks ({date_span(eng)})", "Engine (official) and framework side by side. All times Phoenix. "
                  "No betting lines, records or narrative go into either model.",
                  eng, frm, "neutral site",
                  "QBs: each team's expected starter; a game is a no-pick when the starting QB is out or unconfirmed, "
                  "and any pick whose starting QB changes before kickoff is dropped." + (notes_sentence(eng) if TEAM_NOTES_ON else ""),
                  [P("<b>How far to trust them (NFL, same 887 games, 2022-2025).</b> Engine 64.0% of winners, "
                     "framework 62.6%, closing-line favorite 68.7%. One week is a small sample.", S_BOX)])


# -------------------------------------------------------------- team notes

def expiry_words(notes):
    """'3 weeks' for 21 days, otherwise 'N days'."""
    d = float(notes["expire_after_days"])
    return f"{int(d // 7)} weeks" if d % 7 == 0 and d >= 14 else f"{d:g} days"


def notes_page(story):
    """Your team notes and how they are doing, from team_notes_graded.csv."""
    rows_in = team_notes.scorecard(DIR, NOTES)
    if not rows_in:
        return
    head = ["Team", "Your note", "Compared with", "Graded games", "Team record", "Model alone expected",
            "Points per game vs model alone", "Win chances, Brier (with / without note)", "Picks the note changed",
            "So far"]
    rows, empty = [[P(h, S_HEAD) for h in head]], []
    for i, r in enumerate(rows_in, start=1):
        s = r["s"]
        detail = "; ".join(x for x in (f"since {team_notes.day(r['since'])}" if r["since"] else "",
                                         team_notes.plural(r["reads"], "read") if r["reads"] else "", r["state"]) if x)
        note_cell = ([P(escape(r["label"]), S_TCELL), P(escape(detail), S_SMALL)] if detail
                     else P(escape(r["label"]), S_TCELL))
        cells = [P(escape(r["team"]) if r["model"] == "engine" else "", S_TCELLB),
                 note_cell if r["model"] == "engine" else "",
                 P("Engine" if r["model"] == "engine" else "Framework", S_TCELL)]
        if not s:
            cells += [P("0", S_TCELL), P("No graded games yet", S_TCELL), "", "", "", "", ""]
            rows.append(cells)
            empty.append(i)
            continue
        better = s["brier_noted"] < s["brier_alone"]
        flip = f"{s['flips']}" + (f": {s['flips_noted']} with the note, {s['flips_alone']} alone" if s["flips"] else "")
        cells += [P(str(s["games"]), S_TCELL), P(s["record"], S_TCELL),
                  P(f"{s['exp_wins']:.1f} wins ({s['wins_vs']:+.1f}; luck &#177;{s['luck_wins']:.1f})", S_TCELL),
                  P(f"{s['pts_vs']:+.1f} (luck &#177;{s['luck_pts']:.1f})", S_TCELL),
                  P(f"{s['brier_noted']:.3f} / {s['brier_alone']:.3f}: " + ("more accurate" if better else "less accurate"
                    if s["brier_noted"] > s["brier_alone"] else "the same"), S_TCELL),
                  P(flip, S_TCELL), P(escape(s["status"]), S_TCELL)]
        rows.append(cells)
    t = Table(rows, colWidths=[w * inch for w in (0.85, 1.3, 0.85, 0.6, 0.65, 1.3, 1.15, 1.3, 1.0, 1.0)], repeatRows=1)
    ts = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    ts += [("SPAN", (4, i), (-1, i)) for i in empty]
    for i, r in enumerate(rows_in, start=1):
        if r["model"] == "framework":
            ts.append(("LINEBELOW", (0, i), (-1, i), 0.4, RULE))
    t.setStyle(TableStyle(ts))
    now = team_notes.current(NOTES)
    live = "; ".join(team_notes.note_text(NOTES, e) for e in now) or "none"
    story += [P("Your team notes: how they're doing", S_TITLE), Spacer(1, 3),
              P("Notes you set by hand, case by case. A note moves the team's predicted margin by its points in both "
                "models, for games kicking off after you set it" +
                (f", and runs out {expiry_words(NOTES)} after your last read on that team unless you renew it"
                 if NOTES.get("expire_after_days") else "") +
                f". In force now: {escape(live)}{' points' if now else ''}.", S_SUB),
              Spacer(1, 10), t, Spacer(1, 6),
              P("Every graded pick that involved a noted team. <b>Model alone expected</b>: the wins the model predicted "
                "without your note. <b>Points per game vs model alone</b>: how much better (+) or worse (-) the team "
                "did than the model's predicted margin; an unreliable note is right when this is negative and a "
                "max-effort note when it's positive, ideally by about the note's points. <b>Brier</b>: how close the win chances were to what happened, lower is "
                "better. <b>Luck</b>: how far results land from the model's expectation by chance alone 95% of the "
                "time over that many games; until a number gets outside it, one good or bad stretch can't prove a "
                "note either way.", S_NOTE)]
    story.append(PageBreak())


def cfb_picks(story, dates):
    eng = pd.concat([read(f"cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    frm = pd.concat([read(f"prompt_cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    cells = []
    same = read("cfb_engine_vs_framework_same_games.csv", required=False)
    if same is not None:
        parts = []
        for s in sorted(same.season.unique()):
            d = same[same.season == s]
            e = ((d.p_engine >= .5) == (d.home_win == 1)).mean()
            f = ((d.p_framework >= .5) == (d.home_win == 1)).mean()
            parts.append(f"{s}: {len(d)} games, engine {e:.1%}, framework {f:.1%}")
        cells.append(P("<b>How far to trust them (college, same games).</b> " + "; ".join(parts) + ".", S_BOX))
    label = us_date(dates[0]) if len(dates) == 1 else f"{us_date(dates[0])} to {us_date(dates[-1])}"
    picks_section(story, f"College football picks ({label})", "Engine (official) and framework side by side. "
                  "All times Phoenix.", eng, frm, "neutral site",
                  "No pick: the starting QB is out or unconfirmed, or a team lacks enough play-by-play this season.",
                  cells)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--nfl-graded", help="SEASON:WEEK")
    ap.add_argument("--cfb-graded", action="append", default=[], help="YYYY-MM-DD (repeat)")
    ap.add_argument("--nfl-picks", help="SEASON:WEEK")
    ap.add_argument("--cfb-picks", action="append", default=[], help="YYYY-MM-DD (repeat)")
    ap.add_argument("--title", default="Picks and results")
    ap.add_argument("--dir", default=HERE, help="folder with the logged files (default: results/)")
    ap.add_argument("--no-glance", action="store_true", help="leave out the opening 'What to act on' page")
    ap.add_argument("--season-summary", type=int, metavar="SEASON",
                    help="add the 'Season so far' page (every graded pick this season, both sports and models)")
    a = ap.parse_args()
    global DIR, NOTES
    DIR = a.dir
    story = []
    nfl = bool(a.nfl_graded or a.nfl_picks)
    if nfl and TEAM_NOTES_ON:
        NOTES = team_notes.load()
    if not a.no_glance and (a.nfl_picks or a.cfb_picks):
        glance = []
        if a.nfl_picks:
            s, w = map(int, a.nfl_picks.split(":"))
            e = apply_notes(read(f"nfl_cfbmethod_{s}_week{w:02d}_picks.csv"), "engine")
            glance.append((f"NFL Week {w} ({date_span(e)})", "nfl", e,
                           apply_notes(read(f"prompt_nfl_{s}_week{w:02d}_picks.csv"), "framework")))
        if a.cfb_picks:
            ds = sorted(a.cfb_picks)
            e = pd.concat([read(f"cfb_{d}_picks.csv") for d in ds], ignore_index=True)
            f = pd.concat([read(f"prompt_cfb_{d}_picks.csv") for d in ds], ignore_index=True)
            glance.append((f"College football ({date_span(e)})", "cfb", e, f))
        glance_page(story, glance, pd.Timestamp.now(tz="UTC"))
    if a.season_summary:
        season_page(story, a.season_summary, pd.Timestamp.now(tz="UTC"))
    if a.nfl_graded:
        s, w = map(int, a.nfl_graded.split(":"))
        nfl_graded(story, s, w)
    if a.cfb_graded:
        cfb_graded(story, sorted(a.cfb_graded))
    if a.nfl_picks:
        s, w = map(int, a.nfl_picks.split(":"))
        nfl_picks(story, s, w)
    if a.cfb_picks:
        cfb_picks(story, sorted(a.cfb_picks))
    if not story:
        raise SystemExit("nothing to put in the report: pass at least one section")
    if nfl and TEAM_NOTES_ON and NOTES["events"]:
        notes_page(story)
    story = story[:-1]  # no blank page at the end
    story += [Spacer(1, 8), P("Engine: the locked college method (NFL: with the approved NFL settings), rating every "
                              "offense and defense on EPA and success rate, adjusted for opponents. Framework: your Prompt "
                              "Football criteria (trenches 25%, net efficiency 25%, passing 20%, situational 15%, high "
                              "leverage 15%) scored from this season's play-by-play only." +
                              (" Team notes (NFL): your own calls, set by hand and added on top of both models' numbers."
                               if nfl and TEAM_NOTES_ON and NOTES["events"] else "") +
                              " Files: results/ in the sports-engines repo." +
                              f" Report made {us_date(pd.Timestamp.now(tz=PHX))} "
                              f"{pd.Timestamp.now(tz=PHX).strftime('%-I:%M %p')} Phoenix time.", S_NOTE)]
    out = a.out if os.path.isabs(a.out) else os.path.abspath(a.out)
    doc = SimpleDocTemplate(out, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch, title=a.title, author="sports-engines")
    doc.build(story)
    print("Saved", out)


if __name__ == "__main__":
    main()
