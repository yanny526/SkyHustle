import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import config (absolute import)
import config

# Define the scope for Google Sheets API
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsDBManager:
    _instance = None # Singleton instance
    _client = None
    _spreadsheet = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleSheetsDBManager, cls).__new__(cls)
            cls._instance._initialize_client()
            cls._instance._initialize_spreadsheet()
        return cls._instance

    def _initialize_client(self):
        """Initializes the gspread client using service account credentials from JSON string."""
        if self.__class__._client is None:
            try:
                # Load credentials from the JSON string provided via environment variable (via config)
                if config.GOOGLE_CREDENTIALS_JSON_CONTENT:
                    creds_dict = json.loads(config.GOOGLE_CREDENTIALS_JSON_CONTENT)
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
                    self.__class__._client = gspread.authorize(creds)
                    logging.info("gspread client authorized successfully from JSON string.")
                else:
                    raise ValueError("GOOGLE_CREDENTIALS_JSON_CONTENT not found in config. Make sure it's set in environment variables.")
            except Exception as e:
                logging.error(f"Error authorizing gspread client: {e}")
                raise

    def _initialize_spreadsheet(self):
        """Opens the specified Google Spreadsheet."""
        if self.__class__._spreadsheet is None:
            try:
                if not config.GOOGLE_SHEET_ID:
                    raise ValueError("GOOGLE_SHEET_ID not found in config. Make sure it's set in environment variables.")
                logging.info(f"Opening spreadsheet with ID: {config.GOOGLE_SHEET_ID}")
                self.__class__._spreadsheet = self.__class__._client.open_by_key(config.GOOGLE_SHEET_ID)
                logging.info("Spreadsheet opened successfully.")
            except Exception as e:
                    logging.error(f"Error opening spreadsheet: {e}")
                    raise

    def _get_sheet(self, sheet_name):
        """Helper to get a worksheet by name, creating it if it doesn't exist.
        Initial headers are defined here for the main sheets."""
        try:
            return self._spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            logging.warning(f"Worksheet '{sheet_name}' not found. Creating it.")
            # Define headers for main sheets
            if sheet_name == "Players":
                headers = [
                    "user_id", "commander_name", "coordinates_x", "coordinates_y",
                    "current_resources", "resource_caps", "building_levels",
                    "unit_counts", "player_power", "prestige_level",
                    "last_login_timestamp", "active_hero_assignments", "owned_heroes",
                    "captured_heroes", "active_timers", "alliance_id",
                    "peace_shield_end_timestamp", "strategy_points_available",
                    "strategy_point_allocations", "completed_research", "quest_progress"
                ]
            elif sheet_name == "Alliances":
                headers = [
                    "alliance_id", "alliance_name", "leader_user_id", "member_count",
                    "total_power", "controlled_zones", "chat_log"
                ]
            elif sheet_name == "GameEvents":
                headers = [
                    "event_id", "event_type", "timestamp", "details"
                ]
            else:
                # Generic fallback for other sheets if created later dynamically without predefined headers
                headers = ["id", "data"] 

            worksheet = self._spreadsheet.add_worksheet(title=sheet_name, rows="1", cols=str(len(headers)))
            worksheet.append_row(headers)
            logging.info(f"Worksheet '{sheet_name}' created with headers.")
            return worksheet

    def _row_to_dict(self, headers, row_values):
        """Converts a list of row values into a dictionary using headers,
        handling cases where row_values might be shorter than headers."""
        return {headers[i]: row_values[i] if i < len(row_values) else "" for i in range(len(headers))}

    def _dict_to_row(self, headers, data_dict):
        """Converts a dictionary into a list of row values based on headers order."""
        return [data_dict.get(header, "") for header in headers] # Use "" for missing keys

    def _parse_json_fields(self, data_dict):
        """Parses JSON string fields into Python dictionaries/lists.
        Applies to common JSON fields stored as strings in sheets."""
        json_fields = [
            'current_resources', 'resource_caps', 'building_levels', 'unit_counts',
            'active_timers', 'active_hero_assignments', 'owned_heroes',
            'captured_heroes', 'strategy_point_allocations', 'completed_research',
            'quest_progress', 'controlled_zones', 'chat_log', 'details'
        ]
        
        for field in json_fields:
            if field in data_dict and isinstance(data_dict[field], str) and data_dict[field].strip():
                try:
                    data_dict[field] = json.loads(data_dict[field])
                except json.JSONDecodeError:
                    logging.error(f"Failed to decode JSON for field '{field}': {data_dict[field]}")
                    data_dict[field] = {} if field not in ['completed_research', 'controlled_zones', 'chat_log'] else [] # Default to dict or list

        return data_dict

    def get_player_data(self, user_id: int) -> dict | None:
        """
        Retrieves a player's data from the 'Players' sheet.
        Returns a dictionary of player data if found, None otherwise.
        """
        sheet = self._get_sheet("Players")
        headers = sheet.row_values(1) # Get headers from the first row

        try:
            # Find the row where the first column (user_id) matches
            cell = sheet.find(str(user_id), in_column=1)
            row_index = cell.row
            row_values = sheet.row_values(row_index)
            player_data = self._row_to_dict(headers, row_values)
            return self._parse_json_fields(player_data)
        except gspread.exceptions.CellNotFound:
            logging.info(f"Player with user_id {user_id} not found.")
            return None
        except Exception as e:
            logging.error(f"Error getting player data for {user_id}: {e}")
            return None

    def create_player(self, player_data: dict) -> bool:
        """
        Adds a new player's data to the 'Players' sheet.
        Returns True on success, False on failure.
        """
        sheet = self._get_sheet("Players")
        headers = sheet.row_values(1) # Get headers from the first row

        # Convert dictionary/list values to JSON strings for relevant fields before storing
        player_data_for_sheet = player_data.copy()
        json_fields_to_serialize = [
            'current_resources', 'resource_caps', 'building_levels', 'unit_counts',
            'active_timers', 'active_hero_assignments', 'owned_heroes',
            'captured_heroes', 'strategy_point_allocations', 'completed_research',
            'quest_progress'
        ]
        for field in json_fields_to_serialize:
            if field in player_data_for_sheet:
                player_data_for_sheet[field] = json.dumps(player_data_for_sheet[field])

        row_values = self._dict_to_row(headers, player_data_for_sheet)
        try:
            sheet.append_row(row_values)
            logging.info(f"Player {player_data.get('commander_name', 'N/A')} created successfully.")
            return True
        except Exception as e:
            logging.error(f"Error creating player {player_data.get('commander_name', 'N/A')}: {e}")
            return False

    def update_player_data(self, user_id: int, updates: dict) -> bool:
        """
        Updates specific fields for a player in the 'Players' sheet.
        'updates' should be a dictionary of field_name: new_value.
        Returns True on success, False on failure.
        """
        sheet = self._get_sheet("Players")
        headers = sheet.row_values(1) # Get headers from the first row

        try:
            cell = sheet.find(str(user_id), in_column=1)
            row_index = cell.row

            # Prepare updates: convert dicts/lists to JSON strings
            updates_for_sheet = updates.copy()
            for key, value in updates_for_sheet.items():
                if isinstance(value, (dict, list)):
                    updates_for_sheet[key] = json.dumps(value)
            
            # Get current row values, update, then write back
            current_row_values = sheet.row_values(row_index)
            updated_row_values = list(current_row_values) # Make it mutable
            
            for key, new_value in updates_for_sheet.items():
                try:
                    col_index = headers.index(key) + 1 # +1 because gspread is 1-indexed
                    # Ensure the list is long enough for the column index
                    while len(updated_row_values) < col_index:
                        updated_row_values.append("") 
                    updated_row_values[col_index - 1] = new_value # Update the value in the list
                except ValueError:
                    logging.warning(f"Attempted to update non-existent column: {key}")
                    continue # Skip if header not found

            # Update the entire row using A1 notation for the entire row
            # gspread.utils.rowcol_to_a1 helps generate the correct range
            sheet.update(f'A{row_index}:{gspread.utils.rowcol_to_a1(row_index, len(headers))}', [updated_row_values])
            logging.info(f"Player {user_id} data updated successfully.")
            return True
        except gspread.exceptions.CellNotFound:
            logging.warning(f"Player with user_id {user_id} not found for update.")
            return False
        except Exception as e:
            logging.error(f"Error updating player data for {user_id}: {e}")
            return False

    def get_all_players(self) -> list[dict]:
        """
        Retrieves all players' data from the 'Players' sheet.
        Returns a list of dictionaries, where each dictionary is a player's data.
        """
        sheet = self._get_sheet("Players")
        # Get all records as list of lists, excluding header row
        try:
            records = sheet.get_all_values()
            if not records:
                return []

            headers = records[0]
            player_list = []
            for row_values in records[1:]: # Skip header row
                player_data = self._row_to_dict(headers, row_values)
                player_list.append(self._parse_json_fields(player_data))
            return player_list
        except Exception as e:
            logging.error(f"Error getting all players: {e}")
            return [] 