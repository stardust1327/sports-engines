"""Live college picks vs the backtest code on the same games.

Replays 2026 weeks 4-9 with the college engine exactly as the backtest does
(plays 2024-2026, expected points on that window, calibration on the 2025
replay: weeks 4-8 while the week is 8 or earlier, all weeks after), then lines
each logged live pick (results/cfb_*_picks.csv and cfb_2026-10-10.csv) up with
the replay's win chance for the same game.
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "cfb"))
import download  # noqa: E402
import engine    # noqa: E402
import epa       # noqa: E402
import parse     # noqa: E402

CACHE = os.path.join(REPO, "cfb", "cache")
OUT = os.path.dirname(os.path.abspath(__file__))

rows = []
for s in (2024, 2025, 2026):
    rows += download.final_games(CACHE, s, refresh=False)
rows = [r for r in rows if r[3] < "2026-10-24T16:00Z"]  # nothing from today's slate
games, plays, _, _ = parse.parse(os.path.join(CACHE, "summary"), rows)
sc = engine.prepare(epa.build(plays, games))
prev = engine.walk_forward(sc, games, 2025, range(4, 16))
cal_e, _ = engine.calibrate(prev, 8)
cal_l, _ = engine.calibrate(prev, 99)
cur = engine.walk_forward(sc, games, 2026, range(4, 10))
cur["p_home"] = np.where(cur["week"] <= 8, cal_e.predict_proba(cur[engine.FEATS])[:, 1],
                         cal_l.predict_proba(cur[engine.FEATS])[:, 1])
cur.to_csv(os.path.join(OUT, "cfb_engine_replay_2026.csv"), index=False)
won = (cur.p_home > .5) == (cur.home_win == 1)
print(f"2026 replay weeks 4-9: {int(won.sum())}-{int((~won).sum())} ({won.mean():.1%})")
for w, g in cur.groupby("week"):
    ww = (g.p_home > .5) == (g.home_win == 1)
    print(f"   week {w}: {int(ww.sum())}-{int((~ww).sum())}")

# logged live picks
live = []
for f in sorted(glob.glob(f"{REPO}/results/cfb_2026-1*_picks.csv")):
    d = pd.read_csv(f)
    d["slate"] = re.search(r"(\d{4}-\d\d-\d\d)", f).group(1)
    live.append(d[["slate", "away_name", "home_name", "status", "p_home", "pick", "pick_prob"]])
live = pd.concat(live, ignore_index=True)
m = live.merge(cur, left_on=["away_name", "home_name"], right_on=["away", "home"], how="left")
m = m[m.slate < "2026-10-24"]
m["live_home"] = m.p_home_x >= 0.5
m["replay_home"] = m.p_home_y >= 0.5
both = m[m.p_home_y.notna() & m.p_home_x.notna()]
print(f"\nlogged games found in the replay: {len(both)} of {len(m)}")
print(f"same pick: {(both.live_home == both.replay_home).sum()} of {len(both)}; "
      f"max win-chance gap {np.abs(both.p_home_x - both.p_home_y).max():.4f}, mean {np.abs(both.p_home_x - both.p_home_y).mean():.4f}")
diff = both[np.abs(both.p_home_x - both.p_home_y) > 0.01]
if len(diff):
    print(diff[["slate", "away_name", "home_name", "p_home_x", "p_home_y", "week"]].to_string())
m.to_csv(os.path.join(OUT, "cfb_live_vs_replay.csv"), index=False)
