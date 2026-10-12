"""Build the picks/results PDF for any check-in: graded NFL weeks and college
dates, and new NFL and college picks, engine and framework side by side.

  python3 results/make_report.py --out results/report_2026-10-13.pdf \
      --nfl-graded 2026:5 --nfl-picks 2026:6 --cfb-picks 2026-10-13 --cfb-picks 2026-10-14
  python3 results/make_report.py --out results/report_2026-10-17.pdf \
      --cfb-graded 2026-10-13 --cfb-graded 2026-10-16 --cfb-picks 2026-10-17

Each section gets its own page, in this order: NFL graded, college graded, NFL
picks, college picks. Every number is read from the logged files in results/:
  NFL graded   nfl_cfbmethod_<S>_week<WW>_picks.csv and _graded.csv (nfl_cfbmethod/grade.py),
               prompt_nfl_<S>_week<WW>_picks.csv and _graded.csv (results/grade_picks.py)
  college      cfb_<date>_picks.csv / _graded.csv, prompt_cfb_<date>_picks.csv / _graded.csv
  NFL picks    nfl_cfbmethod_<S>_week<WW>_picks.csv, prompt_nfl_<S>_week<WW>_picks.csv
Kickoff times are Phoenix, as the models write them.
"""
import argparse
import os
from xml.sax.saxutils import escape

import pandas as pd
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


def P(text, st):
    return Paragraph(text, st)


DIR = HERE  # --dir changes it (for tests)


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


def game_label(r, neutral_word):
    return f"{r.away_name} at {r.home_name}" + (f" ({neutral_word})" if bool(r.neutral) else "")


def pick_text(status, pick, prob):
    if status != "PICK":
        return "No pick"
    return f"{escape(str(pick))} {float(prob):.0%}"


# ------------------------------------------------------------------ graded

def graded_section(story, title, sub, eng, eng_g, frm, frm_g, neutral_word, market=None):
    """eng/frm: picks; eng_g/frm_g: graded files (result per game_id); frm may be None (not run)."""
    g_e = eng_g.set_index("game_id")
    m = eng.copy()
    m["e_result"] = m.game_id.map(g_e["result"])
    m["away_score"], m["home_score"] = m.game_id.map(g_e["away_score"]), m.game_id.map(g_e["home_score"])
    if frm is not None:
        f = frm.set_index("game_id")
        m["f_status"], m["f_pick"], m["f_prob"] = m.game_id.map(f["status"]), m.game_id.map(f["pick"]), m.game_id.map(f["pick_prob"])
        m["f_result"] = m.game_id.map(frm_g.set_index("game_id")["result"]) if frm_g is not None else ""
    else:
        m["f_status"], m["f_pick"], m["f_prob"], m["f_result"] = "NOT RUN", "", None, ""
    m = m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)
    both = m[(m.status == "PICK") & (m.f_status == "PICK")]
    split = both[both.pick != both.f_pick]
    items = [(rec(m[m.status == "PICK"].e_result), "Engine (official picks)")]
    if frm is not None:
        items += [(rec(m[m.f_status == "PICK"].f_result), "Framework (your Prompt Football)"),
                  (rec(split.f_result), f"Framework on the {len(split)} games where they split")]
    pend = m[((m.status == "PICK") | (m.f_status == "PICK")) & m.home_score.isna()]
    story += [P(title, S_TITLE), Spacer(1, 3), P(sub + (f" {len(pend)} game(s) not final yet." if len(pend) else ""), S_SUB),
              Spacer(1, 10), big_numbers(items), Spacer(1, 10)]
    rows, bg = [[P(h, S_HEAD) for h in ["Kickoff", "Game", "Final", "Engine pick", "", "Framework pick", ""]]], []
    for i, r in enumerate(m.itertuples(), start=1):
        final = "" if pd.isna(r.home_score) else f"{r.away_name} {int(r.away_score)}, {r.home_name} {int(r.home_score)}"
        if r.status != "PICK" and r.f_status != "PICK":
            why = r.reason if isinstance(r.reason, str) and r.reason else "no pick"
            rows.append([P(r.kickoff, S_CELL), P(escape(game_label(r, neutral_word)), S_CELL), P(escape(final), S_CELL),
                         P(f"No pick (both): {escape(why)}", S_CELL), "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        rows.append([P(r.kickoff, S_CELL), P(escape(game_label(r, neutral_word)), S_CELL), P(escape(final) or "Not final", S_CELL),
                     P(pick_text(r.status, r.pick, r.pick_prob), S_CELL),
                     res_cell(r.e_result) if r.status == "PICK" else "",
                     P(pick_text(r.f_status, r.f_pick, r.f_prob) if r.f_status != "NOT RUN" else "Not run", S_CELL),
                     res_cell(r.f_result) if r.f_status == "PICK" else ""])
        bg.append((i, SPLIT if (r.status == r.f_status == "PICK" and r.pick != r.f_pick) else None, False))
    story += [table(rows, (1.0, 2.2, 2.3, 1.45, 0.75, 1.45, 0.75), bg, span_from=3), Spacer(1, 5),
              P("Amber rows: the two models picked different teams. A tie is graded as a tie. Percentages are each "
                "model's win chance for its pick.", S_NOTE)]
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
    eng = read(f"nfl_cfbmethod_{season}_week{ww}_picks.csv")
    eng_g = read(f"nfl_cfbmethod_{season}_week{ww}_graded.csv")
    frm = read(f"prompt_nfl_{season}_week{ww}_picks.csv", required=False)
    frm_g = read(f"prompt_nfl_{season}_week{ww}_graded.csv", required=frm is not None)
    graded_section(story, f"NFL Week {week} graded", "Engine graded with nfl_cfbmethod/grade.py, framework with "
                   "results/grade_picks.py. All times Phoenix. No betting lines go into either model.",
                   eng, eng_g, frm, frm_g, "neutral site", market=eng_g)


def cfb_graded(story, dates):
    eng = pd.concat([read(f"cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    eng_g = pd.concat([read(f"cfb_{d}_graded.csv") for d in dates], ignore_index=True)
    fr = [read(f"prompt_cfb_{d}_picks.csv", required=False) for d in dates]
    frm = pd.concat([x for x in fr if x is not None], ignore_index=True) if any(x is not None for x in fr) else None
    fg = [read(f"prompt_cfb_{d}_graded.csv", required=False) for d in dates]
    frm_g = pd.concat([x for x in fg if x is not None], ignore_index=True) if any(x is not None for x in fg) else None
    label = dates[0] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"
    graded_section(story, f"College football graded ({label})", "Both models graded with results/grade_picks.py. "
                   "All times Phoenix.", eng, eng_g, frm, frm_g, "neutral site")


# ------------------------------------------------------------------- picks

def picks_section(story, title, sub, eng, frm, neutral_word, note, box_cells):
    m = eng.merge(frm[["game_id", "status", "pick", "pick_prob", "score", "reason"]], on="game_id", how="left",
                  suffixes=("_e", "_f"))
    m["status_f"] = m.status_f.fillna("NOT RUN")
    m = m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)
    rows, bg = [[P(h, S_HEAD) for h in ["Kickoff", "Game", "Engine (official)", "Framework", "Framework score", ""]]], []
    for i, r in enumerate(m.itertuples(), start=1):
        if r.status_e != "PICK" and r.status_f != "PICK":
            why = r.reason_e if isinstance(r.reason_e, str) and r.reason_e else str(r.reason_f)
            rows.append([P(r.kickoff, S_CELL), P(escape(game_label(r, neutral_word)), S_CELL),
                         P(f"No pick (both): {escape(why)}", S_CELL), "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        same = r.status_e == r.status_f == "PICK" and r.pick_e == r.pick_f
        e_strong = r.status_e == "PICK" and r.pick_prob_e >= 0.7
        f_strong = r.status_f == "PICK" and float(r.pick_prob_f) >= 0.7
        rows.append([P(r.kickoff, S_CELL), P(escape(game_label(r, neutral_word)), S_CELL),
                     P(pick_text(r.status_e, r.pick_e, r.pick_prob_e), S_CELLB if e_strong else S_CELL),
                     P(pick_text(r.status_f, r.pick_f, r.pick_prob_f) if r.status_f != "NOT RUN" else "Not run",
                       S_CELLB if f_strong else S_CELL),
                     P(escape(str(r.score)) if isinstance(r.score, str) else "", S_CELL),
                     P("Agree" if same else "<b>Split</b>" if r.status_e == r.status_f == "PICK" else "", S_CELL)])
        bg.append((i, AGREE if same else SPLIT if r.status_e == r.status_f == "PICK" else NOPICK, False))
    made = m[(m.status_e == "PICK") & (m.status_f == "PICK")]
    agree = (made.pick_e == made.pick_f).sum()
    story += [P(title, S_TITLE), Spacer(1, 3), P(sub, S_SUB), Spacer(1, 9),
              table(rows, (1.05, 2.75, 1.75, 1.75, 2.1, 0.6), bg, span_from=2), Spacer(1, 5),
              P(f"They agree on {agree} of {len(made)} picks (green) and split on {len(made) - agree} (amber). "
                f"Bold = 70%+. Grey = no pick. {note}", S_NOTE)]
    if box_cells:
        story += [Spacer(1, 8), boxes(box_cells, 10.0 / len(box_cells))]
    story.append(PageBreak())


def nfl_picks(story, season, week):
    ww = f"{week:02d}"
    eng = read(f"nfl_cfbmethod_{season}_week{ww}_picks.csv")
    frm = read(f"prompt_nfl_{season}_week{ww}_picks.csv")
    picks_section(story, f"NFL Week {week} picks", "Engine (official) and framework side by side. All times Phoenix. "
                  "No betting lines, records or narrative go into either model.", eng, frm, "neutral site",
                  "QBs: each team's expected starter; a game is a no-pick when the starting QB is out or unconfirmed, "
                  "and any pick whose starting QB changes before kickoff is dropped.",
                  [P("<b>How far to trust them (NFL, same 887 games, 2022-2025).</b> Engine 64.0% of winners, "
                     "framework 62.6%, closing-line favorite 68.7%. One week is a small sample.", S_BOX)])


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
    label = dates[0] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"
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
    a = ap.parse_args()
    global DIR
    DIR = a.dir
    story = []
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
    story = story[:-1]  # no blank page at the end
    story += [Spacer(1, 8), P("Engine: the locked college method (NFL: with the approved NFL settings), rating every "
                              "offense and defense on EPA and success rate, adjusted for opponents. Framework: your Prompt "
                              "Football criteria (trenches 25%, net efficiency 25%, passing 20%, situational 15%, high "
                              "leverage 15%) scored from this season's play-by-play only. Files: results/ in the "
                              "sports-engines repo.", S_NOTE)]
    out = a.out if os.path.isabs(a.out) else os.path.abspath(a.out)
    doc = SimpleDocTemplate(out, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch, title=a.title, author="sports-engines")
    doc.build(story)
    print("Saved", out)


if __name__ == "__main__":
    main()
