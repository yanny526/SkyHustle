import json
from telegram import Update
from telegram.ext import ContextTypes
from utils import google_sheets
from utils.ui_helpers import render_status_panel

# Load shop data
with open("config/shop_items.json", "r") as f:
    SHOP_DATA = json.load(f)


# --- Helpers ---
def _format_cost(cost: dict) -> str:
    """Formats a cost dictionary into a string."""
    return ", ".join(f"{amt} {res.title()}" for res, amt in cost.items())


# --- Handlers ---
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /shop — Show the normal shop inventory.
    """
    player_id = str(update.effective_user.id)
    lines = ["<b>🛒 Shop:</b>"]
    for item in SHOP_DATA["normal_shop"]:
        cost_str = _format_cost(item["cost"])
        lines.append(f"• {item['name']} ({cost_str}) — {item['description']}")
    lines.append("")
    lines.append(render_status_panel(player_id))
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buy [item_id] — Purchase an item from the shop.
    """
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "🛒 Usage: /buy [item_id]\n"
            "Example: /buy speedup_30m\n\n"
            + render_status_panel(player_id)
        )

    item_id = context.args[0]
    item = next(
        (i for i in SHOP_DATA["normal_shop"] if i["id"] == item_id),
        None
    )
    if not item:
        return await update.message.reply_text(
            "❌ Item not found in shop.\n\n" + render_status_panel(player_id)
        )

    cost = item["cost"]
    resources = google_sheets.load_resources(player_id)
    for res, amt in cost.items():
        if resources.get(res, 0) < amt:
            return await update.message.reply_text(
                f"❌ Not enough {res.title()} to buy {item['name']}.\n"
                f"Needed: {amt}, You have: {resources.get(res, 0)}\n\n"
                + render_status_panel(player_id)
            )

    # Deduct resources
    for res, amt in cost.items():
        resources[res] -= amt
    google_sheets.save_resources(player_id, resources)

    # Apply effect (simplified for example)
    if item_id == "speedup_30m":
        effect_str = "All timers reduced by 30 minutes (not implemented)."
    elif item_id == "xp_boost_100":
        effect_str = "100 XP added (not implemented)."
    else:
        effect_str = "Effect applied (not implemented)."

    await update.message.reply_text(
        f"✅ {item['name']} purchased! {effect_str}\n\n"
        + render_status_panel(player_id)
    )


async def unlock_blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /unlockblackmarket — Unlock the black market.
    """
    player_id = str(update.effective_user.id)
    cost_str = SHOP_DATA["black_market"]["unlock_cost"]
    credits = google_sheets.load_resources(player_id).get("credits", 0)
    needed = int(cost_str.lstrip("R"))

    if credits < needed:
        return await update.message.reply_text(
            f"❌ Not enough credits to unlock Black Market. Needed: {cost_str}, You have: {credits}\n\n"
            + render_status_panel(player_id)
        )

    # Deduct credits
    resources = google_sheets.load_resources(player_id)
    resources["credits"] -= needed
    google_sheets.save_resources(player_id, resources)

    await update.message.reply_text(
        "🔓 Black Market unlocked! Use /blackmarket to browse.\n\n"
        + render_status_panel(player_id)
    )


async def blackmarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /blackmarket — Show the black market inventory (if unlocked).
    """
    player_id = str(update.effective_user.id)
    # TODO: Check unlocked status from player data
    unlocked = True
    if not unlocked:
        cost = SHOP_DATA["black_market"]["unlock_cost"]
        return await update.message.reply_text(
            f"🔒 Black Market locked. Unlock with /unlockblackmarket (Cost: {cost})\n\n"
            + render_status_panel(player_id)
        )

    lines = ["<b>🏴‍☠️ Black Market:</b>"]
    for item in SHOP_DATA["black_market"]["items"]:
        lines.append(
            f"• {item['name']} (Credits {item['price']}) — {item['description']}"
        )
    lines.append("")
    lines.append(render_status_panel(player_id))
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def bmbuy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /bmbuy [item_id] — Purchase an item from the black market.
    """
    player_id = str(update.effective_user.id)
    if len(context.args) != 1:
        return await update.message.reply_text(
            "🏴‍☠️ Usage: /bmbuy [item_id]\n"
            "Example: /bmbuy shield_breaker\n\n"
            + render_status_panel(player_id)
        )

    item_id = context.args[0]
    item = next(
        (i for i in SHOP_DATA["black_market"]["items"] if i["id"] == item_id),
        None
    )
    if not item:
        return await update.message.reply_text(
            "❌ Item not found in Black Market.\n\n"
            + render_status_panel(player_id)
        )

    # TODO: Check unlocked status from player data
    unlocked = True
    if not unlocked:
        return await update.message.reply_text(
            "🔒 Black Market locked. Unlock with /unlockblackmarket.\n\n"
            + render_status_panel(player_id)
        )

    price = int(item["price"].lstrip("R"))
    credits = google_sheets.load_resources(player_id).get("credits", 0)
    if credits < price:
        return await update.message.reply_text(
            f"❌ Not enough credits to buy {item['name']}.\n"
            f"Needed: {price}, You have: {credits}\n\n"
            + render_status_panel(player_id)
        )

    # Deduct credits
    resources = google_sheets.load_resources(player_id)
    resources["credits"] -= price
    google_sheets.save_resources(player_id, resources)

    await update.message.reply_text(
        f"✅ {item['name']} purchased! Effect applied (not implemented).\n\n"
        + render_status_panel(player_id)
    )
