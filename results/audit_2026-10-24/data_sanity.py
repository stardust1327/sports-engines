"""Is ESPN's 2026 play-by-play shaped like earlier seasons? A format change would
quietly degrade this season's ratings while the backtest (older seasons) looks fine."""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def stats(sport):
    sys.path[:0] = [os.path.join(REPO, "cfb")] + ([os.path.join(REPO, "nfl_cfbmethod")] if sport == "nfl" else [])
    for k in ["download", "engine", "epa", "parse"]:
        sys.modules.pop(k, None)
    import download, engine, epa, parse  # noqa: E401
    cache = os.path.join(REPO, "nfl_cfbmethod" if sport == "nfl" else "cfb", "cache")
    seasons = range(2022, 2027)
    rows = []
    for s in seasons:
        rows += download.final_games(cache, s, refresh=False)
    games, plays, _, _ = parse.parse(os.path.join(cache, "summary"), rows)
    sc = epa.build(plays, games)
    out = []
    for s in seasons:
        g = games[games.season == s]
        p = plays[plays.game_id.isin(g.game_id)]
        x = sc[sc.season == s]
        ng = x[~x.garbage]
        # only weeks 1-7 so every season is compared over the same part of the year
        e = x[x.week <= 7]
        out.append({
            "season": s, "games": len(g),
            "raw plays/game": round(len(p) / len(g), 1),
            "scrimmage plays/game": round(len(x) / x.game_id.nunique(), 1),
            "has down&dist %": round(100 * p.s_down.between(1, 4).mean(), 1),
            "start team set %": round(100 * (p.s_team != "").mean(), 1),
            "pass share %": round(100 * x.is_pass.mean(), 1),
            "mean EPA": round(ng.epa.clip(-10, 10).mean(), 3),
            "success %": round(100 * ng.success.mean(), 1),
            "garbage %": round(100 * x.garbage.mean(), 1),
            "home won %": round(100 * (g.home_score > g.away_score).mean(), 1),
            "wk1-7 success %": round(100 * e[~e.garbage].success.mean(), 1),
            "wk1-7 mean EPA": round(e[~e.garbage].epa.clip(-10, 10).mean(), 3),
        })
    for k in ["download", "engine", "epa", "parse"]:
        sys.modules.pop(k, None)
    sys.path[:] = [p for p in sys.path if not p.startswith(REPO)]
    return pd.DataFrame(out).set_index("season").T


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print("NFL (ESPN feed the engine uses)")
    print(stats("nfl").to_string())
    print("\nCollege (FBS)")
    print(stats("cfb").to_string())
