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

## Backtest audit (owner's request, 2026-10-24)

The owner asked for at least 4-5 seasons of backtesting for both sports after
recent results looked off. Details, scripts and per-game files:
`audit_2026-10-24/README.md`. Nothing in the engines or frameworks changed.

- Multi-season backtests, every game predicted only from earlier plays: college
  engine 2021-2025 1945-834 (70.0%; weeks 4-8 67.3%), college framework
  2021-2025 1873-906 (67.4%; weeks 4-8 64.4%), NFL engine 2016-2025 1332-809
  (62.2%; 2016-2018, never used to pick its settings, 60.9%), NFL framework
  2022-2025 558-335 (62.5%; weeks 4-8 57.1%). Stated win chances match how often
  picks won in every tier.
- The college engine's earlier backtest covered only 2025, the season its
  ridge penalty was tuned on (2025: 71.7%; the four untuned seasons: 69.6%).
- The frameworks' backtests use the QB who actually played most in each game.
  With the previous game's starter instead (what live picks use): NFL 558-335
  either way, college 67.4% vs 67.5%. No material effect.
- Live picks match the backtest code: NFL engine 28 of 28 picks identical,
  college engine 70 of 71 (one 50.7% / 49.3% coin flip). Every logged grade
  re-checked against ESPN: no differences.
- Live so far vs expected (sum of win chances): NFL engine 11-11-1 vs 14.8,
  NFL framework 15-7-1 vs 14.5, college engine 39-25 vs 43.5, college framework
  27-18 vs 30.0. At each model's early-season backtest rate, the NFL and
  college engine records (or worse) come up about 1 time in 6. Verdict: no bug
  found; normal early-season variance, with the framework's 9-2-1 Week 5 the
  lucky outlier.

README "How far to trust it" now shows these multi-season numbers (owner
approved, 2026-10-24).

**Improvement tests (owner's question, same day):**
`proposals/improvement_tests_2026-10-24/README.md`. Tested on the same seasons:
college recency weighting, FCS-opponent down-weighting, separate pass and run
ratings (both sports), two-season calibration (college) and a 50/50
engine-framework blend (both sports). None picked more winners; two-season
calibration and the NFL blend made the win chances slightly more accurate with
the same picks. Nothing proposed for the locked method. When the two models
split, the engine has been right more often (college 57%, NFL 55%).

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

Final with Monday night (graded 2026-10-12 9:51 PM Phoenix): **6-5-1**. Lost
Rams 75% (Bills 37, Rams 34; closing line had the Rams at 62%). Closing-line
favorite 9-2-1 on the same 12 games. Brier: engine 0.2151, closing line 0.1566.
Picks where the engine was 5+ points more confident than the close: 1-4.
No team notes applied (both were set after kickoff). Report card:
`report_2026-10-12_week5-graded.pdf`.

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

Final with Monday night: **9-2-1**. Lost Rams 53% (Bills 37, Rams 34). The Rams
were the only Week 5 game where both models picked the same team and lost.

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

### 2026 Week 6 refreshed Thursday 2026-10-15 (after Wednesday's practice reports)

Run at the owner's request, 6:35 AM Phoenix. The Sunday-night run came before
Week 5's Monday game, so both models were re-run with it included (Bills 37,
Rams 34; nflverse play-by-play and FTN charting through Week 5) and merged with
`merge_rerun.py` (all 14 games still not started). PDF:
`report_2026-10-15_week6-picks.pdf`. Win chances include the owner's team notes;
splits in bold.

| Game | Engine (official) | Framework |
|---|---|---|
| Seahawks at Broncos (Thu) | **Seahawks 53.5%** | **Broncos 51.1%** (22-21) |
| Texans vs Jaguars (London) | Jaguars 56.5% | Jaguars 71.8% (27-20) |
| Titans at Colts | Colts 72.2% | Colts 58.0% (24-22) |
| Jets at Patriots | Patriots 66.5% | Patriots 52.8% (24-23) |
| Saints at Giants | Giants 59.6% | Giants 61.5% (25-22) |
| Panthers at Eagles | Panthers 57.6% | Panthers 62.3% (26-22) |
| Cardinals at Rams* | Rams 67.4% (75.2% alone) | Rams 67.1% (75.0% alone; 27-21) |
| Chargers at Chiefs | Chiefs 61.5% | Chiefs 79.5% (27-17) |
| Bills* at Raiders | Bills 71.3% (67.2% alone) | Bills 64.3% (59.7% alone; 28-23) |
| Cowboys at Packers | Packers 58.4% | Packers 55.6% (26-24) |
| Commanders at 49ers (Mon) | 49ers 82.7% | 49ers 78.7% (29-19) |

\* The owner's team notes: Rams unreliable -3, Bills max effort +1.5. Neither
changes a pick.

No pick (both), from the official practice reports through Wednesday:
- Bears at Falcons: Caleb Williams (hamstring) Week 6 status unconfirmed: full in
  Wed estimated practice report, coach says it will be close.
- Ravens at Browns: Lamar Jackson (ankle) Week 6 status unconfirmed: did not
  practice Wed.
- Steelers at Buccaneers: Baker Mayfield (thumb) did not practice Wed; return
  unconfirmed (Jalon Daniels started the last 2).

Changes from Sunday night: the framework flipped two coin flips, Jets to
**Patriots 52.8%** (now agrees with the engine) and Seahawks to **Broncos 51.1%**
(now the only split). The engine's picks are unchanged; every win chance moved
less than a point. Same three no-picks, reasons updated.

QB check: every other starter is off the report or practiced fully on Wednesday
(full with an injury listed: Michael Penix Jr. rib, Bryce Young knee, Daniel Jones
ankle, Patrick Mahomes knee, Drake Maye shoulder, Tyler Shough hand, Jalen Hurts
calf). Thursday's game: Sam Darnold and Bo Nix are off the final report.
Commanders and 49ers (Monday) hadn't posted a report as of Wednesday evening. The
Friday lock settles Williams, Jackson and Mayfield.

### 2026 Week 6: Thursday night graded, picks refreshed Thursday 2026-10-15 evening

Run at the owner's request, 9 PM Phoenix, after Thursday's practice reports.
PDF: `report_2026-10-15_thursday-night.pdf`.

**Thursday night: Broncos 17, Seahawks 14 (OT).** Engine (official) Seahawks
53.5%: lost. Framework Broncos 51.1%: won. The closing line had the Seahawks at
58%, so the market favorite lost too. Sam Darnold and Bo Nix started, as
expected; no team note involved. Week 6 so far: **engine 0-1, framework 1-0**
(graded files `nfl_cfbmethod_2026_week06_graded.csv` and
`prompt_nfl_2026_week06_graded.csv`; the other 13 games pending).

**New no-pick: Panthers at Eagles.** The Eagles ruled Jalen Hurts out (blood
clot in his calf); Tanner McKee is expected to start. Both models had picked the
Panthers (engine 57.6%, framework 62.3%); both files now carry the no-pick.

Both models were re-run for the Sunday and Monday games with the four no-picks
and merged with `merge_rerun.py` (13 games, none started). The engine's ESPN
play-by-play now includes Thursday's game; nflverse's files didn't have it yet,
so the framework's numbers are unchanged. Every engine win chance moved less
than a point. Win chances include the owner's team notes; the models agree on
all 9 picks.

| Game | Engine (official) | Framework |
|---|---|---|
| Texans vs Jaguars (London) | Jaguars 56.6% | Jaguars 71.8% (27-20) |
| Titans at Colts | Colts 72.6% | Colts 58.0% (24-22) |
| Jets at Patriots | Patriots 66.5% | Patriots 52.8% (24-23) |
| Saints at Giants | Giants 59.9% | Giants 61.5% (25-22) |
| Cardinals at Rams* | Rams 67.2% (75.0% alone) | Rams 67.1% (75.0% alone; 27-21) |
| Chargers at Chiefs | Chiefs 61.6% | Chiefs 79.5% (27-17) |
| Bills* at Raiders | Bills 71.8% (67.8% alone) | Bills 64.3% (59.7% alone; 28-23) |
| Cowboys at Packers | Packers 58.5% | Packers 55.6% (26-24) |
| Commanders at 49ers (Mon) | 49ers 82.4% | 49ers 78.7% (29-19) |

\* The owner's team notes: Rams unreliable -3, Bills max effort +1.5. Neither
changes a pick.

No pick (both), from the practice reports through Thursday:
- Bears at Falcons: Caleb Williams (hamstring) Week 6 status unconfirmed: full
  practice Wed and Thu, but he says he still has medical protocols to complete
  and doesn't know if he'll play.
- Ravens at Browns: Lamar Jackson (ankle) Week 6 status unconfirmed: did not
  practice Wed or Thu.
- Panthers at Eagles: Jalen Hurts (blood clot in calf) ruled out by the Eagles;
  Tanner McKee expected to start.
- Steelers at Buccaneers: Baker Mayfield (thumb) did not practice Wed or Thu,
  Bucs OC says he's not quite ready this week; Jalon Daniels expected to start.

QB check: every other starter is off the report or practiced fully on Thursday
(full with an injury listed: Michael Penix Jr. ribs, Bryce Young knee, Daniel
Jones ankle, Patrick Mahomes knee, Drake Maye shoulder, Tyler Shough hand).
Monday's game: Jayden Daniels was a full participant in the Commanders' first
report; Brock Purdy isn't on the 49ers' report. Friday's game statuses (the
Friday lock) settle Williams, Jackson and Mayfield.

### 2026 Week 6 locked Friday 2026-10-16 (after the 1 PM Pacific game statuses)

Friday lock, scheduled check-in C. PDF: `report_2026-10-16_friday-lock.pdf`.
Both models re-run for the Sunday and Monday games with the no-picks (engine
re-run; framework with `--refresh` for this season's nflverse files) and merged
with `merge_rerun.py` (13 games, none started). **No pick changed and no win
chance moved**; the team notes still change no pick. Locked picks (win chances
include the owner's team notes; the models agree on all 9):

| Game | Engine (official) | Framework |
|---|---|---|
| Texans vs Jaguars (London) | Jaguars 56.6% | Jaguars 71.8% (27-20) |
| Titans at Colts | Colts 72.6% | Colts 58.0% (24-22) |
| Jets at Patriots | Patriots 66.5% | Patriots 52.8% (24-23) |
| Saints at Giants | Giants 59.9% | Giants 61.5% (25-22) |
| Cardinals at Rams* | Rams 67.2% (75.0% alone) | Rams 67.1% (75.0% alone; 27-21) |
| Chargers at Chiefs | Chiefs 61.6% | Chiefs 79.5% (27-17) |
| Bills* at Raiders | Bills 71.8% (67.8% alone) | Bills 64.3% (59.7% alone; 28-23) |
| Cowboys at Packers | Packers 58.5% | Packers 55.6% (26-24) |
| Commanders at 49ers (Mon) | 49ers 82.4% | 49ers 78.7% (29-19) |

\* The owner's team notes: Rams unreliable -3, Bills max effort +1.5.

No pick (both), from Friday's official game statuses:
- Bears at Falcons: Caleb Williams (hamstring) questionable on Friday's report:
  full practice all week, but he says he doesn't know yet if he's playing.
  Check-in F (Sunday inactives) settles it.
- Ravens at Browns: Lamar Jackson (ankle) ruled out; Tyler Huntley starts.
- Panthers at Eagles: Jalen Hurts (blood clot in calf) ruled out; Tanner McKee
  expected to start.
- Steelers at Buccaneers: Baker Mayfield (right thumb) ruled out; Jalon Daniels
  starts.

QB check: no other quarterback has a game status for Sunday (Michael Penix Jr.,
ribs, has no designation and is cleared to start; the Browns' Dillon Gabriel,
back, is out but Deshaun Watson starts). Monday's game statuses come Saturday;
Jayden Daniels and Brock Purdy have no injury news. Sunday's check (F) confirms
the early-game inactives and Williams; Monday's check (G) confirms Daniels and
Purdy.

### Team notes (NFL, the owner's; added 2026-10-12)

`team_notes.json` (the notes), `team_notes.py` (how they're applied and
graded), `team_notes_graded.csv` (every graded pick with a noted team). From
watching the games, the owner marks a team by hand, case by case: unreliable
(docked) or max effort (slightly boosted). The note moves its predicted margin
in both models for games after it was set. Official picks and records include
the notes; the model-alone numbers stay beside them.

Each note runs out 3 weeks after the owner's last read on that team unless the
owner renews it (added 9:41 PM at the owner's OK; `team_notes.py renew` logs a
new read and starts the clock over).

| Team | Note | Since | Runs out unless renewed | Graded games | Scorecard |
|---|---|---|---|---|---|
| Rams | Unreliable, -3 points | 2026-10-12 9:14 PM Phoenix | 2026-11-02 9:14 PM Phoenix | 0 | First noted game: Week 6, Cardinals at Rams |
| Bills | Max effort, +1.5 points | 2026-10-12 9:33 PM Phoenix | 2026-11-02 9:33 PM Phoenix | 0 | First noted game: Week 6, Bills at Raiders |

**Both notes cleared Saturday 2026-10-17, 1:05 AM Phoenix, at the owner's word**
("Can we remove the Bills and Rams owner note. I decided I don't like it"), before
any noted game kicked off, so neither note was ever graded. Week 6 official picks
are now the model-alone numbers; no pick changes: Cardinals at Rams, engine
**Rams 75.0%**, framework **Rams 75.0%** (was 67.2% / 67.1% with the note); Bills
at Raiders, engine **Bills 67.8%**, framework **Bills 59.7%** (was 71.8% / 64.3%).
No team notes are in force. PDF: `report_2026-10-17_nfl-week6-picks.pdf`
(re-made).

**Team notes turned off Saturday 2026-10-17, 1:10 AM Phoenix, at the owner's
word** ("Turn it off and drop the page"). No note applies to any pick, record or
PDF from here on, and the notes page is gone from the PDFs. Official NFL picks
are the engine's own. `team_notes.py` and `team_notes.json` stay in the repo as
a record. NFL Week 6 PDF re-made without the page.

**Week 6 re-run Saturday 2026-10-17, 6:45 PM Pacific, at the owner's request**
(lost copy). Both models re-run for the Sunday and Monday games (framework with
`--refresh`) and merged: no pick and no win chance changed. Monday statuses:
Jayden Daniels has no designation (Marcus Mariota out), Brock Purdy isn't on the
49ers' report; 49ers pick stands. Bears at Falcons stays a no pick: NFL Network
and ESPN sources say Caleb Williams is expected to start, but the Bears haven't
confirmed it; Sunday's inactives settle it. Latest PDF:
`report_2026-10-17_nfl-week6-picks-LATEST-saturday-night.pdf`.

**Sunday check-in (F), 2026-10-18 8:45 AM Pacific (early-game inactives).**
Caleb Williams is active and back as the Bears' starter (Bears inactives:
Case Keenum as emergency third QB, Tyson Bagent the backup; PFT and CBS
inactives tracker, Oct 18). **Bears at Falcons pick comes back**: both models
re-run for the Sunday and Monday games without that no pick (framework with
`--starter "CHI=Caleb Williams"`) and merged: engine **Falcons 69.5%**,
framework **Falcons 61.0%** (25-22). No other pick or win chance changed
(Texans-Jaguars was under way and stays as logged). Michael Penix Jr. (ribs)
active and starting for the Falcons. Still no pick: Ravens (Lamar Jackson out,
Huntley starts), Eagles (Jalen Hurts out, Tanner McKee starts), Buccaneers
(Baker Mayfield out, Jalon Daniels starts), all confirmed by the inactives.
Late games: no QB on the Chargers, Chiefs, Bills, Raiders, Cowboys, Packers,
Cardinals or Rams has a game status; Jacoby Brissett stays the Cardinals'
starter. Monday: Jayden Daniels has no designation (Marcus Mariota out);
check-in G confirms. PDF: `report_2026-10-18_nfl-week6-sunday.pdf`.

Week 5's Monday game (Bills 37, Rams 34) was the only Week 5 game where both
models picked the same team and lost (the Commanders-Giants tie aside). The
owner expected the Rams to lose, but the note was set after kickoff, so it
doesn't count for that game; a read sent before kickoff would have.

### 2026 Week 6 graded through Sunday (Monday 2026-10-19; Commanders at 49ers pending)

Graded Monday 7:50 AM Phoenix at the owner's request. PDF:
`report_2026-10-19_week6-graded.pdf`. ESPN's server was unreachable from that
session, so the final scores came from nflverse's schedule file (`games.csv`,
the same file `grade.py` reads the closing lines from); the grading itself is
the repo's `nfl_cfbmethod/grade.py` and `results/grade_picks.py`, unchanged. The
Tuesday run re-grades the whole week with ESPN after Monday night.

**Engine (official): 4-6.** Won: Bills 68%, Patriots 67%, Chiefs 62%, Packers
59%. Lost: Rams 75% (Cardinals 18, Rams 16), Colts 73% (Titans 26, Colts 20),
Falcons 69% (Bears 31, Falcons 23), Giants 60% (Saints 34, Giants 27), Jaguars
57% (Texans 34, Jaguars 31, London) and Seahawks 53% (Thursday; Broncos 17,
Seahawks 14, OT). Pending: 49ers 82%.

**Framework: 5-5.** Won: Broncos (Thursday, the only split), Patriots, Bills,
Chiefs, Packers. Lost: Jaguars, Falcons, Giants, Colts, Rams. Pending: 49ers
79%.

Closing-line check (grading only): the closing-line favorite also went 4-6 on
the engine's 10 graded games. Brier: engine 0.3073, closing line 0.2843. The
engine picked the market underdog twice (Packers won, Falcons lost); picks 5+
points more confident than the close went 1-2. All graded weeks: engine
10-11-1, closing-line favorite 13-8-1; Brier 0.2570 vs 0.2147.

Off the record (never in either record): both models would have taken the
Panthers (right; Panthers 25, Eagles 14), the Ravens (wrong; Browns 13, Ravens
10) and the Buccaneers (wrong; Steelers 26, Buccaneers 19), 1-2 each. Running
NFL total (`nopick_leans.py`): engine 1-4, framework 1-4.

Week 7 picks were not run in that session (the engine's play-by-play comes from
ESPN).

### 2026 Week 6 final (Tuesday run, 2026-10-20)

Graded Tuesday about 2:50 PM Phoenix at the owner's request. ESPN was still
unreachable (this session's network blocks `site.api.espn.com`, and PyPI too), so
the final scores again came from nflverse's `games.csv` through a wrapper that
hands them to the repo's `grade.py` and `grade_picks.py`, both unchanged. Only
the Monday game was new; the Sunday grades came out identical.

**Monday night: 49ers 23, Commanders 17.** Engine 49ers 82%: won. Framework
49ers 79%: won.

**Final: engine (official) 5-6, framework 6-5.** The framework's edge is the
Thursday split (Broncos).

Closing-line check (grading only): the closing-line favorite also went 5-6 on the
engine's 11 games. Brier: engine 0.2822, closing line 0.2635. The engine picked
the market underdog twice (1-1); picks 5+ points more confident than the close
went 2-2 (-0.79 units, -19.9% per bet). All graded weeks: engine 11-11-1,
closing-line favorite 14-8-1; Brier 0.2472 vs 0.2077; picks against the market
favorite 1-4; 5+ points more confident than the close 3-6 (-4.24 units).

Off the record: unchanged (Monday's game was a pick). Running NFL total
(`nopick_leans.py`): engine 1-4, framework 1-4.

Re-graded with ESPN's scores once ESPN was reachable again (about 3:02 PM): the
same 5-6 and 6-5, file for file.

### 2026 Week 7 (Tuesday run, 2026-10-20): framework first run (engine to follow)

Run Tuesday about 3 PM Phoenix at the owner's request. **The engine (official)
could not run**: its play-by-play comes from ESPN, which this session's network
blocks. The framework ran on nflverse data as usual, with two plumbing changes,
both outside `prompt_football/` (unchanged):
- pyarrow couldn't be installed (PyPI blocked), so the framework read nflverse's
  CSV releases of the same play-by-play and FTN charting tables instead of the
  parquet ones. Check: it reproduced the 2022-2025 backtest exactly (558-335,
  62.5%, Brier 0.2230).
- With no engine `_qbs.csv`, each team's expected starter is its last starter
  from nflverse play-by-play (most pass attempts in its last game, the same rule
  as `cfb/qbs.py`), passed with `--qbs`.

File: `prompt_nfl_2026_week07_picks.csv` (first run of the week, straight into
`results/`).

| Game (Phoenix kickoff) | Framework |
|---|---|
| Patriots at Bears (Thu 5:15 PM) | Bears 63% (26-22) |
| Steelers vs Saints (Paris, Sun 6:30 AM) | Steelers 63% (24-20) |
| 49ers at Falcons | 49ers 64% (26-21) |
| Browns at Titans | Browns 51% (23-22) |
| Colts at Vikings | Vikings 82% (27-15) |
| Dolphins at Jets | Jets 69% (26-20) |
| Broncos at Cardinals | Broncos 62% (25-21) |
| Packers at Lions | Lions 67% (28-22) |
| Rams at Raiders | Rams 63% (26-22) |
| Chiefs at Seahawks (Sun night) | Chiefs 63% (24-20) |

No pick (both models; the engine gets the same no-picks when it runs):
- Bengals at Ravens: Lamar Jackson (left ankle) Week 7 status unconfirmed:
  day-to-day, hasn't practiced since the Oct 4 injury; Jesse Minter says he could
  "potentially" practice this week (Oct 19). Tyler Huntley started the last 2.
- Buccaneers at Panthers: Baker Mayfield (dislocated right thumb) return
  unconfirmed: hasn't practiced since the injury, to be evaluated at Wednesday's
  practice; the Bucs are preparing for Jalon Daniels to start a 4th straight game
  (Oct 19).
- Giants at Texans: starter not named. Jameis Winston was benched for J.J.
  McCarthy during the Week 6 loss; John Harbaugh says the team is "honing in on a
  decision" (Oct 19).
- Cowboys at Eagles (Mon): Jalen Hurts (blood clots) on IR, expected to miss the
  rest of the season (NFL Network/ESPN, Oct 19); Tanner McKee makes his 2nd start.

QB check (news through Tuesday afternoon; the only report out is Monday's
estimate for the Thursday game): Drake Maye (right shoulder) full on the
Patriots' Monday estimate; Caleb Williams off the Bears' report. Daniel Jones
stays the Colts' starter (Shane Steichen, Oct 19; performance question, no
injury). Malik Willis (minor, undisclosed) "should be good" and was throwing
Monday (Jeff Hafley, Oct 19). Michael Penix Jr. visited the injury tent in Week
6, returned and finished ("Just say I am good"). Tyler Shough is playing through
two broken bones in his non-throwing hand. Patrick Mahomes played through his
knee listing in Week 6; Mike Macdonald kept Sam Darnold as QB1. No injury news
found for the other starters (Rodgers, Purdy, Burrow, Young, Stroud, Murray,
Geno Smith, Watson, Ward, Nix, Brissett, Love, Goff, Stafford, Cousins,
Prescott).

### 2026 Week 7 engine (official), Tuesday 2026-10-20, about 3:10 PM Phoenix

ESPN became reachable at about 3:02 PM (the owner allowed it in the account's
network settings), so the engine ran for 2026-10-22, 10-25 and 10-26 with the
four no-picks above (its first Week 7 run, straight into `results/`). Its QB
report gives the same expected starter for all 28 teams as the framework's run,
and the framework re-run with the engine's `_qbs.csv` (into `/tmp/rerun`) came
out byte-identical to the logged file, so nothing needed merging. Engine
backtest with today's data: 961-561 (70%+ 272-92, 60-70% 296-164, under 60%
393-305); 2026 so far out of sample 24-19.

Files: `nfl_cfbmethod_2026_week07_picks.csv` and `_qbs.csv` (engine),
`prompt_nfl_2026_week07_picks.csv` (framework). Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Patriots at Bears (Thu 5:15 PM) | Bears 50.1% | Bears 63% (26-22) |
| Steelers vs Saints (Paris, Sun 6:30 AM) | Steelers 60.5% | Steelers 63% (24-20) |
| 49ers at Falcons (10:00 AM) | 49ers 63.6% | 49ers 64% (26-21) |
| Browns at Titans (10:00 AM) | **Titans 50.7%** | **Browns 51%** (23-22) |
| Colts at Vikings (10:00 AM) | Vikings 58.0% | Vikings 82% (27-15) |
| Dolphins at Jets (10:00 AM) | Jets 75.6% | Jets 69% (26-20) |
| Broncos at Cardinals (1:05 PM) | **Cardinals 57.7%** | **Broncos 62%** (25-21) |
| Packers at Lions (1:25 PM) | Lions 58.0% | Lions 67% (28-22) |
| Rams at Raiders (1:25 PM) | Rams 79.3% | Rams 63% (26-22) |
| Chiefs at Seahawks (5:20 PM) | Chiefs 52.7% | Chiefs 63% (24-20) |

No pick (both), reasons as above: Bengals at Ravens, Buccaneers at Panthers,
Giants at Texans, Cowboys at Eagles. Off the record: engine Ravens 61%, Panthers
60%, Texans 73%, Cowboys 54%; framework Ravens 53%, Panthers 59%, Texans 70%,
Cowboys 51%.

The models agree on 8 of the 10 picks. The engine has two picks at 70%+ (Rams,
Jets); the framework has one (Vikings).

PDF: `report_2026-10-20_tuesday-run.pdf` (NFL Week 6 graded, last week's college
games graded 10-13 to 10-17, NFL Week 7 picks, college picks 10-20 to 10-23),
made with `make_report.py`.

**For the next check-ins:** Wednesday's practice reports settle Jackson and
Mayfield, plus the Giants' starter and Penix; Wednesday's report for the
Thursday game gives Maye's and Williams's statuses. A pick comes back only by
re-running both models without that no-pick (into `/tmp/rerun`, then
`merge_rerun.py`).

### 2026 Week 7 locked Saturday 2026-10-24 (owner's request; after Friday's game statuses)

Run Saturday about 4:30 AM Phoenix at the owner's request, as the Friday lock
(check-in C) for Sunday's games; no midweek or Friday check-in had been logged
since Tuesday. ESPN, nflverse and PyPI were all reachable. Both models re-run for
2026-10-25 and 10-26 with the current no-picks (engine re-run; framework with
`--refresh` and the engine's `_qbs.csv` from the same run) into `/tmp/rerun` and
merged with `merge_rerun.py` (13 games, none started; Thursday's game kept as
logged). Engine backtest with today's data: 968-554 (70%+ 272-93, 60-70%
303-162, under 60% 393-299); 2026 so far out of sample 24-19. The framework
reproduced its 2022-2025 backtest (558-335, Brier 0.2230); 2026 out of sample
27-18.

**Pick back: Giants at Texans** (engine Texans 73.3%, framework Texans 66.4%).
John Harbaugh named J.J. McCarthy the starter after Wednesday's practice: "this
is going to be our direction" (Giants.com, Oct 22). Jameis Winston is healthy and
the backup. A coach's choice going forward, not an injury fill-in, and McCarthy
has 10 career starts (Vikings), so the pick stands; framework re-run with
`--starter "NYG=J.J. McCarthy"`.

Locked picks, splits in bold:

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Steelers vs Saints (Paris, Sun 6:30 AM) | Steelers 60.5% | Steelers 63.0% (24-20) |
| 49ers at Falcons (10:00 AM) | 49ers 63.7% | 49ers 63.3% (26-22) |
| Browns at Titans (10:00 AM) | **Titans 50.6%** | **Browns 50.9%** (23-22) |
| Colts at Vikings (10:00 AM) | Vikings 58.1% | Vikings 82.3% (27-15) |
| Dolphins at Jets (10:00 AM) | Jets 75.7% | Jets 69.4% (26-20) |
| Giants at Texans (10:00 AM) | Texans 73.3% | Texans 66.4% (26-21) |
| Broncos at Cardinals (1:05 PM) | **Cardinals 57.0%** | **Broncos 62.0%** (25-21) |
| Packers at Lions (1:25 PM) | Lions 58.0% | Lions 67.2% (28-22) |
| Rams at Raiders (1:25 PM) | Rams 79.3% | Rams 63.5% (26-22) |
| Chiefs at Seahawks (5:20 PM) | Chiefs 52.9% | Chiefs 62.7% (24-20) |

No pick (both), from Friday's official game statuses:
- Bengals at Ravens: Lamar Jackson (ankle) questionable: limited in practice
  Wed-Fri, says he's trending toward playing (CBS, Oct 23); Tyler Huntley started
  the last 2.
- Buccaneers at Panthers: Baker Mayfield (right thumb) questionable: full practice
  Wed-Fri and Todd Bowles expects him to start (Field Level Media, Oct 23), not
  yet confirmed; Jalon Daniels started the last 3.
- Cowboys at Eagles (Mon): unchanged, Jalen Hurts (blood clots) on IR; Tanner
  McKee makes his 2nd start.

Off the record: engine Ravens 61.1%, Panthers 59.7%, Cowboys 53.4%; framework
Ravens 53.3%, Panthers 58.6%, Cowboys 51.0%.

QB check (Friday's game statuses, NFL.com and CBS, Oct 23): no other starting QB
has a game status. On the report without one: Patrick Mahomes (knee, full all
week), Bryce Young (knee, full all week), Jordan Love (back). Backups with
statuses: Dillon Gabriel (Browns, out), Carson Beck (Cardinals, questionable),
Drew Lock (Seahawks, questionable). Monday's statuses come later Saturday; that
game stays a no pick either way.

Changes from Tuesday: Giants at Texans is back as a pick; every other win chance
moved less than a point (largest: engine Cardinals 57.7% to 57.0%) and no pick
flipped. The models agree on 8 of 10 picks. Engine 70%+: Rams, Jets, Texans;
framework 70%+: Vikings.

PDF: `report_2026-10-24_cfb-saturday-nfl-sunday.pdf` (college graded 10-20 to
10-23, NFL picks, college picks 10-24). At the owner's request ("the NFL games
for tomorrow") its NFL page shows Sunday's 12 games only, made with
`make_report.py --dir` pointed at copies of the logged files with the NFL week
filtered to Sunday; the logged files keep all 14 games (Thursday's is final and
gets graded with the week on Tuesday).

**For the next check-ins:** Sunday's check (F) settles Jackson and Mayfield at
the early-game inactives (about 8:30 AM Phoenix); a pick comes back only by
re-running both models without that no-pick (into `/tmp/rerun`, then
`merge_rerun.py`). Monday's check (G) covers Cowboys at Eagles.

**Sunday 2026-10-25, about 2:45 AM Phoenix (owner's request):** Saturday's news
applied with `set_nopick.py` (both models; still no picks, reasons updated):
Lamar Jackson (ankle) ruled out Saturday afternoon (Adam Schefter, Jeff
Zrebiec), Tyler Huntley makes his 3rd straight start; Baker Mayfield still
questionable on the official report though Todd Bowles says he'll return
Sunday, so the pick waits for the inactives at check-in F (8:40 AM Pacific),
which re-runs both models if he's active and starting. No other quarterback
news. PDF: `report_2026-10-25_cfb-graded-nfl-weekend.pdf` (Saturday's college
games graded, NFL Sunday-Monday picks), the first with the "What to act on"
page (owner, 2026-10-24): act on Rams 79%, Jets 76%, Texans 73%; lean 49ers
64%, Steelers 60%; pass Vikings, Lions, Chiefs (under 60%), Cardinals and
Titans (under 60% and split). All seven check-ins in `CHECKINS.md` are now
scheduled tasks (owner, 2026-10-24).

**Sunday check (F), 2026-10-25, about 8:50 AM Phoenix.** Saturday's college
slate was already graded (engine 20-8, framework 18-10, entry above).
Early-game inactives: **Baker Mayfield (thumb) is active** for the Buccaneers
at Carolina (NBC Sports/Rotoworld, Oct 25, 15:34 UTC) and Todd Bowles said
Friday he returns as the starter (NFL.com, ESPN's Jenna Laine, Oct 23).
Pick back: both models re-run without that no-pick (engine for 10-25 and
10-26; framework with `--starter "TB=Baker Mayfield"` and
`--starter "NYG=J.J. McCarthy"`) into `/tmp/rerun` and merged (Steelers vs
Saints, under way in Paris, kept as logged). **Buccaneers at Panthers: engine
Panthers 59.7%, framework Panthers 60.9%** (both agree; under 60% for the
engine, so a pass on the "What to act on" page). No other pick or win chance
changed. Other early-game QBs: no starting QB inactive (FantasyPros inactives
list: only Dillon Gabriel, a Browns backup, already out); no news on the late
or night starters since Friday's statuses (none had a game status). Still no
pick (both): Bengals at Ravens (Lamar Jackson ruled out; Tyler Huntley starts)
and Cowboys at Eagles (Jalen Hurts on IR; Tanner McKee starts; Monday's check
G). PDF: `report_2026-10-25_nfl-sunday-check.pdf`.

### 2026 Week 7 final (Tuesday run, 2026-10-27)

Graded Tuesday about 7:20 AM Pacific (scheduled check-in A), all 14 games final.
Files `nfl_cfbmethod_2026_week07_graded.csv` and `prompt_nfl_2026_week07_graded.csv`.

**Engine (official) 5-7, framework 7-5** (no pick: 2 in both).
- Engine right: Rams, Steelers, Vikings, Lions, Bears. Wrong: Jets (76%),
  Texans (73%), 49ers, Panthers, Cardinals, Chiefs, Titans. 70%+ went 1-2.
- The 2 splits both went to the framework: Broncos 30-16 at Cardinals, Browns
  27-24 at Titans.
- Missed by both: Dolphins 28-25 at Jets, Giants 27-21 at Texans, Falcons 29-20
  over the 49ers, Buccaneers 43-13 at Panthers, Seahawks 20-3 over the Chiefs.

Closing-line check (grading only): on the engine's 12 games the closing-line
favorite went 8-4. Brier: engine 0.2945, closing line 0.2463. The engine picked
the market underdog 3 times (0-3); picks 5+ points more confident than the close
went 1-4 (-3.44 units). All graded weeks: engine 16-18-1, closing-line favorite
22-12-1; Brier 0.2634 vs 0.2210; against the market favorite 1-7; 5+ points more
confident than the close 4-10 (-7.68 units).

Off the record (no-pick games): Bengals 35-13 at Ravens (both leaned Ravens:
wrong), Cowboys 38-21 at Eagles (both leaned Cowboys: right). Running NFL total
(`nopick_leans.py`): engine 2-5, framework 2-5.

### 2026 Week 8 (Tuesday run, 2026-10-27)

Both models' first run of the week, straight into `results/`, about 7:30 AM
Pacific: engine for 2026-10-29, 11-01 and 11-02; framework with `--refresh` and
the engine's `_qbs.csv`. No-picks applied to both with `set_nopick.py`. Engine
backtest with today's data: 963-559 (70%+ 271-89, 60-70% 298-167, under 60%
394-303); 2026 out of sample 30-27. Framework backtest reproduced (558-335, Brier
0.2230); 2026 out of sample 34-24.

Files: `nfl_cfbmethod_2026_week08_picks.csv` and `_qbs.csv` (engine),
`prompt_nfl_2026_week08_picks.csv` (framework). Kickoffs in Phoenix time as the
engine writes them (the framework's file shows the Nov 1 games an hour earlier:
it doesn't apply the end of Eastern daylight time that morning; display only).
Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Panthers at Packers (Thu 5:15 PM) | **Panthers 53.7%** | **Packers 50.2%** (25-24) |
| Titans at Bengals (Sun 11:00 AM) | Bengals 78.7% | Bengals 79.0% (28-18) |
| Cardinals at Cowboys (11:00 AM) | Cowboys 58.6% | Cowboys 63.5% (27-23) |
| Vikings at Lions (11:00 AM) | **Lions 59.2%** | **Vikings 59.2%** (24-22) |
| Raiders at Jets (11:00 AM) | Jets 75.2% | Jets 63.6% (26-21) |
| Browns at Steelers (11:00 AM) | Steelers 54.0% | Steelers 63.6% (24-20) |
| Falcons at Buccaneers (11:00 AM) | **Buccaneers 52.8%** | **Falcons 51.3%** (22-21) |
| Colts at Jaguars (11:00 AM) | Jaguars 66.3% | Jaguars 85.0% (30-17) |
| Chargers at Rams (2:05 PM) | Rams 82.0% | Rams 78.8% (27-17) |
| Chiefs at Broncos (2:25 PM) | Chiefs 53.5% | Chiefs 52.3% (24-23) |
| Patriots at Dolphins (2:25 PM) | Patriots 70.2% | Patriots 64.5% (27-22) |
| Bears at Seahawks (Mon 6:15 PM) | **Seahawks 70.8%** | **Bears 50.3%** (24-23) |

No pick (both):
- Ravens at Bills: Lamar Jackson (ankle) return unconfirmed: out the last 3
  games; Jesse Minter says he's in a "decent spot" to play vs. the Bills, more
  clarity Wednesday (NFL.com, Oct 26). Tyler Huntley started the last 3.
- Eagles at Commanders (Sun night): Jalen Hurts (blood clots) on season-ending
  IR (FantasyPros, Oct 26); Tanner McKee makes his 3rd start.

Off the record: engine Bills 51.5%, Commanders 51.2%; framework Bills 57.2%,
Commanders 67.0%.

The models agree on 8 of 12 picks. Engine 70%+: Rams, Bengals, Jets, Seahawks,
Patriots; framework 70%+: Jaguars, Bengals, Rams.

QB check (news through Tuesday morning; no official reports yet): Bryce Young
(knee) full participant after Monday's walkthrough; Klint Kubiak says Kirk
Cousins stays the Raiders' starter (NFL.com roundup, Oct 26). Flagged teams with
their regular starter in place and no injury news: Vikings (Kyler Murray, last
4), Buccaneers (Baker Mayfield, back from the thumb injury Week 7), Falcons
(Michael Penix Jr.), Commanders (Jayden Daniels), Seahawks (Sam Darnold), Bears
(Caleb Williams). ESPN's injury list shows no other starting QB. No news found
for the other starters.

**For the next check-ins:** Wednesday's report settles Jackson (a pick comes
back only by re-running both models without the no-pick into `/tmp/rerun`, then
`merge_rerun.py`) and gives Young's and Love's statuses for Thursday.

**Wednesday 2026-10-28 QB check (owner's request, about 10:30 AM Phoenix,
before Wednesday's practice reports).** No pick changed; the picks are the
Tuesday run's.
- Ravens at Bills stays a no-pick in both files: Ian Rapoport expects Lamar
  Jackson to play (NFL Network, Oct 27; "believed to be close to 100 percent"),
  but there's no injury-report status or team confirmation yet. Both files'
  reason now says so (`set_nopick.py`).
- Bryce Young (knee) was a full participant Monday and Tuesday (estimates from
  walkthroughs, Packers-Panthers injury report, Oct 27); Jordan Love isn't on the
  report. Thursday's game statuses come with Wednesday's report (check-in B).
- No other starting QB in the injury news (DraftKings Network report updated Oct
  27, FantasyPros Oct 26). Eagles at Commanders stays a no-pick (Jalen Hurts on
  season-ending IR).

### 2026 Week 8 locked Friday 2026-10-30 (check-in C, after the 1 PM Pacific game statuses)

Run about 1:45 PM Pacific. ESPN, nflverse and PyPI were reachable. Both models
re-run for 2026-11-01 and 11-02 with the current no-pick (engine re-run;
framework with `--refresh`, the engine's `_qbs.csv` from the same run and
`--starter "BAL=Lamar Jackson"`) into `/tmp/rerun` and merged with
`merge_rerun.py` (13 games refreshed, none started; Thursday's Panthers at
Packers kept as logged). Engine backtest with today's data: 964-558 (70%+
273-94, 60-70% 301-163, under 60% 390-301); 2026 out of sample 30-27. Framework
backtest reproduced (558-335, Brier 0.2230); 2026 out of sample 35-24.

**Pick back: Ravens at Bills** (engine Bills 51.6%, framework Bills 52.3%; the
models agree). Lamar Jackson (ankle) has no injury designation and is set to play
Sunday, full participant this week (Ravens injury report, Oct 30; baltimoreravens.com
"Lamar Jackson Set to Play vs. Bills"; NFL.com Friday roundup: "will play Sunday
against the Bills after missing the past three contests"). He's the regular
starter returning (started the first 4), so the pick stands; framework re-run
with `--starter "BAL=Lamar Jackson"` (it had assumed Tyler Huntley, the last
starter).

No other pick changed sides. Probability moves of note: engine Patriots 70.2% ->
69.5% (now a lean, under 70%); framework Cowboys 63.5% -> 65.3%.

Locked picks (Phoenix kickoff), splits in bold:

| Game | Engine (official) | Framework |
|---|---|---|
| Ravens at Bills (Sun 11:00 AM) | Bills 51.6% | Bills 52.3% (27-26) |
| Titans at Bengals (11:00 AM) | Bengals 78.2% | Bengals 78.9% (28-18) |
| Cardinals at Cowboys (11:00 AM) | Cowboys 58.7% | Cowboys 65.3% (28-23) |
| Vikings at Lions (11:00 AM) | **Lions 59.3%** | **Vikings 59.2%** (24-22) |
| Raiders at Jets (11:00 AM) | Jets 74.8% | Jets 63.6% (26-21) |
| Browns at Steelers (11:00 AM) | Steelers 53.9% | Steelers 63.5% (24-20) |
| Falcons at Buccaneers (11:00 AM) | **Buccaneers 53.2%** | **Falcons 51.3%** (22-21) |
| Colts at Jaguars (11:00 AM) | Jaguars 66.4% | Jaguars 85.0% (30-17) |
| Chargers at Rams (2:05 PM) | Rams 81.7% | Rams 78.7% (27-17) |
| Chiefs at Broncos (2:25 PM) | Chiefs 53.6% | Chiefs 52.3% (24-23) |
| Patriots at Dolphins (2:25 PM) | Patriots 69.5% | Patriots 64.5% (27-22) |
| Bears at Seahawks (Mon 6:15 PM) | **Seahawks 70.6%** | **Bears 50.3%** (24-23) |

No pick (both): Eagles at Commanders (Sun night): Jalen Hurts (blood clots) on
season-ending IR (FantasyPros, Oct 26); Tanner McKee makes his 3rd start. Off the
record: engine Commanders 51.7%, framework Commanders 68.1%.

Engine 70%+: Rams, Bengals, Jets, Seahawks. Framework 70%+: Jaguars, Bengals, Rams.
The models agree on 9 of the 12 Sunday-Monday picks (13 of the week with Thursday: 9 agree, 4 split).

QB check (Friday game statuses): NFL.com's Week 8 injury page lists no starting QB
as out, doubtful or questionable. QBs on the reports: Lamar Jackson (full, no
designation), Baker Mayfield (full), Drake Maye (full), Malik Willis (full),
Jayden Daniels and Marcus Mariota (full), Carson Beck (Cardinals backup,
limited). Flagged teams with their regular starter in place and no injury news:
Vikings (Kyler Murray), Buccaneers (Mayfield), Falcons (Michael Penix Jr.),
Commanders (Daniels), Seahawks (Sam Darnold), Bears (Caleb Williams). Bears at
Seahawks statuses come Saturday; check-in G has the final word on Monday.

**Saturday night 2026-10-31, about 7:25 PM Phoenix (owner's request: run both
engines, PDF of results so far and upcoming picks).**
- Thursday graded (`nfl_cfbmethod_2026_week08_graded.csv`,
  `prompt_nfl_2026_week08_graded.csv`): Packers 27, Panthers 19. **Engine 0-1**
  (Panthers 54%), **framework 1-0** (Packers 50%): the split went to the
  framework. Closing-line check: the close had the Packers (engine picked the
  market underdog). All graded weeks: engine 16-19-1, closing-line favorite
  23-12-1; Brier 0.2641 vs 0.2186.
- Both models re-run for 2026-11-01 and 11-02 with the current no-pick (engine;
  framework with `--refresh`, the engine's `_qbs.csv` from the same run and
  `--starter "BAL=Lamar Jackson"`) into `/tmp/rerun` and merged with
  `merge_rerun.py`: 13 games refreshed, **no pick or win chance changed** (engine
  backtest 964-558, 2026 out of sample 30-27; framework 558-335, Brier 0.2230,
  2026 out of sample 35-24). The picks are the Friday lock's.
- Monday statuses (released Saturday): Caleb Williams isn't on the Bears' final
  report (chicagobears.com, Oct 31: T.J. Edwards returns; Malik Muhammad and
  D'Marco Jackson questionable). Sam Darnold isn't on the Seahawks' report; the
  backup Drew Lock (right elbow) is questionable (Seattle Sports, Oct 31). Both
  picks stand; check-in G confirms with the inactives.
- Sunday games: no starting QB listed out, doubtful or questionable (Sharp
  Football's all-32-teams report, Oct 31; Yahoo's Week 8 tracker); Saturday's
  moves were non-QBs (Patriots downgraded A.J. Brown and TreVeyon Henderson to
  out). Eagles at Commanders stays a no-pick (Jalen Hurts on season-ending IR).
  Check-in F confirms the early-game inactives Sunday morning.

**Sunday check (F), 2026-11-01, about 8:45-9:05 AM Pacific. No pick changed;
the picks are the Friday lock's.**
- Early games: no starting QB inactive. Lamar Jackson is active for the Ravens
  at Buffalo (Ravens inactives, NBC Sports/Rotoworld, Nov 1 16:32 UTC: QB Joe
  Fagnano the only QB out); Colts inactives list Riley Leonard as the third QB
  (colts.com, Nov 1); the other early-game QBs listed inactive are backups
  (Cardinals Carson Beck; Browns Taylen Green, Dillon Gabriel; Steelers Drew
  Allar, Will Howard; Fantasy Alarm, Nov 1 11:40 AM ET). FantasyPros' Week 8
  inactives list no QB for any early game. ESPN's injury page lists no starting
  QB in a Week 8 game as out or questionable (Hurts on IR aside).
- Late and night games: no new QB news since Saturday (Chargers, Rams, Chiefs,
  Broncos, Patriots, Dolphins: no QB with a status; their inactives come about
  90 minutes before kickoff, after this check). Eagles at Commanders stays a
  no-pick in both models (Jalen Hurts on season-ending IR; Tanner McKee starts).
  Bears at Seahawks: check-in G (Drew Lock, the backup, questionable).

### 2026 Week 8 final (Tuesday run, 2026-11-03)

All 14 games final. Graded with `nfl_cfbmethod/grade.py --season 2026 --week 8`
(engine) and `results/grade_picks.py` (framework). **Engine (official) 8-5,
framework 8-5** (no pick: Eagles at Commanders).
- Engine: W Rams 82%, Bengals 78%, Patriots 70%, Jaguars 66%, Lions 59%,
  Steelers 54%, Buccaneers 53%, Bills 52%; L Jets 75% (Raiders 38-33), Seahawks
  71% (Bears 34-17), Cowboys 59% (Cardinals 33-30), Panthers 54% (Packers 27-19),
  Chiefs 54% (Broncos 28-24). 70%+: 3-2.
- Framework: W Jaguars, Bengals, Rams, Patriots, Steelers, Bills, Bears,
  Packers; L Jets, Cowboys, Vikings, Chiefs, Falcons.
- The 4 splits went 2-2: engine won Lions and Buccaneers, framework won Packers
  and Bears.
- Closing-line check (Week 8): closing-line favorite 10-3; Brier engine 0.2383,
  close 0.1883; engine picked the market underdog 2 times (0-2). All graded
  weeks: engine 24-23-1, closing-line favorite 32-15-1; Brier 0.2566 vs 0.2121;
  engine 5+ points more confident than the close: 5-13.
- Off the record (no pick): Commanders 27, Eagles 10; both models leaned
  Commanders.

### 2026 Week 9 (Tuesday run, 2026-11-03)

Both models' first run of the week, straight into `results/`, about 8:20 AM
Pacific: engine for 2026-11-05, 11-08 and 11-09; framework with `--refresh` and
the engine's `_qbs.csv`. No-picks applied to both with `set_nopick.py`. Engine
backtest with today's data: 968-554 (70%+ 273-94, 60-70% 306-161, under 60%
389-299); 2026 out of sample 39-32. Framework backtest reproduced (558-335,
Brier 0.2230); 2026 out of sample 43-29.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Bengals at Falcons (Sun 7:30 AM, neutral site) | Bengals 58.8% | Bengals 58.9% (24-22) |
| Cowboys at Colts (11:00 AM) | Cowboys 53.5% | Cowboys 61.3% (26-23) |
| Jets at Chiefs (11:00 AM) | Chiefs 68.3% | Chiefs 68.3% (27-21) |
| Lions at Dolphins (11:00 AM) | Lions 69.6% | Lions 67.8% (28-22) |
| Browns at Saints (11:00 AM) | Saints 52.3% | Saints 52.4% (23-22) |
| Broncos at Panthers (11:00 AM) | Broncos 51.3% | Broncos 58.6% (25-22) |
| Texans at Chargers (2:05 PM) | Texans 63.0% | Texans 68.6% (25-19) |
| Packers at Patriots (2:25 PM) | Patriots 62.0% | Patriots 57.7% (25-22) |
| Raiders at 49ers (2:25 PM) | 49ers 85.9% | 49ers 82.7% (31-19) |
| Cardinals at Seahawks (2:25 PM) | Seahawks 66.1% | Seahawks 70.8% (26-19) |
| Buccaneers at Bears (6:20 PM) | Bears 55.4% | Bears 60.2% (23-20) |

The models agree on all 11 picks. Engine 70%+: 49ers. Framework 70%+: 49ers,
Seahawks.

No pick (both):
- Jaguars at Ravens (Thu): Lamar Jackson (right thumb) out, headed to IR; Tyler
  Huntley (toe) probably out; Joe Fagnano (ankle, limited Monday) not named the
  starter (Jesse Minter, baltimoreravens.com, Nov 2).
- Giants at Eagles: Jalen Hurts (blood clots) on season-ending IR; Tanner McKee
  starts (Sirianni, Nov 2). (Giants: Jaxson Dart on IR; J.J. McCarthy, named
  "our direction" Oct 22, started the last game.)
- Rams at Commanders: Matthew Stafford (throwing-arm soreness) unconfirmed;
  McVay deferring to how he feels, first practice report Wednesday (CBS Sports,
  Nov 2).
- Bills at Vikings (Mon): Kyler Murray (hamstring) undecided; O'Connell still
  evaluating, decision later in the week; Carson Wentz next in line
  (Vikings.com, Nov 2).

Off the record: engine Jaguars 70.2%, Giants 52.8%, Rams 82.9%, Bills 55.5%;
framework Jaguars 75.0%, Giants 62.6%, Rams 67.6%, Vikings 57.2%.

QB check (news through Tuesday morning; no official reports yet):
- Cardinals (CHANGE): Jacoby Brissett benched (not injured); Mike LaFleur named
  Gardner Minshew the starter "moving forward," Carson Beck the backup (Fox
  Sports, Nov 2). A coach's choice going forward, so the pick stands. The
  framework had no 2026 dropbacks for Minshew in its data yet (his Week 8 plays
  aren't in its charted data until the midweek update), so it used a league-
  average QB for him; the Friday `--refresh` picks them up.
- Colts: Shane Steichen sticks with Daniel Jones (performance question after
  the 42-7 loss, no injury; ESPN, Nov 2).
- No injury designation or news for the other flagged starters: Trevor Lawrence
  (not on the Jaguars' report), Michael Penix Jr., Jayden Daniels (elbow, played
  Week 8, not on the report), Sam Darnold (Drew Lock is the emergency third QB),
  Caleb Williams, Baker Mayfield. Patrick Mahomes (knee) and Deshaun Watson
  played Week 8 without a designation and aren't on the Week 9 report
  (DraftKings Network injury report, Nov 3).

**For the next check-ins:** Wednesday's report (B) gives Thursday's statuses
(Jaguars at Ravens stays a no-pick even if a backup is confirmed, since the
regular starter is out) and the first practice reports for Stafford and Murray. Friday's lock (C) settles Stafford; Murray's Monday status
comes Saturday (final word at check-in G).

**Midweek check (check-in B), Wednesday 2026-11-04.** Jaguars at Ravens stays
a no-pick (both models); reason refreshed with `set_nopick.py`: Lamar Jackson
(right thumb) ruled out, headed to IR; Joe Fagnano starts (Jesse Minter, Nov 3;
Fagnano off the final injury report, FantasyPros Nov 4); Tyler Huntley (toe)
out. One unconfirmed report (FantasyPros, Nov 4) says Baltimore traded for
Jacoby Brissett; doesn't change the no-pick. Trevor Lawrence: no designation
found on the Jaguars' report. Thursday's check-in B confirms inactives.

**Midweek check (check-in B), Thursday 2026-11-05 (second run of the check).**
Jaguars at Ravens stays a no-pick (both models); reason refreshed with
`set_nopick.py`: the Ravens put Lamar Jackson (right thumb, out at least 4 games)
and Tyler Huntley (turf toe, out for the season) on IR on Nov 5; Joe Fagnano
starts, Austin Reed (signed to the 53 that day) backs up (Yardbarker, Nov 5).
College: see the Thursday entry in the 2026-11-03 to 11-06 section (James
Madison at Southern Miss is a no-pick under METHOD.md section 6).

**Friday lock (check-in C), 2026-11-06, about 1:45 PM Pacific. Week 9 picks
locked Friday.** Both models re-run for 2026-11-08 and 11-09 with the current
no-picks (engine; framework with `--refresh` and the engine's `_qbs.csv` from the
same run) into `/tmp/rerun` and merged with `merge_rerun.py` (14 games
refreshed in each file). Framework backtest 558-335 (Brier 0.2230); 2026 out of
sample 44-29.

Changes:
- **Pick back: Rams at Commanders** (engine Rams 83.0%, framework Rams 67.6%,
  26-20). Matthew Stafford practiced fully Wednesday and Thursday with no
  designation (NFL.com Week 9 report; Yahoo, Nov 5: "I haven't missed a rep");
  not listed on the final report (SI game preview injury list).
- **New no pick: Cardinals at Seahawks** (was Seahawks, engine 66.1%, framework
  70.8%): Sam Darnold (quad; also a cracked rib) ruled out, week to week; Drew
  Lock (elbow) starts (Mike Macdonald, NFL.com, Nov 4). Announced Wednesday; the
  midweek checks looked only at Thursday's game, so this is the first check to
  catch it. Corrected before kickoff.
- **New no pick: Browns at Saints** (was Saints, engine 52.3%, framework 52.4%):
  Deshaun Watson (concussion) in protocol, won't start; Shedeur Sanders starts
  (Browns, ESPN/AP, Nov 6).
- Reasons refreshed (still no picks): Bills at Vikings: Kyler Murray
  (hamstring) ruled out, week to week; Carson Wentz starts (Kevin O'Connell,
  Vikings.com, Nov 5). Giants at Eagles: Jalen Hurts on season-ending IR;
  Tanner McKee (chest) starts.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Bengals at Falcons (Sun 7:30 AM, neutral site) | Bengals 58.7% | Bengals 58.9% (24-22) |
| Cowboys at Colts (11:00 AM) | Cowboys 53.8% | Cowboys 61.3% (26-23) |
| Jets at Chiefs (11:00 AM) | Chiefs 68.0% | Chiefs 68.3% (27-21) |
| Lions at Dolphins (11:00 AM) | Lions 69.6% | Lions 67.8% (28-22) |
| Rams at Commanders (11:00 AM) | Rams 83.0% | Rams 67.6% (26-20) |
| Broncos at Panthers (11:00 AM) | Broncos 51.8% | Broncos 58.6% (25-22) |
| Texans at Chargers (2:05 PM) | Texans 62.8% | Texans 68.6% (25-19) |
| Packers at Patriots (2:25 PM) | Patriots 62.1% | Patriots 57.7% (25-22) |
| Raiders at 49ers (2:25 PM) | 49ers 85.9% | 49ers 82.7% (31-19) |
| Buccaneers at Bears (6:20 PM) | Bears 55.5% | Bears 60.6% (23-20) |

The models agree on all 10 picks. Engine 70%+: 49ers, Rams. Framework 70%+:
49ers.

No pick (both): Jaguars at Ravens (played Thursday), Browns at Saints, Giants
at Eagles, Cardinals at Seahawks, Bills at Vikings (reasons above). Off the
record: engine Saints 52.3%, Giants 52.6%, Seahawks 66.0%, Bills 55.9%;
framework Saints 52.4%, Giants 62.6%, Seahawks 69.7%, Vikings 57.2%.

QB check (Friday statuses): no other starting QB in a Sunday game is out,
doubtful or questionable. On the reports with full practices and no
designation: Bryce Young, Patrick Mahomes, Malik Willis (groin), Jayden Daniels,
Drake Maye (right shoulder), Baker Mayfield (NFL.com Week 9 report). Jordan Love
not on the Packers' final report (packers.com, Nov 6). Gardner Minshew starts for
the Cardinals (named Nov 2; game is a no-pick for Seattle's QB anyway). No news
against Burrow, Penix, Prescott, Daniel Jones, Geno Smith, Goff, Shough, Nix,
Stroud, Herbert, Purdy, Cousins or Caleb Williams. Monday: Josh Allen no news;
check-in G confirms with the inactives. London game (Bengals-Falcons) kicks off
before check-in F: settled here.

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

**Catch-up, Thursday 2026-10-15 morning.** The owner ran out of usage this week,
so the Tuesday run and Wednesday's check didn't happen. Tuesday's and Wednesday's
games were graded late, and the QB check for Thursday and Friday was done now.

Results (both models, graded files `*_2026-10-13_graded.csv` and
`*_2026-10-14_graded.csv`): **engine 2-0, framework 2-0**.
- Tue: Jacksonville State 27, Florida International 24. Both right.
- Wed: Missouri State 24, Kennesaw State 21. Both right, but Missouri State
  started Henry Belin, who had replaced Skyler Locklear during its Oct 8 game.
  The Wednesday QB check that would have looked at this was missed, so the pick
  stood as logged; noted here rather than changed after the result.
- No picks: Middle Tennessee 33, Delaware 30 (Delaware started Tyler Bell);
  Western Kentucky 16, Sam Houston 3 (Brock Glenn started).

QB check for the rest of the week (news through Thursday morning):
- East Carolina at UAB: Emory Williams (named starter since Sep 26) and Ryder
  Burton, no injury news. Picks stand.
- Georgia Southern at Old Dominion: Max Johnson and Quinn Henicle (back from his
  Week 4 injury, started the last two), no injury news. Picks stand.
- Colorado State at Texas State: K'saan Farrar expected to start (ESPN's Pete
  Thamel, Oct 13), his third straight start with Hauss Hejny (hamstring) still
  out; Brad Jackson for Texas State. Picks stand under the rule above (Farrar
  is the last starter and leads in attempts), the same call as Sunday night.
- Memphis at Tulane, App State at Coastal Carolina: Marcus Stokes, Kadin Semonza,
  Malachi Singleton and Deuce Bailey, no injury news. Picks stand.
- Washington at Purdue: still no pick. Reason updated in both files: Demond
  Williams Jr. hurt in last game, unlikely to play (coach Jedd Fisch, Oct 12);
  Elijah Brown expected to start.

**Thursday 2026-10-15 graded** (Thursday night, 9 PM Phoenix, at the owner's
request; graded files `cfb_2026-10-15_graded.csv` and
`prompt_cfb_2026-10-15_graded.csv`): **engine 2-1, framework 2-1**. Report:
`report_2026-10-15_cfb-graded.pdf` (made by `make_2026-10-15_cfb_report.py`).
The Friday check-in doesn't need to grade Thursday again.
- Georgia Southern 23, Old Dominion 15. Both right (engine 75%, framework 85%).
- Texas State 66, Colorado State 27. Both right (engine 83%, framework 70%).
- UAB 30, East Carolina 17 (overtime). Both wrong (engine East Carolina 59%,
  framework 77%).
- QBs (ESPN play-by-play): every expected starter started (Emory Williams, Ryder
  Burton, Max Johnson, Quinn Henicle, K'saan Farrar, Brad Jackson). Two were
  replaced during the game: Turner Helton took over for Georgia Southern in the
  2nd quarter (30 of its 41 passes) and Ryan Huff played the 2nd half for Old
  Dominion (14 of its 24). Both teams' next QB checks need to settle who starts.

Midweek so far (Tue-Thu): **engine 4-1, framework 4-1**; they haven't split on a
graded game yet. Live record since the first logged picks: engine 15-9 since
2026-10-10 (70%+ picks 8-1, 60-70% 4-5, under 60% 3-3); framework 4-1 since
2026-10-13 (70%+ 1-1, 60-70% 1-0, under 60% 2-0).

**Friday 2026-10-16 QB check (Friday lock, 1:45 PM Pacific): all three games are
now no picks (both models, `set_nopick.py`).**
- Memphis at Tulane (was engine and framework Memphis): QB change, Trace
  Johnson to start per sources (Fox 8 New Orleans, Oct 16), not confirmed by
  Tulane; Kadin Semonza started the last 4 and coach Will Hall called the job
  open (Oct 13). Memphis's Marcus Stokes has no injury news.
- App State at Coastal Carolina (was engine Coastal Carolina, framework App
  State): Malachi Singleton (ankle) is a game-time decision (questionable since
  Oct 13, hurt vs Old Dominion); Henry Hasselbeck starts if he can't. Thursday's
  check missed the Oct 13 questionable note. Deuce Bailey has no injury news.
- Washington at Purdue (already a no pick): Demond Williams Jr. (rib) out;
  Elijah Brown starts (ESPN sources, CBS, Oct 16). Ryan Browne isn't on Purdue's
  availability report.

**Re-checked at the owner's request, 3:50 PM Phoenix: no change, all three stay
no picks.** PDF: `report_2026-10-16_cfb-friday.pdf`.
- Tulane: still sources only (Fox 8, 9:01 AM CDT), no word from Tulane. Trace
  Johnson has 5 pass attempts this season (in relief vs Southern Miss, Sep 26,
  ESPN box scores), so even a confirmed start is a first start with very little
  playing time (METHOD.md section 6). Reason updated in both files to say so.
- App State: Singleton still a game-time decision (RotoWire, Oct 16).
- Washington: nothing newer than Williams Jr. out.
- Both models were re-run into a scratch folder without the App State no-pick;
  that re-run gets merged only if Singleton is confirmed before kickoff.
- 4:40 PM Phoenix, 20 minutes before kickoff: Singleton still a game-time
  decision (RotoWire, Oct 16) and no starter named, so the re-run wasn't merged.
  All three Friday games stay no picks.

## College football Saturday 2026-10-17 (engine and framework)

Run Friday 2026-10-16 afternoon at the owner's request (approved Thursday),
instead of waiting for Saturday's 6:40 AM check-in. Engine file
`cfb_2026-10-17_picks.csv` (official), framework file
`prompt_cfb_2026-10-17_picks.csv`. QB checks use the news through Friday
afternoon; no-picks were applied to both files with `set_nopick.py`. PDF:
`report_2026-10-16_cfb-saturday.pdf`.

**For Saturday's 6:40 AM check-in (D):** this slate is already logged. Re-check
the QBs (above all the no-picks below, several of which may be settled by
morning) and send any re-run through `/tmp/rerun` and `merge_rerun.py` rather
than starting over. Thursday's college games were graded Thursday night (engine
2-1, framework 2-1, in the midweek section); Friday's three games are all no
picks.

52 games: 35 picks in both models, 17 no picks. The models disagree on 7 (in
bold). The engine has 14 picks at 70% or more.

| Game (Phoenix kickoff) | Engine (official) | Framework (score) |
|---|---|---|
| Cincinnati at West Virginia (9:00 AM) | Cincinnati 51% | Cincinnati 56% (33-31) |
| Kansas at Kansas State (9:00 AM) | **Kansas 52%** | **Kansas State 63%** (33-27) |
| Virginia at SMU (9:00 AM) | SMU 75% | SMU 66% (32-25) |
| Ohio State at Indiana (9:00 AM) | Indiana 51% | Indiana 64% (33-27) |
| Northwestern at Michigan State (9:00 AM) | Northwestern 71% | Northwestern 85% (38-21) |
| Florida Atlantic at Army (9:00 AM) | **Army 63%** | **Florida Atlantic 51%** (33-32) |
| Ball State at Bowling Green (9:00 AM) | **Ball State 50%** | **Bowling Green 66%** (29-23) |
| Georgia State at James Madison (9:00 AM) | **James Madison 70%** | **Georgia State 56%** (30-27) |
| Western Michigan at Central Michigan (10:30 AM) | Western Michigan 52% | Western Michigan 59% (28-24) |
| Auburn at Georgia (12:30 PM) | Georgia 92% | Georgia 88% (37-18) |
| Missouri at Ole Miss (12:30 PM) | **Ole Miss 55%** | **Missouri 62%** (30-25) |
| Arizona State at Texas Tech (12:30 PM) | Texas Tech 81% | Texas Tech 61% (28-24) |
| Georgia Tech at Virginia Tech (12:30 PM) | Virginia Tech 83% | Virginia Tech 85% (37-20) |
| North Carolina at Duke (12:30 PM) | **North Carolina 58%** | **Duke 66%** (31-25) |
| Penn State at Michigan (12:30 PM) | Michigan 65% | Michigan 64% (29-24) |
| Northern Illinois at Wyoming (12:30 PM) | Wyoming 56% | Wyoming 70% (32-23) |
| Toledo at Eastern Michigan (12:30 PM) | Toledo 67% | Toledo 75% (32-21) |
| Tulsa at Rice (1:30 PM) | Tulsa 53% | Tulsa 71% (30-21) |
| Troy at Louisiana (2:00 PM) | Troy 51% | Troy 50% (28-27) |
| Washington State at Oregon State (3:00 PM) | Oregon State 91% | Oregon State 90% (37-16) |
| Arkansas at Vanderbilt (4:00 PM) | Vanderbilt 64% | Vanderbilt 69% (31-24) |
| TCU at Baylor (4:00 PM) | Baylor 64% | Baylor 75% (30-19) |
| Florida State at Miami (4:00 PM) | Miami 91% | Miami 92% (44-20) |
| Kent State at South Florida (4:00 PM) | South Florida 86% | South Florida 70% (32-24) |
| Arkansas State at Southern Miss (4:00 PM) | **Arkansas State 53%** | **Southern Miss 53%** (30-29) |
| Kentucky at Oklahoma (4:30 PM) | Oklahoma 65% | Oklahoma 56% (25-23) |
| Notre Dame at BYU (4:30 PM) | Notre Dame 60% | Notre Dame 52% (28-27) |
| Oklahoma State at Houston (4:30 PM) | Houston 81% | Houston 68% (33-26) |
| Wisconsin at UCLA (4:30 PM) | UCLA 71% | UCLA 66% (27-21) |
| Navy at UTSA (5:00 PM) | UTSA 64% | UTSA 67% (33-26) |
| Louisiana Tech at UL Monroe (5:00 PM) | Louisiana Tech 73% | Louisiana Tech 76% (36-25) |
| Ohio at Sacramento State (7:00 PM) | Ohio 63% | Ohio 71% (31-22) |
| Utah at Colorado (7:15 PM) | Utah 78% | Utah 84% (35-18) |
| Fresno State at San Diego State (7:30 PM) | Fresno State 59% | Fresno State 79% (32-19) |
| New Mexico at Hawai'i (7:30 PM) | New Mexico 88% | New Mexico 86% (33-15) |

No pick (both):
- Not enough play-by-play this season for the FCS team: Charleston Southern at
  Clemson, The Citadel at Texas A&M, Elon at Stanford.
- Florida at Texas: Aaron Philo (shoulder) status in question, limited in
  practice all week; Tramell Jones would make his first start.
- Mississippi State at LSU: Kamario Taylor (foot) questionable, decision not
  announced; Parker Puckett would start.
- Pittsburgh at Boston College: Mason Heintschel (torn ACL) out for the season;
  Holden Geriner makes his 2nd start.
- Rutgers at Maryland: Dylan Lonergan (head injury Oct 3 vs Indiana) status
  unconfirmed after the bye; AJ Surace would start.
- Charlotte at Temple: QB changed last game (Conner Harrell started; Cole
  Gonzales started the first 5); starter vs Temple not announced.
- Massachusetts at Buffalo: William Watson III (ankle) questionable, missed last
  game; Aedan McCarthy started it.
- Alabama at Tennessee: Faizon Brandon (shoulder) questionable; George MacIntyre
  named to start a 2nd straight game while Brandon is hurt.
- UNLV at Air Force: Liam Szarka (leg) out for the season; Kemper Hodges has 1
  start.
- Akron at Miami (OH): David McComb (upper body) out for the season (MAC
  availability report); Caleb Heavner has 2 starts.
- Nevada at North Dakota State: Carter Jones (undisclosed) questionable (Oct 15).
- Louisville at Syracuse: starter not named; Amari Odom out, Steve Angeli and
  Malachi Nelson questionable (ACC report, Oct 15).
- San José State at UTEP: EJ Colson Jr. (concussion) questionable; Raymond Moore
  III started the last game.
- Wake Forest at California: Jaron-Keawe Sagapolutele (concussion) questionable;
  Jackson Brousseau started the last 2.
- Nebraska at Oregon: Dante Moore (concussion) out again; Dylan Raiola was
  benched vs UCLA and Dan Lanning calls it a competition; starter not named.

How the QB rule was applied: a regular starter who is out or questionable for
any injury means no pick, even when the coach names the replacement (Tennessee,
Pittsburgh, Air Force, Miami (OH)). A coach's choice with the old starter
healthy keeps the pick: Utah at Colorado stands, since Deion Sanders named Isaac
Wilson after benching Julian Lewis at Baylor. Ohio at Sacramento State stands:
Nick Poulos, the opening-day starter, is back from a concussion, started last
week and has no injury news. Army, Rice and Navy (low pass attempts) run option
offenses with the same starters and no injury news. The other flagged teams
still playing a picked game (Ball State, James Madison, Central Michigan, Tulsa,
Vanderbilt, Baylor, Southern Miss, UL Monroe, Louisiana Tech, Sacramento State,
New Mexico) are SPLIT only: the last starter also leads the team in attempts,
and there's no injury news. Vanderbilt's Jared Curtis starts with Blaze
Berlowitz (collarbone) out about a month.

**Saturday 6:40 AM check-in (D), 2026-10-17: QBs re-checked, both models
re-run into `/tmp/rerun` and merged (`merge_rerun.py`).** News through
Saturday morning (Friday-night SEC/Big Ten/ACC/Big 12 availability reports where
found). PDF: `report_2026-10-17_cfb-saturday-run.pdf` (midweek graded + today's
picks). Now **33 picks, 19 no picks; the models disagree on 7.**

Midweek graded (Friday's three games graded this morning, all no picks: Tulane
31-17 over Memphis, App State 35-32 at Coastal Carolina, Washington 38-26 at
Purdue). **Midweek Tue-Fri final: engine 4-1, framework 4-1.**

Changes:
- **Pick back: Rutgers at Maryland** (engine Maryland 78%, framework Maryland
  67%). Greg Schiano: Dylan Lonergan is "full go and he'll be the starter"
  (NJ.com, Oct 13). Lonergan is Rutgers' regular starter (season leader), so the
  pick stands; framework re-run with `--starter "Rutgers=Dylan Lonergan"`. The
  Friday Big Ten availability report itself wasn't found.
- **New no pick: Wisconsin at UCLA** (was UCLA in both): Nico Iamaleava
  (season-ending injury, Oct 12) out; Ty Dieffenbach makes his first start
  (3 of 6 passing in relief vs Oregon). Friday's check missed this.
- **New no pick: Washington State at Oregon State** (was Oregon State in both):
  Caden Pinnick benched; redshirt freshman Owen Eshelman makes his first career
  start (Spokesman-Review, Oct 16) with no plays in this season's play-by-play
  (METHOD.md section 6).
- **New no pick: Fresno State at San Diego State** (was Fresno State in both):
  SDSU starter not named; Jayden Denegal benched Oct 10, coach Sean Lewis says
  "everything's on the table" (East Village Times, Oct 17).
- Small number moves from the re-run's fresh data: engine Ball State at Bowling
  Green now Bowling Green 51% (was Ball State 50%), so the models now agree;
  framework Troy at Louisiana now Louisiana 51% (was Troy 50%), now a split.
- Reasons updated (still no picks): Florida (Philo questionable on Friday
  night's SEC report, game-time decision), Mississippi State (Taylor
  downgraded to doubtful), Massachusetts (Watson ruled out, McCarthy also out,
  Logan Inagawa first career start), Alabama at Tennessee (Brandon off the
  report but MacIntyre starts per ESPN sources, not confirmed by Heupel),
  Louisville at Syracuse (Angeli, Achilles, not starting; Nelson starts),
  Charlotte (still not announced), Nevada and San José State at UTEP
  (questionable, no update), Wake Forest at California (Sagapolutele probable,
  not confirmed), Nebraska at Oregon (Moore out, starter not named).
- Every other picked team: no QB injury or change news found (checks at
  Friday's/Thursday's availability reports or game previews; the MAC, Sun Belt,
  C-USA, Mountain West and independents don't post league reports).
- For check-in E: Wake Forest at California (Sagapolutele probable), Charlotte,
  Nevada, UTEP, SDSU and Oregon starters could settle before kickoff.

Splits (engine official vs framework): Kansas at Kansas State (Kansas 51% /
Kansas State 64%), Florida Atlantic at Army (Army 63% / FAU 52%), Georgia State
at James Madison (JMU 70% / Georgia State 55%), Missouri at Ole Miss (Ole Miss
54% / Missouri 62%), North Carolina at Duke (UNC 57% / Duke 66%), Troy at
Louisiana (Troy 52% / Louisiana 51%), Arkansas State at Southern Miss (Arkansas
State 52% / Southern Miss 53%).

**Saturday 11:50 AM check-in (E), 2026-10-17: QB news for the 35 games from
12:30 PM Phoenix on.** No pick changed: still **33 picks, 19 no picks** (both
models carry the same no-picks). Two reasons updated with `set_nopick.py`:
- Alabama at Tennessee (still no pick): Faizon Brandon is off the SEC report
  and "ready to go," but he first threw in practice Tuesday since the shoulder
  injury, and Heupel said last week he was there "for emergency use only";
  George MacIntyre starts ("this is George's football game," Heupel, Knox
  News, Oct 17). The regular starter isn't back as the starter for an injury
  reason, so it stays a no pick under the rule. (A re-run without the no-pick
  was made in `/tmp/rerun` while this was checked; it was not merged.)
- Nebraska at Oregon (still no pick): Dante Moore (concussion) out; Brock
  Thomas expected to start (Pete Thamel, College GameDay, Oct 17), not
  announced by Oregon.
- Still unsettled at this check (no picks stand): Nevada (Carter Jones
  questionable, "warmups will be more telling," Rotowire Oct 17), UTEP (EJ
  Colson Jr. questionable, no update), California (Sagapolutele, no
  confirmation found), San Diego State (no starter named).
- Picked games checked with no QB news: final or game-day reports for Penn
  State-Michigan, Missouri-Ole Miss (Austin Simmons cleared), North
  Carolina-Duke, Georgia Tech-Virginia Tech, Arizona State-Texas Tech,
  Florida State-Miami, Kentucky-Oklahoma; previews and news for the rest (the
  MAC, Sun Belt, C-USA, Mountain West and independents post no league
  reports).

**Saturday 2026-10-17 graded, Saturday night 8:30 PM Pacific (at the owner's
request; 29 of 33 picks final, 4 still playing).** Graded files
`cfb_2026-10-17_graded.csv` and `prompt_cfb_2026-10-17_graded.csv`; PDF
`report_2026-10-17_cfb-graded.pdf`. **Engine (official) 18-11, framework 15-14.**
- By win chance: engine 70%+ 8-2, 60-70% 4-3, under 60% 6-6; framework 70%+
  8-2, 60-70% 5-6, under 60% 2-6.
- The 7 splits: engine 5-2 (Army, James Madison, Ole Miss, North Carolina,
  Arkansas State right; Kansas, Troy wrong).
- Biggest misses (both models): Auburn 27, Georgia 24 (engine Georgia 92%,
  framework 87%); Rutgers 37, Maryland 30 (engine Maryland 78%).
- Not final at grading: Navy at UTSA, Ohio at Sacramento State, Utah at Colorado,
  New Mexico at Hawai'i. Sunday's check (F) re-runs `grade_picks.py` to finish
  them.

**Saturday 2026-10-17 final, Sunday check-in (F), 2026-10-18 8:45 AM Pacific.**
All 33 picks final; the 4 late games went right for both models (UTSA 38-34
over Navy, Ohio 48-7 at Sacramento State, Utah 27-24 at Colorado, New Mexico
21-10 at Hawai'i). **Final: engine (official) 22-11, framework 19-14.**
- By win chance: engine 70%+ 10-2, 60-70% 6-3, under 60% 6-6; framework 70%+
  11-2, 60-70% 6-6, under 60% 2-6.
- Off the record (no-pick games, never in either record; `nopick_leans.py`
  running total through 10-17): college engine 10-11, college framework 12-9.

**Proposal backtest, returning starter (2026-10-17, owner's request; nothing
changed in the engine).** `results/proposals/returning_starter_backtest.py`,
output `returning_starter_backtest.txt` and `_games.csv`. Question: when a
team's regular QB plays, does it help to stop its backup's earlier games from
dragging its offense rating down? Graded on the games the engine would actually
pick (both regular starters playing), 2023-2025 weeks 4-15 and 2026 weeks 4-7,
1,207 games, each week fit only on earlier plays:
- Locked engine 843-364 (69.8%), Brier 0.194. Dropping backup games' offensive
  plays: 838-369 (69.4%). A league-wide backup-QB term in the fit: 839-368
  (69.5%).
- On the 642 games where a team's backup had started earlier: engine 70.2%,
  drop 70.1%, term 69.8%. Backups do play worse (about -0.08 EPA per play), but
  correcting for it picks no more winners: the 70% prior and opponent adjustment
  already absorb most of it.
- Saturday 10-17: engine 20-12 on these games, drop 18-14, term 20-12. Rutgers at
  Maryland stays Maryland under both (77% engine, 75% drop, 77% term).
Recommendation: no change to the locked method.

## College football midweek, 2026-10-20 to 10-23 (Tuesday run, 2026-10-20)

ESPN became reachable from the session at about 3:02 PM Phoenix (the owner
allowed it in the account's network settings), so both college models ran.
Engine file `cfb_2026-10-20_picks.csv`, framework file
`prompt_cfb_2026-10-20_picks.csv` (Wednesday to Friday follow below). No-picks
applied to both with `set_nopick.py`.

**Tuesday 10-20 (logged before the 4:00 PM kickoffs):**

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Middle Tennessee at Florida International (4:00 PM) | FIU 78% | FIU 69% (29-22) |

No pick (both):
- Missouri State at Delaware: Delaware's starter unconfirmed: Nick Minicucci
  (season leader) is sidelined and true freshman Tyler Bell, who made his first
  start Oct 13, isn't confirmed for Tuesday (CBS, Oct 20). Missouri State also
  changed QBs last game (Henry Belin IV started Oct 14; Skyler Locklear started
  the first 5).
- South Alabama at Marshall: Marshall's starter unconfirmed: Zion Turner replaced
  Carlos Del Rio-Wilson (started every game) in the last game and Marshall is
  considering a change (WV MetroNews, Oct 20).

QB check: FIU's JJ Kohl and Middle Tennessee's Roman Gagliano have started every
game, with no injury news. South Alabama's Jared Hollins (LOW ATTEMPTS: 10 passes
in his last game) has no injury news; that game is a no-pick for Marshall anyway.

**Wednesday to Friday, 10-21 to 10-23** (engine `cfb_2026-10-21_picks.csv`
through `cfb_2026-10-23_picks.csv`, framework `prompt_cfb_2026-10-21_picks.csv`
through `prompt_cfb_2026-10-23_picks.csv`; logged Tuesday about 3:15 PM Phoenix).
Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| New Mexico State at Sam Houston (Wed 5:00 PM) | **Sam Houston 63%** | **New Mexico State 54%** (23-22) |
| Liberty at Kennesaw State (Thu 4:00 PM) | Liberty 71% | Liberty 68% (31-23) |
| East Carolina at Memphis (Thu 4:30 PM) | Memphis 73% | Memphis 51% (27-26) |
| Duke at Virginia (Fri 4:00 PM) | **Virginia 61%** | **Duke 57%** (30-27) |
| Army at Tulsa (Fri 5:30 PM) | Tulsa 58% | Tulsa 60% (33-29) |
| NC State at Stanford (Fri 7:30 PM) | NC State 57% | NC State 63% (34-28) |

No pick (both):
- James Madison at App State (Thu): Malachi Singleton (ankle) questionable for
  Thursday (Rotowire, Oct 19): hurt again in the Oct 17 win over Coastal
  Carolina, where Henry Hasselbeck played the 2nd half.
- Massachusetts at UConn (Fri): William "Pop" Watson III (ankle) a game-time
  decision: missed the last 2 games, practiced Monday, status to be decided
  Friday afternoon and in pregame warmups (Minuteman Command, Oct 19); Logan
  Inagawa made his first career start Oct 17.
- Air Force at Wyoming (Fri): Liam Szarka (leg) out for the season (KRDO, Oct 5);
  sophomore Evan Medders has started in his place since Oct 10.

Midweek totals: 7 picks in both models, 5 no-picks; they split on 2 (Sam Houston
/ New Mexico State, Virginia / Duke).

QB check (flags from the engine's QB report, news through Tuesday afternoon):
- New Mexico State (CHANGE SPLIT): Trey Hedden was pulled for performance, not
  injury, in the Sep 26 loss to New Mexico, Tony Sanchez opened the job (KFOX,
  Sep 28), and Adam Damante has started the 3 games since. That's a coach's
  choice with no injury news, so the pick stands.
- Liberty (LOW ATTEMPTS, 14 passes): Deshawn Purdie is the named starter; Ethan
  Vasko takes the short-yardage snaps (Liberty Champion, Oct 11). No injury
  news, so the pick stands.
- East Carolina (SPLIT): Emory Williams has started the last 3 and leads in
  attempts; no injury news (AP preview, Oct 18). James Madison (SPLIT): Camden
  Coleman has started 6 straight. Tulsa (SPLIT): Baylor Hayes is back from his
  September knee injury and has started the last 3. Army (LOW ATTEMPTS): option
  offense, Cale Hellums has started every game.
- No injury news found for Landyn Locke (Sam Houston), Rickie Collins (Kennesaw
  State), Marcus Stokes (Memphis), Beau Pribula (Virginia, listed starter Oct
  20), Walker Eget (Duke), CJ Bailey (NC State) or Davis Warren (Stanford).
- To recheck before kickoff: Singleton (App State, Thursday) and Watson (UMass,
  Friday warmups). A pick comes back only by re-running both models without the
  no-pick (into `/tmp/rerun`, then `merge_rerun.py`).

**Midweek graded Saturday 2026-10-24 (with the Saturday run).** No midweek
check-in was logged, so the no-picks above stood as logged. All 7 picks final;
graded files `cfb_2026-10-20_graded.csv` through `cfb_2026-10-23_graded.csv`
and the matching `prompt_cfb_*_graded.csv`. **Engine (official) 2-5, framework
4-3.**
- By win chance: engine 70%+ 2-1 (Liberty and Memphis right, FIU wrong), 60-70%
  0-2, under 60% 0-2; framework 60-70% 1-2, under 60% 3-1.
- Both splits went to the framework: New Mexico State won 30-24 at Sam Houston,
  Duke won 19-16 at Virginia.
- Missed by both: Middle Tennessee 26-23 at FIU (engine 78%), Army 38-35 at Tulsa,
  Stanford 31-28 over NC State.
- Off the record (no-pick games): engine 3-2, framework 1-4. Running total
  (`nopick_leans.py`): college engine 13-13, college framework 13-13.

## College football Saturday 2026-10-24 (engine and framework)

Saturday college run (check-in D), started about 4:10 AM Phoenix at the owner's
request. The engine ran first into `results/` (all 44 FBS games, none started),
then the QB check; the engine was re-run with the no-picks into `/tmp/rerun` and
merged (`merge_rerun.py`, all 44 refreshed), and the framework's first run went
straight into `results/` with the same no-picks. Files `cfb_2026-10-24_picks.csv`
(official) and `prompt_cfb_2026-10-24_picks.csv`. Engine: 2025 backtest weeks 4-8
70%+ 102-22, 60-70% 25-24, under 60% 31-26; 2026 so far out of sample 134-67.
Framework: 2022-2025 replay 1525-718 (68.0%); 2026 weeks 4-7 129-72. PDF:
`report_2026-10-24_cfb-saturday-nfl-sunday.pdf`.

44 games: **28 picks in both models, 16 no picks.** The models disagree on 4 (in
bold). The engine has 14 picks at 70% or more.

| Game (Phoenix kickoff) | Engine (official) | Framework (score) |
|---|---|---|
| LSU at Auburn (9:00 AM) | LSU 77% | LSU 83% (33-18) |
| Rice at Florida Atlantic (9:00 AM) | Florida Atlantic 67% | Florida Atlantic 79% (36-22) |
| Rutgers at Northwestern (9:00 AM) | Northwestern 88% | Northwestern 79% (36-23) |
| Texas Tech at Cincinnati (9:00 AM) | Texas Tech 66% | Texas Tech 51% (31-30) |
| West Virginia at TCU (9:00 AM) | TCU 85% | TCU 60% (31-27) |
| Western Michigan at Toledo (9:00 AM) | Toledo 73% | Toledo 76% (32-21) |
| Akron at Kent State (10:00 AM) | Kent State 64% | Kent State 67% (28-21) |
| Baylor at Kansas (10:00 AM) | **Kansas 64%** | **Baylor 55%** (27-25) |
| BYU at UCF (12:30 PM) | BYU 80% | BYU 80% (32-19) |
| Boston College at Georgia Tech (12:30 PM) | Georgia Tech 67% | Georgia Tech 52% (28-27) |
| Bowling Green at Buffalo (12:30 PM) | **Buffalo 62%** | **Bowling Green 52%** (24-23) |
| Iowa at Minnesota (12:30 PM) | Iowa 71% | Iowa 65% (30-24) |
| North Texas at Navy (12:30 PM) | **Navy 57%** | **North Texas 63%** (35-29) |
| Sacramento State at Ball State (12:30 PM) | Ball State 77% | Ball State 75% (32-21) |
| Texas A&M at Alabama (12:30 PM) | Alabama 85% | Alabama 77% (33-21) |
| Eastern Michigan at Ohio (1:00 PM) | Ohio 83% | Ohio 71% (33-24) |
| Louisiana at Southern Miss (2:00 PM) | Louisiana 55% | Louisiana 58% (28-25) |
| Boise State at Washington State (3:00 PM) | Boise State 70% | Boise State 80% (35-21) |
| Colorado at Oklahoma State (4:00 PM) | Oklahoma State 67% | Oklahoma State 63% (29-24) |
| Georgia State at Arkansas State (4:00 PM) | Georgia State 58% | Georgia State 77% (36-24) |
| Virginia Tech at Clemson (4:00 PM) | Virginia Tech 58% | Virginia Tech 83% (32-17) |
| Iowa State at Arizona (4:30 PM) | Arizona 81% | Arizona 78% (35-22) |
| Ole Miss at Texas (4:30 PM) | **Texas 64%** | **Ole Miss 52%** (27-26) |
| USC at Wisconsin (4:30 PM) | Wisconsin 63% | Wisconsin 51% (29-28) |
| Utah State at Texas State (4:30 PM) | Texas State 76% | Texas State 77% (33-21) |
| Vanderbilt at Kentucky (4:30 PM) | Kentucky 81% | Kentucky 67% (32-25) |
| North Dakota State at New Mexico (7:00 PM) | New Mexico 71% | New Mexico 65% (25-19) |
| Houston at Utah (7:15 PM) | Utah 73% | Utah 66% (35-28) |

No pick (both):
- Regular starter out: Pittsburgh at Miami (Mason Heintschel, torn ACL, out for
  the season; Holden Geriner expected to start), Miami (OH) at Central Michigan
  (David McComb out for the season), Oregon at Illinois (Dante Moore,
  concussion, out a 3rd straight game; Illinois' Katin Houser, broken hand, out),
  Michigan State at UCLA (Nico Iamaleava out for the season; Michigan State's
  Alessio Milivojevic questionable), Old Dominion at Louisiana Tech (Quinn
  Henicle out on the Sun Belt report).
- Starter questionable or doubtful: Oklahoma at Mississippi State (Kamario
  Taylor, toe, questionable), Hawai'i at Northern Illinois (Taron Dickens
  questionable), Kansas State at Arizona State (Avery Johnson doubtful on the Big
  12 report), UL Monroe at Troy (Goose Crowder, shoulder, questionable), San José
  State at Nevada (Carter Jones and AJ Bianco both questionable), San Diego State
  at Colorado State (Jayden Denegal, lower leg, questionable, no starter named),
  Syracuse at North Carolina (Steve Angeli, Achilles, questionable Oct 21;
  expected back as the starter but not confirmed; Amari Odom and Malachi Nelson
  out).
- Starter not named: Indiana at Michigan (Kyle Whittingham won't say; Bryce
  Underwood benched, Tommy Carr would make his first career start), California at
  SMU (Jaron-Keawe Sagapolutele expected back from a concussion, Tosh Lupoi hasn't
  named a starter), Tennessee at South Carolina (Josh Heupel declined to name one;
  CBS reports George MacIntyre while Faizon Brandon returns from a shoulder
  injury), UTSA at Tulane (QB changed last game, Trace Johnson for Kadin Semonza;
  Johnson expected again, no announcement or reason).
- The full reasons, with sources and dates, are in both picks files and the PDF.

How the QB rule was applied (news through Saturday about 4:30 AM Phoenix:
Rotowire's QB notes from the conference availability reports Oct 21-23, team and
local reports):
- Coach's choice with the old starter healthy keeps the pick: Iowa (Kirk Ferentz
  named Jeremy Hecklinski, who won at Washington, over a now-healthy Hank Brown,
  Oct 20), Washington State (Owen Eshelman named the starter after Caden Pinnick
  was benched; now his 2nd start, so no longer a first start), Colorado (Isaac
  Wilson; no change news since Deion Sanders named him over Julian Lewis), Texas
  (Steve Sarkisian sticking with Arch Manning, AP).
- SPLIT teams whose last starter also leads in attempts keep their picks, as on
  10-17: Clemson (Tait Reynolds starts; Christopher Vizzina, elbow, is the backup,
  SI Oct 20), UCF (Keyone Jenkins' 5th straight start; Alonza Barnett III,
  hamstring, questionable), Southern Miss (Landry Lyddy; Ethan Hampton, hand,
  out), Akron (Brayden Roggow; Cibastian Broughton, knee, questionable), Buffalo
  (Jason Wright; Elijah Holmes out for the season), Rutgers, Baylor, Ball State,
  Sacramento State, Vanderbilt, Utah State: no injury news.
- LOW ATTEMPTS: Rice and Navy run option offenses with the same starters; Western
  Michigan's Broc Lowry threw 8 times in a 21-14 win, Texas A&M's Marcel Reed 13
  in a blowout of The Citadel, Ohio's Nick Poulos 14 in a 48-7 win; New Mexico's
  Toa Fa'avae is "our guy moving forward" (Jason Eck). No injury news for any.
- Every other picked team: no QB injury or change news found.

Splits (engine official vs framework): Baylor at Kansas (Kansas 64% / Baylor
55%), Bowling Green at Buffalo (Buffalo 62% / Bowling Green 52%), North Texas at
Navy (Navy 57% / North Texas 63%), Ole Miss at Texas (Texas 64% / Ole Miss 52%).

**For the Saturday afternoon check (E):** Mississippi State's Taylor (the SEC's
final report at 11 AM Phoenix), Syracuse's Angeli, Troy's Crowder, Northern
Illinois' Dickens, Nevada's and San Diego State's starters and Tulane's could
all settle before kickoff; a pick comes back only by re-running both models
without that no-pick (into `/tmp/rerun`, then `merge_rerun.py`). The 9 AM games
(California, Michigan) start before that check.

**Troy pick not logged in time (Saturday ~9:33 AM Phoenix).** Goose Crowder was
cleared on the Sun Belt availability report ("will play," Rotowire, Oct 24), and
both models were re-run with Troy's no-pick removed before the 1:00 PM kickoff
(engine merged locally, framework re-run into `/tmp/rerun`), but the session
stopped before anything was committed or pushed, and the framework file was
never updated. Under the log-before-kickoff rule, Troy stays an official no-pick
in both files as pushed. It lost (UL Monroe 21, Troy 14; engine 81%, framework
74%), so counting it would make Saturday engine 20-9 and framework 18-11. It is
in the off-the-record count below. Old Dominion stays a no-pick (Ryan Huff was
also ruled out Saturday).

**Saturday 2026-10-24 graded, Sunday 2026-10-25 about 2:45 AM Phoenix (owner's
request).** All 44 games final. Graded files `cfb_2026-10-24_graded.csv` and
`prompt_cfb_2026-10-24_graded.csv`; PDF
`report_2026-10-25_cfb-graded-nfl-weekend.pdf`. **Engine (official) 20-8,
framework 18-10.**
- By win chance: engine 70%+ 11-3, 60-70% 8-2, under 60% 1-3; framework 70%+
  11-2, 60-70% 6-2, under 60% 1-6.
- The 4 splits: engine 3-1 (Kansas 25-24 over Baylor, Buffalo 31-24 over
  Bowling Green, Texas 34-27 over Ole Miss right; Navy wrong, North Texas won
  49-39).
- Biggest misses: West Virginia 24-20 at TCU (engine TCU 85%), UCF 39-31 over
  BYU (engine 80%), Minnesota 13-10 over Iowa (engine 71%).
- Off the record (no-pick games): engine 9-7, framework 10-6. Running total
  (`nopick_leans.py`): college engine 22-20, college framework 23-19.

## College football midweek, 2026-10-27 to 10-30 (Tuesday run, 2026-10-27)

Both models' first runs, straight into `results/`, about 7:30 AM Pacific (before
Tuesday's 4:00 PM kickoffs). Engine `cfb_2026-10-27_picks.csv` through
`cfb_2026-10-30_picks.csv`, framework `prompt_cfb_2026-10-27_picks.csv` through
`prompt_cfb_2026-10-30_picks.csv`. No no-picks. Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Delaware at Western Kentucky (Tue 4:00 PM) | **Western Kentucky 55%** | **Delaware 60%** (29-26) |
| Sam Houston at Missouri State (Tue 5:00 PM) | Missouri State 54% | Missouri State 57% (27-24) |
| Kennesaw State at Middle Tennessee (Wed 4:00 PM) | **Kennesaw State 50%** | **Middle Tennessee 66%** (33-26) |
| Jacksonville State at New Mexico State (Wed 5:00 PM) | New Mexico State 52% | New Mexico State 56% (27-25) |
| Florida Atlantic at North Texas (Thu 4:30 PM) | North Texas 88% | North Texas 70% (38-30) |
| Troy at James Madison (Thu 4:30 PM) | James Madison 84% | James Madison 77% (32-20) |
| Tulane at Charlotte (Fri 4:00 PM) | Tulane 67% | Tulane 62% (30-25) |
| Baylor at UCF (Fri 4:30 PM) | **UCF 63%** | **Baylor 50%** (25-24) |
| Kent State at Sacramento State (Fri 7:30 PM) | **Sacramento State 52%** | **Kent State 69%** (28-20) |

The models agree on 5 of 9. Engine 70%+: North Texas, James Madison.

QB check (flags from the engine's QB report, news through Tuesday morning):
- Western Kentucky (SPLIT): the coach benched Rodney Tisdale Jr. for Brock
  Glenn, who started the last 2 wins and leads in attempts (Yahoo,
  Oct 27; "Brock Glenn is likely to start", The Towel Rack, Oct 27). Coach's
  choice, no injury: pick stands.
- Delaware (SPLIT): Nick Minicucci back from his leg injury for a 2nd straight
  start (Yahoo and The Towel Rack, Oct 27).
- Missouri State (SPLIT): Henry Belin IV replaced Skyler Locklear as the starter
  (March2ThePod preview, Oct 26); no injury news.
- New Mexico State (CHANGE SPLIT): Adam Damante, 4 straight starts since Trey
  Hedden was pulled for performance (as on 10-20); no injury news.
- James Madison (SPLIT): Camden Coleman, 7 straight starts. Troy (LOW ATTEMPTS):
  Goose Crowder (shoulder) probable on the Sun Belt availability report
  (RotoWire, Oct 26); he played last game.
- Tulane (CHANGE SPLIT): Trace Johnson has started the last 2 in place of Kadin
  Semonza, a coach's choice ("the quarterback we think gives us the best chance
  to win", Will Hall); no injury; Hall backed him after the UTSA loss ("I
  thought Trace played tough", Oct 25). Pick stands.
- Charlotte (CHANGE SPLIT): Conner Harrell has started the last 2 after Cole
  Gonzales was benched (RotoWire, Oct 12: "appears set to stay under center");
  no injury. Pick stands; the Friday lock re-checks.
- UCF (SPLIT): Scott Frost confirmed Keyone Jenkins starts ("Keyone's going to
  start again"); evaluated after the BYU game and cleared ("He's fine. The
  trainers cleared him", 247Sports/On3, Oct 26). Baylor (SPLIT): DJ Lagway, 4
  straight starts, no injury news (interim coach Joe Klanderman after Dave
  Aranda's firing).
- No injury news found for Landyn Locke (Sam Houston), Rickie Collins (Kennesaw
  State), Roman Gagliano (Middle Tennessee), Caden Creel (Jacksonville State),
  Tayven Jackson (North Texas), Caden Veltkamp (Florida Atlantic), Dru DeShields
  (Kent State) or Jackson Sharman (Sacramento State).

**Tuesday 10-27 graded, Wednesday 2026-10-28 about 10:20 AM Phoenix (owner's
request).** Both games final. Graded files `cfb_2026-10-27_graded.csv` and
`prompt_cfb_2026-10-27_graded.csv`. **Engine (official) 1-1, framework 2-0.**
- Missouri State 24-3 over Sam Houston: both right (engine 54%, framework 57%).
- Delaware 35-21 at Western Kentucky: the split went to the framework (engine
  Western Kentucky 55%, framework Delaware 60%).
- Sam Houston's Landyn Locke was ruled out Tuesday (Rotowire, Oct 27) after the
  picks were logged; DJ Bailey started. No check-in runs Tuesday afternoon, so
  the pick stood as logged and counts in both records (log-before-kickoff rule).
- Wednesday 10-28 QB recheck (news through about 10:30 AM Phoenix): Rotowire's
  college injury feed (Oct 27) and searches on Wednesday's four starters showed
  no new injury or change news for the Wednesday to Friday starters above, so the
  picks stand as logged. Rotowire lists UCF's Alonza Barnett questionable for
  Friday; he's the backup (Keyone Jenkins starts). Check-ins B and C recheck
  each day's games.

**Friday 10-30 QB check (Friday lock, about 1:45 PM Pacific).** No change; the
three Friday picks stand as logged.
- Tulane at Charlotte: Trace Johnson starts again for Tulane (first road start;
  Will Hall: "now we're with Trace Johnson", SI, Oct 28; Crescent City Sports and
  DraftKings Network previews, Oct 29-30); no QB injury reported. Conner Harrell
  starts for Charlotte (3rd straight, DraftKings Network, Oct 30).
- Baylor at UCF: DJ Lagway (Baylor) and Keyone Jenkins (UCF) named as the QBs in
  Friday previews (SI, RotoWire, Oct 30); no injury news on either.
- Kent State at Sacramento State: Dru DeShields and Jackson Sharman, every start
  this season for both; no injury news (AP preview).

**Wednesday to Friday 10-28 to 10-30 graded, Saturday run (D), 2026-10-31 about
6:45 AM Pacific.** All 7 games final. Graded files `cfb_2026-10-28_graded.csv`
to `cfb_2026-10-30_graded.csv` and the `prompt_cfb_` versions. **Engine
(official) 4-3, framework 3-4.**
- Kennesaw State 44-28 at Middle Tennessee: the split went to the engine
  (Kennesaw State 50%; framework Middle Tennessee 66%).
- Jacksonville State 24-0 at New Mexico State: both wrong (engine 52%, framework
  56%).
- North Texas 48-41 over Florida Atlantic: both right (88%, 70%).
- Troy 24-21 at James Madison: both wrong (engine 84%, framework 77%).
- Tulane 38-31 at Charlotte: both right (67%, 62%).
- Baylor 41-9 at UCF: the split went to the framework (engine UCF 63%,
  framework Baylor 50%). UCF benched Keyone Jenkins for Alonza Barnett III during
  the game.
- Sacramento State 31-10 over Kent State: the split went to the engine
  (Sacramento State 52%; framework Kent State 69%).
- **Midweek 10-27 to 10-30 total: engine 5-4, framework 5-4.**

## College football Saturday 2026-10-31 (engine and framework)

Owner's request, Wednesday 2026-10-28: an early first run of Saturday's 47-game
slate. Engine first run straight into `results/` (about 10:20 AM Phoenix), then
re-run with the no-picks into a scratch folder and merged with
`merge_rerun.py`; framework first run with the same no-picks and `--starter
"Iowa State=Jaylen Raynor"` straight into `results/`. Files
`cfb_2026-10-31_picks.csv` and `_qbs.csv` (engine),
`prompt_cfb_2026-10-31_picks.csv` (framework). The models use plays through
Tuesday's games; the Saturday run (check-in D) re-runs both with Wednesday to
Friday's games and the latest QB news. Engine: 2025 backtest weeks 4-8, 70%+
102-23; 2026 out of sample 169-88. Framework: replay 1524-719 (67.9%); 2026
weeks 4-8 162-95. Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Arizona at Texas Tech (9:00 AM) | **Texas Tech 53%** | **Arizona 60%** (29-25) |
| Boston College at Duke (9:00 AM) | Duke 60% | Duke 72% (31-22) |
| Bowling Green at Western Michigan (9:00 AM) | Western Michigan 81% | Western Michigan 67% (29-22) |
| California at NC State (9:00 AM) | NC State 70% | NC State 67% (32-25) |
| Notre Dame at Navy (9:00 AM) | Notre Dame 93% | Notre Dame 83% (37-21) |
| SMU at Syracuse (9:00 AM) | SMU 68% | SMU 74% (33-23) |
| UAB at South Florida (9:00 AM) | South Florida 72% | South Florida 77% (32-20) |
| Wisconsin at Iowa (9:00 AM) | Iowa 56% | Iowa 59% (27-24) |
| Auburn at Ole Miss (9:45 AM) | Ole Miss 77% | Ole Miss 75% (33-22) |
| Louisiana Tech at South Alabama (12:00 PM) | Louisiana Tech 79% | Louisiana Tech 64% (33-28) |
| Stanford at Louisville (12:15 PM) | Louisville 94% | Louisville 81% (40-25) |
| Colorado State at Utah State (12:30 PM) | Utah State 67% | Utah State 52% (32-31) |
| Florida International at Liberty (12:30 PM) | Liberty 89% | Liberty 69% (27-20) |
| Kansas at TCU (12:30 PM) | TCU 59% | TCU 57% (27-24) |
| Minnesota at Indiana (12:30 PM) | Indiana 93% | Indiana 85% (34-17) |
| Southern Miss at UL Monroe (12:30 PM) | **UL Monroe 58%** | **Southern Miss 54%** (27-26) |
| Utah at Cincinnati (12:45 PM) | Utah 85% | Utah 67% (33-26) |
| Virginia at Wake Forest (12:45 PM) | Wake Forest 83% | Wake Forest 76% (34-23) |
| Purdue at Penn State (1:15 PM) | Penn State 68% | Penn State 70% (34-26) |
| South Carolina at Oklahoma (1:15 PM) | Oklahoma 72% | Oklahoma 55% (25-24) |
| Clemson at Florida State (4:00 PM) | Florida State 68% | Florida State 61% (29-25) |
| Oklahoma State at Iowa State (4:00 PM) | Oklahoma State 64% | Oklahoma State 66% (33-26) |
| Miami at North Carolina (4:30 PM) | Miami 77% | Miami 81% (35-20) |
| Missouri at Arkansas (4:45 PM) | Missouri 65% | Missouri 76% (31-20) |
| Army at Memphis (5:00 PM) | Memphis 74% | Memphis 73% (37-27) |
| Texas State at Boise State (7:00 PM) | Boise State 74% | Boise State 75% (35-24) |
| Northern Illinois at UNLV (7:30 PM) | UNLV 91% | UNLV 87% (38-19) |
| Oregon State at Fresno State (8:00 PM) | Oregon State 67% | Oregon State 58% (31-28) |

28 picks in both models, 19 no-picks; they agree on 26 of 28. Engine 70%+ (16):
Louisville, Indiana, Notre Dame, UNLV, Liberty, Utah, Wake Forest, Western
Michigan, Louisiana Tech, Ole Miss, Miami, Boise State, Memphis, South Florida,
Oklahoma, NC State.

No pick (both; news through Wednesday about 10:30 AM Phoenix, before the
conference availability reports):
- Regular starter out: Illinois at Maryland (Katin Houser, broken throwing hand,
  out 3-5 more weeks per AP Oct 28; Michael Clayton II starts), Northwestern at
  Oregon (Dante Moore, concussion, out for the season), Nevada at UCLA (UCLA's
  Nico Iamaleava out with a knee injury, Ty Dieffenbach starts; Nevada's starter
  also unknown), Ohio State at USC (Julian Sayin, throwing arm, out; Ryan Day
  planning to be without him through the postseason; Luke Fahey or Tavien St.
  Clair not decided), Mississippi State at Texas (Kamario Taylor out for the
  season, toe surgery), Georgia Tech at Pittsburgh (Mason Heintschel, torn ACL,
  out for the season), Washington State at San Diego State (Jayden Denegal,
  ankle, day-to-day; Sean Lewis says Stone Saunders starts), UConn at Air Force
  (Liam Szarka out for the season, Evan Medders off the depth chart; Josh
  Johnson or Howard Fisher IV not named).
- Starter questionable or day-to-day: Kansas State at Colorado (Avery Johnson
  day-to-day, Collin Klein doesn't know his starter), Arizona State at BYU (Mikey
  Keene "honestly questionable", Jake Fette if not), UTEP at North Dakota State
  (EJ Colson Jr., hand, day-to-day), App State at Georgia Southern (Max Johnson,
  throwing shoulder, questionable after the bye).
- Starter not named: Michigan at Rutgers (Whittingham "to be determined" though
  On3 reports Tommy Carr; Rutgers' Dylan Lonergan also hurt), Marshall at Old
  Dominion (Gibson expects all three QBs to play; Old Dominion's Quinn Henicle
  missed the last game), Coastal Carolina at Georgia State (Ayden Pereira or
  Cameran Brown), Temple at East Carolina (Emory Williams benched for Mitch
  Griffis last game; no report naming the starter), Florida at Georgia (Jon
  Sumrall won't name Aaron Philo or Tramell Jones Jr.), New Mexico at San José
  State (Weaver, Rolovich or McDaniel; unsettled), Washington at Nebraska (Jedd
  Fisch waits until game time; Demond Williams Jr. back from a fractured rib or
  Elijah Brown).
- The full reasons, with sources and dates, are in both picks files and the PDF.

Off the record (no-pick games): engine Maryland, Michigan, Marshall, Georgia
State, Colorado, East Carolina, Air Force, BYU, Georgia, Oregon, North Dakota
State, New Mexico, UCLA, Georgia Southern, Washington State, Pittsburgh, Texas,
Ohio State, Nebraska; the framework leans the same way except Kansas State,
Northwestern and San Diego State.

How the QB rule was applied:
- Coach named the starter, pick stands: Iowa (Kirk Ferentz: "right now, we plan
  to start Hank Brown", the season leader, over Jeremy Hecklinski, Oct 27), Iowa
  State (Jimmy Rogers: "We're going to go with Jaylen" Raynor, benched in the 2nd
  half last game for a fumble; the framework re-run with `--starter`).
- Regular starter back and healthy, pick stands: Colorado State (Hauss Hejny
  returned from his early-season injury last game), Syracuse (Steve Angeli back
  from the Achilles injury, 34 passes last game), California (Jaron-Keawe
  Sagapolutele back from the concussion), Duke (Walker Eget's finger: "nothing
  structurally wrong", he returned in the 2nd half Oct 23).
- SPLIT or LOW ATTEMPTS with the season leader starting and no injury news, pick
  stands: Navy (Jackson Gutierrez, option offense, 6 straight starts), Wisconsin
  (Colton Joseph), South Alabama (Jared Hollins), Louisiana Tech (Blake Baker),
  Utah State (Grady Brosterhous), UL Monroe (Aidan Armenta), Southern Miss
  (Landry Lyddy), Clemson (Tait Reynolds), Army (Cale Hellums, option).
- Every other picked team: no QB injury or change news found (team searches,
  Rotowire's injury feed, Covers' Oct 28 injury list). Georgia's Gunner Stockton
  had a shoulder stinger Oct 17 and returned in that game; Georgia's game is a
  no-pick for Florida anyway.
- Data note: ESPN's box scores for 3 games this season have no passing stats
  (Bethune-Cookman at UCF Sep 3, Missouri at Ole Miss Oct 17, North Dakota State
  at New Mexico Oct 24), so the QB report skips them (Missouri and New Mexico show
  an older "last game"). Their play-by-play is complete, so the ratings include
  them; the play text shows the usual starters (Austin Simmons, Trinidad
  Chambliss, Toa Fa'avae with 14 passes, Nathan Hayes).

**For the next check-ins:** the conference availability reports (Wednesday to
Friday evenings) and Saturday's 2-hour reports can settle Kansas State, Arizona
State, UTEP, Georgia Southern, Florida, Michigan, Georgia State, Washington and
the others. A pick comes back only by re-running both models without that
no-pick (into a scratch folder, then `merge_rerun.py`); the Saturday run
re-runs everything anyway.

**Saturday run (D), 2026-10-31, about 6:45-7:15 AM Pacific: QBs re-checked, both
models re-run with Wednesday to Friday's games and merged.** Engine re-run into
`/tmp/rerun`, merged with `merge_rerun.py` (all 47 games still "pre"); framework
the same, with `--starter "Iowa State=Jaylen Raynor"`. News checked: Friday's
Big Ten/ACC/SEC/Big 12/Sun Belt availability reports as reported by On3,
247Sports, RotoWire and SI's Week 9 QB injury tracker (Oct 31), DraftEdge's
injury list (Oct 30, 9 PM), team previews. Win chances moved by 0-2 points; no
pick flipped.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Arizona at Texas Tech (9:00 AM) | **Texas Tech 52%** | **Arizona 59%** (29-25) |
| Boston College at Duke (9:00 AM) | Duke 59% | Duke 71% (31-22) |
| Bowling Green at Western Michigan (9:00 AM) | Western Michigan 81% | Western Michigan 68% (29-22) |
| California at NC State (9:00 AM) | NC State 71% | NC State 67% (33-26) |
| Notre Dame at Navy (9:00 AM) | Notre Dame 94% | Notre Dame 82% (36-21) |
| SMU at Syracuse (9:00 AM) | SMU 68% | SMU 73% (33-23) |
| UAB at South Florida (9:00 AM) | South Florida 72% | South Florida 76% (32-20) |
| Wisconsin at Iowa (9:00 AM) | Iowa 56% | Iowa 60% (27-23) |
| Auburn at Ole Miss (9:45 AM) | Ole Miss 76% | Ole Miss 75% (33-22) |
| Louisiana Tech at South Alabama (12:00 PM) | Louisiana Tech 79% | Louisiana Tech 65% (33-27) |
| Stanford at Louisville (12:15 PM) | Louisville 95% | Louisville 82% (40-25) |
| Colorado State at Utah State (12:30 PM) | Utah State 68% | Utah State 52% (32-31) |
| Florida International at Liberty (12:30 PM) | Liberty 88% | Liberty 69% (27-20) |
| Minnesota at Indiana (12:30 PM) | Indiana 93% | Indiana 85% (34-17) |
| Southern Miss at UL Monroe (12:30 PM) | **UL Monroe 59%** | **Southern Miss 54%** (27-26) |
| Utah at Cincinnati (12:45 PM) | Utah 85% | Utah 67% (33-26) |
| Virginia at Wake Forest (12:45 PM) | Wake Forest 82% | Wake Forest 76% (34-23) |
| Purdue at Penn State (1:15 PM) | Penn State 69% | Penn State 68% (33-26) |
| South Carolina at Oklahoma (1:15 PM) | Oklahoma 72% | Oklahoma 55% (25-23) |
| Clemson at Florida State (4:00 PM) | Florida State 68% | Florida State 60% (29-25) |
| Oklahoma State at Iowa State (4:00 PM) | Oklahoma State 63% | Oklahoma State 65% (32-26) |
| Miami at North Carolina (4:30 PM) | Miami 77% | Miami 81% (35-20) |
| Missouri at Arkansas (4:45 PM) | Missouri 67% | Missouri 75% (31-20) |
| Army at Memphis (5:00 PM) | Memphis 72% | Memphis 73% (37-27) |
| Texas State at Boise State (7:00 PM) | Boise State 75% | Boise State 76% (35-24) |
| Northern Illinois at UNLV (7:30 PM) | UNLV 91% | UNLV 87% (38-19) |
| Oregon State at Fresno State (8:00 PM) | Oregon State 65% | Oregon State 58% (32-29) |

27 picks in both models, 20 no-picks; they agree on 25 of 27. Engine 70%+ (16):
Louisville, Notre Dame, Indiana, UNLV, Liberty, Utah, Wake Forest, Western
Michigan, Louisiana Tech, Miami, Ole Miss, Boise State, South Florida, Memphis,
Oklahoma, NC State.

Changes since Wednesday:
- **Kansas at TCU: now a no-pick (both models).** Kansas' Isaiah Marshall was
  downgraded from probable to questionable on Thursday's Big 12 report, a
  game-time decision (On3 via RotoWire, Oct 30); Cole Ballard would start. Was
  TCU 59% (engine) / 57% (framework).
- Reasons updated, still no picks: Illinois at Maryland (Houser upgraded to
  questionable, not confirmed), Michigan at Rutgers (Lonergan ruled out on
  Friday's report; Michigan's starter still not confirmed by the team), Marshall
  at Old Dominion (Henicle doubtful, Huff in line; Marshall unnamed), Kansas State
  at Colorado (Avery Johnson ruled out, Knuth doubtful, starter not named),
  Coastal Carolina at Georgia State (Cameran Brown doubtful, Pereira expected),
  Temple at East Carolina (no on-record starter; Temple's Sheppard listed
  questionable), Florida at Georgia (ESPN sources say Philo starts; not
  confirmed by Sumrall), Arizona State at BYU (Keene a game-time decision), UTEP
  at North Dakota State (Colson questionable), New Mexico at San José State (ESPN
  sources say Luke Weaver starts; not announced), Nevada at UCLA, App State at
  Georgia Southern (Max Johnson probable, not confirmed), Washington State at San
  Diego State, Ohio State at USC (Fahey expected to start; Sayin out), Washington
  at Nebraska (Williams probable, no word on role). Unchanged: Air Force,
  Oregon, Texas, Pittsburgh.

How the QB rule was applied to picked teams with news:
- Syracuse (SMU at Syracuse): Steve Angeli was questionable on Wednesday's ACC
  report; on Friday's report his status improved and he's expected to play
  (RotoWire, Oct 30); he isn't on DraftEdge's Oct 30 night list and he played
  last game. Pick stands (same as Troy's Crowder on 10-29). SI's Saturday tracker
  still says questionable (from the earlier report).
- Duke: Walker Eget (finger) carries no designation on the final ACC report (SI,
  Oct 31). Pick stands.
- Indiana: Josh Hoover probable and expected to start (SI tracker; Cignetti
  expects him "to be fine"); he played last game. Pick stands. Minnesota's
  Michael Merdinger (out for the year) is the backup.
- Iowa State: Jaylen Raynor expected to start, Connor Moberly questionable;
  framework uses Raynor.
- Southern Miss: Ethan Hampton (hand) probable but in an emergency role; Landry
  Lyddy starts again (SI, Oct 29). Pick stands.
- Every other picked team: no QB injury or change news found. Check-in E
  (11:50 AM) re-checks the noon-and-later games, including Kansas at TCU,
  Florida at Georgia, San José State and Georgia Southern.

**Saturday afternoon check (E), 2026-10-31, from 11:50 AM Pacific: QB news for
the noon-and-later games.** Both models re-run into `/tmp/rerun` with the
remaining no-picks (framework also `--starter "Iowa State=Jaylen Raynor"
--starter "UTEP=EJ Colson Jr."`) and merged with `merge_rerun.py`.

Changes:
- **UTEP at North Dakota State: pick back (both models).** EJ Colson Jr. (hand),
  UTEP's season starter, is listed to play on the Mountain West availability
  report and set to start (RotoWire, Oct 31). Engine North Dakota State 94%,
  framework North Dakota State 95% (39-10).
- Checked, still no picks: Florida at Georgia (RotoWire, Oct 31: the SEC
  availability report clears Aaron Philo to play; his start still rests on
  sources (ESPN, GatorsOnline, a team source to TV20), no announcement from Jon
  Sumrall or the team), Kansas at TCU (Isaiah Marshall still a game-time
  decision; no game-day update found), Arizona State at BYU (Mikey Keene limited
  in pregame warmups, game-time decision, Jake Fette expected to start;
  RotoWire via 247Sports, Oct 31), Washington at Nebraska (game-time decision,
  CBS Sports), New Mexico at San José State (Luke Weaver's start still only per
  ESPN sources), App State at Georgia Southern (Max Johnson still probable, not
  confirmed), Nevada at UCLA, Ohio State at USC, Washington State at San Diego
  State, Air Force, East Carolina, Oregon, Texas, Pittsburgh.
- Picked teams: no new QB injury or change news found (SI Week 9 tracker,
  RotoWire, team news searches).

**Graded Saturday night, 2026-10-31 about 8:35 PM Phoenix (owner's request), 25 of
28 picks final.** Graded files `cfb_2026-10-31_graded.csv` and
`prompt_cfb_2026-10-31_graded.csv`. **Engine (official) 20-5, framework 20-5**;
Texas State at Boise State, Northern Illinois at UNLV and Oregon State at Fresno
State not final (check-in F finishes the grading).
- Engine 70%+: 14-1 (Oklahoma 72% lost 42-25 to South Carolina); Boise State
  and UNLV pending.
- Missed by both: SMU 27-30 at Syracuse, South Carolina 42-25 at Oklahoma,
  Oklahoma State 49-51 at Iowa State, Clemson 36-24 at Florida State.
- The 2 splits went 1-1: Texas Tech 34-26 over Arizona (engine), Southern Miss
  35-21 at UL Monroe (framework).
- Off the record (19 no-pick games): engine leans 14-5, framework 13-6. Running
  totals (`nopick_leans.py`): college engine 36-25, framework 36-25.
- Midweek plus Saturday (10-27 to 10-31) so far: engine 25-9, framework 25-9.

**Final grade, Sunday check (F), 2026-11-01 about 8:45 AM Pacific: all 28 picks
final.** `grade_picks.py` re-run on both files. **Engine (official) 22-6,
framework 22-6.** The 3 late games: Boise State 46-45 over Texas State (engine
75%: W), UNLV 31-24 over Northern Illinois (engine 91%: W), Fresno State 38-22
over Oregon State (both picked Oregon State: L).
- Engine 70%+: 16-1. Framework 70%+: 13-1 (SMU 73% lost).
- Missed by both: SMU, Oklahoma, Oklahoma State, Florida State, Oregon State.
- Midweek plus Saturday (10-27 to 10-31): engine 27-10, framework 27-10.

## College football midweek, 2026-11-03 to 11-06 (owner's request, Saturday night 2026-10-31)

Owner's request, Saturday 2026-10-31 about 7:20 PM Phoenix: run both engines and
make a PDF of results so far and upcoming picks. Both models' first runs of next
week's midweek games, straight into `results/`: Tuesday to Thursday about 7:25 PM
(engine 2026 out of sample 203-98; framework 2026 weeks 4-9 195-106), Friday
after Washington at Nebraska went final, about 8:30 PM (engine 210-100;
framework 202-108), since Nebraska plays Friday. The models use every game final
when they ran (Tuesday to Thursday: before the 4 PM and later Saturday games
ended); the Tuesday run (check-in A) re-runs all of them through `/tmp/rerun` and
`merge_rerun.py` with complete data and Tuesday's news. Files
`cfb_2026-11-03_picks.csv` to `cfb_2026-11-06_picks.csv` (engine) and the
`prompt_cfb_` versions. They agree on all 7 picks.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Ohio at Akron (Tue 5:00 PM) | Ohio 75% | Ohio 77% (34-22) |
| Ball State at Massachusetts (Wed 5:00 PM) | Massachusetts 57% | Massachusetts 79% (33-20) |
| Toledo at Sacramento State (Wed 5:00 PM) | Toledo 84% | Toledo 89% (34-14) |
| UTSA at Florida Atlantic (Thu 5:30 PM) | UTSA 64% | UTSA 53% (33-32) |
| James Madison at Southern Miss (Thu 6:00 PM) | James Madison 82% | James Madison 70% (30-22) |
| Virginia Tech at SMU (Fri 5:00 PM) | SMU 71% | SMU 59% (30-26) |
| TCU at Arizona (Fri 8:15 PM) | Arizona 67% | Arizona 68% (30-22) |

Engine 70%+: Toledo, James Madison, Ohio, SMU.

**Data gap found:** ESPN's summary for Washington at Nebraska (10-31, final
17-10) had no play-by-play and no player stats when the Friday run downloaded it
(re-checked about 8:35 PM: still none), so neither model's ratings include that
game. It's the only 2026 game in the cache without plays. The engine caches
finished games for good, so a later re-run in the same session must delete
`cfb/cache/summary/401858504.json` first; fresh sessions download it again.

No pick (both):
- Nebraska at Illinois (Fri): ESPN has no play-by-play yet for Nebraska's 10-31
  game vs Washington (box score only), so neither model's ratings include it.
  Katin Houser (Illinois) returned from his hand surgery and started 10-31 (On3).
- South Florida at East Carolina (Fri): South Florida's Michael Van Buren Jr. left
  the 10-31 game vs UAB in the 1st quarter after a hit near the head, status
  unknown; Luke Kromenhoek finished (WUSF, RotoWire, Oct 31). East Carolina's
  starter is also unsettled: Emory Williams (hurt Oct 22) didn't play 10-31
  despite being listed ready on the AAC availability report; Mitch Griffis
  started.
- New Mexico at Nevada (Fri): Nevada's starter not settled: Carter Jones (season
  leader) and AJ Bianco were questionable for 10-31 with no starter named by Jeff
  Choate; Bianco, Luke Duncan and Reeve Slone all threw passes in the 27-0 loss
  at UCLA (ESPN box score). New Mexico's Toa Fa'avae (LOW ATTEMPTS, option-style)
  started again.
- Buffalo at Miami (OH): David McComb out for the season (injured vs UConn in
  Week 4; The Miami Student, Oct 11); Caleb Heavner makes his 5th straight
  start (as on 10-17 and 10-24).
- Central Michigan at Eastern Michigan: Central Michigan's Angel Flores out for
  the season, Jadyn Glasser starts (Mitten Football, Oct 30); Eastern Michigan's
  Noah Kim (undisclosed injury) status for Nov 4 unclear, Brogan McCaughey
  started the last game (Mitten Football, Oct 28).

Off the record: engine Miami (OH) 78%, Eastern Michigan 52%, East Carolina 60%,
Nebraska 79%, New Mexico 70%; framework Miami (OH) 65%, Central Michigan 50%,
East Carolina 58%, Nebraska 78%, New Mexico 72%.

QB check (news through Saturday night; the MAC and Sun Belt availability reports
come out the day before each game):
- Ohio (SPLIT): Nick Poulos, the named starter, back from his early-October
  concussion for 3 straight starts (RotoWire, Oct 25). Akron (SPLIT): Brayden
  Roggow, 6 straight starts, no injury news (Akron Zipped Up, Oct 25).
- Massachusetts (SPLIT): William Watson III back from his ankle injury and
  started Oct 23 at UConn (RotoWire; 38 attempts); no news since. Ball State
  (SPLIT): Keldric Luster, no injury news since Oct 18.
- Sacramento State (SPLIT): Jackson Sharman started again Oct 30. Toledo (John
  Alan Richter), UTSA (Owen McCown), Florida Atlantic (Caden Veltkamp): not
  flagged, no injury news found.
- James Madison (SPLIT): Camden Coleman, 8 straight starts; JC Evans also plays
  in the team's two-quarterback system (Daily News-Record, Oct 30). Southern
  Miss (SPLIT): Landry Lyddy started and threw a TD in the 35-21 win at UL
  Monroe on 10-31 (WLBT); no injury reported.
- Friday's picked teams: SMU (Kevin Jennings), Virginia Tech (Ethan
  Grunkemeyer, idle 10-31), Arizona (Noah Fifita), TCU (Jaden Craig): not
  flagged, every start this season, no injury news found.

PDF: `report_2026-10-31_results-and-picks.pdf`, with a new "Season so far" page
(`make_report.py --season-summary 2026`, owner's request): every graded pick
this season for both sports and models, by week and by win-chance tier next to
the multi-season backtests, plus the off-the-record, closing-line and live-call
tallies. Read-only; nothing in the engines or frameworks changed.

**Tuesday run (check-in A), 2026-11-03, about 8:45 AM Pacific.** Both models
re-run for 11-03 to 11-06 with complete data through the weekend and Tuesday's
news (engine one date at a time, framework all four dates; fresh session, so
the full cache was downloaded) into `/tmp/rerun` and merged with
`merge_rerun.py` (12 games refreshed, none started). Engine 2026 out of sample
211-102; framework 2026 weeks 4-9 200-113.

**Pick back: Nebraska at Illinois** (engine Nebraska 76%, framework Nebraska
76%, 34-23). ESPN now has the play-by-play for Washington at Nebraska (10-31;
23 drives, 187 plays), so both models include it. QBs: Katin Houser started
and finished Illinois' 20-17 win over Maryland after being cleared early from
his hand surgery (CSOM Sports, Nov 2); Anthony Colandrea has started every
Nebraska game, no injury news.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| Ohio at Akron (Tue 5:00 PM) | Ohio 76% | Ohio 77% (34-22) |
| Ball State at Massachusetts (Wed 5:00 PM) | Massachusetts 60% | Massachusetts 79% (33-20) |
| Toledo at Sacramento State (Wed 5:00 PM) | Toledo 84% | Toledo 89% (34-14) |
| UTSA at Florida Atlantic (Thu 5:30 PM) | UTSA 66% | UTSA 52% (33-32) |
| James Madison at Southern Miss (Thu 6:00 PM) | James Madison 83% | James Madison 69% (29-21) |
| Virginia Tech at SMU (Fri 5:00 PM) | SMU 72% | SMU 60% (30-26) |
| Nebraska at Illinois (Fri 6:00 PM) | Nebraska 76% | Nebraska 76% (34-23) |
| TCU at Arizona (Fri 8:15 PM) | Arizona 68% | Arizona 68% (30-22) |

The models agree on all 8 picks. Engine 70%+: Toledo, James Madison, Ohio,
Nebraska, SMU.

Still no pick (both; reasons refreshed):
- Buffalo at Miami (OH) (Tue): David McComb out for the season; Caleb Heavner
  makes his 6th straight start.
- Central Michigan at Eastern Michigan (Wed): Noah Kim (undisclosed injury)
  status uncertain, Brogan McCaughey started the last game (CM Life, Nov 2);
  Central Michigan's Angel Flores out for the season, Jadyn Glasser starts.
- South Florida at East Carolina (Fri): Michael Van Buren Jr.'s injury
  (left 10-31 early) undisclosed, availability unknown (Tampa Bay Times via
  Yahoo, Nov 1); East Carolina's starter also unsettled.
- New Mexico at Nevada (Fri): Nevada's starter not named; no announcement found
  since 10-31.

Off the record: engine Miami (OH) 78%, Eastern Michigan 51%, East Carolina 59%,
New Mexico 70%; framework Miami (OH) 66%, Eastern Michigan 51%, East Carolina
58%, New Mexico 72%.

QB check (news through Tuesday morning): no new injury or change news for
Ohio (Nick Poulos), Akron (Brayden Roggow), Massachusetts, Ball State,
Sacramento State, Toledo, UTSA, Florida Atlantic, James Madison, Southern Miss,
SMU, Virginia Tech, TCU or Arizona. The MAC, Sun Belt and Big Ten availability
reports come the day before or the day of each game: check-in B (Wed, Thu) and
C (Fri) check them.

**Midweek check (check-in B), Wednesday 2026-11-04, about 3:50 PM Pacific.**
No pick changed. Reason refreshed in both models (`set_nopick.py`):
- Central Michigan at Eastern Michigan (Wed): Noah Kim (undisclosed injury)
  ruled out (MAC availability report, Nov 4, via RotoWire; Mitten Football
  live blog); Brogan McCaughey starts; Central Michigan's Angel Flores out for
  the season, Jadyn Glasser starts. Still no pick: Eastern Michigan's regular
  starter is out.

Picks stand: Ball State at Massachusetts (Keldric Luster, William Watson III)
and Toledo at Sacramento State (John Alan Richter, Jackson Sharman): no QB
injury or change news found (ESPN preview Nov 1, game previews Nov 4).

**Midweek check (check-in B), Thursday 2026-11-05, about 3:50 PM Pacific.**
- **New no pick: James Madison at Southern Miss** (was James Madison in both,
  engine 83%, framework 69%): Landry Lyddy (last 6 starts) benched; John White
  makes his first start of the season with 2 passes this season (SI, Nov 5;
  RotoWire via PineBelt Sports, Nov 5). First start with very little playing
  time (METHOD.md section 6). Applied to both models with `set_nopick.py`.
  Off the record: engine James Madison 83%, framework James Madison 69%.
- Pick stands: UTSA at Florida Atlantic (Owen McCown, Caden Veltkamp): no QB
  injury or change news found (CBS12 preview Nov 5, game previews Nov 5).
- NFL Thursday, Jaguars at Ravens: still no pick (Lamar Jackson out, IR; Joe
  Fagnano starts; Tyler Huntley out). Inactives not yet posted at check time;
  no news against Trevor Lawrence starting.

**Friday lock (check-in C), 2026-11-06, about 1:50 PM Pacific: Friday's
college QB check.** No pick changed.
- Picks stand: Virginia Tech at SMU (Ethan Grunkemeyer, Kevin Jennings: neither
  on the ACC availability report, Nov 6), Nebraska at Illinois (Anthony
  Colandrea, no injury news; Katin Houser no designation, Huskers Today preview
  Nov 6; final Big Ten report due before kickoff), TCU at Arizona (Jaden Craig,
  Noah Fifita: neither on the injury lists, Nov 6).
- Still no pick, reason refreshed (`set_nopick.py`): South Florida at East
  Carolina: Michael Van Buren Jr. unconfirmed, no official word as of midday
  Friday, AAC availability report pending, Luke Kromenhoek the likely
  alternative (Heavy, Nov 6); East Carolina's starter also unsettled.
- Still no pick: New Mexico at Nevada: no Nevada starter named in any news found
  through Friday.

**Friday lock, second session (same check-in, about 2:30 PM Pacific).** A
duplicate run of check-in C reached the same picks and no-picks independently
(NFL: Rams pick back; Seahawks and Browns no-picks; college: no change). Two
no-pick reasons corrected with `set_nopick.py` (no pick changed):
- Giants at Eagles: Jalen Hurts (blood clots) on season-ending IR; Joe Milton
  named the starter over Tanner McKee (NFL Network/ESPN, Nov 4; NFL.com, CBS,
  Inquirer). The earlier reason said McKee starts.
- New Mexico at Nevada: Carter Jones (season leader, 4 starts) out with injury;
  AJ Bianco (ankle) gets his 2nd start (Nevada Sports Net pre-game, Nov 6;
  Albuquerque Journal depth chart lists Bianco first). Still no pick: the
  regular starter is out.
Stafford: the Rams' own Friday report page couldn't be read from this session
either; NFL.com shows him a full participant with no game status. Check-in F
confirms with the inactives (8:30 AM Pacific, before the 10 AM kickoff).
PDF re-made with the corrected reasons.

**Midweek graded (Saturday run, check-in D, 2026-11-07 about 7:00 AM Pacific).**
Graded files `cfb_2026-11-03_graded.csv` to `cfb_2026-11-06_graded.csv` and the
`prompt_cfb_` versions. **Engine (official) 5-2, framework 5-2** (no splits).
- Wins (both): Ohio 28-20 at Akron, Massachusetts 31-30 over Ball State, Toledo
  20-17 at Sacramento State, SMU 51-28 over Virginia Tech, Arizona 29-28 over TCU.
- Losses (both): UTSA (lost 60-29 at Florida Atlantic), Nebraska (lost 24-13 at
  Illinois).
- Engine 70%+: 3-1 (Ohio, Toledo, SMU won; Nebraska 76% lost).
- Off the record (5 no-pick games): engine 3-2, framework 3-2 (Miami (OH) and
  Eastern Michigan wrong; James Madison, East Carolina, New Mexico right).
  Running totals (`nopick_leans.py`): college engine 39-27, framework 39-27.
## College football Saturday 2026-11-07 (engine and framework)

Saturday run (check-in D), about 6:45-7:55 AM Pacific. Engine first run straight
into `results/`, then re-run with the no-picks into `/tmp/rerun` and merged with
`merge_rerun.py` (51 games refreshed, none started); framework first run with the
same no-picks and `--starter "Marshall=Zion Turner"` straight into `results/`.
Files `cfb_2026-11-07_picks.csv` and `_qbs.csv` (engine),
`prompt_cfb_2026-11-07_picks.csv` (framework). Engine: 2025 backtest weeks 4-8,
70%+ 103-22; 2026 out of sample 209-104. Framework: 2026 weeks 4-9 202-111.
Splits in bold.

| Game (Phoenix kickoff) | Engine (official) | Framework |
|---|---|---|
| BYU at Utah (10:00 AM) | Utah 77% | Utah 62% (30-25) |
| Texas at Missouri (10:00 AM) | **Texas 62%** | **Missouri 62%** (25-20) |
| Iowa State at Baylor (10:00 AM) | Baylor 79% | Baylor 83% (34-19) |
| Florida State at Boston College (10:00 AM) | **Florida State 56%** | **Boston College 61%** (31-27) |
| North Carolina at UConn (10:00 AM) | **North Carolina 74%** | **UConn 52%** (29-28) |
| Tulsa at Tulane (10:00 AM) | Tulsa 72% | Tulsa 68% (30-23) |
| Duke at NC State (10:30 AM) | **NC State 52%** | **Duke 64%** (32-26) |
| Maryland at Purdue (10:30 AM) | Purdue 67% | Purdue 51% (29-28) |
| Arkansas at Auburn (10:45 AM) | Auburn 67% | Auburn 59% (28-24) |
| Texas A&M at South Carolina (1:00 PM) | South Carolina 60% | South Carolina 71% (31-22) |
| UL Monroe at Arkansas State (1:00 PM) | Arkansas State 70% | Arkansas State 57% (30-27) |
| Delaware at Kennesaw State (1:00 PM) | **Kennesaw State 60%** | **Delaware 55%** (29-27) |
| Alabama at LSU (1:30 PM) | LSU 74% | LSU 79% (33-20) |
| Cincinnati at Houston (1:30 PM) | Houston 84% | Houston 65% (35-29) |
| Charlotte at UAB (1:30 PM) | UAB 80% | UAB 63% (30-25) |
| Temple at Navy (1:30 PM) | Navy 84% | Navy 62% (34-29) |
| Marshall at Georgia Southern (1:30 PM) | Georgia Southern 83% | Georgia Southern 86% (36-18) |
| Western Kentucky at Middle Tennessee (1:30 PM) | Middle Tennessee 54% | Middle Tennessee 67% (31-24) |
| Missouri State at Florida International (2:00 PM) | Florida International 60% | Florida International 64% (28-23) |
| South Alabama at Louisiana (3:00 PM) | Louisiana 70% | Louisiana 63% (32-27) |
| Kentucky at Tennessee (4:15 PM) | Tennessee 63% | Tennessee 72% (30-20) |
| Miami at Notre Dame (5:30 PM) | **Notre Dame 66%** | **Miami 53%** (30-28) |
| Georgia at Ole Miss (5:30 PM) | Georgia 62% | Georgia 66% (30-24) |
| Colorado at Arizona State (5:30 PM) | Arizona State 58% | Arizona State 55% (27-25) |
| Louisville at Georgia Tech (5:30 PM) | Louisville 85% | Louisville 78% (38-25) |
| Hawai'i at UTEP (7:30 PM) | Hawai'i 63% | Hawai'i 72% (31-22) |
| Texas State at Oregon State (8:30 PM) | Oregon State 66% | Oregon State 64% (33-28) |
| Wyoming at UNLV (8:30 PM) | UNLV 69% | UNLV 63% (30-25) |

28 picks in both models, 23 no-picks; they agree on 22 of 28. Engine 70%+ (12):
Louisville, Navy, Houston, Georgia Southern, UAB, Baylor, Utah, North Carolina,
LSU, Tulsa, Louisiana, Arkansas State. Splits (6): Texas/Missouri, Florida
State/Boston College, NC State/Duke, Kennesaw State/Delaware, Notre Dame/Miami
(engine first), and North Carolina 74% (framework UConn 52%).

No pick (both; full reasons with sources in both picks files and the PDF):
- Regular starter out: UCLA at Minnesota (Iamaleava out for the season),
  Oklahoma State at Kansas State (Avery Johnson out, Knuth unavailable), Georgia
  State at App State (Cameran Brown out), Oregon at Ohio State (Sayin out
  indefinitely), UCF at Kansas (Keyone Jenkins out; Kansas' Marshall also not
  confirmed), Vanderbilt at Mississippi State (Kamario Taylor out for the season;
  AJ Swann hurt Oct 31, not confirmed), Rutgers at Wisconsin (Lonergan out;
  Wisconsin's true freshman Ryan Hopkins reported to make his first start over
  Colton Joseph), Boise State at Colorado State (Madsen, knee, won't play;
  Cutforth starts), Iowa at Northwestern (Chiles out per ESPN; Marchiol starts),
  Air Force at Army (Szarka out for the season; no starter named), Fresno State
  at Utah State (Brosterhous hurt Oct 31, no update; Hillstead not named).
- Starter questionable: Clemson at Syracuse (Angeli questionable on the ACC
  report), Michigan State at Michigan (Milivojevic questionable), Merrimack at
  Wake Forest (also no Merrimack data; Gio Lopez day-to-day).
- Starter not named or confirmed: Old Dominion at Coastal Carolina (Henicle
  probable or Potter), Penn State at Washington (Demond Williams Jr. expected
  back, not confirmed), Rice at North Texas (Brown or Ochoa), Northern Illinois
  at San José State (Rolovich over Weaver per ESPN sources only), Louisiana Tech
  at Troy (Kilcrease reported over Crowder), Sam Houston at Jacksonville State
  (Locke's status unknown), Oklahoma at Florida (Jones Jr. per CBS, no
  announcement), Liberty at New Mexico State (open competition), West Virginia at
  Texas Tech (Castellanos expected, McGuire undecided).

Off the record (no-pick games; never in either record): UCLA at Minnesota: engine UCLA 73%, framework UCLA 79%; Clemson at Syracuse: engine Syracuse 52%, framework Syracuse 60%; Oklahoma State at Kansas State: engine Oklahoma State 55%, framework Kansas State 51%; Old Dominion at Coastal Carolina: engine Coastal Carolina 68%, framework Coastal Carolina 71%; Georgia State at App State: engine Georgia State 55%, framework Georgia State 60%; Oregon at Ohio State: engine Ohio State 81%, framework Ohio State 61%; Merrimack at Wake Forest: engine none, framework none; Penn State at Washington: engine Penn State 51%, framework Washington 52%; UCF at Kansas: engine Kansas 66%, framework Kansas 55%; Rice at North Texas: engine North Texas 85%, framework North Texas 85%; Northern Illinois at San José State: engine San José State 81%, framework San José State 82%; Louisiana Tech at Troy: engine Louisiana Tech 66%, framework Louisiana Tech 66%; Vanderbilt at Mississippi State: engine Mississippi State 71%, framework Vanderbilt 51%; Rutgers at Wisconsin: engine Wisconsin 86%, framework Wisconsin 81%; Boise State at Colorado State: engine Boise State 87%, framework Boise State 82%; Sam Houston at Jacksonville State: engine Jacksonville State 74%, framework Jacksonville State 74%; Iowa at Northwestern: engine Northwestern 65%, framework Northwestern 58%; Michigan State at Michigan: engine Michigan 78%, framework Michigan 87%; Air Force at Army: engine Army 61%, framework Air Force 54%; Oklahoma at Florida: engine Florida 58%, framework Oklahoma 50%; Liberty at New Mexico State: engine Liberty 87%, framework Liberty 72%; West Virginia at Texas Tech: engine Texas Tech 87%, framework Texas Tech 73%; Fresno State at Utah State: engine Utah State 51%, framework Fresno State 60%.

How the QB rule was applied to picked teams (news through Saturday morning:
SEC, ACC, Big 12, Sun Belt availability reports via Hook 'Em Headlines, SI,
Yahoo, On3, RotoWire, Fox Sports game pages; SI's Week 10 QB tracker):
- Coach named the starter, pick stands: Michigan (Kyle Whittingham named Tommy
  Carr "for the foreseeable future", Nov 2; Underwood benched, not hurt; game is
  a no-pick anyway for Michigan State), Arizona State (Kenny Dillingham named
  Jake Fette; Cutter Boley healthy, benched), Marshall (Tony Gibson named Zion
  Turner Tuesday, his 3rd straight start, WV MetroNews Nov 4; framework re-run
  with `--starter`).
- Settled QB change, pick stands: Tulane (Trace Johnson won the reopened
  competition, 4th straight start; Semonza not hurt), Charlotte (Conner Harrell,
  starter since Week 6).
- Regular starter back or cleared, pick stands: Houston (Conner Weigman, ankle,
  no designation, "full-go" after the bye), Iowa State (Jaylen Raynor), Georgia
  Southern (Max Johnson started last game).
- SPLIT or LOW ATTEMPTS with the season leader starting and no injury news, pick
  stands: Baylor (DJ Lagway), Clemson (Tait Reynolds, not on the report), Tulsa
  (Baylor Hayes), UL Monroe, Delaware, Navy, Temple, Western Kentucky, Missouri
  State (Henry Belin IV), Louisiana Tech, South Alabama, Tennessee (George
  MacIntyre), Iowa, Colorado (Isaac Wilson), Army, UTEP (EJ Colson Jr.).
- Every other picked team: no QB injury or change news found.
- Data notes: news says Marshall's Oct 31 starter was Zion Turner (play-by-play
  shows Carlos Del Rio-Wilson), Michigan State's Oct 24 starter was Kayd Coffman
  (play-by-play shows Leo Hannan) and Florida's Oct 31 starter was Aaron Philo
  (play-by-play shows Tramell Jones Jr.). ESPN has 1 Merrimack game this season.

PDF: `report_2026-11-07_saturday.pdf` (midweek graded, today's picks). Check-in
E (11:50 AM) re-checks the noon-and-later games (Big Ten 2-hour reports:
Washington, Michigan State, Northwestern, Wisconsin; also Kansas, Texas Tech,
Florida, Utah State, San José State, Troy, Sam Houston).

**Saturday run, second session (same check-in D, about 6:45-7:58 AM Pacific).**
A duplicate run of check-in D graded the midweek games the same (engine 5-2,
framework 5-2) and did its own QB check of all 51 games. It agreed on 46 games.
Two picks became no-picks in both models (`set_nopick.py`; both games kick off
at 5:30 PM Phoenix):
- **Louisville at Georgia Tech: now a no-pick** (was Louisville in both, engine
  85%). Georgia Tech's starter isn't announced: Alberto Mendoza (benched in the
  4th quarter Oct 31 after 4 fumbles) or Grady Adamson. Brent Key's staff
  decision isn't public (SI Nov 4 and its game-day preview Nov 7; AJC Nov 6).
- **Colorado at Arizona State: now a no-pick** (was Arizona State in both).
  Mikey Keene (right knee, hurt Oct 24) started the 2 games before and is still
  rehabbing. Jake Fette starts in his place (Arizona Sports, "ASU starts Jake
  Fette with Mikey Keene injured"). He is an injury fill-in, the same call as
  Keene/Fette on 10-31.
Left as logged (the stricter call stands): Clemson at Syracuse (the second check
found RotoWire's Nov 6 note that the ACC report upgraded Steve Angeli to
probable, but SI/Yahoo still list him questionable), Northern Illinois at San
José State and West Virginia at Texas Tech. Now 26 picks, 25 no-picks. PDF
re-made.

**Saturday afternoon check (check-in E, about 11:50 AM Pacific).** QB news for
the 37 games kicking off at noon Pacific or later. Two picks became no-picks in
both models (`set_nopick.py`, pushed before their 12:30 PM Pacific kickoffs):
- **Temple at Navy: now a no-pick** (was Navy). Temple's Ajani Sheppard
  (undisclosed) questionable on the American availability report, likely a
  game-time decision (RotoWire, Nov 7); Jaxon Smolik starts if he can't.
- **Marshall at Georgia Southern: now a no-pick** (was Georgia Southern).
  Marshall's Carlos Del Rio-Wilson (undisclosed) a game-time decision on the
  Sun Belt availability report (RotoWire, Nov 7); Marshall used three QBs last
  game.
Picks stand: Alabama at LSU (game-day availability report: Keelon Russell and
Sam Leavitt not listed; backup Jett Thomalla a game-time decision), Kentucky at
Tennessee (no new Tennessee injuries on the SEC report), and every other picked
game (no QB injury news found). No pick came back (no earlier no-pick's QB was
confirmed in this check). Now 24 picks, 27 no-picks.

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

## Live winner calls (separate tool, started 2026-10-17)

The owner's goal: know who wins a game as early as possible before it ends.
`live/backtest_calls.py` replayed college 2025 weeks 4-15 (580 games, plays
2023-2024 for training) and compared three ways of calling a game the first time
one team's live win chance reaches a threshold (`live/backtest_calls_cfb.txt`):

| Source | Call at | Right | Median time left at the call | Called before the 4th quarter |
|---|---|---|---|---|
| ESPN's live win probability | 98% | 97.2% | 12 min | 42% of games |
| ESPN's live win probability | 95% | 94.7% | 20 min | 57% |
| ESPN's live win probability | 90% | 91.7% | 31 min | 71% |
| Our own tracker (engine pregame + score, clock, field position) | 98% | 94.5% | 26 min | 54% |
| Score only: 8+ point lead after the 3rd quarter | | 95.3% | 15 min | 63% of games |

ESPN's number (read from the same free feed the engines use) was the most
accurate at every point of the game, so `live/calls.py` uses it, calling at 98%.
Our tracker was overconfident (its 90% calls were right 81%). No betting lines
are read. This tool is separate from the engines and feeds nothing into them;
calls are logged in `results/live_calls_<date>.csv` and graded with
`python3 live/calls.py --grade --date <date>`.

NFL check (`live/backtest_espn_nfl.py`, `live/backtest_calls_nfl.txt`), ESPN's live
win probability on every regular-season game 2023-2025 (816):

| Call at | Right | Median time left | Called before the 4th quarter |
|---|---|---|---|
| 98% | 98.5% | 4 min | 23% of games |
| 95% | 96.8% | 8 min | 35% |
| 90% | 92.9% | 16 min | 53% |

NFL games stay closer longer than college games, so 98% calls come later (4 min
left vs 12 in college). Real-time delivery: `live/worker/` (Cloudflare Worker,
every minute, posts to Discord), replacing the hourly scheduled checks once it's
deployed.

Our own "history says" live model (`live/backtest_situation.py`,
`live/backtest_situation.txt`): the live score margin, time left, possession,
field position, down and distance compared with every past game (college
2023-2024, NFL 2018-2024), tested on 2025, which it never saw. College also tried
with the engine's pregame win chance added. Calls at 98%:

| | Right | Median time left | Games called |
|---|---|---|---|
| College, history + team strength | 98.5% | 14 min | 480 of 580 |
| College, history only | 96.8% | 13 min | 495 of 580 |
| College, ESPN | 97.2% | 12 min | 566 of 580 |
| NFL, history only | 96.4% | 10 min | 223 of 271 |
| NFL, ESPN | 98.1% | 5 min | 261 of 271 |

Our model is about as good as ESPN's: slightly more accurate in college when it
calls, but it holds back on more games (it never gets to 98% in some games ESPN
does). In the NFL ours calls earlier but is wrong more often.

## Off-the-record no-pick leans (owner's request, 2026-10-18)

No-pick rules are unchanged: no official pick and nothing in either record. The
reports now list, separately and in italics, the team each model would have
taken in each no-pick game (from the win chance both models already save). Graded
pages add a separate off-the-record box. `results/nopick_leans.py` keeps the
running total. As of 2026-10-18 (graded no-pick games so far): college engine
8-9, college framework 10-7, NFL engine 0-2, NFL framework 0-2; 18-20 overall at
an average stated win chance of about 70%, versus 22-12 / 19-15 (college) and
6-6 / 10-2 (NFL) on official picks. Small sample, but holding these games back
has been the right call so far.

## Watch my bets (live/worker, owner's request 2026-10-18)

The Discord worker also watches the owner's own team-to-win bets, added on its
`/bets` page (team + full payout). Alerts when that team's ESPN live win chance
crosses 75/50/25/10%, each with the fair value of the payout (win chance x
payout) to compare with a cash-out offer. No sportsbook odds are read; the
payout is typed in by the owner. Separate from the engines. Offline test:
`node live/worker/test_bets.mjs`.
