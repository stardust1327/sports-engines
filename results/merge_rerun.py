"""Bring a re-run into the logged picks without touching games already under way
or finished.

The models only price games that haven't kicked off, so a re-run written straight
into results/ after a slate has started would drop the picks already logged for
the earlier games. Instead, re-run with --out <scratch folder>, then:

  python3 results/merge_rerun.py <scratch>/nfl_cfbmethod_2026_week06_picks.csv
  python3 results/merge_rerun.py <scratch>/prompt_cfb_2026-10-17_picks.csv --into results/prompt_cfb_2026-10-17_picks.csv

(--into defaults to results/<same file name>.) Each game in the re-run whose
ESPN status is still "pre" replaces its logged row; games already started or
final keep their logged rows; games new to the slate are added. Every change in
status, pick or win chance is printed. Cells are copied as text, so nothing else
in the file changes.
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/{sport}/summary?event={gid}"


def state(sport, gid):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(SUMMARY.format(sport=sport, gid=gid),
                                                               headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return json.load(r)["header"]["competitions"][0]["status"]["type"]["state"]
        except Exception:  # noqa: BLE001
            if i == 3:
                return None
            time.sleep(2 * (i + 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("new", help="the re-run's picks file (in a scratch folder)")
    ap.add_argument("--into", help="the logged picks file (default: results/<same name>)")
    a = ap.parse_args()
    name = os.path.basename(a.new)
    into = a.into or os.path.join(HERE, name)
    if os.path.abspath(into) == os.path.abspath(a.new):
        sys.exit("the re-run must be written somewhere else first (use the model's --out with a scratch folder)")
    if not os.path.exists(into):
        sys.exit(f"{into} doesn't exist: nothing logged yet, so the re-run can go straight into results/")
    sport = "nfl" if "nfl" in name else "college-football"
    old = pd.read_csv(into, dtype=str, keep_default_na=False)
    new = pd.read_csv(a.new, dtype=str, keep_default_na=False)
    extra = [c for c in new.columns if c not in old.columns]
    if extra:
        print(f"note: the re-run has columns the logged file doesn't ({', '.join(extra)}); they are left out")
    new = new.reindex(columns=old.columns, fill_value="")
    pos = {g: i for i, g in enumerate(old.game_id)}
    replaced, added, kept = 0, 0, 0
    for _, r in new.iterrows():
        st = state(sport, r.game_id)
        label = f"{r.away_name} at {r.home_name}"
        if st != "pre":
            kept += 1
            print(f"  kept as logged ({'status unknown' if st is None else 'already ' + ('final' if st == 'post' else 'under way')}): {label}")
            continue
        if r.game_id in pos:
            o = old.iloc[pos[r.game_id]]
            diff = [f"{c} {o[c] or '-'} -> {r[c] or '-'}" for c in ("status", "pick", "pick_prob", "reason")
                    if c in old.columns and o[c] != r[c]]
            if diff:
                print(f"  updated: {label}: " + "; ".join(diff))
            old.iloc[pos[r.game_id]] = r.values
            replaced += 1
        else:
            old = pd.concat([old, r.to_frame().T], ignore_index=True)
            pos[r.game_id] = len(old) - 1
            added += 1
            print(f"  added: {label}")
    old.to_csv(into, index=False)
    print(f"{os.path.basename(into)}: {replaced} game(s) refreshed, {added} added, {kept} left as logged "
          f"(games not in the re-run are untouched)")


if __name__ == "__main__":
    main()
