# Improvement tests, 2026-10-24

The owner's question after the backtest audit: is there anything else that would
predict these games more accurately? Each idea below was backtested before being
suggested (CLAUDE.md rule 3). Nothing in `cfb/`, `nfl_cfbmethod/` or
`prompt_football/` was changed, and none of these is proposed for adoption.

Every test predicts each game only from plays before it: college 2021-2025 (5
seasons, run the way the live engine picks, calibrated on the season before),
NFL 2016-2025 (10 seasons). All variants of a model share one expected points
model, so the comparison is like for like (the locked baselines here differ from
the audit by a game or two for that reason).

| Idea | Model | Result | Verdict |
|---|---|---|---|
| Recency: plays count half every 5 weeks older | College engine | 69.6% vs 70.0% | worse |
| Recency, 10-week half-life | College engine | 70.0% vs 70.0% | no change |
| Plays against FCS opponents count half | College engine | 69.9% vs 70.0% | no change |
| Separate pass and run EPA ratings | College engine | 69.4% vs 70.0% | worse |
| Calibrate on the two previous seasons, not one | College engine, 2022-2025 | 1569-674 either way; Brier 0.1954 vs 0.1978 | same picks, slightly better win chances |
| Separate pass and run EPA ratings | NFL engine | 62.2% vs 62.3% (calibrated on earlier seasons only: 63.0% vs 63.2%) | no change |
| Engine and framework averaged 50/50 | College, 2021-2025 | 69.7% vs engine 70.0% | worse |
| Engine and framework averaged 50/50 | NFL, 2022-2025 | 570-317 either way; Brier 0.2216 vs 0.2240 | same picks, slightly better win chances |

When the engine and the framework pick different teams, the engine has been
right more often: college 57.4% of 486 games, NFL 54.5% of 176.

Where the accuracy is (engine, same games): 70%+ picks won 80.9% in college and
74.9% in the NFL; picks under 60% won 52-59%. Requiring the framework to agree
adds almost nothing on top of the 70%+ tier (college 80.8%, NFL 75.5%), since
the strong picks nearly always agree.

Conclusion: none of these picks more winners, so nothing is proposed for the
locked method. Both engines look close to the limit of what play-by-play
efficiency can do. The betting market is still more accurate (NFL 2022-2025,
same 887 games: closing-line favorite 68.7%, engine 64.0%; 2019-2025 in
`METHOD.md`: 1024-498), and the owner's rules keep it out of the inputs.

Re-run from the repo root:

```
python3 results/proposals/improvement_tests_2026-10-24/cfb_engine_variants.py
python3 results/proposals/improvement_tests_2026-10-24/nfl_engine_variants.py
python3 results/proposals/improvement_tests_2026-10-24/cfb_blend.py
```
