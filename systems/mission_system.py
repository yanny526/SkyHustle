# mission_system.py

import json
import datetime
from utils import google_sheets

# Load mission templates
with open("config/mission_data.json", "r") as f:
    MISSIONS = json.load(f)

# Helper to format rewards
def format_rewards(r):
    parts = []
    for k, v in r.items():
        parts.append(f"{v} {k.capitalize()}")
    return ", ".join(parts)

# -------------- /missions (Daily) --------------
async def missions(update, context):
    player_id = str(update.effective_user.id)
    today = datetime.date.today().isoformat()

    # Ensure daily missions assigned
    assigned = google_sheets.get_player_missions(player_id, "daily", today)
    if not assigned:
        for tmpl in MISSIONS["daily_templates"]:
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "daily", today, 0, False
            )
        assigned = google_sheets.get_player_missions(player_id, "daily", today)

    # Build reply
    lines = ["📜 Daily Missions:"]
    for m in assigned:
        status = "✅" if m["claimed"] else f"{m['progress']}/{m.get('amount', '?')}"
        lines.append(f"- {m['description']} ({status}) → {format_rewards(m['rewards'])}")
    await update.message.reply_text("\n".join(lines))

# -------------- /storymissions --------------
async def storymissions(update, context):
    player_id = str(update.effective_user.id)
    level = google_sheets.get_player_level(player_id)

    # Load or assign story missions up to level
    available = [t for t in MISSIONS["story_missions"] if level >= t["level_required"]]
    saved = google_sheets.get_player_missions(player_id, "story")
    # Save any new ones
    for tmpl in available:
        if tmpl["id"] not in [m["mission_id"] for m in saved]:
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "story", None, 0, False
            )
    saved = google_sheets.get_player_missions(player_id, "story")

    # Build reply
    lines = ["📜 Story Missions:"]
    for m in saved:
        lines.append(f"- {m['description']} ({m['progress']}/{m.get('requirement_value', '?')}) → {format_rewards(m['rewards'])}")
    await update.message.reply_text("\n".join(lines))

# -------------- /epicmissions --------------
async def epicmissions(update, context):
    player_id = str(update.effective_user.id)

    # Load or assign epic missions
    saved = google_sheets.get_player_missions(player_id, "epic")
    if not saved:
        for tmpl in MISSIONS["epic_missions"]:
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "epic", None, 0, False
            )
        saved = google_sheets.get_player_missions(player_id, "epic")

    # Build reply
    lines = ["📜 Epic Missions:"]
    for m in saved:
        lines.append(f"- {m['description']} ({m['progress']}/{m.get('requirement_value', '?')}) → {format_rewards(m['rewards'])}")
    await update.message.reply_text("\n".join(lines))

# -------------- /claimmission --------------
async def claimmission(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("🛡️ Usage: /claimmission [mission_id]")
        return

    mission_id = args[0]
    m = google_sheets.get_single_mission(player_id, mission_id)
    if not m:
        await update.message.reply_text("❌ Mission not found.")
        return

    if m["claimed"]:
        await update.message.reply_text("⚡ Mission already claimed.")
        return

    # Check requirement dynamically
    req_type = m["type"]
    req = MISSIONS[f"{req_type}_templates" if req_type=="daily" else f"{req_type}_missions"]
    tmpl = next((t for t in MISSIONS[f"{req_type}_templates" if req_type=="daily" else f"{req_type}_missions"] if t["id"]==mission_id), None)

    # Determine current progress
    if tmpl["type"] == "train":
        count = google_sheets.get_training_total(player_id, tmpl["unit"], tmpl["amount"])
    elif tmpl["type"] == "mine":
        count = google_sheets.get_mined_total(player_id, tmpl["resource"], tmpl["amount"])
    elif tmpl["type"] == "attack":
        count = google_sheets.get_attack_count(player_id)
    elif tmpl["type"] == "upgrade":
        count = google_sheets.get_building_level(player_id, tmpl["requirement"]["building"])
    elif "battle_wins" in tmpl["requirement"]:
        count = google_sheets.get_battle_wins(player_id)
    else:
        count = m["progress"]

    if count < (tmpl.get("amount") or tmpl["requirement"].get("level") or tmpl["requirement"].get("battle_wins")):
        await update.message.reply_text("⏳ You have not met the mission requirement yet.")
        return

    # Award rewards
    google_sheets.award_mission_rewards(player_id, tmpl["rewards"])
    google_sheets.mark_mission_claimed(player_id, mission_id)
    await update.message.reply_text(f"🎉 Mission '{tmpl['description']}' claimed: {format_rewards(tmpl['rewards'])}")

