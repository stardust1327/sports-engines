# The exact college engine as run on Saturday, 2026-10-10

These are the scripts, unchanged, that produced the college picks sent before
the 12:30 PM (Phoenix) kickoffs on 2026-10-10. `cfb/` one folder up is the same
method packaged to run on any date; this folder is the reference copy.

Files:

- `ids.py`: lists finished games from ESPN weekly scoreboards
- `parse.py`: turns ESPN game summaries into play, game and passer tables
- `epa.py`: fits the expected points model, computes EPA and success, flags garbage time
- `final.py`: ratings, backtest, calibration and picks (the engine)
- `today.py`: builds the day's game list (the 23 games from 12:30 PM on were hardcoded)
- `qbs.py`: each team's starting quarterback history, for the manual QB check
- `grade.py`: grades the picks against final scores
- `picks_raw_2026-10-10.csv`: the engine's output that morning

## Commands, in order

```
# 1. ESPN scoreboards, regular season weeks 1-16, FBS (groups=80), for 2025 and 2026
curl "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=$YEAR&seasontype=2&week=$WEEK&groups=80&limit=400" -o raw/sb/sb_${YEAR}_w${WEEK}.json
python3 -I scripts/ids.py raw/sb ids.csv

# 2. Every finished game's summary (play-by-play)
cut -d, -f1 ids.csv | xargs -P 16 -I{} curl -s "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={}" -o raw/summ/{}.json

# 3. Same two steps for 2024 into raw/sb24, raw/summ24, ids24.csv

# 4. Parse each set, then combine 2024 + 2025 + 2026 into data3/
python3 -I scripts/parse.py raw/summ ids.csv data
python3 -I scripts/parse.py raw/summ24 ids24.csv data24
#    (games, plays and passers parquet files concatenated into data3/)

# 5. Expected points and EPA on all three seasons
python3 -I scripts/epa.py data3

# 6. Backtest 2025 week by week (2024 as the starting point), weight on last season 0, 0.3, 0.5, 0.7
python3 -I scripts/final.py data3 backtest

# 7. Day's games (scoreboard for 20261010 saved at 9:41 AM), then picks with weight 0.7
python3 -I scripts/today.py raw/sb_today.json data/today_games.csv
python3 -I scripts/final.py data3 predict 0.7 data/today_games.csv data/picks_raw.csv

# 8. Quarterback check: 2026 passers (passers.parquet joined to games, 2026 only) -> passers26.csv
python3 -I scripts/qbs.py data/passers26.csv data/today_games.csv data/qb_summary.csv
```

Step 8 flags teams whose starter changed; each flagged team was checked in the
news. Four games became no-picks:

- UCLA at Oregon: Oregon QB Dante Moore ruled out; Dylan Raiola (36 throws) started
- Tennessee at Arkansas: George MacIntyre's first career start (20 throws)
- Ole Miss at Vanderbilt: Jared Curtis listed probable, so the starter wasn't confirmed
- Virginia Tech at Cal: Jaron-Keawe Sagapolutele questionable (concussion protocol)
