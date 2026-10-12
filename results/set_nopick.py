"""Mark games as no-pick in logged picks files without re-running the models.
Use it when a starting QB is ruled out, or becomes unconfirmed, after the picks
were logged. Every game involving the team (matched by the team name in the
file, case-insensitive) becomes a no-pick with the reason given.

  python3 results/set_nopick.py --team Ravens --reason "Lamar Jackson (ankle) ruled out" \
      results/nfl_cfbmethod_2026_week06_picks.csv results/prompt_nfl_2026_week06_picks.csv

Always pass both models' files so they keep the same no-picks. Engine files keep
their numbers (as the engines write no-picks); framework files (prompt_*) clear
the pick, win chance, confidence and score, as the framework writes no-picks.
To bring a pick back (QB confirmed after all), re-run the models instead.
"""
import argparse
import os
import sys

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--team", required=True, help="team name as written in the file (NFL nickname, college school)")
    ap.add_argument("--reason", required=True, help="exactly what's missing")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for path in a.files:
        # read every cell as text so nothing but the marked games changes in the file
        p = pd.read_csv(path, dtype=str, keep_default_na=False)
        m = (p.away_name.str.lower() == a.team.lower()) | (p.home_name.str.lower() == a.team.lower())
        if not m.any():
            sys.exit(f"{os.path.basename(path)}: no game with team '{a.team}' (nothing changed)")
        p.loc[m, "status"] = "NO PICK"
        p.loc[m, "reason"] = a.reason
        if os.path.basename(path).startswith("prompt_"):
            for c in ("pick", "pick_prob", "confidence", "score"):
                if c in p:
                    p.loc[m, c] = ""
        p.to_csv(path, index=False)
        for r in p[m].itertuples():
            print(f"{os.path.basename(path)}: {r.away_name} at {r.home_name} -> NO PICK ({a.reason})")


if __name__ == "__main__":
    main()
