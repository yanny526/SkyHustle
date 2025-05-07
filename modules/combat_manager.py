# modules/combat_manager.py
import random
import time
from datetime import datetime
import json

from sheets_service import get_rows, update_row, append_row
from utils.format_utils import section_header

class CombatManager:
    def __init__(self, attacker_id, defender_id, attacker_name, defender_name):
        self.attacker_id = attacker_id
        self.defender_id = defender_id
        self.attacker_name = attacker_name
        self.defender_name = defender_name
        self.weather_effect = self.get_weather_effect()
        self.terrain_bonus = self.get_terrain_bonus(defender_id)
        self.battle_start = time.time()

    def resolve_combat(self):
        # Step 1: Calculate combat power for both sides
        attacker_power, defender_power = self.calculate_combat_power()

        # Step 2: Apply combat modifiers
        attacker_power *= self.weather_effect * self.terrain_bonus
        defender_power *= self.weather_effect

        # Step 3: Determine combat outcome
        if attacker_power > defender_power * 0.9:  # 10% leeway for defender
            outcome = "victory"
            spoils = self.calculate_spoils(defender_id=self.defender_id, is_win=True)
        else:
            outcome = "defeat"
            spoils = self.calculate_spoils(attacker_id=self.attacker_id, is_win=False)

        # Step 4: Calculate unit casualties
        casualties = self.calculate_casualties(attacker_power, defender_power)

        # Step 5: Update game state
        self.update_game_state(outcome, spoils, casualties)

        # Step 6: Generate battle report
        report = self.generate_battle_report(
            attacker_power, defender_power, outcome, spoils, casualties
        )

        return report, outcome, spoils

    def calculate_combat_power(self):
        attacker_power = 0
        defender_power = 0

        # Calculate attacker power from deployed army
        attacker_units = self.get_deployed_units(self.attacker_id)
        for unit, count in attacker_units.items():
            base_power = self.get_unit_power(unit)
            attacker_power += base_power * count

        # Calculate defender power from main army
        defender_units = self.get_main_army(self.defender_id)
        for unit, count in defender_units.items():
            base_power = self.get_unit_power(unit)
            defender_power += base_power * count * 1.2  # Home defense bonus

        return attacker_power, defender_power

    def get_deployed_units(self, player_id):
        deployed_rows = get_rows("DeployedArmy")
        units = {}
        for row in deployed_rows[1:]:
            if row[0] == player_id:
                unit_type = row[2]
                count = int(row[3])
                units[unit_type] = count
        return units

    def get_main_army(self, player_id):
        army_rows = get_rows("Army")
        units = {}
        for row in army_rows[1:]:
            if row[0] == player_id:
                unit_type = row[1]
                count = int(row[2])
                units[unit_type] = count
        return units

    def get_unit_power(self, unit_type):
        unit_power = {
            "infantry": 10,
            "tanks": 30,
            "artillery": 50
        }
        return unit_power.get(unit_type.lower(), 10)

    def get_weather_effect(self):
        weather_types = [
            ("Clear", 1.0),
            ("Fog", 0.9),
            ("Rain", 0.8),
            ("Storm", 0.7),
            ("Sandstorm", 0.6)
        ]
        weather_name, effect = random.choice(weather_types)
        self.current_weather = weather_name
        return effect

    def get_terrain_bonus(self, defender_id):
        terrain_types = {
            "forest": 1.3,
            "mountains": 0.7,
            "plains": 1.0,
            "desert": 1.2,
            "swamps": 0.5
        }
        # Get defender's terrain from player data
        players = get_rows("Players")
        for row in players[1:]:
            if row[0] == defender_id:
                terrain = row[8] if len(row) > 8 else "plains"
                return terrain_types.get(terrain.lower(), 1.0)
        return 1.0

    def calculate_spoils(self, player_id=None, defender_id=None, is_win=True):
        if is_win and defender_id:
            players = get_rows("Players")
            for row in players[1:]:
                if row[0] == defender_id:
                    credits = int(row[3])
                    return max(1, credits // 10)
        elif not is_win and player_id:
            players = get_rows("Players")
            for row in players[1:]:
                if row[0] == player_id:
                    credits = int(row[3])
                    return max(1, credits // 20)
        return 0

    def calculate_casualties(self, attacker_power, defender_power):
        casualties = {}
        all_units = {**self.get_deployed_units(self.attacker_id), **self.get_main_army(self.defender_id)}
        total_power = attacker_power + defender_power

        for unit, count in all_units.items():
            base_power = self.get_unit_power(unit)
            unit_power_contribution = base_power * count
            casualty_rate = (unit_power_contribution / total_power) * 0.3  # 30% max casualties
            casualties[unit] = int(count * casualty_rate)
        return casualties

    def update_game_state(self, outcome, spoils, casualties):
        # Update attacker's credits
        players = get_rows("Players")
        for idx, row in enumerate(players[1:], start=1):
            if row[0] == self.attacker_id:
                current_credits = int(row[3])
                if outcome == "victory":
                    new_credits = current_credits + spoils
                else:
                    new_credits = max(0, current_credits - spoils)
                row[3] = str(new_credits)
                update_row("Players", idx, row)
                break

        # Update defender's credits if applicable
        if outcome == "victory":
            for idx, row in enumerate(players[1:], start=1):
                if row[0] == self.defender_id:
                    current_credits = int(row[3])
                    new_credits = max(0, current_credits - spoils)
                    row[3] = str(new_credits)
                    update_row("Players", idx, row)
                    break

        # Apply casualties
        for unit, lost in casualties.items():
            if lost <= 0:
                continue

            # Reduce from deployed units first
            deployed_rows = get_rows("DeployedArmy")
            for idx, row in enumerate(deployed_rows[1:], start=1):
                if row[0] == self.attacker_id and row[2] == unit:
                    current_count = int(row[3])
                    new_count = max(0, current_count - lost)
                    row[3] = str(new_count)
                    update_row("DeployedArmy", idx, row)
                    lost = max(0, lost - current_count)
                    if lost == 0:
                        break

            # If still casualties, reduce from main army
            if lost > 0:
                army_rows = get_rows("Army")
                for idx, row in enumerate(army_rows[1:], start=1):
                    if row[0] == self.attacker_id and row[1] == unit:
                        current_count = int(row[2])
                        new_count = max(0, current_count - lost)
                        row[2] = str(new_count)
                        update_row("Army", idx, row)
                        break

        # Log combat result
        append_row("CombatLog", [
            self.attacker_id,
            self.defender_id,
            str(int(time.time())),
            outcome,
            str(spoils)
        ])

    def generate_battle_report(self, attacker_power, defender_power, outcome, spoils, casualties):
        lines = []
        lines.append(section_header(f"BATTLE REPORT", "⚔️", color="red"))
        lines.append(f"Attacker: {self.attacker_name}")
        lines.append(f"Defender: {self.defender_name}")
        lines.append(f"Result: {outcome.upper()}")
        lines.append(f"Weather: {self.current_weather} (Effect: {self.weather_effect:.1f}x)")
        lines.append(f"Terrain Bonus: {self.terrain_bonus:.1f}x")
        lines.append("")
        lines.append(section_header("COMBAT STATS", "📊", color="gold"))
        lines.append(f"Attacker Power: {attacker_power:.0f}")
        lines.append(f"Defender Power: {defender_power:.0f}")
        lines.append(f"Spoils of War: {'+' if outcome == 'victory' else '-'}{spoils} Credits")
        lines.append("")
        lines.append(section_header("CASUALTIES", "💀", color="brown"))
        
        for unit, lost in casualties.items():
            if lost > 0:
                emoji = "👨‍✈️" if unit == "infantry" else "🛡️" if unit == "tanks" else "🚀"
                lines.append(f"{emoji} {unit.capitalize()}: {lost} lost")

        return "\n".join(lines)
