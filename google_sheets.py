import gspread
from google.oauth2.service_account import Credentials

class GoogleSheets:
    """
    Handles all interactions with Google Sheets.
    """
    def __init__(self, config):
        self.config = config
        self.gc = self._authenticate()
        self.sheet = self._get_spreadsheet()

    def _authenticate(self):
        """Authenticates with Google Sheets."""
        decoded_creds = self.config.get_decoded_creds()
        self.config.write_creds_to_file(decoded_creds)
        credentials = Credentials.from_service_account_info(
            decoded_creds, scopes=self.config.SCOPES)
        return gspread.service_account(filename=self.config.CREDS_FILE)

    def _get_spreadsheet(self):
        """Opens the Google Sheet."""
        try:
            return self.gc.open_by_key(self.config.SHEET_ID)
        except gspread.SpreadsheetNotFound:
            raise ValueError(f"Spreadsheet with ID '{self.config.SHEET_ID}' not found.")

    def create_worksheet(self, title):
        """Creates a new worksheet or returns an existing one."""
        try:
            worksheet = self.sheet.add_worksheet(
                title=title, rows=self.config.DEFAULT_ROWS, cols=self.config.DEFAULT_COLS)
            print(f"Worksheet '{title}' created.")
            return worksheet
        except gspread.exceptions.APIError as e:
            if "duplicate name" in e.response.text:
                worksheet = self.sheet.worksheet(title)
                print(f"Worksheet '{title}' already exists. Using existing one.")
                return worksheet
            else:
                raise

    def initialize_resource_sheet(self):
        """Initializes the 'Resources' worksheet."""
        resources_sheet = self.create_worksheet(self.config.RESOURCES_SHEET_NAME)
        resources_data = [
            ["PlayerID", "Wood", "Stone", "Gold", "Food", "Premium",
             "Lumberhouse Level", "Mine Level", "Warehouse Level",
             "Lumberhouse Production", "Mine Stone Production",
             "Mine Gold Production", "Warehouse Capacity"]
        ]
        resources_sheet.update('A1', resources_data)
        return resources_sheet

    def get_player_resources(self, resources_sheet, player_id):
        """Retrieves a player's resources from the 'Resources' worksheet."""
        try:
            cell = resources_sheet.find(str(player_id), in_column=1)
            if cell:
                row = cell.row
                resources = resources_sheet.row_values(row)
                if len(resources) >= 13:
                    return {
                        "PlayerID": int(resources[0]),
                        "Wood": int(resources[1]),
                        "Stone": int(resources[2]),
                        "Gold": int(resources[3]),
                        "Food": int(resources[4]),
                        "Premium": int(resources[5]),
                        "Lumberhouse Level": int(resources[6]),
                        "Mine Level": int(resources[7]),
                        "Warehouse Level": int(resources[8]),
                        "Lumberhouse Production": float(resources[9]),
                        "Mine Stone Production": float(resources[10]),
                        "Mine Gold Production": float(resources[11]),
                        "Warehouse Capacity": int(resources[12]),
                    }
                else:
                    print(f"Warning: Incomplete data for PlayerID {player_id}. Expected 13 values, got {len(resources)}.")
                    return None
            else:
                return None
        except gspread.exceptions.CellNotFound:
            return None

    def create_player_resources(self, resources_sheet, player_id):
        """Creates a new entry for a player in the 'Resources' worksheet."""
        default_resources = [player_id, 1000, 500, 200, 2000, 0, 1, 1, 1, 10, 5, 5, 1000]
        resources_sheet.append_row(default_resources)
        print(f"Resources created for PlayerID {player_id}.")
        return default_resources

    def update_player_resources(self, resources_sheet, player_id, resources):
        """Updates a player's resources in the 'Resources' worksheet."""
        try:
            cell = resources_sheet.find(str(player_id), in_column=1)
            if cell:
                row = cell.row
                update_values = [
                    resources["Wood"], resources["Stone"], resources["Gold"],
                    resources["Food"], resources["Premium"],
                    resources["Lumberhouse Level"], resources["Mine Level"],
                    resources["Warehouse Level"],
                    resources["Lumberhouse Production"],
                    resources["Mine Stone Production"],
                    resources["Mine Gold Production"],
                    resources["Warehouse Capacity"]
                ]
                resources_sheet.update(f'B{row}:M{row}', [update_values])
                print(f"Resources updated for PlayerID {player_id}.")
            else:
                print(f"PlayerID {player_id} not found in 'Resources' sheet.")
        except gspread.exceptions.CellNotFound:
            print(f"PlayerID {player_id} not found in 'Resources' sheet.")
