# bot/modules/unit_evolution.py

class UnitEvolution:
    def __init__(self, name, description, requirements, effect):
        self.name = name
        self.description = description
        self.requirements = requirements  # e.g., {"credits": 500, "minerals": 200}
        self.effect = effect  # Function to apply the evolution effect
        self.unlocked = False

    def can_evolve(self, player_id):
        # Check if the player meets the requirements
        player_data = load_player_data(player_id)
        for resource, amount in self.requirements.items():
            if resource == 'credits' and player_data.get('credits', 0) < amount:
                return False
            if resource == 'minerals' and player_data.get('minerals', 0) < amount:
                return False
            if resource == 'skybucks' and player_data.get('skybucks', 0) < amount:
                return False
        return True

    def apply_effect(self, player_id):
        # Apply the evolution effect (this is a placeholder for actual game logic)
        player_data = load_player_data(player_id)
        # Example effect: increase unit power
        units = get_rows("Units")
        for idx, row in enumerate(units[1:], start=1):
            if row[0] == player_id and row[1].lower() == self.name.split()[0].lower():
                current_power = int(row[3])
                new_power = current_power * 1.5  # Example power boost
                row[3] = str(new_power)
                update_row("Units", idx, row)
                return True
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "requirements": self.requirements,
            "unlocked": self.unlocked
        }
