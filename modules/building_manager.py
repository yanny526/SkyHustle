import logging
import time
from datetime import datetime
from googleapiclient.errors import HttpError
from sheets_service import get_rows, append_row, update_row

logger = logging.getLogger(__name__)

# ─── Sheet names ─────────────────────────────────────────────────────────────
BUILDING_DEFS_SHEET = "BuildingDefs"
BUILD_QUEUE_SHEET   = "BuildQueue"       # cols: user_id, building, to_level, start_ts, end_ts
BUILD_DONE_SHEET    = "CompletedBuilds"  # cols: user_id, building, level, completed_ts
PLAYERS_SHEET       = "Players"

# ─── Production-per-level config ─────────────────────────────────────────────
PRODUCTION_PER_LEVEL = {
    "Bank":       ("credits",   10),
    "Mine":       ("minerals",   5),
    "PowerPlant": ("energy",     3),
    # …add any others here…
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_completed_rows() -> list[list[str]]:
    """All data rows from CompletedBuilds (skip header)."""
    try:
        return get_rows(BUILD_DONE_SHEET)[1:]
    except HttpError as e:
        logger.error("Cannot read %s: %s", BUILD_DONE_SHEET, e)
        return []

def get_current_level(user_id: str, key: str) -> int:
    """
    Current level = count of CompletedBuilds rows for (user_id, key).
    """
    return sum(1 for r in _get_completed_rows() if r[0] == user_id and r[1] == key)

# ─── Load Definitions ─────────────────────────────────────────────────────────

def get_build_defs() -> dict[str, dict]:
    """
    Load master definitions from the BuildingDefs sheet.
    Returns a dict keyed by build-key → info dict.
    """
    try:
        rows = get_rows(BUILDING_DEFS_SHEET)
    except HttpError as e:
        logger.error("get_build_defs: cannot read %s: %s", BUILDING_DEFS_SHEET, e)
        return {}
    if len(rows) < 2:
        return {}

    header   = rows[0]
    key_i    = header.index("key")
    name_i   = header.index("name")
    defs:dict[str,dict] = {}

    for row in rows[1:]:
        if len(row) <= key_i or not row[key_i]:
            continue
        info = dict(zip(header, row))
        key  = row[key_i]
        info["key"]  = key
        info["name"] = row[name_i] or key
        # parse numeric fields
        for fld in ("tier","cost_c","cost_m","cost_e","time_sec","slots_required"):
            try: info[fld] = int(info.get(fld, 0))
            except: info[fld] = 0
        # prerequisites
        info["prereqs"] = [
            p.strip() for p in info.get("prereqs","").split(",") if p.strip()
        ]
        defs[key] = info

    return defs

# ─── Available Builds ────────────────────────────────────────────────────────

def get_available_builds(user_id: str) -> list[dict]:
    defs = get_build_defs()
    if not defs:
        return []

    # load player resources
    try:
        prow = next(r for r in get_rows(PLAYERS_SHEET)[1:] if r[0] == user_id)
        credits, minerals, energy = map(int, (prow[3], prow[4], prow[5]))
    except:
        credits = minerals = energy = 0

    done_keys = {r[1] for r in _get_completed_rows()}
    out: list[dict] = []

    for info in defs.values():
        key = info["key"]
        lvl = get_current_level(user_id, key)

        e = info.copy()
        e["level"]      = lvl
        e["done"]       = key in done_keys
        e["locked"]     = any(pr not in done_keys for pr in e["prereqs"])
        e["affordable"] = (
            credits  >= e["cost_c"] and
            minerals >= e["cost_m"] and
            energy   >= e["cost_e"]
        )
        out.append(e)

    return sorted(out, key=lambda x: (x["tier"], x["key"]))

# ─── Queue Management ────────────────────────────────────────────────────────

def start_build(user_id: str, key: str) -> bool:
    """
    Deduct resources & append a build-job row:
      [user_id, key, to_level, start_ts, end_ts]
    """
    defs = get_build_defs()
    info = defs.get(key)
    if not info:
        return False

    # 1) Deduct from Players
    try:
        rows = get_rows(PLAYERS_SHEET)
    except HttpError:
        return False
    header, *pdata = rows
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

    # 2) Compute next level & timings
    to_level = get_current_level(user_id, key) + 1
    now      = time.time()
    end_ts   = now + info["time_sec"]

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

# ─── Completion Jobs ─────────────────────────────────────────────────────────

async def complete_build_job(context):
    """
    Runs every minute; sweeps BuildQueue for finished jobs,
    records them in CompletedBuilds, clears the queue row,
    and sends the user a completion notice.
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
            end_ts = float(r[4])
        except:
            continue
        if end_ts <= now:
            user_id, key, lvl_str = r[0], r[1], r[2]
            lvl = int(lvl_str)
            iso = datetime.utcnow().isoformat()

            append_row(BUILD_DONE_SHEET, [user_id, key, str(lvl), iso])
            update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))

            # notify user
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🏗️ Build *{key}* complete! Now at level {lvl}.",
                parse_mode="Markdown"
            )

def _complete_single_build(context):
    """
    One-off build completion (if you schedule per‐build jobs).
    Clears its queue row, logs to CompletedBuilds, and notifies.
    """
    job     = context.job
    user_id = job.data["user_id"]
    key     = job.data["key"]
    try:
        rows = get_rows(BUILD_QUEUE_SHEET)
        header, *data = rows
        to_level = None
        for idx, r in enumerate(data, start=1):
            if len(r) >= 2 and r[0] == user_id and r[1] == key:
                to_level = int(r[2])
                update_row(BUILD_QUEUE_SHEET, idx, [""] * len(header))
                break
        if to_level is None:
            to_level = get_current_level(user_id, key)

        iso = datetime.utcnow().isoformat()
        append_row(BUILD_DONE_SHEET, [user_id, key, str(to_level), iso])

        context.bot.send_message(
            chat_id=user_id,
            text=f"🏗️ Build *{key}* complete! Now at level {to_level}.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Error in _complete_single_build for %s/%s: %s", user_id, key, e)

def load_pending_builds(app):
    """
    On bot startup: re-schedule any in‐flight builds you crashed on.
    """
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
        user_id, key, lvl_str, _, end_ts = r
        try:
            end = float(end_ts)
        except:
            continue
        delay = end - now
        if delay <= 0:
            app.job_queue.run_once(_complete_single_build, 0,
                                   data={"user_id": user_id, "key": key})
        else:
            app.job_queue.run_once(_complete_single_build, delay,
                                   data={"user_id": user_id, "key": key})

# ─── Status Helpers ─────────────────────────────────────────────────────────

def get_building_info(user_id: str) -> dict[str, int]:
    """
    Returns a map {building_key: current_level}.
    """
    return {
        key: get_current_level(user_id, key)
        for key in get_build_defs().keys()
    }

def get_production_rates(build_info: dict[str, int]) -> dict[str, int]:
    rates = {"credits": 0, "minerals": 0, "energy": 0}
    for bld, lvl in build_info.items():
        prod = PRODUCTION_PER_LEVEL.get(bld)
        if prod:
            res, per = prod
            rates[res] += per * lvl
    return rates

def get_building_health(user_id: str) -> dict[str, dict]:
    info = get_building_info(user_id)
    return { bld: {"current": lvl * 100, "max": lvl * 100}
             for bld, lvl in info.items() }
