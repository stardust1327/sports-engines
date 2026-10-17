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

Only the high-confidence tiers have held up:

- **College:** 2025 backtest, weeks 4-8: 70%+ picks 100-21, 60-70% picks 31-25,
  under-60% picks 25-28. Live on 2026-10-10: 70%+ 6-1, 60-70% 3-5, coin flips 2-2.
- **NFL:** 2019-2025 backtest (1,522 games): 963-559 overall; 70%+ picks 271-93,
  60-70% 305-161, under 60% 387-305. The closing line was still more accurate,
  and the engine's picks against the market favorite went 119-180.

Betting markets already price most of what these engines know, so a high win
chance is not the same as a good bet. See `results/RESULTS.md` for the running
record.

## Parlay builder (dashboard)

`streamlit run app.py` opens a dashboard for the picks the engines save in `results/`.

**What it reads:**
- the college picks by date (`cfb_<date>_picks.csv`)
- the NFL picks by week (`nfl_cfbmethod_<season>_week<NN>_picks.csv`)
- the matching `_graded.csv` files, for results

**What it never does:** change a pick or a setting, or use a betting line. NFL picks are the engine's own: your team notes are turned off (2026-10-17), as in the PDFs.

**Tabs:**
- **Games:** every game on the chosen college day and NFL week, with:
  - the pick, its win chance and confidence tier
  - no-picks with the reason
  - results once graded
- **Build a parlay:** choose the number of legs and how to fill them (highest chances, lowest chances, a chance range, or teams you pick). It shows the parlay's chance to win and the fair odds that chance implies.
- **Recommended parlays:** up to 25 parlays, strongest first, under a redundancy limit: how many parlays a team may appear in, and how many legs any two parlays may share. It also shows:
  - the expected number of winning parlays
  - the chance at least one wins
  - for every pick, how many parlays lose if it loses
- **Track record:** graded picks by confidence tier.

**How the numbers are figured:** a parlay's chance is the product of its legs' win chances, since legs come from different games and are treated as independent. "Fair odds" are what that chance would pay with no sportsbook margin. A sportsbook pays less on every leg, and the closing line is still more accurate than the engines (see `results/RESULTS.md`), so this manages risk; it doesn't find an edge.

Install with `pip install -r requirements.txt` (plus `pip install pytest` for the tests in `tests/`). To deploy on Streamlit Community Cloud, use this repository, branch `main`, and main file `app.py`. New picks appear there whenever the check-ins push them to `results/`.
