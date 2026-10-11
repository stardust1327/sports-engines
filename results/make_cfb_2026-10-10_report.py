"""Build the downloadable list of Saturday 2026-10-10 college picks and results:
every game, the earlier chat's pick, the engine's pick, and the final score.

Inputs: the earlier chat's list (text), the engine's picks CSV, and ESPN's final
scoreboard for the day. Output: a PDF and a CSV next to this script."""
import datetime
import json
import os
import re
import sys

import pandas as pd
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LIST_TXT, ENGINE_CSV, SCOREBOARD, OUT_DIR = sys.argv[1:5]

# ESPN names for the earlier chat's 36 games, in the list's order
ESPN = [("Arizona", "West Virginia"), ("Texas A&M", "Missouri"), ("Indiana", "Nebraska"), ("UCF", "Oklahoma State"),
        ("Sacramento State", "Bowling Green"), ("North Carolina", "Pittsburgh"), ("Tulane", "Army"),
        ("Wake Forest", "NC State"), ("Ball State", "Northwestern"), ("South Carolina", "Florida"),
        ("Old Dominion", "App State"), ("Rice", "East Carolina"), ("Miami (OH)", "Massachusetts"),
        ("Illinois", "Michigan State"), ("Tulsa", "Navy"), ("Ole Miss", "Vanderbilt"), ("Virginia Tech", "California"),
        ("Buffalo", "Toledo"), ("UCLA", "Oregon"), ("Eastern Michigan", "Akron"), ("Central Michigan", "Ohio"),
        ("Duke", "Georgia Tech"), ("Kent State", "Western Michigan"), ("Texas", "Oklahoma"), ("Houston", "Kansas State"),
        ("Charlotte", "North Texas"), ("Stanford", "Notre Dame"), ("UConn", "Temple"), ("Maryland", "Ohio State"),
        ("Tennessee", "Arkansas"), ("San Diego State", "Oregon State"), ("North Dakota State", "UNLV"),
        ("LSU", "Kentucky"), ("UAB", "Memphis"), ("Coastal Carolina", "Marshall"), ("Nevada", "UTEP")]
NO_PICK = {"Oregon": "Oregon QB Dante Moore ruled out; Dylan Raiola (36 throws) started",
           "Arkansas": "Tennessee QB George MacIntyre's first career start (20 throws)",
           "Vanderbilt": "Vanderbilt QB Jared Curtis listed probable; starter not confirmed",
           "California": "Cal QB Sagapolutele questionable (concussion protocol)"}

text = open(LIST_TXT).read()
listed = re.findall(r"\n([^\n*]+?@[^\n]+)\n\* Winner Pick: ([^\n]+)\n\* Predicted Score / Margin: ([^\n]+)\n"
                    r"\* Confidence Score: (\d+)", text)
assert len(listed) == len(ESPN) == 36

sb = json.load(open(SCOREBOARD))
final = {}
for e in sb["events"]:
    c = e["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    final[(t["away"]["team"]["location"], t["home"]["team"]["location"])] = (
        e["date"], e["status"]["type"]["state"], int(t["away"].get("score") or 0), int(t["home"].get("score") or 0))

eng = pd.read_csv(ENGINE_CSV, dtype={"game_id": str})
eng = eng[eng["in_user_list"] == True]  # noqa: E712
eng_by = {(r.away_name, r.home_name): r for r in eng.itertuples()}


def espn_name(list_name, away, home):
    # the list abbreviates names ("S. Carolina", "Oklahoma St."); match to the side it refers to
    a = list_name.replace(".", "").lower()
    def score(n):
        n2 = n.replace(".", "").lower()
        return sum(w in n2 for w in a.split())
    return away if score(away) >= score(home) else home


rows = []
for (gname, pick, pred, conf), (away, home) in zip(listed, ESPN):
    date, state, a_s, h_s = final[(away, home)]
    assert state == "post", (away, home, state)
    winner = home if h_s > a_s else away
    lp = espn_name(pick, away, home)
    kick = (datetime.datetime.strptime(date, "%Y-%m-%dT%H:%MZ") - datetime.timedelta(hours=7))
    e = eng_by.get((away, home))
    if e is None:
        e_pick, e_prob, e_res, e_txt = "", None, "", "not priced (already started)"
    elif home in NO_PICK:
        e_pick, e_prob, e_res, e_txt = "", None, "", "no pick: " + NO_PICK[home]
    else:
        e_pick, e_prob = e.pick, float(e.pick_prob)
        e_res = "W" if e_pick == winner else "L"
        e_txt = f"{e_pick} {int(e_prob * 100 + 0.5)}%"
    rows.append({"kickoff": kick, "away": away, "home": home, "away_score": a_s, "home_score": h_s, "winner": winner,
                 "list_pick": lp, "list_confidence": int(conf), "list_predicted_score": pred,
                 "list_result": "W" if lp == winner else "L",
                 "engine_pick": e_pick, "engine_win_pct": "" if e_prob is None else round(e_prob * 100, 1),
                 "engine_win_pct_rounded": "" if e_prob is None else int(e_prob * 100 + 0.5),
                 "engine_result": e_res, "engine_note": e_txt})
df = pd.DataFrame(rows).sort_values(["kickoff"], kind="stable").reset_index(drop=True)
df["kickoff_phoenix"] = df["kickoff"].dt.strftime("%I:%M %p").str.lstrip("0")
df.drop(columns=["kickoff"]).to_csv(os.path.join(OUT_DIR, "cfb_2026-10-10_both_lists.csv"), index=False)

# records
lw, ll = (df.list_result == "W").sum(), (df.list_result == "L").sum()
picked = df[df.engine_result != ""]
ew, el = (picked.engine_result == "W").sum(), (picked.engine_result == "L").sum()
both = picked
bw = (both.list_result == "W").sum()
dis = both[both.list_pick != both.engine_pick]
dw = (dis.list_result == "W").sum()


def tier(lo, hi):
    s = picked[(picked.engine_win_pct >= lo) & (picked.engine_win_pct < hi)]
    return f"{(s.engine_result == 'W').sum()}-{(s.engine_result == 'L').sum()}"


# ---------- PDF ----------
path = os.path.join(OUT_DIR, "cfb_2026-10-10_picks_and_results.pdf")
doc = SimpleDocTemplate(path, pagesize=landscape(letter), leftMargin=0.45 * inch, rightMargin=0.45 * inch,
                        topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                        title="College Football Picks and Results, Oct 10, 2026")
ss = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=17, leading=21, alignment=0, spaceAfter=2)
sub = ParagraphStyle("sub", parent=ss["Normal"], fontSize=9.5, textColor=colors.HexColor("#555555"))
body = ParagraphStyle("body", parent=ss["Normal"], fontSize=9, leading=12)
cell = ParagraphStyle("cell", parent=ss["Normal"], fontSize=7.6, leading=9.2)
small = ParagraphStyle("small", parent=ss["Normal"], fontSize=7.6, leading=10, textColor=colors.HexColor("#444444"))
GREEN, RED, GREY = colors.HexColor("#1e7d32"), colors.HexColor("#c62828"), colors.HexColor("#777777")

story = [Paragraph("College football picks and results", h1),
         Paragraph("Saturday, October 10, 2026  ·  every game on the slate  ·  kickoff times in Phoenix time", sub),
         Spacer(1, 8)]
summary = [
    [Paragraph("<b>List</b>", body), Paragraph("<b>Record</b>", body), Paragraph("<b>Details</b>", body)],
    [Paragraph("Earlier chat (your football prompt)", body), Paragraph(f"<b>{lw}-{ll}</b>", body),
     Paragraph(f"All 36 games. On the {len(both)} games both lists picked: {bw}-{len(both) - bw}. Where the two "
               f"disagreed ({len(dis)} games): {dw}-{len(dis) - dw}. Its $25 parlay (Ohio State, Oregon, Notre Dame) lost "
               "when Oregon fell to UCLA 17-15.", body)],
    [Paragraph("Engine (play-by-play, tested on 2025)", body), Paragraph(f"<b>{ew}-{el}</b>", body),
     Paragraph(f"{len(picked)} picks from the 12:30 PM games on: 70%+ {tier(70, 101)}, 60-70% {tier(60, 70)}, "
               f"under 60% {tier(0, 60)}. Four no-picks (quarterback out or unconfirmed). The 13 earlier games had "
               "already started.", body)],
]
st = Table(summary, colWidths=[2.3 * inch, 0.8 * inch, 7.0 * inch])
st.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story += [st, Spacer(1, 10)]

head = ["Kickoff", "Game", "Final", "Earlier chat pick (confidence)", "", "Engine pick (win chance)", ""]
data = [[Paragraph(f"<b>{h}</b>", cell) for h in head]]
styles = []
for i, r in df.iterrows():
    final_txt = f"{r.away} {r.away_score}, {r.home} {r.home_score}"
    eng_cell = r.engine_note if r.engine_result == "" else f"{r.engine_pick} ({r.engine_win_pct_rounded}%)"
    data.append([Paragraph(r.kickoff_phoenix, cell), Paragraph(escape(f"{r.away} at {r.home}"), cell),
                 Paragraph(escape(final_txt), cell), Paragraph(escape(f"{r.list_pick} ({r.list_confidence})"), cell),
                 Paragraph(f"<b>{r.list_result}</b>", cell), Paragraph(escape(eng_cell), cell),
                 Paragraph(f"<b>{r.engine_result}</b>", cell)])
    row = i + 1
    styles.append(("TEXTCOLOR", (4, row), (4, row), GREEN if r.list_result == "W" else RED))
    if r.engine_result:
        styles.append(("TEXTCOLOR", (6, row), (6, row), GREEN if r.engine_result == "W" else RED))
    if i % 2 == 1:
        styles.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#f6f6f6")))
cw = [0.7, 2.2, 2.25, 1.75, 0.3, 2.6, 0.3]
t = Table(data, colWidths=[w * inch for w in cw], repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                       ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#999999")),
                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                       ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)] + styles))
story += [t, Spacer(1, 8),
          Paragraph("<b>How each list was made.</b> Earlier chat: Claude's analysis from your football prompt, weighing "
                    "trench play, efficiency, passing matchups, situation and high-leverage execution; no stats were "
                    "shown. Engine: opponent-adjusted expected points and success rate from 2024-2026 play-by-play, "
                    "calibrated on the 2025 season; no betting lines, records, yards or points scored. Confidence is the "
                    "earlier chat's 1-10 score; win chance is the engine's.", small)]
doc.build(story)
print(path)
print(f"list {lw}-{ll} | engine {ew}-{el} | both {bw}-{len(both) - bw} | disagree {dw}-{len(dis) - dw}")
