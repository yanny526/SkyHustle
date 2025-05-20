import os
import json

class Config:
    """
    Configuration class to manage environment variables and game settings.
    """
    def __init__(self):
        self.BASE64_CREDS = os.environ.get('BASE64_CREDS')
        self.SHEET_ID = os.environ.get('SHEET_ID')
        if not self.BASE64_CREDS:
            raise EnvironmentError("BASE64_CREDS environment variable not set.")
        if not self.SHEET_ID:
            raise EnvironmentError("SHEET_ID environment variable not set.")

        self.CREDS_FILE = 'service_account.json'
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
                         'https://www.googleapis.com/auth/drive.file']
        self.RESOURCES_SHEET_NAME = 'Resources'
        self.DEFAULT_ROWS = "100"
        self.DEFAULT_COLS = "20"

    def get_decoded_creds(self):
        """Decodes the base64 credentials."""
        try:
            return json.loads(self.BASE64_CREDS)
        except json.JSONDecodeError:
            raise ValueError("BASE64_CREDS is not valid JSON.")

    def write_creds_to_file(self, decoded_creds):
        """Writes the decoded credentials to a file."""
        with open(self.CREDS_FILE, 'w') as f:
            json.dump(decoded_creds, f)

    def get_base_lumberhouse_production(self):
        return 10
    def get_base_mine_stone_production(self):
        return 5
    def get_base_mine_gold_production(self):
        return 5
    def get_base_warehouse_capacity(self):
        return 1000

    def get_lumberhouse_production_multiplier(self):
        return 0.1
    def get_mine_stone_production_multiplier(self):
        return 0.15
    def get_mine_gold_production_multiplier(self):
        return 0.15
    def get_warehouse_capacity_multiplier(self):
        return 0.2
