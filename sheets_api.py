"""
sheets_api.py:

This file handles all interactions with the Google Sheets API.
It provides functions to read from, write to, and update the Google Sheet.
"""

import gspread
import json
import base64
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import credentials

from config import SHEET_ID, BASE64_CREDS

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def authenticate():
    """Authenticates with Google Sheets API using BASE64_CREDS from config.py."""
    try:
        creds_decoded = base64.b64decode(BASE64_CREDS).decode('utf-8')
        creds_json = json.loads(creds_decoded)
        creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
        gc = gspread.Client(credentials=creds)
        return gc
    except Exception as e:
        print(f"Error authenticating with Google Sheets API: {e}")
        return None

def read_sheet(sheet_name, range_string):
    """Reads data from a specified range in a Google Sheet."""
    try:
        gc = authenticate()
        if gc:
            sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
            return sheet.get(range_string)
        else:
            return None
    except Exception as e:
        print(f"Error reading from sheet {sheet_name}, range {range_string}: {e}")
        return None

def write_to_sheet(sheet_name, range_string, data):
    """Writes data to a specified range in a Google Sheet."""
    try:
        gc = authenticate()
        if gc:
            sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
            sheet.update(range_string, data)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error writing to sheet {sheet_name}, range {range_string}: {e}")
        return False

def append_to_sheet(sheet_name, data):
    """Appends data to the end of a sheet."""
    try:
        gc = authenticate()
        if gc:
            sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
            sheet.append_row(data)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error appending to sheet {sheet_name}: {e}")
        return False

def create_sheet(sheet_name):
    """Creates a new sheet within the spreadsheet."""
    try:
        gc = authenticate()
        if gc:
            spreadsheet = gc.open_by_key(SHEET_ID)
            spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")  # You can adjust rows/cols
            return True
        else:
            return False
    except Exception as e:
        print(f"Error creating sheet {sheet_name}: {e}")
        return False

# Example Usage (for testing - remove in final version)
if __name__ == '__main__':
    gc = authenticate()
    if gc:
        print("Successfully authenticated with Google Sheets!")

        # Example: Read data
        data = read_sheet("Players", "A1:B2")
        print(f"Data from Players!A1:B2: {data}")

        # Example: Write data
        write_result = write_to_sheet("Players", "C1:D2", [["test1", "test2"],["test3","test4"]])
        print(f"Write successful? {write_result}")

        # Example: Append data
        append_result = append_to_sheet("Players", ["new_data1", "new_data2"])
        print(f"Append successful? {append_result}")

        #Example: Create sheet
        create_result = create_sheet("TestSheet")
        print(f"Create successful? {create_result}")

    else:
        print("Authentication failed. Check your credentials.")
