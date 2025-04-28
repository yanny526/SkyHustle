import json
import datetime
from utils import google_sheets
from utils.ui_helpers import render_status_panel

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
        for tmpl in MISSIONS.get("daily_templates", []):
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "daily", today, 0, False
            )
        assigned = google_sheets.get_player_missions(player_id, "daily", today)

    # Build reply
    lines = ["📜 Daily Missions:"]
    for m in assigned:
        status = "✅" if m.get("claimed") else f"{m.get('progress',0)}/{m.get('amount','?')}"
        lines.append(f"- {m.get('description','')} ({status}) → {format_rewards(m.get('rewards',{}))}")

    msg = "\n".join(lines) + "\n\n" + render_status_panel(player_id)
    await update.message.reply_text(msg)

# -------------- /storymissions --------------
async def storymissions(update, context):
    player_id = str(update.effective_user.id)
    # Fetch player level from resources
    res = google_sheets.load_resources(player_id)
    level = res.get('level', 1)

    # Load or assign story missions up to level
    available = [t for t in MISSIONS.get("story_missions", []) if level >= t.get("level_required", 0)]
    saved = google_sheets.get_player_missions(player_id, "story")
    for tmpl in available:
        if tmpl["id"] not in [m.get("mission_id") for m in saved]:
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "story", None, 0, False
            )
    saved = google_sheets.get_player_missions(player_id, "story")

    # Build reply
    lines = ["📜 Story Missions:"]
    for m in saved:
        req_val = m.get('progress',0)
        total = m.get('requirement_value','?')
        lines.append(
            f"- {m.get('description','')} ({req_val}/{total}) → {format_rewards(m.get('rewards',{}))}"
        )

    msg = "\n".join(lines) + "\n\n" + render_status_panel(player_id)
    await update.message.reply_text(msg)

# -------------- /epicmissions --------------
async def epicmissions(update, context):
    player_id = str(update.effective_user.id)

    # Load or assign epic missions
    saved = google_sheets.get_player_missions(player_id, "epic")
    if not saved:
        for tmpl in MISSIONS.get("epic_missions", []):
            google_sheets.save_player_mission(
                player_id, tmpl["id"], "epic", None, 0, False
            )
        saved = google_sheets.get_player_missions(player_id, "epic")

    # Build reply
    lines = ["📜 Epic Missions:"]
    for m in saved:
        req_val = m.get('progress',0)
        total = m.get('requirement_value','?')
        lines.append(
            f"- {m.get('description','')} ({req_val}/{total}) → {format_rewards(m.get('rewards',{}))}"
        )

    msg = "\n".join(lines) + "\n\n" + render_status_panel(player_id)
    await update.message.reply_text(msg)

# -------------- /claimmission --------------
async def claimmission(update, context):
    player_id = str(update.effective_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text(
            "🛡️ Usage: /claimmission [mission_id]\n\n" + render_status_panel(player_id)
        )
        return

    mission_id = args[0]
    m = google_sheets.get_single_mission(player_id, mission_id)
    if not m:
        await update.message.reply_text(
            "❌ Mission not found.\n\n" + render_status_panel(player_id)
        )
        return

    if m.get("claimed"):
        await update.message.reply_text(
            "⚡ Mission already claimed.\n\n" + render_status_panel(player_id)
        )
        return

    # Determine template
    key = m["type"]
    tmpl_list_key = "daily_templates" if key == "daily" else f"{key}_missions"
    tmpl = next((t for t in MISSIONS.get(tmpl_list_key, []) if t.get("id") == mission_id), None)
    if not tmpl:
        await update.message.reply_text(
            "❌ Mission template missing.\n\n" + render_status_panel(player_id)
        )
        return

    # Calculate progress
    progress = 0
    if tmpl.get("type") == "train":
        progress = google_sheets.get_training_total(player_id, tmpl.get("unit"), tmpl.get("amount"))
    elif tmpl.get("type") == "mine":
        progress = google_sheets.get_mined_total(player_id, tmpl.get("resource"), tmpl.get("amount"))
    elif tmpl.get("type") == "attack":
        progress = google_sheets.get_attack_count(player_id)
    elif tmpl.get("type") == "upgrade":
        progress = google_sheets.get_building_level(player_id, tmpl.get("requirement", {}).get("building"))
    elif "battle_wins" in tmpl.get("requirement", {}):
        progress = google_sheets.get_battle_wins(player_id)
    else:
        progress = m.get("progress", 0)

    needed = tmpl.get("amount") or tmpl.get("requirement", {}).get("level") or tmpl.get("requirement", {}).get("battle_wins") or 0
    if progress < needed:
        await update.message.reply_text(
            "⏳ You have not met the mission requirement yet.\n\n" + render_status_panel(player_id)
        )
        return

    # Award rewards and mark
    google_sheets.award_mission_rewards(player_id, tmpl.get("rewards", {}))
    google_sheets.mark_mission_claimed(player_id, mission_id)

    msg = (
        f"🎉 Mission '{tmpl.get('description','')}' claimed: {format_rewards(tmpl.get('rewards',{}))}\n\n"
        + render_status_panel(player_id)
    )
    await update.message.reply_text(msg)
