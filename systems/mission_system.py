import json
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# Load mission templates
with open("config/mission_data.json", "r") as f:
    MISSIONS = json.load(f)

# Helper to format rewards
def _format_rewards(rewards: dict) -> str:
    return ", ".join(f"{v} {k.capitalize()}" for k, v in rewards.items())

# Merge assigned records with their templates
def _merge_records(records: list[dict], templates: list[dict]) -> list[dict]:
    out = []
    for r in records:
        tmpl = next((t for t in templates if t.get("id") == r.get("mission_id")), {})
        merged = {
            'row_idx':    r.get('row_idx'),
            'mission_id': r.get('mission_id'),
            'type':       r.get('type'),
            'date':       r.get('date'),
            'progress':   int(r.get('progress', 0)),
            'claimed':    bool(r.get('claimed')),
            'description':tmpl.get('description', ''),
            'rewards':    tmpl.get('rewards', {}),
            'total':      tmpl.get('amount') or tmpl.get('requirement', {}).get('value') or 0
        }
        out.append(merged)
    return out

# Build inline menu of missions
async def menu_missions(context, player_id: str) -> tuple[str, InlineKeyboardMarkup]:
    today = datetime.date.today().isoformat()
    # Ensure daily missions
    daily_assigned = google_sheets.get_player_missions(player_id, 'daily', today)
    if not daily_assigned:
        for tmpl in MISSIONS.get('daily_templates', []):
            google_sheets.save_player_mission(
                player_id, tmpl['id'], 'daily', today, 0, False
            )
        daily_assigned = google_sheets.get_player_missions(player_id, 'daily', today)
    daily = _merge_records(daily_assigned, MISSIONS.get('daily_templates', []))

    # Story missions
    res = google_sheets.load_resources(player_id)
    lvl = res.get('level', 1)
    story_templates = [t for t in MISSIONS.get('story_missions', []) if lvl >= t.get('level_required', 0)]
    saved_story = google_sheets.get_player_missions(player_id, 'story')
    if len(saved_story) < len(story_templates):
        for tmpl in story_templates:
            if tmpl['id'] not in [r['mission_id'] for r in saved_story]:
                google_sheets.save_player_mission(
                    player_id, tmpl['id'], 'story', None, 0, False
                )
        saved_story = google_sheets.get_player_missions(player_id, 'story')
    story = _merge_records(saved_story, story_templates)

    # Epic missions
    epic_assigned = google_sheets.get_player_missions(player_id, 'epic')
    if not epic_assigned:
        for tmpl in MISSIONS.get('epic_missions', []):
            google_sheets.save_player_mission(
                player_id, tmpl['id'], 'epic', None, 0, False
            )
        epic_assigned = google_sheets.get_player_missions(player_id, 'epic')
    epic = _merge_records(epic_assigned, MISSIONS.get('epic_missions', []))

    # Build text and buttons
    text_lines = ["📜 <b>Your Missions</b>"]
    buttons = []
    for section, lst in (('Daily', daily), ('Story', story), ('Epic', epic)):
        text_lines.append(f"\n<b>{section}:</b>")
        for m in lst:
            status = '✅' if m['claimed'] else f"{m['progress']}/{m['total']}"
            text_lines.append(
                f"– {m['description']} ({status}) → {_format_rewards(m['rewards'])}"
            )
            if not m['claimed'] and m['progress'] >= m['total']:
                buttons.append([
                    InlineKeyboardButton(
                        f"Claim {m['mission_id']}",
                        callback_data=f"MISSION_CLAIM:{m['mission_id']}"
                    )
                ])
    # Back to main menu button at bottom
    buttons.append([
        InlineKeyboardButton("« Back", callback_data="NAV:back")
    ])

    # Append status panel
    text = "\n".join(text_lines) + "\n\n" + render_status_panel(player_id)
    markup = InlineKeyboardMarkup(buttons)
    return text, markup

# Slash‑command entrypoints
async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = str(update.effective_user.id)
    text, markup = await menu_missions(context, pid)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)

async def storymissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await missions(update, context)

async def epicmissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await missions(update, context)

# Claim via inline button
async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = str(query.from_user.id)
    mission_id = query.data.split(':',1)[1]
    # reuse existing logic
    context.args = [mission_id]
    from systems.mission_system import claimmission
    update.message = query.message
    await claimmission(update, context)
    # refresh list
    text, markup = await menu_missions(context, pid)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
