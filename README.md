# sports-engines

Win-probability engines for **college football** and the **NFL**, built from
play-by-play data. They rate every team by how efficient it is on each play,
adjusted for the opponent, and turn that into a win chance for each game.

**What goes in:** play-level EPA (expected points added) and success rate,
and home field.
**What never goes in:** betting lines, records, yards, points scored, or
narrative. Final scores are used only to check and calibrate the engines.
**Missing data means no pick:** a team without enough play-by-play, or a
starting QB who is out or unconfirmed, gets a no-pick with the reason.

## Start here

- `METHOD.md`: the locked method (exactly what made the 2026-10-10 college picks)
- `CLAUDE.md`: the owner's rules. The method doesn't change, and new models don't
  deviate from it, without the owner's approval.
- `cfb/original_2026-10-10/`: the exact scripts as run that morning
- `cfb/`: the same method packaged to run on any date
- `nfl_cfbmethod/`: the NFL version: the same method and `cfb/` code, with three
  approved NFL settings (end of `METHOD.md`); `grade.py` grades each week and runs
  the closing-line check
- `prompt_football/nfl.py`: the owner's "Prompt Football" prompt (trenches 25%,
  net efficiency 25%, passing 20%, situational 15%, high leverage 15%) scored with
  play-by-play numbers, for comparison with the engine. It's separate from the
  locked method; how each criterion is measured is at the top of the file

## How each engine works

| | College football (`cfb/`) | NFL (`nfl_cfbmethod/`) |
|---|---|---|
| Data | ESPN play-by-play, last 3 seasons | ESPN play-by-play since 2018 |
| Ratings | Offense and defense EPA + success rate, opponent-adjusted (ridge penalty 50) | Same (ridge penalty 500) |
| Starting point | 70% of last season's rating | 30% of last season's rating |
| Recency | Every play this season counts the same | Plays count half as much for every 5 weeks older |
| Calibration | Last season's week-by-week replay, weeks 4-8 | Every season's replay since 2019, weeks 4-18 |
| No-pick rules | Under 150 plays this season; starting QB out or unconfirmed | Same |

## Running it

Needs Python 3.10+.

```
pip install -r requirements.txt

# College football: every game on a date that hasn't kicked off
python3 cfb/run.py --date 2026-10-17
python3 cfb/run.py --date 2026-10-17 --nopick "Oregon=starting QB ruled out"

# NFL: college method with the approved NFL settings (team nicknames for --nopick)
python3 nfl_cfbmethod/run.py --date 2026-10-18 --date 2026-10-19 --nopick "Ravens=starting QB out"

# NFL: grade a week after it's played, with the closing-line check (scorecard only)
python3 nfl_cfbmethod/grade.py --season 2026 --week 5
```

Each run prints the picks grouped by confidence, the backtest record, this
season's out-of-sample record, and the starting QBs it used. It saves
`results/<sport>_<date or week>_picks.csv` and a matching `_qbs.csv`.

The first college run downloads about 1 GB of ESPN game files into
`cfb/cache/` (a few minutes); later runs only fetch new games. Kickoff times
print in Phoenix time; change with `--tz`.

**Before trusting a run, check the quarterbacks.** The engines can't read
injury reports. Look up every flagged team (and, for the NFL, every starter)
in the final injury report, then rerun with `--nopick` for any game whose
regular starter is out or unconfirmed.

## How far to trust it

Only the high-confidence tiers have held up:

- **College:** 2025 backtest, weeks 4-8: 70%+ picks 100-21, 60-70% picks 31-25,
  under-60% picks 25-28. Live on 2026-10-10: 70%+ 6-1, 60-70% 3-5, coin flips 2-2.
- **NFL:** 2019-2025 backtest (1,522 games): 963-559 overall; 70%+ picks 271-93,
  60-70% 305-161, under 60% 387-305. The closing line was still more accurate,
  and the engine's picks against the market favorite went 119-180.

Betting markets already price most of what these engines know, so a high win
chance is not the same as a good bet. See `results/RESULTS.md` for the running
record.
