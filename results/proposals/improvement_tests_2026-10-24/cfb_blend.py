"""College engine + framework blend: the two win chances averaged (log-odds, equal
weights, nothing fitted) on the 2021-2025 games both rated, from the audit's
per-game files (engine run live-style; framework with the previous starter at QB)."""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "audit_2026-10-24")


def lo(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def summary(name, d, p):
    right = (d[p] > .5) == (d.home_win == 1)
    brier = ((d[p] - d.home_win) ** 2).mean()
    e = d.week <= 8
    by = " ".join(f"{s}:{((g[p] > .5) == (g.home_win == 1)).mean():.1%}" for s, g in d.groupby("season"))
    return (f"{name:14s} {int(right.sum())}-{int((~right).sum())} ({right.mean():.2%})  wks4-8 {right[e].mean():.2%}  "
            f"wks9+ {right[~e].mean():.2%}  Brier {brier:.4f} | {by}")


eng = pd.read_csv(os.path.join(AUDIT, "cfb_engine_backtest_2021_2025.csv"))
fw = pd.read_csv(os.path.join(AUDIT, "cfb_framework_backtest_2021_2025_pregame_qb.csv"))
fw = fw.rename(columns={"home_name": "home", "away_name": "away", "p_home": "p_fw"})
b = eng.merge(fw[["season", "week", "home", "away", "p_fw"]], on=["season", "week", "home", "away"])
b["p_blend"] = 1 / (1 + np.exp(-(0.5 * lo(b.p_home) + 0.5 * lo(b.p_fw))))
lines = [f"2021-2025 games both rated: {len(b)} (engine file {len(eng)}, framework file {len(fw)})",
         summary("engine", b, "p_home"), summary("framework", b, "p_fw"), summary("blend (50/50)", b, "p_blend")]
agree = (b.p_home > .5) == (b.p_fw > .5)
for nm, sub in (("models agree", b[agree]), ("models split", b[~agree])):
    lines.append(f"   {nm}: {len(sub)} games; engine right {((sub.p_home > .5) == (sub.home_win == 1)).mean():.1%}, "
                 f"framework right {((sub.p_fw > .5) == (sub.home_win == 1)).mean():.1%}")
txt = "\n".join(lines)
print(txt)
open(os.path.join(HERE, "cfb_blend.txt"), "w").write(txt + "\n")
b.to_csv(os.path.join(HERE, "cfb_blend_2021_2025.csv"), index=False)
