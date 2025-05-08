# handlers/weather.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.weather import get_current_weather
from utils.format import section_header

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weather = get_current_weather()
    combat_mod = weather.combat_modifier
    production_mod = weather.production_modifier
    remaining = (weather.end_time - datetime.now()).total_seconds() / 3600

    await update.message.reply_text(
        f"{section_header('WEATHER REPORT', '🌤️')}\n\n"
        f"**Current Weather**: {weather.name}\n"
        f"{weather.description}\n\n"
        f"Combat Modifier: {combat_mod:.1f}x\n"
        f"Production Modifier: {production_mod:.1f}x\n"
        f"Remaining: {remaining:.1f} hours",
        parse_mode="Markdown"
    )
