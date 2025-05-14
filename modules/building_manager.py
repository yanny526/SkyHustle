import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row
from config import BUILDING_MAX_LEVEL

logger = logging.getLogger(__name__)

# ─── Sheet names ─────────────────────────────────────────────────────────────
BUILDING_DEFS_SHEET = "BuildingDefs"   # master definitions tab
USER_BUILD_SHEET    = "Buildings"      # per-user table: user_id, building_type, level, upgrade_end_ts
BUILD_QUEUE_SHEET   = "BuildQueue"
BUILD_DONE_SHEET    = "CompletedBuilds"
PLAYERS_SHEET       = "Players"

# ─── Production-per-level config ─────────────────────────────────────────────
PRODUCTION_PER_LEVEL = {
    "Bank":       ("credits", 10),
    "Mine":       ("minerals", 5),
    "PowerPlant": ("energy", 3),
    # add other resource buildings as needed
}

# ─── Definitions Loader ───────────────────────────────────────────────────────

def get_build_defs() -> dict:
    """
    Load building definitions from BUILDING_DEFS_SHEET.
    Expects columns: key, name, tier, cost_c, cost_m, cost_e, time_sec, prereqs.
    Returns a dict mapping key -> info dict.
    """
    try:
        rows = get_rows(BUILDING_DEFS_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILDING_DEFS_SHEET, e)
        return {}

    if len(rows) < 2:
        return {}

    header = rows[0]
    # locate required columns
    key_idx  = header.index("key")
    name_idx = header.index("name")

    defs = {}
    for row in rows[1:]:
        if len(row) <= key_idx or not row[key_idx]:
            continue
        info = dict(zip(header, row))
        key  = row[key_idx]
        name = row[name_idx] or key
        info["key"]  = key
        info["name"] = name

        # parse numeric fields
        for fld in ("tier", "cost_c", "cost_m", "cost_e", "time_sec", "slots_required"):
            try:
                info[fld] = int(info.get(fld, 0))
            except:
                info[fld] = 0

        # prerequisites
        info["prereqs"] = [
            p.strip() for p in info.get("prereqs", "").split(",") if p.strip()
        ]

        defs[key] = info

    return defs

# ─── Available / Start / Queue / Cancel ──────────────────────────────────────

def get_available_builds(user_id: str) -> list[dict]:
    """
    Return a list of all building definitions, annotated with:
      - level (from USER_BUILD_SHEET)
      - done, locked, affordable flags
    """
    defs = get_build_defs()
    if not defs:
        return []

    # load user levels
    try:
        user_rows = get_rows(USER_BUILD_SHEET)
    except HttpError as e:
        logger.error("get_available_builds: cannot read %s: %s", USER_BUILD_SHEET, e)
        return []
    user_levels = {
        r[1]: int(r[2] or 0)
        for r in user_rows[1:]
        if r[0] == user_id
    }

    # load resources
    try:
        rows = get_rows(PLAYERS_SHEET)
        header, *data = rows
        row = next(r for r in data if r[0] == user_id)
        credits, minerals, energy = map(int, (row[3], row[4], row[5]))
    except:
        credits = minerals = energy = 0

    # completed builds
    try:
        done = [r[1] for r in get_rows(BUILD_DONE_SHEET)[1:]]
    except:
        done = []

    out = []
    for info in defs.values():
        key  = info["key"]
        lvl  = user_levels.get(key, 0)
        entry = info.copy()
        entry["level"]      = lvl
        entry["done"]       = key in done
        entry["locked"]     = any(pr not in done for pr in entry["prereqs"])
        entry["affordable"] = (
            credits >= entry["cost_c"]
            and minerals >= entry["cost_m"]
            and energy >= entry["cost_e"]
        )
        out.append(entry)

    return sorted(out, key=lambda x: (x["tier"], x["key"]))

def start_build(user_id: str, key: str) -> bool:
    """
    Deduct resources & queue a build.
    """
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False

    try:
        rows = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header, *data = rows

    # deduct
    for idx, row in enumerate(data, start=1):
        if row[0] == user_id:
            c, m, e = map(int, (row[3], row[4], row[5]))
            if c < info["cost_c"] or m < info["cost_m"] or e < info["cost_e"]:
                return False
            row[3], row[4], row[5] = (
                str(c - info["cost_c"]),
                str(m - info["cost_m"]),
                str(e - info["cost_e"])
            )
            update_row(PLAYERS_SHEET, idx, row)
            break
    else:
        return False

    # queue
    now = time.time()
    append_row(
        BUILD_QUEUE_SHEET,
        [user_id, key, str(now), str(now + info["time_sec"])]
    )
    return True

def get_build_queue(user_id: str) -> list[dict]:
    """
    Return pending builds from BUILD_QUEUE_SHEET.
    """
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError:
        return []
    header, *data = rows

    out = []
    for r in data:
        if len(r) >= 4 and r[0] == user_id:
            out.append({
                "key":      r[1],
                "start_ts": float(r[2]),
                "end_ts":   float(r[3]),
            })
    return out

def cancel_build(user_id: str, key: str) -> bool:
    """
    Cancel a pending build.
    """
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("cancel_build: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return False
    header, *data = rows

    for idx, r in enumerate(data, start=1):
        if len(r) >= 2 and r[0] == user_id and r[1] == key:
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
            return True
    return False

# ─── Batch Completion Job (async) ────────────────────────────────────────────

async def complete_build_job(context):
    """
    Runs every minute to clear finished builds in batch.
    """
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("complete_build_job: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header, *data = rows

    for idx, r in enumerate(data, start=1):
        try:
            end_ts = float(r[3])
        except:
            continue
        if end_ts <= now:
            user_id, key = r[0], r[1]
            iso = datetime.utcnow().isoformat()
            append_row(BUILD_DONE_SHEET, [user_id, key, iso])
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))

# ─── Single-build completion & Crash-resilience ────────────────────────────

def _complete_single_build(context):
    job     = context.job
    user_id = job.data["user_id"]
    key     = job.data["key"]
    try:
        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, iso])

        rows = get_rows(BUILD_QUEUE_SHEET)
        header, *data = rows
        for idx, r in enumerate(data, start=1):
            if len(r) >= 2 and r[0] == user_id and r[1] == key:
                update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
                break

        context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ Your build *{key}* is now complete!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)

def load_pending_builds(app):
    """
    On startup, schedule any pending builds that survived a crash.
    """
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("load_pending_builds: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header, *data = rows

    for r in data:
        if len(r) < 4:
            continue
        user_id, key = r[0], r[1]
        try:
            end_ts = float(r[3])
        except:
            continue
        delay = end_ts - now
        if delay <= 0:
            app.job_queue.run_once(_complete_single_build, 0,
                                   data={"user_id": user_id, "key": key})
        else:
            app.job_queue.run_once(_complete_single_build, delay,
                                   data={"user_id": user_id, "key": key})

# ─── Status-helper exports ───────────────────────────────────────────────────

def get_building_info(user_id: str) -> dict:
    rows = get_rows(PLAYERS_SHEET)
    if not rows or len(rows) < 2:
        return {}
    header = rows[0]
    for row in rows[1:]:
        if row[0] == user_id:
            info = {}
            for bld in BUILDING_MAX_LEVEL:
                if bld in header:
                    idx = header.index(bld)
                    try:
                        info[bld] = int(row[idx] or 0)
                    except:
                        info[bld] = 0
            return info
    return {}

def get_production_rates(build_info: dict) -> dict:
    rates = {"credits": 0, "minerals": 0, "energy": 0}
    for bld, lvl in build_info.items():
        prod = PRODUCTION_PER_LEVEL.get(bld)
        if prod:
            resource, per = prod
            rates[resource] += per * lvl
    return rates

def get_building_health(user_id: str) -> dict:
    info = get_building_info(user_id)
    health = {}
    for bld, lvl in info.items():
        max_hp = lvl * 100
        health[bld] = {"current": max_hp, "max": max_hp}
    return health
