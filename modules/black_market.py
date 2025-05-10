# bot/modules/black_market.py

class BlackMarketItem:
    def __init__(self, name, description, cost, effect):
        self.name = name
        self.description = description
        self.cost = cost
        self.effect = effect
        self.uses = 1  # Most items are use-once

    def apply_effect(self, player_id):
        if self.effect == "revive":
            # Logic to revive all lost units
            units = get_rows("Units")
            for row in units[1:]:
                if row[0] == player_id:
                    unit_name = row[1]
                    count = int(row[2])
                    # Reset unit count to maximum (simplified logic)
                    if unit_name == "infantry":
                        new_count = 50
                    elif unit_name == "tanks":
                        new_count = 30
                    elif unit_name == "artillery":
                        new_count = 20
                    else:
                        new_count = count
                    update_row("Units", units.index(row), [row[0], row[1], str(new_count)])
            return True
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "effect": self.effect,
            "uses": self.uses
        }
