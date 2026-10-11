# sports-engines

Win-probability engines for **college football** and the **NFL**, built from
play-by-play data. They rate every team by how efficient it is on each play,
adjusted for the opponent, and turn that into a win chance for each game.

**What goes in:** play-level EPA (expected points added) and success rate,
home field, and rest days (NFL).
**What never goes in:** betting lines, records, yards, points scored, or
narrative. Final scores are used only to check and calibrate the engines.
**Missing data means no pick:** a team without enough play-by-play, or a
starting QB with too little history, gets a no-pick with the reason.

## How each engine works

| | College football (`cfb/`) | NFL (`nfl/`) |
|---|---|---|
| Data | ESPN play-by-play, last 3 seasons | nflverse play-by-play, last 5 seasons |
| Ratings | Offense and defense EPA + success rate, opponent-adjusted | Pass offense (team + QB) and rush offense vs defense, opponent-adjusted |
| Starting point | 70% of last season's rating, updated with this season's plays | 45% of last season's rating, updated with this season's plays |
| Calibration | Walk-forward backtest of last season | Walk-forward backtest of the last two seasons |
| No-pick rule | Team has under 150 non-garbage plays this season | Starting QB has under 100 dropbacks in the last 3 seasons |
| QB check | Manual: the run lists teams whose QB situation changed | Starters come from nflverse; override with `--qb` |

## Running it

Needs Python 3.10+.

```
pip install -r requirements.txt

# College football: every game on a date that hasn't kicked off
python3 cfb/run.py --date 2026-10-17
python3 cfb/run.py --date 2026-10-17 --nopick "Oregon=starting QB ruled out"

# NFL: one week
python3 nfl/run.py --season 2026 --week 6
python3 nfl/run.py --season 2026 --week 6 --qb "SEA=Sam Darnold" --nopick "CHI=starter questionable"
```

Each run prints the picks grouped by confidence, the backtest record, this
season's out-of-sample record, and the starting QBs it used. It saves
`results/<sport>_<date or week>_picks.csv` and a matching `_qbs.csv`.

The first college run downloads about 1 GB of ESPN game files into
`cfb/cache/` (a few minutes); later runs only fetch new games. Kickoff times
print in Phoenix time; change with `--tz`.

**Before trusting a run, check the quarterbacks.** The engines can't read
injury reports. Look up every flagged team (and, for the NFL, every starter)
in the final injury report, then rerun with `--nopick` (college) or `--qb`
(NFL) as needed.

## How far to trust it

Only the high-confidence tier has held up. As of October 10, 2026:

- **College:** 2025 backtest, weeks 4-8: 70%+ picks 100-21, 60-70% picks
  31-25, under-60% picks 25-28. 2026 weeks 4-5 out of sample: 70%+ 38-8,
  60-70% 10-7, under 60% 11-10. Live on 2026-10-10: 70%+ 6-1, 60-70% 3-5,
  coin flips 2-2.
- **NFL:** 2024-25 backtest (469 games): 70%+ picks won 77%, 60-70% won 67%,
  under 60% won 54%. 2026 weeks 1-4 out of sample: 60%+ picks 19-7, under 60%
  13-21 (32-28 overall).

Betting markets already price most of what these engines know, so a high win
chance is not the same as a good bet. See `results/RESULTS.md` for the running
record.
