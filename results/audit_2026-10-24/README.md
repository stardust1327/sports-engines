# Backtest audit, 2026-10-24 (owner's request)

The owner's question: the models were backtested around 63%, the NFL framework's
first live week went 9-2-1, and recent weeks have looked bad. Is something off?
Asked for: a backtest over at least 4-5 seasons of NFL and college games.

Nothing in `cfb/`, `nfl_cfbmethod/` or `prompt_football/` was changed. Every
script here imports that code as it is. No betting lines anywhere.

## 1. Multi-season backtests (every game predicted only from earlier plays)

| Model | Seasons | Record | By season | Weeks 4-8 | Weeks 9+ |
|---|---|---|---|---|---|
| College engine | 2021-2025 | 1945-834 (70.0%) | 68.0-71.7% | 67.3% | 71.9% |
| College framework | 2021-2025 | 1873-906 (67.4%) | 64.3-70.1% | 64.4% | 69.5% |
| NFL engine | 2016-2025 | 1332-809 (62.2%) | 53.9-68.6% | 62.3%* | 63.3%* |
| NFL framework | 2022-2025 | 558-335 (62.5%) | 58.0-65.6% | 57.1% | 65.2% |

\* NFL engine weeks split from the strict version (2017-2025, each season
calibrated only on the seasons before it: 1218-717, 62.9%).

- **College engine:** run exactly as the live engine picks: three-season play
  window, calibration from the previous season's week-by-week replay (weeks 4-8
  while it's early, all weeks after). Its only earlier backtest was 2025, the
  season its ridge penalty was tuned on; 2025 came out 71.7% against 69.6% for
  the four seasons never used for tuning, so the tuning flattered it by about 2
  points at most. `cfb_engine_backtest.py`
- **NFL engine:** reproduces `nfl_cfbmethod/run.py` exactly (2019-2025, 968-554).
  2016-2018 were never used to pick the NFL settings: with the live calibration
  they went 377-242 (60.9%). `nfl_engine_backtest.py`
- **Frameworks:** both backtests score the passing matchup with the QB who threw
  the most passes in that game, which is only known afterwards. Replayed with
  the team's previous starter instead (what a live pick uses), nothing material
  changes: NFL 558-335 both ways, college 2021-2025 67.4% vs 67.5%. The college
  framework's replay was also run back to 2021 (its own file covers 2022-2025).
  The NFL framework can't go before 2022: its blitz numbers start then.
  `framework_qb_check.py`
- **Stated win chances are honest** (stated vs how often the pick won): NFL
  engine 70%+ 77% vs 74%, 60-70% 65% vs 65%, under 60% 55% vs 54%; college
  engine 70%+ 81% vs 81%, 60-70% 65% vs 65%, under 60% 55% vs 57%.

## 2. Are the live picks what the backtested code picks?

Yes. 2026 replayed with the backtest code, game by game against the logged picks:
NFL engine 28 of 28 the same pick (largest win-chance gap 0.5 points); college
engine 70 of 71 (the one difference is a 50.7% vs 49.3% coin flip; the small gaps
come from midweek games that were in the live data and not in a week-by-week
replay). `cfb_live_vs_replay.py`, `nfl_engine_backtest.py` (part C)

Every logged pick was also re-graded against ESPN's final scores: 0
differences. `live_scorecard.py`

ESPN's 2026 play-by-play has the same shape as 2022-2025 (plays per game,
success rate, pass share); college average EPA runs higher this season, which
the ratings absorb (they're relative to the league). `data_sanity.py`

## 3. Luck or a real gap?

| Live, 2026 (logged picks) | Record | Expected (sum of win chances) | Chance of this or worse |
|---|---|---|---|
| NFL engine | 11-11-1 | 14.8 wins | 17% |
| NFL framework | 15-7-1 | 14.5 wins | (better than expected) |
| College engine | 39-25 | 43.5 wins | 17% |
| College framework | 27-18 | 30.0 wins | 32% |

("Chance of this or worse" uses each model's weeks 4-8 backtest rate.) The
engines' replays of every 2026 game are inside their usual early-season range:
college 65.3% in weeks 4-8 (2021-2025 range 64.4-70.9%), NFL 56.8% in weeks
4-7 (2016-2025 range 51.7-72.7%). In the NFL engine's backtest a quarter of all
weeks were 50% or worse and two such weeks in a row happened in 5% of week
pairs, about once a season. The framework's 9-2-1 Week 5 was the outlier on the
good side (its best backtest weeks hit 88%).

`luck_check.py`

## Re-run

From the repo root (data caches fill on the first run):

```
python3 results/audit_2026-10-24/cfb_engine_backtest.py
python3 results/audit_2026-10-24/nfl_engine_backtest.py
python3 results/audit_2026-10-24/framework_qb_check.py nfl
python3 results/audit_2026-10-24/framework_qb_check.py cfb
python3 results/audit_2026-10-24/cfb_live_vs_replay.py
python3 results/audit_2026-10-24/live_scorecard.py
python3 results/audit_2026-10-24/luck_check.py
python3 results/audit_2026-10-24/data_sanity.py
```
