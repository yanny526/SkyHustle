from config import Config
from google_sheets import GoogleSheets
from resource_manager import ResourceManager

def main():
    """
    Main function to initialize the game and demonstrate resource management.
    """
    try:
        config = Config()
        sheets = GoogleSheets(config)
        resources_sheet = sheets.initialize_resource_sheet()
        resource_manager = ResourceManager(config)

        player_id_1 = 12345
        player_id_2 = 67890

        if not sheets.get_player_resources(resources_sheet, player_id_1):
            sheets.create_player_resources(resources_sheet, player_id_1)
        if not sheets.get_player_resources(resources_sheet, player_id_2):
            sheets.create_player_resources(resources_sheet, player_id_2)

        print(f"\nInitial Resources for Player {player_id_1}:")
        print(sheets.get_player_resources(resources_sheet, player_id_1))
        print(f"\nInitial Resources for Player {player_id_2}:")
        print(sheets.get_player_resources(resources_sheet, player_id_2))

        player_1_resources = sheets.get_player_resources(resources_sheet, player_id_1)
        if player_1_resources:
            player_1_resources["Wood"] += 500
            player_1_resources["Stone"] += 200
            sheets.update_player_resources(resources_sheet, player_id_1, player_1_resources)

        print("\nUpdating resources per turn:")
        updated_player_1_data = resource_manager.update_resources_per_turn(sheets, resources_sheet, player_id_1)
        updated_player_2_data = resource_manager.update_resources_per_turn(sheets, resources_sheet, player_id_2)

        if updated_player_1_data:
            print(f"\nResources for Player {player_id_1} after turn update:")
            print(updated_player_1_data)
        if updated_player_2_data:
            print(f"\nResources for Player {player_id_2} after turn update:")
            print(updated_player_2_data)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
