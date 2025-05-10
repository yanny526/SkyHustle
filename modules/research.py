# bot/modules/research.py

class ResearchItem:
    def __init__(self, name, description, prerequisites, cost, effect):
        self.name = name
        self.description = description
        self.prerequisites = prerequisites  # List of research items that must be completed first
        self.cost = cost  # {'credits': 100, 'minerals': 50}
        self.effect = effect  # Function to apply the effect
        self.unlocked = False

    def is_unavailable(self, player_id):
        # Check if prerequisites are met
        for prereq in self.prerequisites:
            if not prereq.unlocked:
                return True
        return False

    def apply_effect(self, player_id):
        # Apply the research effect
        return self.effect(player_id)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "prerequisites": [prereq.name for prereq in self.prerequisites],
            "cost": self.cost,
            "unlocked": self.unlocked
        }

def advanced_infantry(player_id):
    # Update infantry power
    units = get_rows("Units")
    for idx, row in enumerate(units[1:], start=1):
        if row[0] == player_id and row[1] == "infantry":
            current_power = int(row[3])
            new_power = current_power * 1.3
            row[3] = str(new_power)
            update_row("Units", idx, row)
            return f"Infantry power increased by 30%!"
    return "Infantry not found."

def energy_efficiency(player_id):
    # Update energy production
    buildings = get_rows("Buildings")
    for idx, row in enumerate(buildings[1:], start=1):
        if row[0] == player_id and row[1] == "Research Lab":
            current_production = int(row[3])
            new_production = current_production * 1.2
            row[3] = str(new_production)
            update_row("Buildings", idx, row)
            return f"Research Lab energy production increased by 20%!"
    return "Research Lab not found."

# Define research items
research_items = {}

# Initialize research items
research_items['advanced_infantry'] = ResearchItem(
    'Advanced Infantry',
    'Unlock advanced infantry units',
    [],
    {'credits': 500, 'minerals': 200},
    advanced_infantry
)

research_items['energy_efficiency'] = ResearchItem(
    'Energy Efficiency',
    'Improve energy production efficiency',
    [],
    {'credits': 800, 'minerals': 300},
    energy_efficiency
)

research_items['quantum_shielding'] = ResearchItem(
    'Quantum Shielding',
    'Develop advanced shielding technology for units',
    [research_items['advanced_infantry']],
    {'credits': 1200, 'minerals': 500, 'skybucks': 100},
    lambda pid: 'Shielding technology unlocked!'
)
