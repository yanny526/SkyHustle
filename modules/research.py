"""
modules/research.py

Defines ResearchItem class and all available research items.
"""

from typing import Callable, List

class ResearchItem:
    def __init__(
        self,
        name: str,
        description: str,
        prerequisites: List['ResearchItem'],
        costs: dict,
        action: Callable[[str], str]
    ):
        self.name = name
        self.description = description
        self.prerequisites = prerequisites
        self.costs = costs
        self.action = action

# === Research effect functions ===

def infantry_research(player_id: str) -> str:
    # TODO: insert real logic for applying advanced infantry research
    return "Advanced Infantry research completed."

def energy_efficiency(player_id: str) -> str:
    # TODO: insert real logic for applying energy efficiency research
    return "Energy Efficiency research completed."

# === Research items registry ===

research_items: dict[str, ResearchItem] = {}

# 1) Advanced Infantry
research_items['advanced_infantry'] = ResearchItem(
    name='Advanced Infantry',
    description='Unlock advanced infantry units.',
    prerequisites=[],
    costs={'credits': 500, 'minerals': 200},
    action=infantry_research
)

# 2) Energy Efficiency
research_items['energy_efficiency'] = ResearchItem(
    name='Energy Efficiency',
    description='Improve energy production efficiency.',
    prerequisites=[],
    costs={'credits': 800, 'minerals': 300},
    action=energy_efficiency
)

# 3) Quantum Shielding (requires advanced infantry)
research_items['quantum_shielding'] = ResearchItem(
    name='Quantum Shielding',
    description='Develop advanced shielding technology for units.',
    prerequisites=[research_items['advanced_infantry']],
    costs={'credits': 1200, 'minerals': 500, 'skybucks': 100},
    action=lambda pid: 'Quantum Shielding research completed.'
)
