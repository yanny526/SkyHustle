import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row
from config import BUILDING_MAX_LEVEL

logger = logging.getLogger(__name__)

# ─── Sheet names ─────────────────────────────────────────────────────────────
BUILDING_DEFS_SHEET = "BuildingDefs"   # master definitions
USER_BUILD_SHEET    = "Buildings"      # per-user table: user_id, building, level, ...
BUILD_QUEUE_SHEET   = "BuildQueue"     # now with columns user_id, building, to_level, start_ts, end_ts
BUILD_DONE_SHEET    = "CompletedBuilds"
PLAYERS_SHEET       = "Players"

# ─── Production-per-level config ─────────────────────────────────────────────
PRODUCTION_PER_LEVEL = {
    "Bank":       ("credits", 10),
    "Mine":       ("minerals", 5),
    "PowerPlant": ("energy", 3),
    # extend as needed...
}

# ─── Definitions Loader ───────────────────────────────────────────────────────

def get_build_defs() -> dict:
    try:
        rows = get_rows(BUILDING_DEFS_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILDING_DEFS_SHEET, e)
        return {}
    if len(rows) < 2:
        return {}
    header = rows[0]
    key_idx  = header.index("key")
    name_idx = header.index("name")
    defs = {}
    for row in rows[1:]:
        if len(row) <= key_idx or not row[key_idx]:
            continue
        info = dict(zip(header, row))
        key = row[key_idx]
        info["key"]  = key
        info["name"] = row[name_idx] or key
        # parse numeric fields
        for fld in ("tier", "cost_c", "cost_m", "cost_e", "time_sec", "slots_required"):
            try: info[fld] = int(info.get(fld, 0))
            except: info[fld] = 0
        # prerequisites list
        info["prereqs"] = [p.strip() for p in info.get("prereqs", "").split(",") if p.strip()]
        defs[key] = info
    return defs

# ─── Available / Start / Queue / Cancel ──────────────────────────────────────

def get_available_builds(user_id: str) -> list[dict]:
    defs = get_build_defs()
    if not defs:
        return []

    # load the user's current levels from USER_BUILD_SHEET
    try:
        rows = get_rows(USER_BUILD_SHEET)
    except HttpError as e:
        logger.error("get_available_builds: cannot read %s: %s", USER_BUILD_SHEET, e)
        return []
    header, *data = rows
    bld_idx = header.index("building")
    lvl_idx = header.index("level")
    user_levels = {
        r[bld_idx]: int(r[lvl_idx] or 0)
        for r in data if r[0] == user_id
    }

    # load player resources
    try:
        prow = next(r for r in get_rows(PLAYERS_SHEET)[1:] if r[0] == user_id)
        credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))
    except:
        credits = minerals = energy = 0

    # already completed builds
    try:
        done = [r[1] for r in get_rows(BUILD_DONE_SHEET)[1:]]
    except:
        done = []

    out = []
    for info in defs.values():
        key = info["key"]
        lvl = user_levels.get(key, 0)
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
    Deduct resources & append a row to BuildQueue with:
      user_id, building key, to_level, start_ts, end_ts
    """
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False

    # 1) Deduct resources in Players sheet
    try:
        prow_rows = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header, *pdata = prow_rows
    for idx, row in enumerate(pdata, start=1):
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

    # 2) Compute to_level by reading current from USER_BUILD_SHEET
    try:
        urows = get_rows(USER_BUILD_SHEET)
        uheader, *udata = urows
        bld_idx = uheader.index("building")
        lvl_idx = uheader.index("level")
        curr_lvl = 0
        for uidx, urow in enumerate(udata, start=1):
            if urow[0] == user_id and urow[bld_idx] == key:
                try: curr_lvl = int(urow[lvl_idx] or 0)
                except: curr_lvl = 0
                break
    except HttpError:
        curr_lvl = 0

    to_level = curr_lvl + 1
    now = time.time()
    end_ts = now + info["time_sec"]

    # 3) Append into BuildQueue: user_id, key, to_level, start_ts, end_ts
    append_row(
        BUILD_QUEUE_SHEET,
        [user_id, key, str(to_level), str(now), str(end_ts)]
    )
    return True


def get_build_queue(user_id: str) -> list[dict]:
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError:
        return []
    header, *data = rows

    out = []
    for r in data:
        if len(r) >= 5 and r[0] == user_id:
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
    header, *data = rows
    for idx, r in enumerate(data, start=1):
        if len(r) >= 2 and r[0] == user_id and r[1] == key:
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
            return True
    return False

# ─── Batch Completion Job ────────────────────────────────────────────────────

async def complete_build_job(context):
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("complete_build_job: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header, *data = rows

    for idx, r in enumerate(data, start=1):
        try:
            end_ts = float(r[4])
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
        # 1) mark complete
        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, iso])

        # 2) clear BuildQueue row
        rows = get_rows(BUILD_QUEUE_SHEET)
        header, *data = rows
        for idx, r in enumerate(data, start=1):
            if len(r) >= 2 and r[0] == user_id and r[1] == key:
                update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
                break

        # 3) bump level in USER_BUILD_SHEET
        urows = get_rows(USER_BUILD_SHEET)
        uheader, *udata = urows
        bld_idx = uheader.index("building")
        lvl_idx = uheader.index("level")
        # find and update
        for uidx, urow in enumerate(udata, start=1):
            if urow[0] == user_id and urow[bld_idx] == key:
                try:
                    cur = int(urow[lvl_idx] or 0)
                except:
                    cur = 0
                urow[lvl_idx] = str(cur + 1)
                # clear any timestamp column if present
                for j, col in enumerate(uheader):
                    if col in ("start_ts", "end_ts", "upgrade_end_ts", "completed_ts"):
                        urow[j] = ""
                update_row(USER_BUILD_SHEET, uidx, urow)
                break

        # 4) notify
        context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ Build *{key}* complete! Level is now {cur+1}.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)


def load_pending_builds(app):
    now = time.time()
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
    except HttpError as e:
        logger.error("load_pending_builds: cannot read %s: %s", BUILD_QUEUE_SHEET, e)
        return
    header, *data = rows
    for r in data:
        if len(r) < 5:
            continue
        user_id, key = r[0], r[1]
        try:
            end_ts = float(r[4])
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
                    try: info[bld] = int(row[idx] or 0)
                    except: info[bld] = 0
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
