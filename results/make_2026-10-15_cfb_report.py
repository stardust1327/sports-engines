"""College results report, Thursday night 2026-10-15 (made at the owner's request).

Page 1: Thursday's games graded. Page 2: this week's midweek games so far
(Tue-Thu) and the live running record of both college models. Built from
make_report.py's own graded section, so every pick, score and record comes from
the logged picks and graded files in results/ (results/grade_picks.py).

  python3 results/make_2026-10-15_cfb_report.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_report as mr  # noqa: E402  (results/make_report.py)
from reportlab.lib.pagesizes import landscape, letter  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Spacer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "report_2026-10-15_cfb-graded.pdf")
THU = ["2026-10-15"]
WEEK = ["2026-10-13", "2026-10-14", "2026-10-15"]
SUB = ("Both models graded with results/grade_picks.py against ESPN's final scores. All times Phoenix. "
       "No betting lines, records or narrative go into either model.")

# Checked by hand in ESPN's play-by-play after the games (who threw each team's passes).
QB_NOTE = ("<b>Quarterbacks (ESPN play-by-play).</b> Every expected starter started: Emory Williams (East Carolina), "
           "Ryder Burton (UAB), Max Johnson (Georgia Southern), Quinn Henicle (Old Dominion), K'saan Farrar "
           "(Colorado State) and Brad Jackson (Texas State). Two were replaced during the game: Turner Helton took "
           "over for Georgia Southern in the 2nd quarter (30 of its 41 passes) and Ryan Huff played the 2nd half "
           "for Old Dominion (14 of its 24). Both teams' next QB checks need to settle who starts.")


def section(story, dates, title, box_html):
    eng = pd.concat([mr.read(f"cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    eng_g = pd.concat([mr.read(f"cfb_{d}_graded.csv") for d in dates], ignore_index=True)
    frm = pd.concat([mr.read(f"prompt_cfb_{d}_picks.csv") for d in dates], ignore_index=True)
    frm_g = pd.concat([mr.read(f"prompt_cfb_{d}_graded.csv") for d in dates], ignore_index=True)
    mr.graded_section(story, title, SUB, eng, eng_g, frm, frm_g, "neutral site")
    page_break = story.pop()
    story += [Spacer(1, 8), mr.boxes([mr.P(box_html, mr.S_BOX)], 10.0), page_break]


def tier(p):
    return "70%+" if p >= 0.70 else "60-70%" if p >= 0.60 else "under 60%"


def wl(results):
    r = pd.Series(list(results))
    return f"{(r == 'W').sum()}-{(r == 'L').sum()}" + (f"-{(r == 'T').sum()}" if (r == "T").any() else "")


def running_record():
    """Every graded live pick: the engine since 2026-10-10 (cfb_2026-10-10.csv, logged before
    the 12:30 PM kickoffs), both models since 2026-10-13 (the midweek graded files)."""
    rows = []
    d = pd.read_csv(os.path.join(HERE, "cfb_2026-10-10.csv"))
    rows += [("engine", r.win_prob, r.result) for r in d[d.status == "PICK"].itertuples()]
    for day in WEEK:
        for model, name in (("engine", f"cfb_{day}_graded.csv"), ("framework", f"prompt_cfb_{day}_graded.csv")):
            g = pd.read_csv(os.path.join(HERE, name))
            rows += [(model, r.pick_prob, r.result) for r in g[g.status == "PICK"].itertuples()]
    x = pd.DataFrame(rows, columns=["model", "prob", "result"])
    x["tier"] = x.prob.map(tier)

    def line(model):
        y = x[x.model == model]
        return wl(y.result), ", ".join(f"{t} picks {wl(y[y.tier == t].result)}" for t in ("70%+", "60-70%", "under 60%"))

    e_all, e_tiers = line("engine")
    f_all, f_tiers = line("framework")
    return (f"<b>Live record (every pick logged before kickoff).</b> Engine (official): <b>{e_all}</b> since Oct 10; "
            f"{e_tiers}. Framework: <b>{f_all}</b> since Oct 13, its first logged college picks; {f_tiers}. "
            "Oct 10 counts the engine's 19 picks from the 12:30 PM kickoffs on (4 no-picks). A tier's record means "
            "little until it has dozens of games.")


def main():
    story = []
    section(story, THU, "College football results: Thursday, Oct 15", QB_NOTE)
    section(story, WEEK, "College football results: this week so far (Tue Oct 13 to Thu Oct 15)", running_record())
    story = story[:-1]  # no blank page at the end
    story += [Spacer(1, 8), mr.P("Engine: the locked college method, rating every offense and defense on EPA and "
                                 "success rate, adjusted for opponents. Framework: your Prompt Football criteria "
                                 "(trenches 25%, net efficiency 25%, passing 20%, situational 15%, high leverage 15%) "
                                 "scored from this season's play-by-play only. Files: results/ in the sports-engines "
                                 "repo.", mr.S_NOTE)]
    doc = SimpleDocTemplate(OUT, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                            title="College football results, Thu Oct 15 2026", author="sports-engines")
    doc.build(story)
    print("Saved", OUT)


if __name__ == "__main__":
    main()
