class ResourceManager:
    """
    Handles the core logic for resource management.
    """
    def __init__(self, config):
        self.config = config

    def calculate_resource_production(self, player_data):
        """Calculates resource production based on building levels."""
        lumberhouse_level = player_data["Lumberhouse Level"]
        mine_level = player_data["Mine Level"]
        warehouse_level = player_data["Warehouse Level"]

        base_lumberhouse_production = self.config.get_base_lumberhouse_production()
        base_mine_stone_production = self.config.get_base_mine_stone_production()
        base_mine_gold_production = self.config.get_base_mine_gold_production()
        base_warehouse_capacity = self.config.get_base_warehouse_capacity()

        lumberhouse_production = base_lumberhouse_production * (1 + lumberhouse_level * self.config.get_lumberhouse_production_multiplier())
        mine_stone_production = base_mine_stone_production * (1 + mine_level * self.config.get_mine_stone_production_multiplier())
        mine_gold_production = base_mine_gold_production * (1 + mine_level * self.config.get_mine_gold_production_multiplier())
        warehouse_capacity = base_warehouse_capacity * (1 + warehouse_level * self.config.get_warehouse_capacity_multiplier())

        lumberhouse_production = max(0, lumberhouse_production)
        mine_stone_production = max(0, mine_stone_production)
        mine_gold_production = max(0, mine_gold_production)
        warehouse_capacity = max(0, warehouse_capacity)
        return {
            "Lumberhouse Production": lumberhouse_production,
            "Mine Stone Production": mine_stone_production,
            "Mine Gold Production": mine_gold_production,
            "Warehouse Capacity": warehouse_capacity,
        }

    def update_resources_per_turn(self, sheets, resources_sheet, player_id):
        """Updates a player's resources based on production rates."""
        player_data = sheets.get_player_resources(resources_sheet, player_id)
        if player_data:
            production_rates = self.calculate_resource_production(player_data)

            new_wood = player_data["Wood"] + production_rates["Lumberhouse Production"]
            new_stone = player_data["Stone"] + production_rates["Mine Stone Production"]
            new_gold = player_data["Gold"] + production_rates["Mine Gold Production"]
            new_food = player_data["Food"]
            new_food = min(new_food, player_data["Warehouse Capacity"])

            new_wood = max(0, new_wood)
            new_stone = max(0, new_stone)
            new_gold = max(0, new_gold)
            new_food = max(0, new_food)

            player_data["Wood"] = new_wood
            player_data["Stone"] = new_stone
            player_data["Gold"] = new_gold
            player_data["Food"] = new_food
            player_data["Lumberhouse Production"] = production_rates["Lumberhouse Production"]
            player_data["Mine Stone Production"] = production_rates["Mine Stone Production"]
            player_data["Mine Gold Production"] = production_rates["Mine Gold Production"]
            player_data["Warehouse Capacity"] = production_rates["Warehouse Capacity"]

            sheets.update_player_resources(resources_sheet, player_id, player_data)
            return player_data
        else:
            print(f"PlayerID {player_id} not found in 'Resources' sheet.")
            return None
