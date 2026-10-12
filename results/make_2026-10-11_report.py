"""Build the PDF for Sunday night, 2026-10-11: NFL Week 5 graded (engine and
framework) plus the next games: NFL Week 6 and the midweek college games
(Oct 13-16), both models side by side.

Every pick, score and percentage is read from the logged files in results/.
It also writes results/prompt_nfl_2026_week05_graded.csv (the framework's Week 5
grades, ties graded T).

  python3 results/make_2026-10-11_report.py
"""
import os
import sys
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results_and_next_picks_2026-10-11.pdf")
CFB_DATES = ["2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]

INK, MUTED, RULE = colors.HexColor("#1F2937"), colors.HexColor("#6B7280"), colors.HexColor("#D1D5DB")
AGREE, SPLIT, NOPICK = colors.HexColor("#E7F4EA"), colors.HexColor("#FDF1DC"), colors.HexColor("#EEEEEE")
WIN, LOSS, TIE = colors.HexColor("#15803D"), colors.HexColor("#B91C1C"), colors.HexColor("#6B7280")


def style(name, size, bold=False, color=INK, lead=None, align=0):
    return ParagraphStyle(name, fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                          leading=lead or size * 1.25, textColor=color, alignment=align)


S_TITLE, S_SUB, S_H = style("t", 18, True), style("s", 9.5, color=MUTED), style("h", 12, True)
S_CELL, S_CELLB = style("c", 9), style("cb", 9, True)
S_HEAD = style("hd", 8.5, True, colors.white)
S_NOTE, S_BOX = style("n", 7.9, color=MUTED, lead=10), style("bx", 8.8, lead=11.4)
S_BIG, S_BIGL = style("bg", 20, True, align=1, lead=23), style("bl", 8.5, color=MUTED, align=1)


def P(text, st):
    return Paragraph(text, st)


def res_cell(r):
    col = {"W": WIN, "L": LOSS, "T": TIE}.get(r)
    word = {"W": "Win", "L": "Loss", "T": "Tie"}.get(r, "")
    return P(f'<font color="{col.hexval() if col else "#6B7280"}"><b>{word or "Pending"}</b></font>', S_CELL)


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
          ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    st += [("BOX", (i, 0), (i, 0), 0.6, RULE) for i in range(len(cells))]
    t.setStyle(TableStyle(st))
    return t


def week5():
    picks = pd.read_csv(os.path.join(HERE, "nfl_cfbmethod_2026_week05_picks.csv"), dtype={"game_id": str})
    graded = pd.read_csv(os.path.join(HERE, "nfl_cfbmethod_2026_week05_graded.csv"), dtype={"game_id": str})
    frm = pd.read_csv(os.path.join(HERE, "prompt_nfl_2026_week05_picks.csv"), dtype={"game_id": str})
    m = picks.merge(frm[["game_id", "status", "pick", "pick_prob"]], on="game_id", suffixes=("_e", "_f"))
    m = m.merge(graded[["game_id", "away_score", "home_score", "result"]], on="game_id", how="left")
    assert len(m) == len(picks) == len(frm) == 14
    assert (m.status_e == m.status_f).all(), "engine and framework no-picks differ"

    def grade(r, pick):
        if pd.isna(r.home_score):
            return ""
        if r.home_score == r.away_score:
            return "T"
        winner = r.home_name if r.home_score > r.away_score else r.away_name
        return "W" if pick == winner else "L"

    m["fw_result"] = [grade(r, r.pick_f) if r.status_f == "PICK" else "" for r in m.itertuples()]
    m["eng_check"] = [grade(r, r.pick_e) if r.status_e == "PICK" else "" for r in m.itertuples()]
    done = m[m.result.notna() & (m.status_e == "PICK")]
    assert (done.result == done.eng_check).all(), "engine grades in the graded file don't match the scores"
    fw = m[["game_id", "away_name", "home_name", "away_score", "home_score", "status_f", "pick_f", "pick_prob_f", "fw_result"]]
    fw.columns = ["game_id", "away", "home", "away_score", "home_score", "status", "pick", "pick_prob", "result"]
    fw = fw.astype({"away_score": "Int64", "home_score": "Int64"})
    fw.to_csv(os.path.join(HERE, "prompt_nfl_2026_week05_graded.csv"), index=False)
    return m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)


def rec(series):
    w, l, t = (series == "W").sum(), (series == "L").sum(), (series == "T").sum()
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def page_results(story):
    m = week5()
    played = m[m.status_e == "PICK"]
    eng_rec, fw_rec = rec(played.result.fillna("")), rec(played.fw_result)
    split = played[(played.pick_e != played.pick_f) & (played.fw_result != "")]
    pend = m[(m.status_e == "PICK") & m.home_score.isna()]
    parlay_legs = ["Jaguars", "Vikings", "Bengals"]
    legs = played[played.pick_f.isin(parlay_legs)]
    parlay_hit = len(legs) == 3 and (legs.fw_result == "W").all()

    story += [P("NFL Week 5 graded, and the next games", S_TITLE), Spacer(1, 3),
              P("Graded Sunday night, October 11, 2026. Monday night (Bills at Rams) is still to play. All times "
                "Phoenix. No betting lines, records or narrative go into either model.", S_SUB), Spacer(1, 10)]
    big = [[P(eng_rec, S_BIG), P(fw_rec, S_BIG), P(rec(split.fw_result), S_BIG), P("Hit" if parlay_hit else "Missed", S_BIG)],
           [P("Engine (official picks)", S_BIGL), P("Framework (your Prompt Football)", S_BIGL),
            P(f"Framework on the {len(split)} games where they split", S_BIGL), P("$25 parlay: Jaguars + Vikings + Bengals", S_BIGL)]]
    bt = Table(big, colWidths=[2.5 * inch] * 4)
    bt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LINEAFTER", (0, 0), (-2, -1), 0.6, RULE),
                            ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 1), (-1, 1), 8)]))
    story += [bt, Spacer(1, 10)]

    head = ["Kickoff", "Game", "Final", "Engine pick", "", "Framework pick", ""]
    rows, bg = [[P(h, S_HEAD) for h in head]], []
    for i, r in enumerate(m.itertuples(), start=1):
        game = f"{r.away_name} at {r.home_name}" + (" (London)" if r.neutral else "")
        final = "" if pd.isna(r.home_score) else f"{r.away_name} {int(r.away_score)}, {r.home_name} {int(r.home_score)}"
        if r.status_e != "PICK":
            rows.append([P(r.kickoff, S_CELL), P(escape(game), S_CELL), P(escape(final), S_CELL),
                         P(f"No pick (both): {escape(r.reason)}", S_CELL), "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        rows.append([P(r.kickoff, S_CELL), P(escape(game), S_CELL), P(escape(final) or "Monday", S_CELL),
                     P(f"{r.pick_e} {r.pick_prob_e:.0%}", S_CELL), res_cell(r.result if isinstance(r.result, str) else ""),
                     P(f"{r.pick_f} {r.pick_prob_f:.0%}", S_CELL), res_cell(r.fw_result)])
        bg.append((i, None if r.pick_e == r.pick_f else SPLIT, False))
    story += [table(rows, (1.0, 2.0, 2.3, 1.5, 0.8, 1.5, 0.8), bg, span_from=3), Spacer(1, 5),
              P("Amber rows: the two models picked different teams. A tie counts as a tie for both "
                "(grade.py now grades ties as T). Percentages are each model's win chance for its pick.", S_NOTE),
              Spacer(1, 8)]
    g = pd.read_csv(os.path.join(HERE, "nfl_cfbmethod_2026_week05_graded.csv"))
    g = g[(g.status == "PICK") & g.market_p_home.notna()]
    y = g.home_win.astype(float)
    eb, mb = ((g.p_home - y) ** 2).mean(), ((g.market_p_home - y) ** 2).mean()
    fav = [("T" if yy == 0.5 else "W" if (pm > .5) == (yy == 1) else "L") for pm, yy in zip(g.market_p_home, y)]
    dog = g[(g.p_home > .5) != (g.market_p_home > .5)]
    dog_res = rec(dog.result)
    story += [boxes([
        P(f"<b>Against the betting market (grading only, never an input).</b> The closing-line favorite went "
          f"{rec(pd.Series(fav))} on the engine's {len(g)} graded games. Accuracy of the win chances (Brier, lower "
          f"is better): engine {eb:.3f}, closing line {mb:.3f}. The engine picked against the market favorite "
          f"{len(dog)} times and went {dog_res}.", S_BOX),
        P(f"<b>Still to play.</b> Bills at Rams, Monday 5:15 PM: both models picked the Rams "
          f"(engine {pend.pick_prob_e.iloc[0]:.0%}, framework {pend.pick_prob_f.iloc[0]:.0%}). " if len(pend) == 1
          and pend.pick_e.iloc[0] == pend.pick_f.iloc[0] == "Rams" else "<b>Still to play.</b> See the table. ", S_BOX)
        if len(pend) else P("<b>All games final.</b>", S_BOX)], 5.0), PageBreak()]


def side_by_side(story, eng, frm, title, sub, note, kick_col="kickoff", neutral_label="(neutral site)"):
    m = eng.merge(frm[["game_id", "status", "pick", "pick_prob", "score", "reason"]], on="game_id", suffixes=("_e", "_f"))
    assert len(m) == len(eng) == len(frm), f"{title}: games don't match between the two models"
    assert (m.status_e == m.status_f).all(), f"{title}: no-picks differ between the two models"
    m = m.sort_values(["kickoff_utc", "away_name"]).reset_index(drop=True)
    head = ["Kickoff", "Game", "Engine (official)", "Framework", "Framework score", ""]
    rows, bg = [[P(h, S_HEAD) for h in head]], []
    for i, r in enumerate(m.itertuples(), start=1):
        game = f"{r.away_name} at {r.home_name}" + (f" {neutral_label}" if r.neutral else "")
        if r.status_e != "PICK":
            rows.append([P(getattr(r, kick_col), S_CELL), P(escape(game), S_CELL),
                         P(f"No pick (both): {escape(str(r.reason_e))}", S_CELL), "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        same = r.pick_e == r.pick_f
        ep, fp = r.pick_prob_e * 100, r.pick_prob_f * 100
        rows.append([P(getattr(r, kick_col), S_CELL), P(escape(game), S_CELL),
                     P(f"{escape(r.pick_e)} {ep:.0f}%", S_CELLB if ep >= 70 else S_CELL),
                     P(f"{escape(r.pick_f)} {fp:.0f}%", S_CELLB if fp >= 70 else S_CELL),
                     P(escape(str(r.score)), S_CELL), P("Agree" if same else "<b>Split</b>", S_CELL)])
        bg.append((i, AGREE if same else SPLIT, False))
    made = m[m.status_e == "PICK"]
    agree = (made.pick_e == made.pick_f).sum()
    story += [P(title, S_H), Spacer(1, 2), P(sub, S_SUB), Spacer(1, 7),
              table(rows, (1.05, 2.75, 1.75, 1.75, 2.1, 0.6), bg, span_from=2), Spacer(1, 5),
              P(f"They agree on {agree} of {len(made)} picks (green) and split on {len(made) - agree} (amber). "
                f"Bold = 70%+. {note}", S_NOTE)]


def page_nfl6(story):
    eng = pd.read_csv(os.path.join(HERE, "nfl_cfbmethod_2026_week06_picks.csv"), dtype={"game_id": str})
    frm = pd.read_csv(os.path.join(HERE, "prompt_nfl_2026_week06_picks.csv"), dtype={"game_id": str})
    side_by_side(story, eng, frm, "NFL Week 6: Thursday Oct 15 to Monday Oct 19",
                 "Logged Sunday night, before the week's injury reports. The engine's picks are the official ones.",
                 "QBs assumed: each team's last starter (Giants: Jameis Winston, Jaxson Dart is out for the season; "
                 "Commanders: Jayden Daniels). The QBs get re-checked before each kickoff, and any pick whose starting "
                 "QB changes is dropped.", neutral_label="(London)")
    story += [Spacer(1, 8), boxes([
        P("<b>How far to trust them (NFL, same 887 games, 2022-2025).</b> Engine 64.0% of winners, framework 62.6%, "
          "closing-line favorite 68.7%. Week 5 went the framework's way (above), but one week is a small sample.", S_BOX),
        P("<b>Missing data, so no pick.</b> Bears at Falcons: Caleb Williams (hamstring) has no Week 6 status yet. "
          "Ravens at Browns: Lamar Jackson missed Week 5 and has no Week 6 status. Steelers at Buccaneers: Baker "
          "Mayfield (thumb) has been out since Sep 28 and his return isn't confirmed.", S_BOX)], 5.0), PageBreak()]


def page_cfb(story):
    eng = pd.concat([pd.read_csv(os.path.join(HERE, f"cfb_{d}_picks.csv"), dtype={"game_id": str}) for d in CFB_DATES])
    frm = pd.concat([pd.read_csv(os.path.join(HERE, f"prompt_cfb_{d}_picks.csv"), dtype={"game_id": str}) for d in CFB_DATES])
    side_by_side(story, eng, frm, "College football, Tuesday Oct 13 to Friday Oct 16",
                 "Both models, first run of the new college framework. The engine's picks are the official ones.",
                 "No pick (grey): the team changed quarterbacks in its last game and hasn't named a starter yet; it "
                 "gets re-checked before kickoff.")
    same = pd.read_csv(os.path.join(HERE, "cfb_engine_vs_framework_same_games.csv"))
    bt = pd.read_csv(os.path.join(HERE, "prompt_cfb_backtest_2022_2025.csv"))
    bt = bt[bt.result != 0]
    won = (bt.p_home >= .5) == (bt.result > 0)

    def pct(d, col):
        w = (d[col] >= .5) == (d.home_win == 1)
        return f"{w.mean():.1%}", len(d)

    e25, n25 = pct(same[same.season == 2025], "p_engine")
    f25, _ = pct(same[same.season == 2025], "p_framework")
    e26, n26 = pct(same[same.season == 2026], "p_engine")
    f26, _ = pct(same[same.season == 2026], "p_framework")
    story += [Spacer(1, 8), boxes([
        P(f"<b>The college framework, tested.</b> Replaying 2022-2025 week by week, it picked {won.sum()}-{(~won).sum()} "
          f"({won.mean():.1%}). On the same games as the engine: 2025, {n25} games, engine {e25}, framework {f25}; "
          f"2026 so far, {n26} games, engine {e26}, framework {f26}. In college the engine has been the more "
          "accurate of the two.", S_BOX),
        P("<b>Same five criteria and weights as your NFL version.</b> Where the college data differs: pressure is "
          "sacks only (no QB-hit data), passing uses all dropbacks (no blitz charting), scrambles count as runs, "
          "overtime drives are left out of red-zone trips, and home field (2.45 points) comes from conference games, "
          "because non-conference games are mostly strong teams hosting weak ones.", S_BOX)], 5.0)]


def main():
    story = []
    page_results(story)
    page_nfl6(story)
    page_cfb(story)
    story += [Spacer(1, 8), P("Engine: the locked college method (NFL: with the approved NFL settings), rating every "
                              "offense and defense on EPA and success rate, adjusted for opponents. Framework: your Prompt "
                              "Football criteria (trenches 25%, net efficiency 25%, passing 20%, situational 15%, high "
                              "leverage 15%) scored from this season's play-by-play only. EPA = expected points added "
                              "per play. Files: results/ in the sports-engines repo.", S_NOTE)]
    doc = SimpleDocTemplate(OUT, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                            title="Week 5 graded and next games (2026-10-11)", author="sports-engines")
    doc.build(story)
    print("Saved", OUT)


if __name__ == "__main__":
    main()
