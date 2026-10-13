# Scheduled check-ins (runbook)

Each check-in runs as a fresh session started by a scheduled task. **Read
`CLAUDE.md` first: the owner's rules always win over anything here.** Times
below are Pacific; the check-ins follow kickoff times, which are set in Eastern
(the two shift together for daylight saving). The pick files and PDFs show
Phoenix times, as the models write them.

| Check-in | When (Pacific) | Job |
|---|---|---|
| A. Tuesday run | Tue 7:10 AM | Grade last NFL week; run next NFL week and Tue-Fri college games (both models); PDF |
| B. Midweek check | Wed and Thu 3:48 PM | Thursday-night NFL game: statuses (Wed), inactives (Thu); QBs for today's college games |
| C. Friday lock | Fri 1:40 PM | NFL game statuses (due 1 PM); refresh both NFL models; QBs for today's college games; PDF |
| D. Saturday college run | Sat 6:40 AM | Grade the week's midweek college games; run today's college slate (both models); PDF |
| E. Saturday afternoon check | Sat 11:50 AM | QB news for college games kicking off at noon or later |
| F. Sunday check | Sun 8:40 AM | Grade Saturday's college games; NFL inactives (early games) and QB news (later games) |
| G. Monday night check | Mon 3:47 PM | Monday-night NFL inactives |

## 0. Setup (every check-in)

```
git clone --depth 1 https://github.com/stardust1327/sports-engines /home/claude/sports-engines
cd /home/claude/sports-engines
pip install --break-system-packages -q -r requirements.txt
python3 results/whats_next.py
```

If the clone fails, attach the repo first (add_repo: owner `stardust1327`,
repo `sports-engines`, access `push`). `whats_next.py` prints the NFL week just
played and the next one (with the Eastern game dates the NFL engine needs), the
college dates with games in the next 7 days, and which picks and grades are
already logged. Work from what it prints.

Scratch folder for re-runs: `/tmp/rerun` (`mkdir -p /tmp/rerun`).

## Rules for every check-in

- Never change `METHOD.md`, the engines (`cfb/`, `nfl_cfbmethod/`) or the
  framework scripts (`prompt_football/`). Ideas for improvements go to the owner
  as proposals, never into the code.
- No betting lines, odds, records, traditional stats or narrative as inputs.
  Closing lines appear only in `nfl_cfbmethod/grade.py`, for grading.
- Missing key data means no pick, and the reason says exactly what's missing.
  **Both models always carry the same no-picks.**
- Log every set of picks in `results/` before the first kickoff it covers, and
  grade it afterwards. Commit and push before that kickoff.
- The engine's picks are the official ones (NFL: with the owner's team notes
  applied); the framework is the comparison.
- **First run of a slate** (no picks file yet): write straight into `results/`.
  **Every later run of that slate**: write to `/tmp/rerun` with `--out` and merge
  with `python3 results/merge_rerun.py /tmp/rerun/<file>`. The models only price
  games that haven't started, so a re-run written straight into `results/` would
  drop picks already logged for games under way or finished. `merge_rerun.py`
  refreshes only games ESPN still shows as not started.
- If a step fails, say what failed and stop that part. Never fill a gap with a
  guess.
- Postseason (college bowls and playoff, NFL playoffs) isn't set up yet: ask the
  owner before the first postseason run. If `whats_next.py` shows no games in the
  next 7 days, the season is over: send one message saying so and suggest pausing
  these scheduled tasks.
- **Team notes (NFL) are the owner's alone.** Never add, change or remove one; see
  "Team notes" below.

## Team notes (NFL, the owner's; added 2026-10-12)

From watching the games, the owner marks a team by hand, case by case:
**unreliable** (doesn't want to win or looks lazy, earlier results came from luck
rather than effort, loses games it shouldn't; losing a game alone doesn't
qualify) or **max effort** (plays hard and aggressive, out there to win). The
notes live in `results/team_notes.json`; `whats_next.py` prints the ones in force.

- A note moves the team's predicted margin in both NFL models (defaults:
  unreliable -3 points, max effort +1.5) and only counts for games kicking off
  after it was set. The models' own numbers in the picks files never change:
  `results/team_notes.py` and `make_report.py` apply the notes when they read the
  files, so runs, re-runs, `merge_rerun.py` and `set_nopick.py` work exactly as
  before. In the PDF a noted team gets an asterisk, explained under the table.
- **Official picks and records include the notes.** The model-alone pick and
  record stay beside them (they differ only when a note flips a pick).
- Picks: after the week's picks are logged or refreshed, run
  `python3 results/team_notes.py show --season S --week W` and use its lines in the
  message (every noted game with and without the note; any pick a note changed).
  The PDF applies the notes by itself and ends with the notes scorecard.
- Grading: after `grade.py` and `grade_picks.py`, run
  `python3 results/team_notes.py grade --season S --week W`. Report its "official
  (with your team notes)" record, plus the model-alone record when they differ,
  and the scorecard lines for the noted teams.
- Only when the owner says so in a conversation: `python3 results/team_notes.py set
  --team <Nickname> [--kind max_effort] --said "<the owner's words>" [--points N]`
  (the kind defaults to unreliable) or `clear --team <Nickname> --said "..."`.
  Never edit past events in the file.

## QB check (used by every check-in)

1. **Which teams.** Every team flagged in the QB report the models print (NFL
   "QB history": SPLIT, CHANGE; college "QB check needed": CHANGE, SPLIT, LOW
   ATTEMPTS; also `results/*_qbs.csv`), plus any team whose starting QB is in the
   injury news. NFL: read the official injury report (game statuses: Wednesday for
   Thursday games, Friday for Sunday games, Saturday for Monday games) and the
   inactive lists (about 90 minutes before kickoff). College: the Big Ten posts
   availability reports for conference games (Wed, Thu, Fri evenings and 2 hours
   before kickoff); otherwise team announcements and local reporters.
2. **Decide.**
   - The team's regular starter is out (injury, suspension, illness): **no pick**,
     even when the backup is confirmed to start (NFL Week 5: Ravens with Tyler
     Huntley, Bears with Tyson Bagent).
   - The starter isn't confirmed (questionable, doubtful, game-time decision, an
     open competition, or a college team that changed QBs last game and hasn't
     named one): **no pick** until he's confirmed.
   - The regular starter is confirmed (or the coach names a new starter going
     forward, not as an injury fill-in): the pick stands. If he isn't the QB the
     framework assumed (each team's last starter), re-run the framework with
     `--starter`.
   - College flags, as used on 2026-10-11: CHANGE (the last starter isn't the
     season leader in attempts) means no pick until the news settles who starts and
     why; SPLIT alone (the last starter is also the season leader) keeps its pick
     unless the news says otherwise.
3. **Write the reason exactly**, e.g. `Lamar Jackson (ankle) ruled out; Tyler
   Huntley starts` or `QB changed last game (X started; Y started the first 5);
   starter not yet named`.
4. **Apply it to both models.**
   - At run time: engine `--nopick "Team=reason"` (NFL nickname, college school
     name, as in the picks file); framework NFL `--nopick "ABBR=reason"` (nflverse
     abbreviation: CHI, BAL, TB, LA, WAS, ...); framework college
     `--nopick "School=reason"`.
   - After picks are logged: `python3 results/set_nopick.py --team "<Team>"
     --reason "<reason>" <engine picks file> <framework picks file>` (team name as
     written in the files).
   - A pick comes back (QB confirmed after a no-pick) only by re-running both
     models without that `--nopick` (into `/tmp/rerun`, then `merge_rerun.py`).

## Commands

NFL engine (official), all game dates of a week (Eastern dates from `whats_next.py`):
```
python3 nfl_cfbmethod/run.py --date 2026-10-15 --date 2026-10-18 --date 2026-10-19 \
    [--nopick "Ravens=Lamar Jackson (ankle) ruled out; Tyler Huntley starts"] [--out /tmp/rerun]
```
NFL framework (needs the engine's `_qbs.csv` from the same run):
```
python3 prompt_football/nfl.py --season 2026 --week 6 --raw prompt_football/cache \
    --qbs results/nfl_cfbmethod_2026_week06_qbs.csv [--nopick "BAL=..."] [--starter "WAS=Jayden Daniels"] \
    [--refresh] [--out /tmp/rerun]
```
(With `--out /tmp/rerun`, pass `--qbs /tmp/rerun/nfl_cfbmethod_..._qbs.csv`.
`--refresh` re-downloads this season's nflverse files: use it from the Friday
lock on, so last week's blitz charting, posted midweek, is included.)

College engine (official), one date at a time; college framework, any dates:
```
python3 cfb/run.py --date 2026-10-17 [--nopick "Oregon=..."] [--out /tmp/rerun]
python3 prompt_football/cfb.py --date 2026-10-17 [--nopick "Oregon=..."] [--starter "Oregon=Full Name"] [--out /tmp/rerun]
```
(The college framework needs schedules from 2019 and play-by-play from 2022 on;
in a fresh session the first run downloads about 4,000 games, a few minutes.)

Grading:
```
python3 nfl_cfbmethod/grade.py --season 2026 --week 6                 # NFL engine alone, with the closing-line check
python3 results/grade_picks.py results/prompt_nfl_2026_week06_picks.csv   # NFL framework
python3 results/team_notes.py grade --season 2026 --week 6            # official NFL record with the team notes; notes scorecard
python3 results/grade_picks.py results/cfb_2026-10-17_picks.csv results/prompt_cfb_2026-10-17_picks.csv
```
Team notes (NFL): `python3 results/team_notes.py show --season 2026 --week 6` prints
the week's picks with the notes applied; `list` and `scorecard` print the notes
and how they're doing.
PDF (sections in this order: NFL graded, college graded, NFL picks, college picks):
```
python3 results/make_report.py --out results/report_<YYYY-MM-DD>_<checkin>.pdf --title "<title>" \
    [--nfl-graded 2026:6] [--cfb-graded 2026-10-13 ...] [--nfl-picks 2026:7] [--cfb-picks 2026-10-17 ...]
```
Open the PDF (render a page to an image) and check its records and picks against
the printouts before sending it.

## A. Tuesday run (Tue 7:10 AM)

1. Setup. From `whats_next.py`: last NFL week W (all games final after Monday
   night) and next week W+1 with its game dates; college dates Tue-Fri this week.
2. Grade NFL week W (skip what isn't logged, and say so): `grade.py` for the
   engine, `grade_picks.py` for the framework, then `team_notes.py grade` for the
   official record with the owner's team notes and the notes scorecard.
3. NFL week W+1, both models: run the engine for all its dates, then the
   framework; do the QB check; re-run both with the no-picks (the first run of the
   week writes to `results/`; once picks are logged, re-runs go through
   `/tmp/rerun` and `merge_rerun.py`). Statuses aren't out yet on Tuesday: a QB
   with an injury still in doubt is a no-pick for now. Then `team_notes.py show`
   for the week.
4. College games Tue-Fri this week, if any: both models, same QB check.
5. Update `results/RESULTS.md`: Week W results for both models (official record
   with the team notes, the model-alone record if a note changed a pick, ties,
   the closing-line line from `grade.py`, the notes scorecard lines), Week W+1
   picks table (engine vs framework with the notes applied, splits in bold, each
   noted game marked with the model-alone number) with no-picks and reasons,
   midweek college picks.
6. PDF: `--nfl-graded S:W --nfl-picks S:W+1 [--cfb-picks <midweek dates>]`.
7. Commit and push. Send the owner the PDF and a short summary: last week's
   records, this week's picks where the models disagree, every noted game (with
   and without the note), every no-pick with exactly what's missing, and what gets
   re-checked later in the week.

## B. Midweek check (Wed and Thu 3:48 PM)

1. Setup.
2. NFL Thursday game, if there is one this week. Wednesday: its injury report
   with game statuses is out. Thursday: inactives are out (about 3:45 PM for a
   5:15 PM kickoff). Check both starting QBs.
3. College games today: QB check for both teams in every game.
4. Apply changes: `set_nopick.py` for new no-picks; re-run both models into
   `/tmp/rerun` and merge for picks that come back. Change nothing if nothing
   changed.
5. If anything changed: update `RESULTS.md`, re-make the PDF for the affected
   slate, commit and push, send the PDF and what changed. If nothing changed: a
   one-line message ("QBs confirmed for ...; no changes").

## C. Friday lock (Fri 1:40 PM)

1. Setup.
2. NFL: game statuses for Sunday's games came out at 1 PM. Check every starting
   QB (out, doubtful, questionable, or no designation). Monday's statuses come
   Saturday: use the latest news and leave the final word to check-in G.
3. Refresh both NFL models with the current no-picks: engine for the week's
   remaining dates, framework with `--refresh`, both into `/tmp/rerun`, then
   `merge_rerun.py` for each file, then `team_notes.py show`. Report any pick that
   changed and why (including a pick a team note changed).
4. College games today (Friday): QB check.
5. Update `RESULTS.md` (mark the week's picks "locked Friday", list changes).
   PDF: `--nfl-picks S:W` (plus today's college dates if any changed). Commit,
   push, send the PDF and summary.

## D. Saturday college run (Sat 6:40 AM)

1. Setup.
2. Grade this week's midweek college dates (both models) that `whats_next.py`
   lists without grades.
3. Today's slate: run the engine (`cfb/run.py --date TODAY`), do the QB check
   for every flagged team and any team with QB news, then re-run both models with
   the no-picks (engine re-run into `/tmp/rerun` and merge; the framework's first
   run can go straight into `results/`). The first games kick off at 9 AM: if the
   QB checks run long, log and send the picks for the games already checked first,
   with every unchecked game a no-pick ("QB not yet checked"), then finish.
4. Update `RESULTS.md` (today's picks table, both models, no-picks; midweek
   results). PDF: `--cfb-graded <midweek dates> --cfb-picks TODAY`. Commit, push,
   send the PDF and summary.

## E. Saturday afternoon check (Sat 11:50 AM)

1. Setup.
2. QB news for both teams in every game kicking off at noon or later (late
   scratches, injuries announced since the morning, Big Ten 2-hour reports).
3. Apply changes as in B. Message the owner only with what changed, or one line
   saying nothing did.

## F. Sunday check (Sun 8:40 AM)

1. Setup.
2. Grade yesterday's college slate (both models); add the results to
   `RESULTS.md`.
3. NFL: inactives for the early games are out (8:30 AM). Confirm every starting
   QB for the early games; for the late and night games use the latest news (a QB
   still undecided is a no-pick). London games kick off before this check: their
   QBs were settled at the Friday lock.
4. Apply changes as in B. PDF only if a pick changed. Commit, push, send the
   college results and any NFL changes.

## G. Monday night check (Mon 3:47 PM)

1. Setup.
2. Monday-night inactives are out (about 90 minutes before kickoff). Confirm
   both starting QBs; apply changes as in B; one-line message if nothing changed.

## Logging and messages

- `results/RESULTS.md` is the running record: add to it, never rewrite earlier
  entries except to fill in results.
- Commit messages say what the check-in did ("Tuesday run: Week 6 graded 9-5,
  Week 7 picks logged"), with the session's attribution lines. Fetch and rebase
  before pushing.
- Messages to the owner are short: records first, then picks that changed or
  where the models disagree, then every game with a team note (with and without
  the note), then every no-pick with exactly what's missing. Send the PDF when the
  check-in makes one.
