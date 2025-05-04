# handlers/chaos_event.py

import random
from datetime import datetime
from telegram import ParseMode
from telegram.ext import ContextTypes
from sheets_service import get_rows, update_row

# Define your 5 storms
STORMS = [
    {
        "name": "Acidic Rain",
        "emoji": "🌧️☠️",
        "desc": "Days of acid rain wash over your base, corroding half your workshop levels.",
        "effect": lambda binfo: {bt: max(lvl//2,1) for bt,lvl in binfo.items()},
    },
    {
        "name": "Solar Flare",
        "emoji": "☀️⚡",
        "desc": "A massive solar flare surges through your power plant—gain +200 Energy!",
        "effect": lambda res: {"energy": res["energy"] + 200},
    },
    {
        "name": "Sandstorm Siege",
        "emoji": "🏜️🛡️",
        "desc": "A relentless sandstorm batters your Barracks—units train 50% slower until next storm.",
        "effect": lambda _: {"train_slow": True},
    },
    {
        "name": "Prosperity Winds",
        "emoji": "🍃💎",
        "desc": "Fortune whispers on the wind—gain +300 Minerals and +300 Credits!",
        "effect": lambda res: {"minerals": res["minerals"] + 300, "credits": res["credits"] + 300},
    },
    {
        "name": "Blight of Locusts",
        "emoji": "🐛🔥",
        "desc": "A plague of locusts devours half your mine output—Credits and Minerals production halved.",
        "effect": lambda _: {"prod_halved": True},
    },
]

async def chaos_event_job(context: ContextTypes.DEFAULT_TYPE):
    # pick one at random
    storm = random.choice(STORMS)
    header, *players = get_rows("Players")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    for row in players:
        uid, name, *_ = row
        chat_id = int(uid)

        # 1) Apply core effect (you can write these back to sheets if needed)
        # e.g.:
        #   if storm["name"] == "Solar Flare": update energy column in Players sheet...
        # (omitted for brevity)

        # 2) Notify the user
        text = (
            f"{storm['emoji']} *Random Chaos Storm!* {now}\n\n"
            f"*{storm['name']}*\n"
            f"_{storm['desc']}_\n\n"
            "These storms rage once a week. Prepare accordingly!"
        )
        await context.bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN)
