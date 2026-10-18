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
Thresholds are in `wrangler.toml` (`THRESHOLD_COLLEGE`, `THRESHOLD_NFL`); change
and `npx wrangler deploy` again. `https://<worker url>/calls` shows the last 3 days
of calls. Local dry run with real ESPN data and no Discord:
`NODE_USE_ENV_PROXY=1 node test_local.mjs`.

Limits: Cloudflare's free plan allows 50 outside requests per run, so on the
busiest Saturday windows (more than about 40 games live at once) some games wait
a minute or two for their check.
