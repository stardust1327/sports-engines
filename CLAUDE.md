# Rules for this repo (set by the owner)

1. **The college football method is locked.** `METHOD.md` describes exactly what
   produced the 2026-10-10 college picks; the original scripts are in
   `cfb/original_2026-10-10/`. Do not change any rule, metric, setting or step
   without asking the owner first and getting a yes.
2. **New models follow the same structure.** Any new prediction model (another
   sport or a new version) uses the `METHOD.md` structure unless the owner
   approves a deviation. Sport plumbing (data URLs, number of weeks in a
   season) is not a deviation. Anything that changes what goes into a
   prediction or how it's calculated is.
3. **Improvements are proposals.** Present them to the owner with backtest
   evidence and wait for approval. Never apply them silently.
4. **Standing prediction rules.** No betting lines or odds, records, traditional
   stats or narrative as inputs (the owner's own team notes, rule 6, are the one
   exception). If key data is missing (for example the starting QB is out or
   unconfirmed), say exactly what's missing and make no pick for that game.
5. **Log everything.** Save every set of picks in `results/` before kickoff and
   grade it after (NFL: `nfl_cfbmethod/grade.py`, which also runs the
   closing-line check; closing lines are for grading only, never an input; then
   `results/team_notes.py grade`).
6. **Team notes are the owner's alone (approved 2026-10-12).** From watching
   the games, the owner marks an NFL team by hand, case by case
   (`results/team_notes.json`): unreliable (docked) or max effort (slightly
   boosted). The note moves that team's predicted margin in both NFL models,
   official picks include it, and the model-alone numbers are always kept beside
   it and graded so the note's accuracy is tracked. Never add, change or remove a note, or its
   points, unless the owner says so; record it with `results/team_notes.py` and
   the owner's words. The engines' own code and numbers don't change.

`nfl_cfbmethod/` is the NFL version. It follows `METHOD.md` with the NFL
settings the owner approved on 2026-10-11 (listed at the end of `METHOD.md`).
Those are locked the same way. The earlier quarterback version (`nfl/`) was
retired on 2026-10-11 after the owner left the call to accuracy; it's in git
history if ever needed.
