# ui_helpers.py (Part 1 of X)

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ── Send Main Menu ───────────────────────────────────────────────────────
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Missions", callback_data="mission_main")],
        [InlineKeyboardButton("🏗 Build", callback_data="build_main")],
        [InlineKeyboardButton("⚔ Train", callback_data="train_main")],
        [InlineKeyboardButton("🚀 Attack", callback_data="combat_main")],
        [InlineKeyboardButton("🛰 Spy", callback_data="spy_main")],
        [InlineKeyboardButton("🧬 Research", callback_data="tech_main")],
        [InlineKeyboardButton("🛒 Store", callback_data="store_main")],
        [InlineKeyboardButton("💣 Black Market", callback_data="bm_main")],
        [InlineKeyboardButton("🎁 Rewards", callback_data="reward_main")],
        [InlineKeyboardButton("📈 Status", callback_data="status_main")],
    ]
    await update.message.reply_text(
        "👋 *Welcome to SkyHustle!*\nSelect an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ── Helper: Button Grid ──────────────────────────────────────────────────
def button_grid(buttons, cols=2):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=data)
         for text, data in buttons[i:i+cols]]
        for i in range(0, len(buttons), cols)
    ])
# ui_helpers.py (Part 2 of X)

def render_resources(player_data):
    return (
        f"🪙 *Resources:*\n"
        f"• Metal: `{player_data['metal']}`\n"
        f"• Energy: `{player_data['energy']}`\n"
        f"• Oil: `{player_data['oil']}`\n"
        f"• Credits: `{player_data['credits']}`"
    )

def render_buildings(building_data):
    if not building_data:
        return "🏗 No buildings constructed yet."
    lines = ["🏗 *Your Buildings:*"]
    for name, level in building_data.items():
        lines.append(f"• {name.title()}: `Lvl {level}`")
    return "\n".join(lines)

def render_army(army_data):
    if not army_data:
        return "⚔ You have no units trained yet."
    lines = ["⚔ *Your Army:*"]
    for unit, count in army_data.items():
        lines.append(f"• {unit.title()}: `{count}`")
    return "\n".join(lines)

def render_tech_tree(tech_data):
    if not tech_data:
        return "🧬 No tech researched yet."
    lines = ["🧬 *Tech Tree:*"]
    for tech, level in tech_data.items():
        lines.append(f"• {tech.title()}: `Lvl {level}`")
    return "\n".join(lines)
# ui_helpers.py (Part 3 of X)

def render_spy_report(report: dict):
    if not report:
        return "🛰 No data available. Target may have cloaking tech."
    
    lines = [f"🛰 *Spy Report on Player {report.get('target')}*"]
    if "resources" in report:
        res = report["resources"]
        lines.append(
            f"• Metal: `{res['metal']}` | Energy: `{res['energy']}` | Oil: `{res['oil']}` | Credits: `{res['credits']}`"
        )
    if "army" in report:
        for unit, count in report["army"].items():
            lines.append(f"• {unit.title()}: `{count}`")
    if "tech" in report:
        for tech, level in report["tech"].items():
            lines.append(f"• {tech.title()} Tech: `Lvl {level}`")
    return "\n".join(lines)

def render_missions(missions: list):
    if not missions:
        return "🎯 No missions available."
    return "\n".join(
        [f"• {m['name']}: {m['desc']} — *Reward:* {m['reward']} credits" for m in missions]
    )

def render_blackmarket_item(item):
    return (
        f"{item['name']}\n"
        f"{item['desc']}\n"
        f"💳 Cost: *{item['cost']}* credits"
    )

def render_store_item(item):
    return (
        f"{item['name']}\n"
        f"{item['desc']}\n"
        f"💵 Price: *{item['price']}* credits"
    )
# ui_helpers.py (Part 4 of 4)

def render_zone_control(zone_data):
    if not zone_data:
        return "🧭 No zones controlled yet."
    lines = ["🧭 *Zone Control:*"]
    for zone, info in zone_data.items():
        lines.append(f"• {zone.title()}: {info['faction']} (Player {info['claimed_by']})")
    return "\n".join(lines)

def render_rewards(rewards: list):
    if not rewards:
        return "🎁 No rewards available."
    return "\n".join([f"• {r['name']} — *{r['amount']}* credits" for r in rewards])

def render_expand_options(current_slots: int, max_slots: int, cost: int):
    return (
        f"📦 *Base Slots:*\n"
        f"• Current Slots: `{current_slots}` / `{max_slots}`\n"
        f"• Expansion Cost: *{cost} credits*"
    )

def back_button(callback_data: str = "main_menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=callback_data)]
    ])
