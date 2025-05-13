# modules/chaos_engine.py

import random
import logging
from datetime import datetime, timedelta

from sheets_service import get_rows, append_row, update_row
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class ChaosEngine:
    LOG_SHEET = "ChaosLog"
    LOG_HEADER = ["storm_id", "timestamp"]
    PLAYER_SHEET = "Players"

    # Define your storms in one place
    STORMS = [
        {
            "id": "ember_rain",
            "name": "Ember Rain",
            "emoji": "🌋",
            "story": (
                "Dark ember rain scorches your mineral caches,\n"
                "burning away 100 Minerals from every commander."
            ),
            "delta": {"minerals": -100},
        },
        {
            "id": "silver_gale",
            "name": "Silver Gale",
            "emoji": "🍃",
            "story": (
                "A refreshing silver gale revitalizes everyone’s energy,\n"
                "granting +150 Energy to all."
            ),
            "delta": {"energy": 150},
        },
        {
            "id": "ruinsquake",
            "name": "Ruinsquake",
            "emoji": "🏚️",
            "story": (
                "Tremors shake your base foundations,\n"
                "costing 100 Credits from each commander."
            ),
            "delta": {"credits": -100},
        },
        {
            "id": "golden_sunrise",
            "name": "Golden Sunrise",
            "emoji": "🌅",
            "story": (
                "A golden sunrise bathes the land,\n"
                "bestowing +200 Minerals to every commander."
            ),
            "delta": {"minerals": 200},
        },
        {
            "id": "voidstorm",
            "name": "Voidstorm",
            "emoji": "🌀",
            "story": (
                "An unnatural voidstorm rips through,\n"
                "siphoning 50 Energy and 50 Credits from all."
            ),
            "delta": {"energy": -50, "credits": -50},
        },
    ]

    def __init__(self, cooldown_days: int = 7):
        self.cooldown = timedelta(days=cooldown_days)
        self._ensure_log_sheet()

    def _ensure_log_sheet(self):
        try:
            rows = get_rows(self.LOG_SHEET)
        except HttpError as e:
            logger.warning("ChaosEngine: cannot read log sheet: %s", e)
            rows = []
        if not rows or rows[0] != self.LOG_HEADER:
            try:
                append_row(self.LOG_SHEET, self.LOG_HEADER)
            except HttpError as e:
                logger.error("ChaosEngine: cannot initialize log sheet: %s", e)

    def _last_storm_time(self) -> datetime | None:
        try:
            rows = get_rows(self.LOG_SHEET)[1:]
        except HttpError as e:
            logger.warning("ChaosEngine: cannot fetch log rows: %s", e)
            return None
        if not rows:
            return None
        ts = rows[-1][1]
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            logger.error("ChaosEngine: bad timestamp in log: %s", ts)
            return None

    def can_trigger(self) -> bool:
        last = self._last_storm_time()
        if not last:
            return True
        return datetime.utcnow() - last >= self.cooldown

    def record_storm(self, storm_id: str):
        now = datetime.utcnow().isoformat()
        try:
            append_row(self.LOG_SHEET, [storm_id, now])
        except HttpError as e:
            logger.error("ChaosEngine: failed to record storm: %s", e)

    def get_random_storm(self) -> dict:
        return random.choice(self.STORMS)

    def apply_storm(self, storm: dict):
        try:
            rows = get_rows(self.PLAYER_SHEET)
        except HttpError as e:
            logger.error("ChaosEngine: cannot read Players sheet: %s", e)
            return

        header, *players = rows
        for idx, row in enumerate(players, start=1):
            try:
                credits = int(row[3])
                minerals = int(row[4])
                energy = int(row[5])
            except (IndexError, ValueError) as ex:
                logger.warning("ChaosEngine: skipping bad row %s: %s", row, ex)
                continue

            delta = storm["delta"]
            credits = max(0, credits + delta.get("credits", 0))
            minerals = max(0, minerals + delta.get("minerals", 0))
            energy = max(0, energy + delta.get("energy", 0))

            row[3], row[4], row[5] = str(credits), str(minerals), str(energy)
            try:
                update_row(self.PLAYER_SHEET, idx, row)
            except HttpError as ex:
                logger.error("ChaosEngine: failed to update row %d: %s", idx, ex)

    def trigger_storm(self) -> dict | None:
        """
        If cooldown has passed, pick & apply a storm, record it, and return it.
        Otherwise returns None.
        """
        if not self.can_trigger():
            return None

        storm = self.get_random_storm()
        self.apply_storm(storm)
        self.record_storm(storm["id"])
        return storm


# Singleton instance you can import elsewhere
engine = ChaosEngine()
