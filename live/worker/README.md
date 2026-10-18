# Live winner calls -> Discord, every minute

A Cloudflare Worker (free plan) that checks every college (FBS) and NFL game in
progress once a minute and posts to a Discord channel:

- `CALL: Ohio wins (99.9%). Ohio 41, Sacramento State 7, Q4 11:37` the first time
  ESPN's live win probability reaches 98% for one team
- `CALL IN DOUBT: ...` if a called team later drops below 50% (rare)
- `FINAL: ... (called X: right / WRONG)` when a called game ends

No computer needs to stay on. No betting lines or odds are read; it doesn't touch
the prediction engines. Backtests: `live/backtest_calls_cfb.txt`,
`live/backtest_calls_nfl.txt`.

## Setup (about 10 minutes, once)

1. **Discord webhook.** In your Discord server: Server Settings > Integrations >
   Webhooks > New Webhook, pick the channel, Copy Webhook URL.
2. **Cloudflare account** (free): dash.cloudflare.com. Then My Profile > API
   Tokens > Create Token > template "Edit Cloudflare Workers". Note your Account ID
   (Workers & Pages overview page).
3. Deploy (from this folder):
   ```
   export CLOUDFLARE_API_TOKEN=...  CLOUDFLARE_ACCOUNT_ID=...
   npx wrangler kv namespace create STATE        # paste the id into wrangler.toml
   npx wrangler secret put DISCORD_WEBHOOK       # paste the webhook URL
   npx wrangler deploy
   ```
4. **Watch my bets** (optional): pick any long random password and run
   `npx wrangler secret put BETS_KEY` (paste it). Then open
   `https://<worker url>/bets?key=<that password>` on your phone and bookmark it.

## Watch my bets

Add a bet on the `/bets` page: league, the team you bet on to win, and the full
payout if it wins (stake included). During that team's game, Discord gets:

- `YOUR BET: watching Bears vs Falcons. Bears 60% to win. ... Fair value of your $250 payout: $150.` once ESPN has a live number
- `YOUR BET: Bears down to 20% (below 25%). ... Fair value ... now: $50; compare with the cash-out offer.` each time
  the win chance crosses 75%, 50%, 25% or 10% (up or down; your own levels can be set per bet). It has to get
  2 points past a line, so a team sitting on 50% doesn't send an alert every minute.
- `YOUR BET FINAL: ...` when it ends; the bet is then removed.

Fair value = win chance x payout: what the bet is worth right now if ESPN's number is right. A cash-out offer
below it costs you that difference on average; you trade it for certainty. Team-to-win bets only (no spreads,
totals or parlays). The sportsbook's odds are never read. Backtests of ESPN's number: how often a team that
falls to 10% / 5% / 2% comes back: college about 8 / 5 / 3 in 100, NFL about 7 / 3 / 1-2 in 100.

Thresholds are in `wrangler.toml` (`THRESHOLD_COLLEGE`, `THRESHOLD_NFL`); change
and `npx wrangler deploy` again. `https://<worker url>/calls` shows the last 3 days
of calls. Local dry run with real ESPN data and no Discord:
`NODE_USE_ENV_PROXY=1 node test_local.mjs`.

Limits: Cloudflare's free plan allows 50 outside requests per run, so on the
busiest Saturday windows (more than about 40 games live at once) some games wait
a minute or two for their check.
