# bot/modules/chaos_events.py

import random
from datetime import datetime, timedelta

class ChaosEvent:
    def __init__(self, name, description, duration, effect):
        self.name = name
        self.description = description
        self.duration = duration  # in hours
        self.effect = effect  # function to apply the effect
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=duration)

    def is_active(self):
        return datetime.now() <= self.end_time

    def apply_effect(self, player_id):
        return self.effect(player_id)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "duration": self.duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }

def create_random_event():
    events = [
        {
            "name": "Resource Boom",
            "description": "All players receive a 50% increase in resource production!",
            "duration": 2,
            "effect": lambda pid: increase_production(pid, 1.5)
        },
        {
            "name": "Unit Recruitment Drive",
            "description": "Unit training costs reduced by 30% for all players!",
            "duration": 1,
            "effect": lambda pid: reduce_unit_costs(pid, 0.7)
        },
        {
            "name": "Energy Crisis",
            "description": "Energy production reduced by 40% for all players!",
            "duration": 3,
            "effect": lambda pid: decrease_energy_production(pid, 0.6)
        }
    ]
    event_data = random.choice(events)
    return ChaosEvent(
        event_data["name"],
        event_data["description"],
        event_data["duration"],
        event_data["effect"]
    )

def increase_production(player_id, multiplier):
    buildings = get_rows("Buildings")
    for idx, row in enumerate(buildings[1:], start=1):
        if row[0] == player_id:
            building_name = row[1]
            current_production = int(row[3])
            new_production = int(current_production * multiplier)
            update_row("Buildings", idx, [row[0], row[1], row[2], str(new_production)])
    return True

def reduce_unit_costs(player_id, multiplier):
    units = get_rows("Units")
    for idx, row in enumerate(units[1:], start=1):
        if row[0] == player_id:
            unit_name = row[1]
            current_count = int(row[2])
            # Simplified logic - actual implementation would adjust costs
            new_count = int(current_count * multiplier)
            update_row("Units", idx, [row[0], row[1], str(new_count)])
    return True

def decrease_energy_production(player_id, multiplier):
    buildings = get_rows("Buildings")
    for idx, row in enumerate(buildings[1:], start=1):
        if row[0] == player_id and row[1] == "Research Lab":
            current_production = int(row[3])
            new_production = int(current_production * multiplier)
            update_row("Buildings", idx, [row[0], row[1], row[2], str(new_production)])
    return True
