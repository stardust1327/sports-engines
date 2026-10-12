# Against the moneyline (checked 2026-10-12)

How both models' picks have done against the betting market's moneylines.
**Grading only: lines never feed a prediction** (CLAUDE.md rule 5).

## Re-run

```
python3 results/moneyline/build_preds.py nfl    # NFL engine: 2019-2025 backtest + 2026 so far, rebuilt exactly as nfl_cfbmethod/run.py grades it
python3 results/moneyline/build_preds.py cfb    # college engine: 2024-2026, rebuilt exactly as cfb/run.py would have run each season
python3 results/moneyline/build_preds.py ids    # game ids for the odds pull
python3 results/moneyline/fetch_odds.py college-football cfb/cache/odds results/moneyline/cfb_ids.txt
python3 results/moneyline/fetch_odds.py nfl nfl_cfbmethod/cache/odds results/moneyline/nfl_ids.txt
python3 results/moneyline/analyze.py
```

Framework rows come from `results/prompt_*_backtest_*.csv` and
`results/prompt_cfb_2026_out_of_sample.csv`. Lines: NFL closing moneylines from
nflverse (2019 on); opening and closing moneylines from ESPN's odds service (one
sportsbook per game: ESPN BET, Caesars or DraftKings; NFL and college openers
from 2023 on). Full printout: `analysis_2026-10-12.txt`. Ties are pushes and left
out.

## Results (every game each model rated out of sample)

| Model | Games | Picks right | Moneyline favorite right | $100 on every pick at the closing line | Betting every favorite instead |
|---|---|---|---|---|---|
| NFL engine, 2019-2025 | 1,522 | 63.2% | 67.1% | -$5,190 (-3.4%; 95% range -7.4% to +0.6%) | -3.0% |
| NFL framework, 2022-2025 | 893 | 62.5% | 68.8% | -$4,130 (-4.6%; -9.9% to +0.6%) | +0.1% |
| College engine, 2024-2026 | 1,256 | 70.0% | 72.2% | -$1,490 (-1.2%; -5.2% to +2.8%) | -1.9% |
| College framework, 2022-2026 | 2,356 | 67.4% | 72.1% | -$7,930 (-3.4%; -6.7% to -0.1%) | -3.0% |

- Accuracy of the win chances (Brier, lower is better): the closing line beats
  every model (NFL 0.209 vs 0.226 engine; college 0.184 vs 0.194 engine).
- Adding a model's number to the closing line doesn't make the line more
  accurate out of sample. The college engine is the only faint exception, and
  it's not statistically meaningful (weight +0.19, standard error 0.12).
- Picks against the market favorite: NFL engine 118-178, NFL framework 73-129
  (-16.8%), college engine 75-103, college framework 165-276.
- Opening lines: when a model disagrees with the opening line by 5+ points, the
  line moves toward the model by kickoff on average (NFL +1.4 to +1.5 points,
  college +0.5). So the models see something real early in the week. It isn't
  enough to beat the sportsbook's cut: judged by the closing line, betting those
  picks at the opening price is worth -1.4% to -2.5% per bet, against about -4%
  for a random bet.

## Live picks so far (closing moneylines, $100 per pick)

| Slate | Engine | Framework / other |
|---|---|---|
| NFL Week 5, Sunday games | 6-4-1, -$117 | Framework 9-1-1, +$419 |
| College, Saturday Oct 10 (games with a closing line) | 9-8, -$298 | Earlier-chat Prompt Football list 24-10, +$995 |

## How long until results can prove an edge

Simulated with the models' real pick odds; "prove" = the 95% range sits above
zero in 4 of 5 runs.

| True edge | Bets needed | NFL (about 217 picks a season) | College (about 560 a season) |
|---|---|---|---|
| +2% | about 10,000-13,000 | 50+ seasons | 20+ seasons |
| +5% | about 2,000 | about 9 seasons | about 3.5 seasons |
| +10% | about 500 | about 2.3 seasons | about 1 season |

Closing-line value (the price when the bet is made vs the closing price) shows
an edge much sooner: an average beat of +1.5 points shows up after about 110 NFL
or 60 college bets.
