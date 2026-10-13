# Running record

Every pick is logged before kickoff, graded after. One week is too small a
sample to judge an engine; the record means more as it grows.

## Against the moneyline (checked 2026-10-12)

Details, method and re-run steps: `moneyline/README.md`. Grading only; lines
never feed a pick. On every game each model rated out of sample, betting $100 on
every pick at the closing moneyline: NFL engine (2019-2025, 1,522 games) -3.4%,
NFL framework (2022-2025, 893) -4.6%, college engine (2024-2026, 1,256) -1.2%,
college framework (2022-2026, 2,356) -3.4%. That's about what betting every
favorite returns. All four pick fewer winners than the moneyline favorite, and
the closing line's win chances are more accurate than every model's.

## College football

### 2026-10-10 (23 games from the 12:30 PM Phoenix kickoffs on)

Files: `cfb_2026-10-10.csv` (engine), and `cfb_2026-10-10_picks_and_results.pdf` /
`cfb_2026-10-10_both_lists.csv` (every game, both lists, final scores)

| Tier | Record |
|---|---|
| 70%+ | 6-1 (only Toledo lost) |
| 60-70% | 3-5 |
| Under 60% (coin flips) | 2-2 |
| **Total** | **11-8** |

No picks (starting QB out or unconfirmed): Ole Miss at Vanderbilt, UCLA at
Oregon (UCLA won 17-15), Virginia Tech at Cal, Tennessee at Arkansas.

For comparison, a pick list from an earlier Claude chat (written without
numbers behind it) went 26-10 over 36 games that day. On the 19 games both
picked it went 15-4, and it won 5 of the 6 games where the two disagreed.

## NFL

### 2026 Week 5 (official): college method with the approved NFL settings

File: `nfl_cfbmethod_2026_week05_picks.csv`. Grade it after Monday night with
`python3 nfl_cfbmethod/grade.py --season 2026 --week 5`.

| Pick | Win chance |
|---|---|
| Rams over Bills (Monday) | 74.5% |
| Jaguars over Eagles (London) | 74.5% |
| Bengals over Dolphins | 74% |
| Patriots over Raiders | 70% |
| Texans over Titans | 64% |
| Cardinals over Lions | 59% |
| Vikings over Saints | 59% |
| Colts over Steelers | 58.5% |
| Jets over Browns | 56% |
| Commanders over Giants | 56% |
| Chargers over Broncos | 56% |
| Seahawks over 49ers | 55.5% |

No pick: Bears at Packers (Caleb Williams questionable, Tyson Bagent starts),
Ravens at Falcons (Lamar Jackson out, Tyler Huntley starts).

Result (Sunday graded 2026-10-11; Rams-Bills Monday pending): **6-4-1**.
Won: Jaguars, Bengals, Patriots, Texans, Vikings, Jets. Lost: Cardinals, Colts,
Chargers, Seahawks. Tie: Giants 27, Commanders 27. Closing-line favorite went
9-1-1 on the same games; the engine's 3 picks of the market underdog all lost.
Brier: engine 0.1842, closing line 0.1356. Graded with the tie fix to `grade.py`
(2026-10-11; before it, a tie was scored as an away-team win, so this printed
6-5). Graded file: `nfl_cfbmethod_2026_week05_graded.csv`.

### 2026 Week 5: Prompt Football framework (comparison run)

Files: `prompt_nfl_2026_week05.md` (picks in the prompt's format, with rationale,
parlay and backtest) and `prompt_nfl_2026_week05_picks.csv`. This is the owner's
five-criteria prompt scored with play-by-play numbers (`prompt_football/nfl.py`);
it went 558-335 (62.5%) on a 2022-2025 backtest, against the engine's 64.0% on
the same games.

| Pick | Win chance | Engine |
|---|---|---|
| Jaguars over Eagles (London) | 85% | agrees (74.5%) |
| Vikings over Saints | 76% | agrees (59%) |
| Bengals over Dolphins | 69% | agrees (74%) |
| Raiders over Patriots | 64% | Patriots 70% |
| Commanders over Giants | 63% | agrees (56%) |
| Steelers over Colts | 60% | Colts 58.5% |
| 49ers over Seahawks | 57% | Seahawks 55.5% |
| Jets over Browns | 57% | agrees (56%) |
| Lions over Cardinals | 56% | Cardinals 59% |
| Broncos over Chargers | 55% | Chargers 56% |
| Texans over Titans | 53% | agrees (64%) |
| Rams over Bills (Monday) | 53% | agrees (74.5%) |

Parlay ($25): Jaguars + Vikings + Bengals. Same no-picks as the engine.

Both sets side by side: `nfl_2026_week05_engine_vs_framework.pdf` (made by
`make_nfl_2026_week05_report.py`). The engine was re-run at 4:50 AM Sunday and
matched the logged picks exactly.

Result (Sunday; Rams-Bills Monday pending): **9-1-1**. Only loss: Raiders
(Patriots won 45-17). Tie: Commanders-Giants 27-27. Parlay (Jaguars + Vikings +
Bengals) hit. On the 5 games where the two models disagreed, the framework went
4-1 (Steelers, 49ers, Lions, Broncos right; Raiders wrong). Graded file:
`prompt_nfl_2026_week05_graded.csv`.

Earlier Week 5 runs, kept to compare after the games (all pending):

- `nfl_cfbmethod-3seasons_2026_week05_picks.csv`: first tuning (3 seasons, no
  recency): Jaguars 74%, Patriots 71%, Rams 71%, Bengals 69%, Texans 63%, ...
- `nfl_cfbmethod-untuned_2026_week05_picks.csv`: college settings unchanged:
  Jaguars 79%, Rams 67%, Patriots 62%, Broncos 61%, ...
- `nfl_2026_week05_picks.csv`: the retired quarterback version: Texans 72%,
  Jaguars 66%, Patriots 64%, Broncos 60%, ...

### 2026 Week 6 (logged Sunday night 2026-10-11, before QB reports)

PDF of Week 5 graded plus these picks and the midweek college picks:
`results_and_next_picks_2026-10-11.pdf` (made by `make_2026-10-11_report.py`).

Engine file: `nfl_cfbmethod_2026_week06_picks.csv`. Framework file:
`prompt_nfl_2026_week06_picks.csv`. Recheck QBs before each kickoff.

| Game | Engine | Framework |
|---|---|---|
| Seahawks at Broncos (Thu) | Seahawks 54% | Seahawks 50% |
| Texans vs Jaguars (London) | Jaguars 56% | Jaguars 74% |
| Titans at Colts | Colts 73% | Colts 56% |
| Jets at Patriots | Patriots 67% | **Jets 51%** |
| Saints at Giants | Giants 60% | Giants 59% |
| Panthers at Eagles | Panthers 57.5% | Panthers 61.5% |
| Cardinals at Rams | Rams 75% | Rams 74% |
| Chargers at Chiefs | Chiefs 61% | Chiefs 80% |
| Bills at Raiders | Bills 68% | Bills 59% |
| Cowboys at Packers | Packers 59% | Packers 53% |
| Commanders at 49ers (Mon) | 49ers 82% | 49ers 79% |

No pick (both): Bears at Falcons (Caleb Williams status unconfirmed), Ravens at
Browns (Lamar Jackson status unconfirmed), Steelers at Buccaneers (Baker
Mayfield, thumb, return unconfirmed).

Team note added Monday night 2026-10-12, before any Week 6 kickoff: the owner
marked the Rams unreliable, docked 3 points. Cardinals at Rams with the note:
engine **Rams 67%** (75% alone), framework **Rams 66%** (74% alone, predicted
Rams 26-21). The pick doesn't change; the Rams drop out of the 70%+ tier.

Second note, 9:33 PM: the Bills, max effort, slightly boosted 1.5 points. Bills
at Raiders with the note: engine **Bills 72%** (68% alone), framework **Bills
64%** (59% alone, predicted Bills 27-23). The pick doesn't change; the engine's
Bills move up into the 70%+ tier.

### Team notes (NFL, the owner's; added 2026-10-12)

`team_notes.json` (the notes), `team_notes.py` (how they're applied and
graded), `team_notes_graded.csv` (every graded pick with a noted team). From
watching the games, the owner marks a team by hand, case by case: unreliable
(docked) or max effort (slightly boosted). The note moves its predicted margin
in both models for games after it was set. Official picks and records include
the notes; the model-alone numbers stay beside them.

| Team | Note | Since | Graded games | Scorecard |
|---|---|---|---|---|
| Rams | Unreliable, -3 points | 2026-10-12 9:14 PM Phoenix | 0 | First noted game: Week 6, Cardinals at Rams |
| Bills | Max effort, +1.5 points | 2026-10-12 9:33 PM Phoenix | 0 | First noted game: Week 6, Bills at Raiders |

## College football midweek, 2026-10-13 to 10-16 (engine and framework)

Engine files: `cfb_2026-10-13_picks.csv` through `cfb_2026-10-16_picks.csv`.
Framework files: `prompt_cfb_2026-10-13_picks.csv` through
`prompt_cfb_2026-10-16_picks.csv`. Logged Sunday night 2026-10-11; QBs get
rechecked before each kickoff. Disagreements in bold.

| Game | Engine | Framework |
|---|---|---|
| Florida International at Jacksonville State (Tue) | Jacksonville State 63% | Jacksonville State 51% |
| Kennesaw State at Missouri State (Wed) | Missouri State 54% | Missouri State 60% |
| East Carolina at UAB (Thu) | East Carolina 59% | East Carolina 77% |
| Georgia Southern at Old Dominion (Thu) | Georgia Southern 75% | Georgia Southern 85% |
| Colorado State at Texas State (Thu) | Texas State 83% | Texas State 70% |
| Memphis at Tulane (Fri) | Memphis 73% | Memphis 86% |
| App State at Coastal Carolina (Fri) | Coastal Carolina 58% | **App State 65%** |

No pick (both), starter not yet named after a QB change in the last game:
Delaware at Middle Tennessee (Tue), Western Kentucky at Sam Houston (Wed),
Washington at Purdue (Fri). Rule used: a team whose last starter isn't its season leader
in attempts (the CHANGE flag) is a no-pick until the news names the starter. A
team whose last starter also leads it in attempts keeps its pick (East Carolina,
Colorado State and Old Dominion here).

## College Prompt Football framework (built 2026-10-11)

`prompt_football/cfb.py`: the owner's five criteria and weights, built the same
way as `prompt_football/nfl.py` but with the college play-by-play (the
differences the college data forces are listed at the top of the file). Replay
of 2022-2025, weeks 4-15, each season calibrated on the others: 1523-720
(67.9%). Home field is worth 2.45 points (conference games 2019, 2021-25).

Same games as the college engine (`cfb_engine_vs_framework_same_games.csv`, made
by `compare_cfb_engine_vs_framework.py`):

| Games both rated | Engine | Framework |
|---|---|---|
| 2025 weeks 4-15 (580) | 411-169 (70.9%) | 394-186 (67.9%) |
| 2026 so far (142) | 96-46 (67.6%) | 93-49 (65.5%) |

The engine's picks stay the official ones.
