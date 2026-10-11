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
   stats or narrative as inputs. If key data is missing (for example the
   starting QB is out or unconfirmed), say exactly what's missing and make no
   pick for that game.
5. **Log everything.** Save every set of picks in `results/` before kickoff and
   grade it after.

`nfl/` (quarterback ratings plus rest days) was built before these rules and
deviates from `METHOD.md`. It stays only until the owner decides whether to
keep it. `nfl_cfbmethod/` is the NFL version that follows `METHOD.md`.
