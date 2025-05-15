import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row

logger = logging.getLogger(__name__)

# ─── Sheet names ────────────────────────────────────────────────────────────
BUILDING_DEFS_SHEET = "BuildingDefs"
BUILD_QUEUE_SHEET   = "BuildQueue"       # cols: user_id, building, to_level, start_ts, end_ts
BUILD_DONE_SHEET    = "CompletedBuilds"  # cols: user_id, building, level, completed_ts
PLAYERS_SHEET       = "Players"

# ─── Production-per-level config ────────────────────────────────────────────
PRODUCTION_PER_LEVEL = {
    "Bank":       ("credits",   10),
    "Mine":       ("minerals",   5),
    "PowerPlant": ("energy",     3),
}

# ─── Helpers ────────────────────────────────────────────────────────────────
def _get_completed_rows() -> list[list[str]]:
    try:
        return get_rows(BUILD_DONE_SHEET)[1:]
    except HttpError as e:
        logger.error("Cannot read %s: %s", BUILD_DONE_SHEET, e)
        return []

def get_current_level(user_id: str, key: str) -> int:
    kl = key.lower()
    return sum(1 for r in _get_completed_rows() if r[0]==user_id and r[1].lower()==kl)

# ─── Load Definitions ───────────────────────────────────────────────────────
def get_build_defs() -> dict:
    try:
        rows = get_rows(BUILDING_DEFS_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILDING_DEFS_SHEET, e)
        return {}
    if len(rows) < 2:
        return {}
    header = rows[0]
    key_i = header.index("key")
    name_i = header.index("name")
    defs = {}
    for row in rows[1:]:
        if len(row) <= key_i or not row[key_i]:
            continue
        info = dict(zip(header, row))
        info["key"]  = row[key_i]
        info["name"] = row[name_i] or info["key"]
        for fld in ("tier","cost_c","cost_m","cost_e","time_sec","slots_required"):
            try: info[fld] = int(info.get(fld,0))
            except: info[fld] = 0
        info["prereqs"] = [p.strip() for p in info.get("prereqs","").split(",") if p.strip()]
        defs[info["key"]] = info
    return defs

# ─── Available / Start / Queue / Cancel ────────────────────────────────────
def get_available_builds(user_id: str) -> list[dict]:
    defs = get_build_defs()
    if not defs:
        return []
    try:
        prow = next(r for r in get_rows(PLAYERS_SHEET)[1:] if r[0]==user_id)
        credits, minerals, energy = map(int,(prow[3],prow[4],prow[5]))
    except:
        credits = minerals = energy = 0
    done = {r[1].lower() for r in _get_completed_rows()}
    out = []
    for info in defs.values():
        key = info["key"]
        lvl = get_current_level(user_id,key)
        e = info.copy()
        e["level"]      = lvl
        e["done"]       = key.lower() in done
        e["locked"]     = any(pr.lower() not in done for pr in e["prereqs"])
        e["affordable"] = credits>=e["cost_c"] and minerals>=e["cost_m"] and energy>=e["cost_e"]
        out.append(e)
    return sorted(out, key=lambda x:(x["tier"],x["key"]))

def start_build(user_id: str, key: str) -> bool:
    # deduct resources
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False
    try:
        rows = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header,*pdata = rows
    for idx,row in enumerate(pdata, start=1):
        if row[0]==user_id:
            c,m,e = map(int,(row[3],row[4],row[5]))
            if c<info["cost_c"] or m<info["cost_m"] or e<info["cost_e"]:
                return False
            row[3],row[4],row[5] = str(c-info["cost_c"]), str(m-info["cost_m"]), str(e-info["cost_e"])
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    # queue it
    to_level = get_current_level(user_id,key) + 1
    now = time.time()
    end_ts = now + info["time_sec"]
    append_row(BUILD_QUEUE_SHEET, [user_id, key, str(to_level), str(now), str(end_ts)])
    return True

def get_build_queue(user_id: str) -> list[dict]:
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError:
        return []
    header,*data = rows
    out = []
    for r in data:
        if len(r)>=5 and r[0]==user_id:
            out.append({
                "key":      r[1],
                "to_level": int(r[2]),
                "start_ts": float(r[3]),
                "end_ts":   float(r[4]),
            })
    return out

def cancel_build(user_id: str, key: str) -> bool:
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_build: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return False
    header,*data = rows
    for idx,r in enumerate(data, start=1):
        if len(r)>=2 and r[0]==user_id and r[1]==key:
            update_row(BUILD_QUEUE_SHEET, idx, [""]*len(header))
            return True
    return False

# ─── One-off Completion ──────────────────────────────────────────────────────
def _complete_single_build(context):
    job     = context.job
    user_id = job.data["user_id"]
    key     = job.data["key"]
    chat_id     = job.data.get("chat_id")
    message_id  = job.data.get("message_id")
    try:
        # clear queue & record completion
        rows = get_rows(BUILD_QUEUE_SHEET)
        header,*data = rows
        to_level = None
        for idx,r in enumerate(data, start=1):
            if len(r)>=2 and r[0]==user_id and r[1]==key:
                to_level = int(r[2])
                update_row(BUILD_QUEUE_SHEET, idx, [""]*len(header))
                break
        if to_level is None:
            to_level = get_current_level(user_id,key)
        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, str(to_level), iso])

        # edit original “🌱 Building …” message
        if chat_id and message_id:
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🏗️ Build *{key}* complete! Now at level {to_level}.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # fallback notification
            context.bot.send_message(
                chat_id=user_id,
                text=f"🏗️ Build *{key}* complete! Now at level {to_level}.",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)
