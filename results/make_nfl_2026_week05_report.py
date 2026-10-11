"""Build the downloadable PDF of NFL Week 5 (2026-10-11/12) picks: the engine's
official picks next to the Prompt Football framework's, with the framework's
reasoning and parlay.

Inputs: the engine's picks CSV and the framework's picks CSV (both in results/).
Output: results/nfl_2026_week05_engine_vs_framework.pdf
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
ENGINE = os.path.join(HERE, "nfl_cfbmethod_2026_week05_picks.csv")
FRAME = os.path.join(HERE, "prompt_nfl_2026_week05_picks.csv")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "nfl_2026_week05_engine_vs_framework.pdf")

INK, MUTED, RULE = colors.HexColor("#1F2937"), colors.HexColor("#6B7280"), colors.HexColor("#D1D5DB")
AGREE, SPLIT, NOPICK = colors.HexColor("#E7F4EA"), colors.HexColor("#FDF1DC"), colors.HexColor("#EEEEEE")

# the framework's reasoning, condensed from prompt_nfl_2026_week05.md (keyed by home team)
WHY = {
    "Jaguars": "Ahead on 4 of 5 criteria: +0.31 net EPA per play vs -0.18; the Eagles' rush gets pressure on 8.6% "
               "of dropbacks (Jaguars 18.5%); Lawrence +0.29 EPA per dropback vs Hurts -0.06; 55% on third down, "
               "86% red-zone TDs, +1.5 turnovers per game. Neutral site, equal rest.",
    "Saints": "Vikings defense: -0.18 EPA per play allowed, 25.5% pressure, blitz on 73% of dropbacks against a "
              "Shough at -0.17 when blitzed. Saints D allows +0.14 per play, 48% on third down, 73% red-zone TDs; "
              "Saints -1.5 turnovers per game. Home field and Murray's -0.16 per dropback trim it.",
    "Dolphins": "Net EPA +0.08 vs -0.27; Burrow (+0.12 per dropback) faces a pass defense allowing +0.31 while "
                "Willis is at -0.17. Trenches even; home field is Miami's only edge.",
    "Patriots": "Ahead on 4 of 5: net EPA +0.11 vs -0.06, pressure 22.6% vs 15.8%, Cousins +0.17 per dropback vs "
                "Maye -0.01, turnovers +1.25 vs -1.25 per game. The engine likes New England because it uses last "
                "season and opponent strength; the framework uses neither.",
    "Commanders": "Giants' line allows pressure on 19.8% of dropbacks and their rush gets 9.8%; Winston is at -0.75 "
                  "EPA when blitzed and Washington blitzes 47%. Net efficiency even. Daniels returns from a "
                  "dislocated elbow; his +0.20 per dropback is from weeks 1-2 only (61 dropbacks).",
    "Steelers": "Efficiency nearly even (-0.13 vs -0.11 net EPA), so 10 days' rest vs 7 (Colts back from London) "
                "and home field tip it. Engine leans Colts: treat as a coin flip.",
    "Seahawks": "Purdy +0.58 EPA per dropback (+1.16 when blitzed); San Francisco converts 59% on third down and "
                "89% of red-zone trips vs Seattle's 31% and 65%. Seattle's defense wins the trenches; home field "
                "keeps it close.",
    "Jets": "Small edges add up: net EPA +0.04 vs -0.08, Smith +0.16 per dropback vs Watson +0.10, turnovers +0.5 "
            "vs 0 per game. Cleveland's rush and 10 days' rest offset part of home field.",
    "Cardinals": "Two leaky defenses; Goff +0.22 per dropback (+0.32 when blitzed) vs Brissett -0.03 (-0.39). "
                 "Detroit's rush 18.7% pressure vs 13.8%. Home field takes most of it back; engine leans Arizona.",
    "Chargers": "Denver's line allows pressure on 10.5% of dropbacks vs the Chargers' 21.4%; Chargers' offense "
                "-0.16 EPA per play, Herbert -0.15 per dropback. Engine leans Chargers: coin flip.",
    "Titans": "Slightly better efficiency (-0.07 vs -0.16 net EPA) and QB (Stroud +0.09 per dropback vs Ward "
              "-0.11); home field gives most of it back. Engine is more confident (64%).",
    "Rams": "Buffalo has the better offense (+0.20 EPA per play, Allen +0.29 per dropback) but allows +0.10 per "
            "play; the Rams lead net efficiency (+0.16 vs +0.10). Home field makes it a coin flip leaning Rams; "
            "engine much more confident.",
}


def style(name, size, bold=False, color=INK, lead=None, align=0):
    return ParagraphStyle(name, fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                          leading=lead or size * 1.25, textColor=color, alignment=align)


S_TITLE, S_SUB = style("t", 18, True), style("s", 9.5, color=MUTED)
S_H = style("h", 11, True)
S_CELL, S_CELLB = style("c", 9), style("cb", 9, True)
S_HEAD = style("hd", 8.5, True, colors.white)
S_SMALL, S_NOTE = style("sm", 8.2, lead=10.4), style("n", 7.8, color=MUTED, lead=9.8)
S_BOX = style("bx", 8.6, lead=11.2)


def P(text, st):
    return Paragraph(text, st)


def game_label(r):
    return f"{r.away_name} vs {r.home_name} (London)" if r.neutral else f"{r.away_name} at {r.home_name}"


def main():
    eng = pd.read_csv(ENGINE, dtype={"game_id": str})
    frm = pd.read_csv(FRAME, dtype={"game_id": str})
    m = eng.merge(frm[["game_id", "pick", "pick_prob", "confidence", "score", "status"]],
                  on="game_id", suffixes=("_e", "_f")).sort_values(["kickoff_utc", "away_name"])
    assert len(m) == len(eng) == len(frm)
    picks = m[m.status_e == "PICK"]
    agree = (picks.pick_e == picks.pick_f).sum()

    story = [P("NFL Week 5: Engine vs. Framework", S_TITLE), Spacer(1, 3),
             P("Sunday, October 11, 2026, plus Monday night. All times Phoenix. Logged before kickoff "
               "(4:50 AM Sunday). No betting lines go into either one.", S_SUB), Spacer(1, 9)]

    head = ["Kickoff", "Game", "Engine (official)", "Framework", "Framework score", "Conf.", ""]
    rows, bg = [[P(h, S_HEAD) for h in head]], []
    for i, r in enumerate(m.itertuples(), start=1):
        t = r.kickoff.replace("Sun ", "")
        if r.status_e != "PICK":
            rows.append([P(t, S_CELL), P(escape(game_label(r)), S_CELL), P(f"No pick: {escape(r.reason)}", S_CELL),
                         "", "", "", ""])
            bg.append((i, NOPICK, True))
            continue
        same = r.pick_e == r.pick_f
        ep, fp = r.pick_prob_e * 100, r.pick_prob_f * 100
        rows.append([P(t, S_CELL), P(escape(game_label(r)), S_CELL),
                     P(f"{r.pick_e} {ep:.1f}%", S_CELLB if ep >= 70 else S_CELL),
                     P(f"{r.pick_f} {fp:.1f}%", S_CELLB if fp >= 70 else S_CELL),
                     P(escape(r.score.replace(" - ", "-")), S_CELL), P(str(int(r.confidence)), S_CELL),
                     P("Agree" if same else "Split", S_CELLB if not same else S_CELL)])
        bg.append((i, AGREE if same else SPLIT, False))
    widths = [x * inch for x in (0.95, 2.3, 1.75, 1.45, 1.9, 0.55, 1.1)]
    tbl = Table(rows, colWidths=widths, repeatRows=1)
    ts = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
          ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE)]
    for i, c, span in bg:
        ts.append(("BACKGROUND", (0, i), (-1, i), c))
        if span:
            ts.append(("SPAN", (2, i), (-1, i)))
    tbl.setStyle(TableStyle(ts))
    story += [tbl, Spacer(1, 5),
              P(f"They agree on {agree} of {len(picks)} picks (green) and split on {len(picks) - agree} (amber). "
                "Bold = 70%+. Conf. is the framework's confidence, its win chance in tenths (7 = about 70%).",
                S_NOTE), Spacer(1, 9)]

    parlay = ("<b>Parlay (framework, $25): Jaguars + Vikings + Bengals.</b> All three hit about 45% of the time "
              "by the framework's numbers and about 32% by the engine's (it has the Vikings at 58.6%). Fair payout "
              "on $25 is about $56; a sportsbook pays less, so the ticket must pay at least $50 to reach the $25 "
              "profit target. The Jaguars leg kicks off at 6:30 AM.")
    trust = ("<b>How far to trust them.</b> On the same 887 games (2022-2025), the engine picked 64.0% of winners, "
             "the framework 62.6% and the closing-line favorite 68.7%. When the two split, the engine was right "
             "54% of the time. Both are weaker early in the season. The closing line has been more accurate than "
             "either, so a high win chance is not the same as a good bet.")
    boxes = Table([[P(parlay, S_BOX), P(trust, S_BOX)]], colWidths=[5.0 * inch, 5.0 * inch])
    boxes.setStyle(TableStyle([("BOX", (0, 0), (0, 0), 0.6, RULE), ("BOX", (1, 0), (1, 0), 0.6, RULE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [boxes, Spacer(1, 8),
              P("QB status as of 4:50 AM Sunday: Jayden Daniels reported starting for Washington; Jameis Winston "
                "starts for the Giants (Jaxson Dart out for the season). Re-check inactives 90 minutes before each "
                "kickoff; if a starting QB changes, drop that pick.", S_NOTE),
              PageBreak()]

    story += [P("Why the framework picked each team", S_H), Spacer(1, 5)]
    rows = [[P(h, S_HEAD) for h in ("Game", "Framework", "Engine", "Why (framework)")]]
    for r in m[m.status_e == "PICK"].sort_values("pick_prob_f", ascending=False).itertuples():
        rows.append([P(escape(game_label(r)), S_SMALL), P(f"<b>{r.pick_f}</b> {r.pick_prob_f * 100:.1f}%", S_SMALL),
                     P(f"{r.pick_e} {r.pick_prob_e * 100:.1f}%", S_SMALL), P(escape(WHY[r.home_name]), S_SMALL)])
    t2 = Table(rows, colWidths=[x * inch for x in (2.0, 1.25, 1.25, 5.5)], repeatRows=1)
    t2.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE)]))
    story += [t2, Spacer(1, 8),
              P("<b>Engine:</b> the locked college method with the approved NFL settings. It rates every offense and "
                "defense on EPA and success rate, adjusted for opponents, starting from 30% of last season, with "
                "recent games counting more. <b>Framework:</b> your Prompt Football criteria (trenches 25%, net "
                "efficiency 25%, passing 20%, situational 15%, high leverage 15%) scored from this season's "
                "play-by-play only. EPA = expected points added per play; pressure = sacks plus QB hits per "
                "dropback; blitz = 5+ pass rushers. Files: results/nfl_cfbmethod_2026_week05_picks.csv, "
                "results/prompt_nfl_2026_week05_picks.csv.", S_NOTE)]

    doc = SimpleDocTemplate(OUT, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                            title="NFL Week 5: Engine vs. Framework", author="sports-engines")
    doc.build(story)
    print("Saved", OUT)


if __name__ == "__main__":
    main()
