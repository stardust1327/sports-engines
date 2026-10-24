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

- `CHECKINS.md`: the runbook the scheduled check-ins follow (grading, weekly runs,
  QB checks, PDFs), with the helper scripts in `results/` (`whats_next.py`,
  `grade_picks.py`, `set_nopick.py`, `merge_rerun.py`, `make_report.py`)
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
- `prompt_football/cfb.py`: the same framework for college football (built
  2026-10-11), on the college engine's play-by-play; the differences the college
  data forces are listed at the top of the file.
  `results/compare_cfb_engine_vs_framework.py` compares it with the engine on
  the same games
- `results/team_notes.json` and `results/team_notes.py`: the owner's NFL team
  notes (added 2026-10-12, **turned off by the owner 2026-10-17**; kept as a
  record, applied nowhere). From watching the games, the owner marks a team
  unreliable (docked points on its predicted margin in both NFL models) or max
  effort (slightly boosted); official picks include the note, the model-alone
  numbers stay beside it, and every noted game is graded
  (`team_notes_graded.csv`) to track whether the notes are right. A note runs
  out 3 weeks after the owner's last read on that team unless renewed

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

# College: the Prompt Football framework on the same dates (same --nopick rules)
python3 prompt_football/cfb.py --date 2026-10-17 --nopick "Oregon=starting QB ruled out"

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

Multi-season backtests from the 2026-10-24 audit (`results/audit_2026-10-24/`),
every game predicted only from what was known before it (approved by the owner
2026-10-24):

| Model | Record | Weeks 4-8 | 70%+ picks | 60-70% picks | Under 60% |
|---|---|---|---|---|---|
| College engine, 2021-2025 | 1945-834 (70.0%) | 771-375 (67.3%) | 1043-247 (80.9%) | 473-258 (64.7%) | 429-329 (56.6%) |
| College framework, 2021-2025 | 1873-906 (67.4%) | 738-408 (64.4%) | 879-228 (79.4%) | 507-256 (66.4%) | 487-422 (53.6%) |
| NFL engine, 2016-2025 | 1332-809 (62.2%) | 437-278 (61.1%) | 374-123 (75.3%) | 445-223 (66.6%) | 513-463 (52.6%) |
| NFL framework, 2022-2025 | 558-335 (62.5%) | 169-127 (57.1%) | 172-59 (74.5%) | 197-102 (65.9%) | 189-174 (52.1%) |

- The college engine is run the way it picks live (calibrated on the season
  before). The NFL engine is each season calibrated on the other nine; on
  2016-2018, seasons never used to choose its settings, it went 60.9%. The
  frameworks use each team's previous starter at QB, as live picks do.
- Weeks 4-8 are the hardest part of the year for every model, so judge
  October results against that column.
- Only the 70%+ picks are reliably better than a lean; under 60% is close to a
  coin flip.
- The closing line is still more accurate (NFL 2019-2025: the closing-line
  favorite went 1024-498 on the engine's games), and the engine's picks
  against the market favorite went 119-180. Betting markets already price most
  of what these engines know, so a high win chance is not the same as a good
  bet. See `results/RESULTS.md` for the running record.
