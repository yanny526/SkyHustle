# handlers/save_load.py

from telegram import Update
from telegram.ext import ContextTypes
import time

from modules.save_system import save_player_data, save_building_data, save_unit_data
from modules.save_system import load_player_data, load_buildings_data, load_units_data
from utils.format import section_header

async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.name

    # Get current game state
    player_data = {
        "name": name,
        "credits": 1000,
        "minerals": 500,
        "energy": 200,
        "skybucks": 0,
        "experience": 0,
        "level": 1,
        "last_login": int(time.time()),
        "alliance": "None",
        "global_rank": "?"
    }
    buildings_data = {
        "barracks": {"level": 1, "production": 10},
        "factory": {"level": 1, "production": 15},
        "research_lab": {"level": 1, "production": 20}
    }
    units_data = {
        "infantry": 0,
        "tanks": 0,
        "artillery": 0
    }

    # Save data
    save_player_data(uid, player_data)
    for building, data in buildings_data.items():
        save_building_data(uid, building, data)
    for unit, count in units_data.items():
        save_unit_data(uid, unit, count)

    await update.message.reply_text(
        f"{section_header('SAVE SYSTEM', '💾', 'none')}\n\n"
        "Your progress has been saved!",
        parse_mode="Markdown"
    )

async def load_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    # Load data
    player_data = load_player_data(uid)
    buildings_data = load_buildings_data(uid)
    units_data = load_units_data(uid)

    await update.message.reply_text(
        f"{section_header('LOAD SYSTEM', '💿', 'none')}\n\n"
        "Your progress has been loaded!\n\n"
        f"Commander: {player_data['name']}\n"
        f"Credits: {player_data['credits']}\n"
        f"Minerals: {player_data['minerals']}\n"
        f"Energy: {player_data['energy']}\n"
        f"Level: {player_data['level']}\n\n"
        f"Buildings:\n"
        f"Barracks: Level {buildings_data.get('barracks', {'level': 1})['level']}\n"
        f"Factory: Level {buildings_data.get('factory', {'level': 1})['level']}\n"
        f"Research Lab: Level {buildings_data.get('research_lab', {'level': 1})['level']}\n\n"
        f"Units:\n"
        f"Infantry: {units_data.get('infantry', 0)}\n"
        f"Tanks: {units_data.get('tanks', 0)}\n"
        f"Artillery: {units_data.get('artillery', 0)}",
        parse_mode="Markdown"
    )
