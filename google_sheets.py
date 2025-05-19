import os
import base64
import gspread
from google.oauth2.service_account import Credentials

# Load credentials from environment
BASE64_CREDS = os.environ.get("BASE64_CREDS")
SHEET_ID = os.environ.get("SHEET_ID")

# Authenticate with Google Sheets
def get_gspread_client():
    creds_json = base64.b64decode(BASE64_CREDS).decode("utf-8")
    creds_dict = eval(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

# Load or create the SkyHustleData sheet
def get_sheet():
    client = get_gspread_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    sheet_title = "SkyHustleData"

    try:
        sheet = spreadsheet.worksheet(sheet_title)
        print("✅ Found existing sheet:", sheet_title)
    except gspread.exceptions.WorksheetNotFound:
        print("📄 Sheet not found. Creating new one:", sheet_title)
        sheet = spreadsheet.add_worksheet(title=sheet_title, rows="1000", cols="20")

    ensure_headers(sheet)
    return sheet

# Ensure correct headers exist
def ensure_headers(sheet):
    headers = sheet.row_values(1)
    expected = [
        "game_name", "user_id", "wood", "stone", "gold", "food", "premium",
        "power", "base_lvl", "mine_lvl", "lumber_lvl", "barracks_lvl", "warehouse_lvl",
        "hospital_lvl", "jail_lvl", "research_lvl"
    ]
    if headers != expected:
        print("🔧 Setting up headers...")
        if headers:
            sheet.delete_rows(1)
        sheet.insert_row(expected, index=1)

# Fetch user by game name
def get_user_by_name(game_name):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["game_name"].lower() == game_name.lower():
            return row, i
    return None, None

# Add new user to the sheet
def add_new_user(game_name, user_id):
    sheet = get_sheet()
    existing, _ = get_user_by_name(game_name)
    if existing:
        return False
    default_row = [
        game_name, str(user_id), 100, 100, 100, 100, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0
    ]
    sheet.append_row(default_row)
    return True

# Update a specific field for a user
def update_user_field(game_name, field, new_value):
    sheet = get_sheet()
    row_data, row_index = get_user_by_name(game_name)
    if not row_data:
        return False
    headers = sheet.row_values(1)
    col_index = headers.index(field) + 1
    sheet.update_cell(row_index, col_index, new_value)
    return True

# Get user resource info
def get_user_resources(game_name):
    row, _ = get_user_by_name(game_name)
    if not row:
        return None
    return {
        "wood": row["wood"],
        "stone": row["stone"],
        "gold": row["gold"],
        "food": row["food"],
        "premium": row["premium"]
    }
