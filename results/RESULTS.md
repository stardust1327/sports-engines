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

Result: pending.

Earlier Week 5 runs, kept to compare after the games (all pending):

- `nfl_cfbmethod-3seasons_2026_week05_picks.csv`: first tuning (3 seasons, no
  recency): Jaguars 74%, Patriots 71%, Rams 71%, Bengals 69%, Texans 63%, ...
- `nfl_cfbmethod-untuned_2026_week05_picks.csv`: college settings unchanged:
  Jaguars 79%, Rams 67%, Patriots 62%, Broncos 61%, ...
- `nfl_2026_week05_picks.csv`: the retired quarterback version: Texans 72%,
  Jaguars 66%, Patriots 64%, Broncos 60%, ...
