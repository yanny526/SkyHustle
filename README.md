# SkyHustle

SkyHustle is a Telegram-based strategy RPG where players build and manage futuristic aerial bases, train armies, research technologies, form alliances, and engage in PvE/PvP battles—all via chat commands and interactive menus.

## Features
- Build and upgrade structures
- Train and evolve units
- Research technologies
- Form and manage alliances
- PvE and PvP combat
- Daily rewards, achievements, and events
- All data stored in Google Sheets for easy management

## Project Structure

- `main.py` — Bot entrypoint and command handlers
- `modules/sheets_service.py` — Business logic and Google Sheets integration
- `handlers/` — (Optional) Additional command handlers
- `utils/` — Helpers: formatting, validation, logging
- `tests/` — Pytest suites: unit and integration
- `docs/` — PRD, API specs, architecture diagrams

## Setup

1. **Clone the repository**
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your credentials.
   - Required variables:
     - `BOT_TOKEN`: Telegram Bot API token
     - `BASE64_CREDS`: Base64-encoded Google service account credentials JSON
     - `SHEET_ID`: Google Sheet ID for game data
     - `REDIS_URL`: Redis connection string (optional, for caching)
     - `ADMIN_IDS`: Comma-separated Telegram user IDs for admin access
4. **Prepare your Google Sheet:**
   - The bot will auto-create all required worksheets and headers if they do not exist.
5. **Run the bot:**
   ```sh
   python main.py
   ```

## Environment Variables (.env)
```
BOT_TOKEN=your-telegram-bot-token
BASE64_CREDS=your-base64-google-service-account-json
SHEET_ID=your-google-sheet-id
REDIS_URL=redis://localhost:6379/0
ADMIN_IDS=123456789,987654321
```

## Testing
- Run all tests:
  ```sh
  pytest
  ```

## Linting & Formatting
- Lint:
  ```sh
  flake8
  ```
- Format:
  ```sh
  black .
  ```

## License
MIT 