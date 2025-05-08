# bot/main.py

import logging
from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from handlers.start import handler as start_handler
from handlers.status import handler as status_handler
from handlers.build import handler as build_handler
from handlers.train import handler as train_handler
from handlers.attack import handler as attack_handler
from handlers.shop import handler as shop_handler
from handlers.black_market import handler as black_market_handler
from handlers.achievements import handler as achievements_handler
from handlers.alliance import handler as alliance_handler_alliance
from handlers.leaderboard import handler as leaderboard_handler
from handlers.daily import handler as daily_handler
from handlers.events import handler as events_handler
from handlers.notifications import handler as notifications_handler
from handlers.chat import private_message, alliance_chat
from handlers.save_load import save_handler, load_handler
from handlers.faction import handler as faction_handler
from handlers.chaos_events import handler as chaos_events_handler
from handlers.endgame import handler as endgame_handler
from handlers.tutorial import handler as tutorial_handler
from handlers.scanner import handler as scanner_handler
from handlers.unit_specialization import handler as specialization_handler
from handlers.weather import handler as weather_handler
from handlers.unit_evolution import handler as evolution_handler
from handlers.defensive_structures import handler as defensive_handler
from handlers.research import handler as research_handler
from handlers.alliance_war import handler as war_handler
from handlers.admin import handler as admin_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Start the game"),
        ("status", "View your base status"),
        ("build", "Construct buildings"),
        ("train", "Train units"),
        ("attack", "Attack other players"),
        ("shop", "Visit the normal shop"),
        ("blackmarket", "Visit the black market"),
        ("achievements", "View your achievements"),
        ("alliance", "Manage alliances"),
        ("leaderboard", "View leaderboards"),
        ("daily", "Claim daily rewards"),
        ("events", "View current events"),
        ("notifications", "Set up notifications"),
        ("msg", "Send a private message"),
        ("save", "Save your progress"),
        ("load", "Load your progress"),
        ("faction", "Join or view factions"),
        ("chaos", "View or trigger chaos events"),
        ("endgame", "Attempt endgame challenges"),
        ("tutorial", "Access the game tutorial"),
        ("scan", "Get suggested targets"),
        ("specialize", "Enhance units with special abilities"),
        ("weather", "Check current weather conditions"),
        ("evolve", "Evolve your units"),
        ("defensive", "Build defensive structures"),
        ("research", "Unlock advanced technologies"),
        ("war", "Participate in alliance wars"),
        ("admin", "Access admin commands"),
    ])

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init = post_init

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("build", build_handler))
    app.add_handler(CommandHandler("train", train_handler))
    app.add_handler(CommandHandler("attack", attack_handler))
    app.add_handler(CommandHandler("shop", shop_handler))
    app.add_handler(CommandHandler("blackmarket", black_market_handler))
    app.add_handler(CommandHandler("achievements", achievements_handler))
    app.add_handler(CommandHandler("alliance", alliance_handler_alliance))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("daily", daily_handler))
    app.add_handler(CommandHandler("events", events_handler))
    app.add_handler(CommandHandler("notifications", notifications_handler))
    app.add_handler(CommandHandler("msg", private_message))
    app.add_handler(CommandHandler("save", save_handler))
    app.add_handler(CommandHandler("load", load_handler))
    app.add_handler(CommandHandler("faction", faction_handler))
    app.add_handler(CommandHandler("chaos", chaos_events_handler))
    app.add_handler(CommandHandler("endgame", endgame_handler))
    app.add_handler(CommandHandler("tutorial", tutorial_handler))
    app.add_handler(CommandHandler("scan", scanner_handler))
    app.add_handler(CommandHandler("specialize", specialization_handler))
    app.add_handler(CommandHandler("weather", weather_handler))
    app.add_handler(CommandHandler("evolve", evolution_handler))
    app.add_handler(CommandHandler("defensive", defensive_handler))
    app.add_handler(CommandHandler("research", research_handler))
    app.add_handler(CommandHandler("war", war_handler))
    app.add_handler(CommandHandler("admin", admin_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, alliance_chat))

    app.run_polling()

if __name__ == "__main__":
    main()