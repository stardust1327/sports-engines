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
