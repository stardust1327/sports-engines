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

Week 5's Monday game (Bills 37, Rams 34) was the only Week 5 game where both
models picked the same team and lost (the Commanders-Giants tie aside). The
owner expected the Rams to lose, but the note was set after kickoff, so it
doesn't count for that game; a read sent before kickoff would have.

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
