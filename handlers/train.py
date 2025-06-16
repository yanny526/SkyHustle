
# handlers/train.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from sheets_service import get_rows, update_row, append_row
from utils.decorators import game_command
from utils.time_utils import format_hhmmss
from utils.format_utils import section_header
from modules.unit_manager import get_unlocked_tier, UNITS
from modules.challenge_manager import load_challenges, update_player_progress

@game_command
async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train               → show help & examples
    /train <unit> <cnt>  → train units of current tier
    """
    uid  = str(update.effective_user.id)
    args = context.args.copy()

    # 0) Help screen
    if not args or args[0].lower() == "help":
        lines = [
            section_header("🏰 TRAINING COMMANDS 🏰", pad_char="=", pad_count=3),
            "",
            "Ready your forces! Issue training orders like:",
            "",
            section_header("🗡️ Train Infantry", pad_char="-", pad_count=3),
            "`/train infantry 10`",
            "→ Queues 10 Infantry (Tier 1) in your Barracks.",
            "",
            section_header("🚀 Train Artillery", pad_char="-", pad_count=3),
            "`/train artillery 5`",
            "→ Queues 5 Artillery (Tier 2) once unlocked.",
            "",
            "After training, check `/status` to see your updated army.",
        ]
        return await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )

    # 1) Validate args
    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Usage: `/train <unit> <count>`",
            parse_mode=ParseMode.MARKDOWN
        )

    raw_key = args[0]
    # normalize and match unit key
    def aliases(k, info):
        disp = info[0]
        return {k.lower(), k.replace("_","").lower(), disp.replace(" ","").lower()}
    matches = [k for k,info in UNITS.items() if raw_key.lower() in aliases(k,info)]
    if not matches:
        return await update.message.reply_text(
            f"❌ Unknown unit *{raw_key}*.", parse_mode=ParseMode.MARKDOWN
        )
    if len(matches) > 1:
        return await update.message.reply_text(
            f"❌ Ambiguous unit name *{raw_key}* matches: {', '.join(matches)}.",
            parse_mode=ParseMode.MARKDOWN
        )
    key = matches[0]

    # parse count
    try:
        cnt = int(args[1])
        if cnt < 1:
            raise ValueError
    except ValueError:
        return await update.message.reply_text(
            "❌ Count must be a positive integer.", parse_mode=ParseMode.MARKDOWN
        )

    name, emoji, tier, power, cost = UNITS[key]
    unlocked = get_unlocked_tier(uid)
    if tier != unlocked:
        return await update.message.reply_text(
            f"❌ *{name}* is Tier {tier}. You have only unlocked Tier {unlocked}.",
            parse_mode=ParseMode.MARKDOWN
        )

    # calculate total cost
    totC = cost['c'] * cnt
    totM = cost['m'] * cnt
    totE = cost['e'] * cnt

    # fetch player row and capture tutorial progress
    players = get_rows('Players')
    if not players:
        return
    header = players[0]
    # find indices
    progress_idx = header.index('progress') if 'progress' in header else None
    credits_idx = header.index('credits')
    # fetch current prow and index
    prow = None
    prow_idx = None
    for pi, row in enumerate(players[1:], start=1):
        if row[0] == uid:
            prow = row.copy()
            prow_idx = pi
            break
    if prow is None:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    # record old progress
    old_progress = prow[progress_idx] if progress_idx is not None and len(prow) > progress_idx else None

    # resource check
    try:
        creds = int(prow[credits_idx])
        minerals = int(prow[header.index('minerals')])
        energy = int(prow[header.index('energy')])
    except Exception:
        return await update.message.reply_text("❗ Run /start first.", parse_mode=ParseMode.MARKDOWN)
    if creds < totC or minerals < totM or energy < totE:
        return await update.message.reply_text(
            f"❌ Need {totC}💳 {totM}⛏️ {totE}⚡.", parse_mode=ParseMode.MARKDOWN
        )

    # deduct resources & update row
    prow[credits_idx] = str(creds - totC)
    prow[header.index('minerals')] = str(minerals - totM)
    prow[header.index('energy')] = str(energy - totE)
    update_row('Players', prow_idx, prow)

    # update Army sheet
    army = get_rows('Army')
    found = None
    for ai, row in enumerate(army[1:], start=1):
        if row[0] == uid and row[1] == key:
            found = (ai, row.copy())
            break

    if found:
        ai, arow = found
        new_count = int(arow[2]) + cnt
        arow[2] = str(new_count)
        update_row('Army', ai, arow)
    else:
        append_row('Army', [uid, key, str(cnt)])
        new_count = cnt

    # 2) Confirmation UI
    lines = [
        section_header("✅ Training Complete"),
        "",
        f"{emoji} *{name}* × {cnt} trained successfully!",
        f"💳 Spent {totC}   ⛏️ {totM}   ⚡ {totE}",
        f"🛡️ New {name} count: {new_count}",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # 3) Tutorial progression: Step 3 → 4
    if old_progress == "3":
        # reward 200 credits and advance to step 4 (view status)
        prow[credits_idx] = str(int(prow[credits_idx]) + 200)
        if progress_idx is not None:
            prow[progress_idx] = "4"
        update_row('Players', prow_idx, prow)

        lines = [
            section_header("🎉 Tutorial Complete Step!"),
            "",
            "✅ You’ve trained your first units!",
            "💳 +200 Credits awarded!",
            "",
            section_header("🧾 Tutorial Step 4", pad_char="-", pad_count=3),
            "`/status` — View your base status to proceed.",
        ]
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("/status")]],
            resize_keyboard=True
        )
        return await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    # 4) Track daily challenge
    for ch in load_challenges('daily'):
        if ch.key == f"{name.lower()}_trained":
            update_player_progress(uid, ch, cnt)
            break

handler = CommandHandler('train', train)
