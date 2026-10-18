"""Off-the-record tally: how the no-pick games would have gone.

A no-pick game (starting QB out or unconfirmed, or not enough play-by-play) gets
no official pick, but both models still save their win chance for it (p_home in
the picks files). This script reads those saved numbers and the final scores in
the graded files and shows which team each model would have taken and whether
it won. Nothing here counts in either model's record, and nothing is written to
the picks or graded files; it only reads them.

  python3 results/nopick_leans.py            # every graded slate so far
  python3 results/nopick_leans.py --csv out.csv
"""
import argparse
import glob
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def rows():
    out = []
    for g in sorted(glob.glob(os.path.join(HERE, "*_graded.csv"))):
        base = os.path.basename(g)
        if base.startswith("team_notes"):
            continue
        pk = os.path.join(HERE, base.replace("_graded", "_picks"))
        if not os.path.exists(pk):
            continue
        G = pd.read_csv(g, dtype={"game_id": str})
        P = pd.read_csv(pk, dtype={"game_id": str}).set_index("game_id")
        if "status" not in G.columns or "p_home" not in P.columns:
            continue
        model = "framework" if base.startswith("prompt") else "engine"
        sport = "NFL" if "nfl" in base else "College"
        slate = base.replace("_graded.csv", "").replace("prompt_", "").replace("nfl_cfbmethod_", "nfl_")
        for r in G[G.status != "PICK"].itertuples():
            if pd.isna(r.away_score) or pd.isna(r.home_score):
                continue  # not final
            ph = P["p_home"].get(r.game_id)
            win = r.home if r.home_score > r.away_score else r.away if r.away_score > r.home_score else "tie"
            if ph is None or pd.isna(ph):
                lean, prob, res = "", None, ""
            else:
                lean, prob = (r.home, ph) if ph >= 0.5 else (r.away, 1 - ph)
                res = "T" if win == "tie" else "W" if lean == win else "L"
            out.append({"sport": sport, "model": model, "slate": slate, "game": f"{r.away} at {r.home}",
                        "final": f"{r.away} {int(r.away_score)}, {r.home} {int(r.home_score)}",
                        "lean": lean, "win_chance": None if prob is None else round(prob, 3), "result": res,
                        "reason": r.reason})
    return pd.DataFrame(out)


def rec(x):
    return f"{(x == 'W').sum()}-{(x == 'L').sum()}" + (f"-{(x == 'T').sum()}" if (x == "T").any() else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="also save the game list here")
    a = ap.parse_args()
    d = rows()
    if d.empty:
        print("no graded no-pick games yet")
        return
    g = d[d.result != ""]
    print("Off the record: the team each model would have taken in no-pick games (never in the official record)")
    for (sport, model), x in g.groupby(["sport", "model"]):
        print(f"  {sport} {model}: {rec(x.result)} (average win chance {x.win_chance.mean():.0%})")
    print(f"  All: {rec(g.result)}; {int((d.result == '').sum())} game(s) had no number (not enough data)")
    print()
    for r in g.itertuples():
        print(f"  {r.result}  {r.sport} {r.model:9s} {r.slate}: {r.game}: {r.lean} {r.win_chance:.0%}; final {r.final}")
    if a.csv:
        d.to_csv(a.csv, index=False)
        print("Saved", a.csv)


if __name__ == "__main__":
    main()
