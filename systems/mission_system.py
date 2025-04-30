import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import google_sheets
from utils.ui_helpers import render_status_panel


# Load mission templates
with open("config/mission_data.json", "r") as f:
    MISSION_TEMPLATES = json.load(f)


# --- Helpers ---
def _generate_missions(mission_type: str, count: int):
    """
    Picks `count` random missions of a given type.
    (In a real game, this might consider player level, etc.)
    """
    templates = MISSION_TEMPLATES.get(f"{mission_type}_templates", [])
    if not templates:
        return []
    return [templates[i % len(templates)] for i in range(count)]


def _format_rewards(rewards: dict) -> str:
    """Formats a reward dictionary into a string."""
    return ", ".join(f"{amt} {res.title()}" for res, amt in rewards.items())


# --- /missions — Show daily missions ---
async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    today = datetime.now().date()
    missions_data = google_sheets.load_player_missions(player_id)

    # Ensure missions_data has today's date
    if not missions_data or missions_data.get("date") != str(today):
        new_missions = _generate_missions("daily", 3)
        missions_data = {
            "date": str(today),
            "missions": {m["id"]: False for m in new_missions},
        }
        google_sheets.save_player_missions(player_id, missions_data)
    else:
        # Reconstruct mission objects for display
        new_missions = [
            tpl for tpl in MISSION_TEMPLATES.get("daily_templates", [])
            if tpl["id"] in missions_data["missions"]
        ]

    # Build message
    lines = ["<b>📜 Daily Missions:</b>"]
    buttons = []
    for m in new_missions:
        done = missions_data["missions"].get(m["id"], False)
        icon = "✅" if done else "⬜"
        lines.append(
            f"{icon} {m['description']}  (Reward: {_format_rewards(m['rewards'])})"
        )
        if not done:
            buttons.append([
                InlineKeyboardButton(
                    "Claim", callback_data=f"MISSION_CLAIM:daily:{m['id']}"
                )
            ])
        lines.append("")

    lines.append(render_status_panel(player_id))
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=markup
    )


# --- /storymissions — Show story missions ---
async def storymissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    missions_data = google_sheets.load_player_missions(player_id) or {}

    if "story" not in missions_data:
        new_missions = _generate_missions("story", 5)
        missions_data["story"] = {m["id"]: False for m in new_missions}
        google_sheets.save_player_missions(player_id, missions_data)
    else:
        new_missions = [
            tpl for tpl in MISSION_TEMPLATES.get("story_templates", [])
            if tpl["id"] in missions_data["story"]
        ]

    lines = ["<b>📜 Story Missions:</b>"]
    buttons = []
    for m in new_missions:
        done = missions_data["story"].get(m["id"], False)
        icon = "✅" if done else "⬜"
        lines.append(
            f"{icon} {m['description']}  (Reward: {_format_rewards(m['rewards'])})"
        )
        if not done:
            buttons.append([
                InlineKeyboardButton(
                    "Claim", callback_data=f"MISSION_CLAIM:story:{m['id']}"
                )
            ])
        lines.append("")

    lines.append(render_status_panel(player_id))
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=markup
    )


# --- /epicmissions — Show epic missions ---
async def epicmissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = str(update.effective_user.id)
    missions_data = google_sheets.load_player_missions(player_id) or {}

    if "epic" not in missions_data:
        new_missions = _generate_missions("epic", 5)
        missions_data["epic"] = {m["id"]: False for m in new_missions}
        google_sheets.save_player_missions(player_id, missions_data)
    else:
        new_missions = [
            tpl for tpl in MISSION_TEMPLATES.get("epic_templates", [])
            if tpl["id"] in missions_data["epic"]
        ]

    lines = ["<b>📜 Epic Missions:</b>"]
    buttons = []
    for m in new_missions:
        done = missions_data["epic"].get(m["id"], False)
        icon = "✅" if done else "⬜"
        lines.append(
            f"{icon} {m['description']}  (Reward: {_format_rewards(m['rewards'])})"
        )
        if not done:
            buttons.append([
                InlineKeyboardButton(
                    "Claim", callback_data=f"MISSION_CLAIM:epic:{m['id']}"
                )
            ])
        lines.append("")

    lines.append(render_status_panel(player_id))
    markup = InlineKeyboardMarkup(buttons) if buttons else None

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=markup
    )


# --- Callback for mission claims ---
async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player_id = str(query.from_user.id)
    _, mtype, mission_id = query.data.split(":", 2)

    missions_data = google_sheets.load_player_missions(player_id) or {}
    category = {
        "daily": "missions",
        "story": "story",
        "epic": "epic"
    }.get(mtype)

    if not category or mission_id not in missions_data.get(category, {}):
        return await query.edit_message_text(
            "❌ Cannot claim this mission.", parse_mode="HTML"
        )

    if missions_data[category][mission_id]:
        return await query.edit_message_text(
            "❌ Mission already claimed.", parse_mode="HTML"
        )

    # Mark claimed and apply rewards
    tpl_list = MISSION_TEMPLATES.get(f"{mtype}_templates", [])
    rewards = next((m["rewards"] for m in tpl_list if m["id"] == mission_id), {})
    missions_data[category][mission_id] = True
    google_sheets.save_player_missions(player_id, missions_data)

    await _apply_rewards(player_id, rewards)
    return await query.edit_message_text(
        f"✅ Mission Claimed! Rewards: {_format_rewards(rewards)}",
        parse_mode="HTML"
    )


async def _apply_rewards(player_id: str, rewards: dict):
    """
    Helper: Applies rewards to the player's resources.
    """
    resources = google_sheets.load_resources(player_id)
    for res, amt in rewards.items():
        resources[res] = resources.get(res, 0) + amt
    google_sheets.save_resources(player_id, resources)
