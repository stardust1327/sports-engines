"""Grade a week of NFL picks and run the closing-line check (approved 2026-10-11).

  python3 nfl_cfbmethod/grade.py --season 2026 --week 5

Closing moneylines are used here ONLY to grade picks after they lock. They are
never an input to any prediction. For every pick it records the final score,
the closing moneylines, the market's no-vig win chance for the picked team and
the gap between the engine's win chance and the market's. It appends the week
to results/nfl_scorecard.csv and prints how the engine compares with the
closing line so far.

Scores come from ESPN; closing moneylines from nflverse's schedule file.

Ties (fixed 2026-10-11 at the owner's request): a tie is graded T, not W or L.
Records print as W-L-T whenever there is a tie (W-L otherwise). In the Brier
score a tie counts as half a win for each side (home_win = 0.5), and in the
closing-odds units it is a push (the stake comes back, 0 units). Before this fix
a tie was scored as an away-team win. Games without a tie grade exactly as before.
"""
import argparse
import json
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype=2&week={week}&limit=400"
NFLVERSE_GAMES = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
ESPN_TO_NFLVERSE = {"LAR": "LA", "WSH": "WAS"}


def implied(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def no_vig(home_ml, away_ml):
    h, a = implied(home_ml), implied(away_ml)
    return h / (h + a)


def espn_week(season, week):
    with urllib.request.urlopen(urllib.request.Request(SCOREBOARD.format(season=season, week=week),
                                                       headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
        data = json.load(r)
    out = {}
    for e in data.get("events", []):
        t = {x["homeAway"]: x for x in e["competitions"][0]["competitors"]}
        ab = {s: ESPN_TO_NFLVERSE.get(t[s]["team"]["abbreviation"], t[s]["team"]["abbreviation"]) for s in ("home", "away")}
        out[e["id"]] = {"state": e["status"]["type"]["state"], "home_abbr": ab["home"], "away_abbr": ab["away"],
                        "home_score": int(t["home"].get("score") or 0), "away_score": int(t["away"].get("score") or 0)}
    return out


def outcome(home_score, away_score):
    """1 = home win, 0 = away win, 0.5 = tie."""
    if home_score > away_score:
        return 1
    if home_score < away_score:
        return 0
    return 0.5


def record(w, l, t):
    """W-L, or W-L-T when there is at least one tie."""
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def market_table(path=None):
    g = pd.read_csv(path or NFLVERSE_GAMES)
    return g[g["game_type"] == "REG"][["season", "week", "home_team", "away_team", "home_moneyline", "away_moneyline"]]


def compare(df, label):
    """Engine vs closing line on graded picks (df needs p_home, market_p_home, home_win)."""
    d = df.dropna(subset=["market_p_home"])
    if d.empty:
        return
    y = d["home_win"].values.astype(float)
    pe, pm = d["p_home"].values, d["market_p_home"].values
    be, bm = np.mean((pe - y) ** 2), np.mean((pm - y) ** 2)
    tie = y == 0.5
    won = ((pe > .5) == (y == 1)) & ~tie
    lost = ~won & ~tie
    m_won = ((pm > .5) == (y == 1)) & ~tie
    m_lost = ~m_won & ~tie
    agree = (pe > .5) == (pm > .5)
    print(f"  {label}: {len(d)} games | engine {record(won.sum(), lost.sum(), tie.sum())}, closing-line favorite "
          f"{record(m_won.sum(), m_lost.sum(), tie.sum())}")
    print(f"    accuracy of the win chances (Brier, lower is better): engine {be:.4f}, closing line {bm:.4f}")
    if (~agree).any():
        print(f"    engine picked the market underdog {int((~agree).sum())} times: "
              f"{record(int(won[~agree].sum()), int(lost[~agree].sum()), int(tie[~agree].sum()))}")
    pick_p = np.where(pe > .5, pe, 1 - pe)
    mkt_p = np.where(pe > .5, pm, 1 - pm)
    edge = pick_p - mkt_p
    big = edge >= 0.05
    if big.any():
        ml = np.where(pe > .5, d["home_moneyline"].values, d["away_moneyline"].values).astype(float)
        payout = np.where(ml > 0, ml / 100, 100 / -ml)
        profit = np.where(won, payout, np.where(tie, 0.0, -1.0))  # a tie is a push
        print(f"    picks where the engine was 5+ points more confident than the close: "
              f"{record(int(won[big].sum()), int(lost[big].sum()), int(tie[big].sum()))}, "
              f"{profit[big].sum():+.2f} units at closing odds ({profit[big].mean():+.1%} per bet)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--picks", help="picks CSV (default results/nfl_cfbmethod_<season>_week<WW>_picks.csv)")
    ap.add_argument("--games-csv", help="local nflverse games.csv instead of downloading it")
    ap.add_argument("--out", default=os.path.join(ROOT, "results"), help="where the graded file and scorecard go")
    a = ap.parse_args()
    picks_path = a.picks or os.path.join(ROOT, "results", f"nfl_cfbmethod_{a.season}_week{a.week:02d}_picks.csv")
    picks = pd.read_csv(picks_path, dtype={"game_id": str})
    espn = espn_week(a.season, a.week)
    mk = market_table(a.games_csv)
    mk = mk[(mk["season"] == a.season) & (mk["week"] == a.week)]
    rows = []
    for r in picks.itertuples():
        g = espn.get(r.game_id)
        if g is None or g["state"] != "post":
            print(f"  {r.away_name} at {r.home_name}: not final yet")
            continue
        m = mk[(mk["home_team"] == g["home_abbr"]) & (mk["away_team"] == g["away_abbr"])]
        hml = m["home_moneyline"].iloc[0] if len(m) else np.nan
        aml = m["away_moneyline"].iloc[0] if len(m) else np.nan
        home_win = outcome(g["home_score"], g["away_score"])
        winner = r.home_name if home_win == 1 else (r.away_name if home_win == 0 else "Tie")
        mp = no_vig(hml, aml) if pd.notna(hml) and pd.notna(aml) else np.nan
        rows.append({"season": a.season, "week": a.week, "game_id": r.game_id, "away": r.away_name, "home": r.home_name,
                     "away_score": g["away_score"], "home_score": g["home_score"], "winner": winner,
                     "status": r.status, "reason": r.reason if isinstance(r.reason, str) else "",
                     "pick": r.pick if r.status == "PICK" else "", "pick_prob": r.pick_prob if r.status == "PICK" else np.nan,
                     "p_home": r.p_home,
                     "result": ("T" if winner == "Tie" else "W" if r.pick == winner else "L") if r.status == "PICK" else "",
                     "home_moneyline": hml, "away_moneyline": aml, "market_p_home": mp,
                     "market_p_pick": (mp if r.pick == r.home_name else 1 - mp) if r.status == "PICK" and pd.notna(mp) else np.nan,
                     "home_win": home_win})
    if not rows:
        print("Nothing final to grade yet.")
        return
    wk = pd.DataFrame(rows)
    wk["edge_vs_close"] = wk["pick_prob"] - wk["market_p_pick"]
    out = os.path.join(a.out, f"nfl_cfbmethod_{a.season}_week{a.week:02d}_graded.csv")
    wk.to_csv(out, index=False)
    card_path = os.path.join(a.out, "nfl_scorecard.csv")
    card = pd.read_csv(card_path, dtype={"game_id": str}) if os.path.exists(card_path) else pd.DataFrame()
    if len(card):
        card = card[~((card["season"] == a.season) & (card["week"] == a.week))]
    card = pd.concat([card, wk], ignore_index=True)
    card.to_csv(card_path, index=False)
    graded = wk[wk["status"] == "PICK"]
    print(f"Week {a.week}: {record((graded.result == 'W').sum(), (graded.result == 'L').sum(), (graded.result == 'T').sum())} "
          f"(no picks: {(wk.status != 'PICK').sum()})")
    for t in graded.sort_values("pick_prob", ascending=False).itertuples():
        mkt = f"close {t.market_p_pick:.0%}" if pd.notna(t.market_p_pick) else "no closing line"
        print(f"  {t.result}  {t.pick} {t.pick_prob:.0%} ({mkt})  {t.away} {t.away_score}, {t.home} {t.home_score}")
    print("\nClosing-line check (a scorecard only; lines never feed the picks):")
    compare(graded, f"Week {a.week}")
    allp = card[card["status"] == "PICK"]
    compare(allp, "All graded weeks")
    print(f"\nSaved {out} and {card_path}")


if __name__ == "__main__":
    main()
