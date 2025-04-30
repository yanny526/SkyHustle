# zone_control_system.py

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.google_sheets import (
    get_player_faction,
    set_player_faction,
    get_zone_control,
    update_zone_control
)

FACTIONS = {
    "dominion": {
        "name": "Dominion",
        "emoji": "🟥",
        "bonus": "Metal production +10%"
    },
    "eclipse": {
        "name": "Eclipse",
        "emoji": "🟦",
        "bonus": "Unit training -5% time"
    },
    "vanguard": {
        "name": "Vanguard",
        "emoji": "🟩",
        "bonus": "Defense +5%"
    }
}

ZONES = {
    "zone_a": {
        "name": "Iron Frontier",
        "controlled_by": None,
        "bonus": "Metal +10%",
    },
    "zone_b": {
        "name": "Ash Dunes",
        "controlled_by": None,
        "bonus": "Fuel +10%",
    },
    "zone_c": {
        "name": "Crystal Gulf",
        "controlled_by": None,
        "bonus": "Crystal +10%",
    }
}


async def choose_faction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    current = get_player_faction(user_id)
    if current:
        return await update.message.reply_text(
            f"🛡️ You already joined <b>{FACTIONS[current]['name']}</b>.",
            parse_mode=ParseMode.HTML,
        )

    buttons = [
        [InlineKeyboardButton(f"{f['emoji']} {f['name']}", callback_data=f"JOIN_FACTION:{fid}")]
        for fid, f in FACTIONS.items()
    ]
    await update.message.reply_text(
        "🏳️ Choose your Faction:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def join_faction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    faction_id = query.data.split(":")[1]

    current = get_player_faction(user_id)
    if current:
        return await query.edit_message_text(
            f"🛡️ You are already part of <b>{FACTIONS[current]['name']}</b>.",
            parse_mode=ParseMode.HTML
        )

    set_player_faction(user_id, faction_id)
    await query.edit_message_text(
        f"✅ You joined <b>{FACTIONS[faction_id]['name']}</b> {FACTIONS[faction_id]['emoji']}!\n"
        f"Faction Bonus: {FACTIONS[faction_id]['bonus']}",
        parse_mode=ParseMode.HTML
    )
async def show_zone_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    zone_data = get_zone_control()
    lines = ["🌍 <b>Zone Map Overview</b>"]

    for zid, zinfo in ZONES.items():
        faction_id = zone_data.get(zid)
        faction = FACTIONS.get(faction_id) if faction_id else None
        control_str = (
            f"{faction['emoji']} {faction['name']}" if faction else "🕳️ Unclaimed"
        )
        lines.append(
            f"• <b>{zinfo['name']}</b> → {control_str} | Bonus: {zinfo['bonus']}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def capture_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    args = context.args

    if not args or args[0].lower() not in ZONES:
        available = ", ".join(ZONES.keys())
        return await update.message.reply_text(
            f"Usage: /capturezone [zone_id]\nAvailable: {available}"
        )

    faction = get_player_faction(player_id)
    if not faction:
        return await update.message.reply_text("❗Join a faction first using /faction")

    zone_id = args[0].lower()
    zone_owner = get_zone_control().get(zone_id)

    if zone_owner == faction:
        return await update.message.reply_text("✅ Your faction already controls this zone.")

    update_zone_control(zone_id, faction)

    await update.message.reply_text(
        f"🏴 You captured <b>{ZONES[zone_id]['name']}</b> for <b>{FACTIONS[faction]['name']}</b> {FACTIONS[faction]['emoji']}!",
        parse_mode=ParseMode.HTML
    )


def get_faction_bonus(player_id: str) -> dict:
    faction = get_player_faction(player_id)
    if not faction:
        return {}

    bonus_map = {
        "dominion": {"metal_pct": 10},
        "eclipse": {"train_time_pct": -5},
        "vanguard": {"defense_pct": 5}
    }
    return bonus_map.get(faction, {})
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_zone_markup():
    buttons = []
    zone_data = get_zone_control()
    for zid, zinfo in ZONES.items():
        owner = zone_data.get(zid)
        faction_str = FACTIONS[owner]["emoji"] if owner else "❔"
        label = f"{zinfo['name']} {faction_str}"
        buttons.append(
            [InlineKeyboardButton(label, callback_data=f"ZONEINFO:{zid}")]
        )
    return InlineKeyboardMarkup(buttons)


async def zone_ui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    await update.message.reply_text(
        "🌐 <b>Territorial Zones</b>\nSelect a zone below to view or attempt capture.",
        parse_mode=ParseMode.HTML,
        reply_markup=build_zone_markup()
    )


async def zone_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    zid = query.data.split(":", 1)[1]

    zone = ZONES[zid]
    owner_id = get_zone_control().get(zid)
    owner_text = (
        f"{FACTIONS[owner_id]['emoji']} {FACTIONS[owner_id]['name']}"
        if owner_id else "None"
    )

    player_faction = get_player_faction(pid)
    can_capture = player_faction and player_faction != owner_id

    text = (
        f"🌍 <b>{zone['name']}</b>\n"
        f"• Controlled by: {owner_text}\n"
        f"• Strategic Bonus: {zone['bonus']}\n\n"
        f"{'You may attempt capture below.' if can_capture else 'You cannot capture this zone.'}"
    )

    buttons = [[
        InlineKeyboardButton("« Back", callback_data="ZONE_MAIN")
    ]]

    if can_capture:
        buttons.insert(0, [
            InlineKeyboardButton("⚔️ Capture Zone", callback_data=f"CAPTURE:{zid}")
        ])

    markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
async def capture_zone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    zid = query.data.split(":", 1)[1]

    player_faction = get_player_faction(pid)
    if not player_faction:
        return await query.edit_message_text(
            "❌ You must join a faction before capturing zones.",
            parse_mode=ParseMode.HTML,
        )

    zone_data = get_zone_control()
    current_owner = zone_data.get(zid)
    if current_owner == player_faction:
        return await query.edit_message_text(
            "✅ This zone is already under your control.",
            parse_mode=ParseMode.HTML,
        )

    # Simulate capture success
    update_zone_control(zid, player_faction)

    zone = ZONES[zid]
    text = (
        f"🎉 <b>{zone['name']}</b> has been captured by "
        f"{FACTIONS[player_faction]['emoji']} {FACTIONS[player_faction]['name']}!\n"
        f"All faction members now benefit from: {zone['bonus']}."
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back to Zones", callback_data="ZONE_MAIN")]
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def zone_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌐 <b>Territorial Zones</b>\nSelect a zone below to view or attempt capture.",
        parse_mode=ParseMode.HTML,
        reply_markup=build_zone_markup()
    )
# ── Utility Functions ──────────────────────────────────────────────────────────

def get_zone_control() -> dict:
    try:
        recs = zone_control_ws.get_all_records()
        return {r["zone_id"]: r["faction"] for r in recs}
    except Exception:
        return {}


def update_zone_control(zone_id: str, faction: str):
    try:
        recs = zone_control_ws.get_all_records()
        for idx, r in enumerate(recs, start=2):
            if r["zone_id"] == zone_id:
                zone_control_ws.update(f"B{idx}", faction)
                return
        zone_control_ws.append_row([zone_id, faction])
    except Exception:
        pass


# ── Handler Registration ──────────────────────────────────────────────────────

def register_zone_handlers(app: ApplicationBuilder):
    app.add_handler(CommandHandler("zones", zone_main_command))
    app.add_handler(CallbackQueryHandler(view_zone_callback, pattern="^VIEW_ZONE:"))
    app.add_handler(CallbackQueryHandler(capture_zone_callback, pattern="^CAPTURE_ZONE:"))
    app.add_handler(CallbackQueryHandler(zone_main_callback, pattern="^ZONE_MAIN"))


