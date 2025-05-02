# SkyHustle

A simple, strategic, text-based Telegram war game.

## Setup

1. Add your environment variables:
   - `BASE64_CREDS`
   - `BOT_TOKEN`
   - `SHEET_ID`
2. Deploy to your host (Render/Heroku).
3. The bot will auto-create required sheets on startup.

## Commands

- `/start` - Register & welcome message
- `/status` - Show base status
- `/menu` - Show menu
- `/build <building>` - Upgrade/build
- `/upgrade <building>` - Alias for /build
- `/queue` - Show pending upgrades
- `/train <unit> <count>` - Train units
- `/attack <user_id>` - Attack another player
- `/leaderboard` - View top players
