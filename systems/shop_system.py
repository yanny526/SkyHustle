# shop_system.py

import json
from datetime import datetime
from utils import google_sheets

# Load shop items
with open("config/shop_items.json", "r") as f:
    SHOP = json.load(f)

# -------------- /shop — Normal Shop Browser --------------
async def shop(update, context):
    player_id = str(update.effective_user.id)
    resources = google_sheets.load_resources(player_id)
    lines = [
        f"💰 Your Resources: Metal {resources['metal']}, Fuel {resources['fuel']}, Crystals {resources['crystal']}",
        "",
        "🛒 Normal Shop Items:"
    ]
    for item in SHOP["normal_shop"]:
        cost_str = ", ".join(f"{v} {k}" for k, v in item["cost"].items())
        lines.append(f"- {item['id']}: {item['name']} ({cost_str})")
        lines.append(f"  {item['description']}")
    lines.append("")
    lines.append("To purchase: /buy [item_id]")
    await update.message.reply_text("\n".join(lines))

# -------------- /buy — Purchase Normal Shop Item --------------
async def buy(update, context):
    player_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("🛒 Usage: /buy [item_id]")
        return

    item_id = args[0]
    item = next((i for i in SHOP["normal_shop"] if i["id"] == item_id), None)
    if not item:
        await update.message.reply_text("❌ Item not found in the Normal Shop.")
        return

    resources = google_sheets.load_resources(player_id)
    # Check costs
    for res, cost in item["cost"].items():
        if resources.get(res, 0) < cost:
            await update.message.reply_text(f"❌ Not enough {res}. You need {cost}.")
            return

    # Deduct cost
    for res, cost in item["cost"].items():
        resources[res] -= cost
    google_sheets.save_resources(player_id, resources)
    google_sheets.save_purchase(player_id, "normal", item_id, datetime.now().isoformat())

    await update.message.reply_text(f"✅ Purchased {item['name']}! {item['description']}")

# -------------- /unlockblackmarket — Unlock Premium Store --------------
async def unlock_blackmarket(update, context):
    player_id = str(update.effective_user.id)
    if google_sheets.has_unlocked_blackmarket(player_id):
        await update.message.reply_text("🔓 Black Market already unlocked!")
        return

    # In a real integration, you’d verify payment here.
    google_sheets.unlock_blackmarket(player_id)
    await update.message.reply_text(
        f"🔓 Black Market unlocked for {SHOP['black_market']['unlock_cost']}! Use /blackmarket to browse."
    )

# -------------- /blackmarket — Premium Shop Browser --------------
async def blackmarket(update, context):
    player_id = str(update.effective_user.id)
    if not google_sheets.has_unlocked_blackmarket(player_id):
        unlock_cost = SHOP["black_market"]["unlock_cost"]
        await update.message.reply_text(
            f"🔒 Black Market locked. Unlock it for {unlock_cost} via /unlockblackmarket."
        )
        return

    lines = ["💎 Black Market Items:"]
    for item in SHOP["black_market"]["items"]:
        lines.append(f"- {item['id']}: {item['name']} (Price: {item['price']})")
        lines.append(f"  {item['description']}")
    lines.append("")
    lines.append("To purchase: /bmbuy [item_id]")
    await update.message.reply_text("\n".join(lines))

# -------------- /bmbuy — Purchase Premium Item --------------
async def bmbuy(update, context):
    player_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("💎 Usage: /bmbuy [item_id]")
        return

    item_id = args[0]
    item = next((i for i in SHOP["black_market"]["items"] if i["id"] == item_id), None)
    if not item:
        await update.message.reply_text("❌ Item not found in Black Market.")
        return

    if google_sheets.has_purchase(player_id, item_id):
        await update.message.reply_text("⚠️ You already purchased this item.")
        return

    # Record the purchase; assume real‐money handled externally
    google_sheets.save_purchase(player_id, "blackmarket", item_id, datetime.now().isoformat())
    await update.message.reply_text(f"✅ Purchased {item['name']} for {item['price']}! {item['description']}")
