# Running record

Every pick is logged before kickoff, graded after. One week is too small a
sample to judge an engine; the record means more as it grows.

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
Chargers, Seahawks. Tie: Giants 27, Commanders 27 (`grade.py` currently counts a
tie as a loss and prints 6-5). Closing-line favorite went 9-2 on the same games;
the engine's 3 picks of the market underdog all lost. Graded file:
`nfl_cfbmethod_2026_week05_graded.csv`.

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
4-1 (Steelers, 49ers, Lions, Broncos right; Raiders wrong).

Earlier Week 5 runs, kept to compare after the games (all pending):

- `nfl_cfbmethod-3seasons_2026_week05_picks.csv`: first tuning (3 seasons, no
  recency): Jaguars 74%, Patriots 71%, Rams 71%, Bengals 69%, Texans 63%, ...
- `nfl_cfbmethod-untuned_2026_week05_picks.csv`: college settings unchanged:
  Jaguars 79%, Rams 67%, Patriots 62%, Broncos 61%, ...
- `nfl_2026_week05_picks.csv`: the retired quarterback version: Texans 72%,
  Jaguars 66%, Patriots 64%, Broncos 60%, ...

### 2026 Week 6 (logged Sunday night 2026-10-11, before QB reports)

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

## College football midweek, 2026-10-13 to 10-16 (engine only)

Files: `cfb_2026-10-13.csv` through `cfb_2026-10-16.csv`.

| Pick | Win chance | QB status |
|---|---|---|
| Jacksonville State over FIU (Tue) | 63% | ok |
| Middle Tennessee over Delaware (Tue) | 55% | Delaware starter unconfirmed |
| Sam Houston over Western Kentucky (Wed) | 74% | WKU starter unconfirmed |
| Missouri State over Kennesaw State (Wed) | 54% | ok |
| Texas State over Colorado State (Thu) | 83% | CSU split starters |
| Georgia Southern over Old Dominion (Thu) | 75% | ODU split starters |
| East Carolina over UAB (Thu) | 59% | ECU split starters |
| Purdue over Washington (Fri) | 77% | Washington starter unconfirmed |
| Memphis over Tulane (Fri) | 73% | ok |
| Coastal Carolina over App State (Fri) | 58% | ok |

Games with an unconfirmed starter become no-picks unless the starter is
confirmed before kickoff.
