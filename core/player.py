# core/player.py
import json

class Player:
    def __init__(self, chat_id, name="", ore=0, energy=100, credits=100, army=None,
                 zone="", shield_until=None, daily_streak=0, last_daily="",
                 black_market_unlocked=False, items=None, missions=None,
                 last_mission_reset="", wins=0, losses=0, banner="",
                 refinery_level=0, lab_level=0, defense_level=0, research=None,
                 faction=None):
        self.chat_id = chat_id
        self.name = name
        self.ore = ore
        self.energy = energy
        self.credits = credits
        self.army = army if army is not None else {"scout": 0, "tank": 0, "drone": 0}
        self.zone = zone
        self.shield_until = shield_until
        self.daily_streak = daily_streak
        self.last_daily = last_daily
        self.black_market_unlocked = black_market_unlocked
        self.items = items if items is not None else []
        self.missions = missions if missions is not None else {}
        self.last_mission_reset = last_mission_reset
        self.wins = wins
        self.losses = losses
        self.banner = banner
        self.refinery_level = refinery_level
        self.lab_level = lab_level
        self.defense_level = defense_level
        self.research = research if research is not None else {"speed": 0, "armor": 0}
        self.faction = faction

    def to_dict(self):
        """Converts the Player object to a dictionary for storage."""
        return {
            "ChatID": self.chat_id,
            "Name": self.name,
            "Ore": self.ore,
            "Energy": self.energy,
            "Credits": self.credits,
            "Army": json.dumps(self.army),
            "Zone": self.zone,
            "ShieldUntil": self.shield_until,
            "DailyStreak": self.daily_streak,
            "LastDaily": self.last_daily,
            "BlackMarketUnlocked": self.black_market_unlocked,
            "Items": json.dumps(self.items),
            "Missions": json.dumps(self.missions),
            "LastMissionReset": self.last_mission_reset,
            "Wins": self.wins,
            "Losses": self.losses,
            "Banner": self.banner,
            "RefineryLevel": self.refinery_level,
            "LabLevel": self.lab_level,
            "DefenseLevel": self.defense_level,
            "Research": json.dumps(self.research),
            "Faction": self.faction,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Player object from a dictionary (retrieved from storage)."""
        #  Handle potential JSONDecodeErrors
        try:
            army = json.loads(data.get("Army", '{"scout": 0, "tank": 0, "drone": 0}'))
        except (json.JSONDecodeError, TypeError):
            army = {"scout": 0, "tank": 0, "drone": 0}

        try:
            items = json.loads(data.get("Items", "[]"))
        except (json.JSONDecodeError, TypeError):
            items = []

        try:
            missions = json.loads(data.get("Missions", "{}"))
        except (json.JSONDecodeError, TypeError):
            missions = {}

        try:
            research = json.loads(data.get("Research", "{}"))
        except (json.JSONDecodeError, TypeError):
            research = {}

        return cls(
            chat_id=int(data.get("ChatID", 0)),  # Provide default value
            name=data.get("Name", ""),
            ore=int(data.get("Ore", 0)),
            energy=int(data.get("Energy", 100)),
            credits=int(data.get("Credits", 100)),
            army=army,
            zone=data.get("Zone", ""),
            shield_until=data.get("ShieldUntil", None),
            daily_streak=int(data.get("DailyStreak", 0)),
            last_daily=data.get("LastDaily", ""),
            black_market_unlocked=bool(data.get("BlackMarketUnlocked", False)),
            items=items,
            missions=missions,
            last_mission_reset=data.get("LastMissionReset", ""),
            wins=int(data.get("Wins", 0)),
            losses=int(data.get("Losses", 0)),
            banner=data.get("Banner", ""),
            refinery_level=int(data.get("RefineryLevel", 0)),
            lab_level=int(data.get("LabLevel", 0)),
            defense_level=int(data.get("DefenseLevel", 0)),
            research=research,
            faction=data.get("Faction", None)
        )
