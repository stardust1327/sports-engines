# The method (locked)

This is exactly how the 2026-10-10 college football picks were made. The
original scripts are in `cfb/original_2026-10-10/`. **Nothing here changes
without the owner's approval, and every new model follows this structure
unless the owner approves a deviation.**

## 1. What goes in

- ESPN play-by-play (game summaries) for regular-season games of the current
  season and the two seasons before it. Only games finished before the first
  kickoff being predicted.
- Nothing else. No betting lines or odds, records, yards, points scored,
  rankings or narrative. Final scores are used only as the target the win
  probabilities are calibrated against, and the score margin only to spot
  garbage time.

## 2. Plays

Scrimmage plays only: passes (receptions, incompletions, sacks, passing
touchdowns, interceptions), runs (rushes, rushing touchdowns) and fumbles,
on downs 1-4, first and second halves (no overtime), with 1-99 yards to goal.

## 3. Expected points, EPA and success

- **Expected points (EP):** a gradient-boosted model (300 rounds, learning rate
  0.08, 31 leaves, at least 300 plays per leaf) predicts the next score in the
  same half (touchdown 7, field goal 3, safety 2; negative when the opponent
  scores; 0 if nobody scores before the half ends) from down, distance (capped
  1-30), yards to goal and seconds left in the half. It is fit on all three
  seasons of plays.
- **EPA:** EP after the play minus EP before. An offensive touchdown counts as
  +7, a defensive touchdown -7, a safety -2, and a change of possession flips
  the sign. EPA is capped at ±10 for the ratings.
- **Success:** at least 50% of the distance on 1st down, 70% on 2nd, 100% on 3rd
  or 4th, or an offensive touchdown. Turnovers are failures.
- **Garbage time (thrown out):** score margin before the play over 38 in the
  2nd quarter, over 28 in the 3rd, over 22 in the 4th.

## 4. Team ratings

- Ridge regression (penalty 50) on every non-garbage scrimmage play: each play's
  value = offense rating + defense rating + home-field term. Fit once on EPA and
  once on success, so every team gets four numbers.
- **Starting point:** last season's ratings (the same fit on all of last season),
  weighted 70%. This season's plays move each team from there.
- **No pick** if a team has fewer than 150 non-garbage offensive plays this
  season.

## 5. Win probability

- Three numbers per game: the home team's EPA edge and success edge (its offense
  plus what the opponent's defense allows, minus the reverse), and home field
  (0 at a neutral site).
- A logistic regression with no intercept turns them into a win chance. It is
  fit on a week-by-week replay of last season, where each week is predicted
  only from plays before it (with the season before as the starting point).
  While the current week is 8 or earlier, only last season's weeks 4-8 are used.

## 6. Quarterback rule (checked by hand)

Each team's starting QB is checked in the news before posting. **No pick** if
the regular starter is out, the starter is questionable or unconfirmed, or the
starter is making a first start with very little playing time.

## 7. Output

The pick is the team with at least a 50% win chance, grouped as 70%+
(strongest), 60-70% (leans) and under 60% (coin flips), with every no-pick and
its reason. Picks are logged in `results/` before kickoff and graded after.

## NFL version (`nfl_cfbmethod/`): approved NFL settings

The NFL version runs the college code above unchanged except for the settings
the owner approved on 2026-10-11 (`nfl_cfbmethod/nfl_engine.py`), each chosen
on a week-by-week backtest of the 2019-2025 NFL seasons (1,522 games, weeks
4-18, each season graded with a calibration fit on the other seasons):

| Setting | College (locked) | NFL (approved) |
|---|---|---|
| Ridge penalty | 50 | 500 |
| Weight on last season's ratings | 70% | 30% |
| Recency within the season | none (every play counts the same) | plays count half as much for every 5 weeks older |
| Calibration games | last season, weeks 4-8 (~230 college games) | every season since 2019, weeks 4-18 (~1,500 games) |

Data is ESPN's NFL play-by-play from 2018 through the current season (2018 is
the starting point for the 2019 replay), and the expected points model is fit
on all of it. These NFL settings are locked the same way as the college method.

**Backtest with these settings:** 963-559 (63%). 70%+ picks 271-93 (74%),
60-70% 305-161 (65%), under 60% 387-305 (56%). Every season landed between 61%
and 68%. With the unchanged college settings it was 128-91 on 2025, and its
early-season win chances scored worse than a coin flip.

**Closing-line check (scorecard only; lines never feed a pick):** over the same
1,522 games, the closing line was more accurate than the engine (Brier 0.2087
vs 0.2264). Taking the closing-line favorite went 1024-498. When the engine
picked the market underdog it went 119-180, and picks where the engine was 5+
points more confident than the close went 207-245, losing 7.3% per bet at
closing odds. `nfl_cfbmethod/grade.py` runs this check on every graded week.

The earlier quarterback version (`nfl/`) was retired: on the same 387 games of
2024-25, a tuned version of this method picked 67.2% of winners against its
66.1%, and averaging the two didn't pick more winners.

## Owner's team notes (NFL, approved 2026-10-12; turned off 2026-10-17)

**Turned off by the owner on 2026-10-17** ("Turn it off and drop the page"),
after the Bills and Rams notes were cleared before any noted game was played.
No note applies to any pick, record or PDF. The description below is kept as a
record of what ran from 2026-10-12 to 2026-10-17; it never touched the method
above.

At the owner's request, official NFL picks also carry the owner's manual team
notes (`results/team_notes.json`, applied by `results/team_notes.py`). This sits
on top of the method above and changes nothing in it: the engine's code, inputs
and win chances are untouched and kept in every file as the "model alone".

- **Unreliable** (the owner's call from watching the games, case by case): a
  team that doesn't want to win or looks lazy, whose earlier results came from
  luck rather than effort, so it loses games it shouldn't. Losing a game alone
  doesn't qualify. Docked 3 points by default.
- **Max effort** (same): a team that plays hard and aggressive and is out there
  to win. Slightly boosted, 1.5 points by default.
- The note moves the team's predicted margin by its points. The engine's win
  chance moves along its own scale: 7.8 points per unit of log-odds, the slope
  of the final margin on the engine's log-odds over the 2019-2025 backtest
  (1,522 games). The framework moves its predicted margin by the points and
  follows its own margin-to-win-chance scale. A note counts only for games
  kicking off after it was set, and runs out 21 days after the owner's last read
  on that team unless the owner renews it.
- Notes are for what the plays can't show (effort, attitude). The engine
  already rates every play, so a bad game lowers a team's numbers on its own;
  the scorecard shows whether a note adds anything on top of that.
- The official pick is the team at 50% or more after the notes. A note is graded
  on every pick involving the team: record, wins and points per game against what
  the model alone expected (with the range luck alone covers), accuracy of the
  win chances with and without the note, and picks the note changed.
