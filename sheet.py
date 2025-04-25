import os
import base64
import json
import gspread
from google.oauth2.service_account import Credentials

def get_sheet():
    # Decode base64 credentials from environment variable
    creds_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode("utf-8")
    creds_dict = json.loads(creds_json)

    # Authorize with Google Sheets
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)

    # Open your specific sheet (edit this URL or name if needed)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit")
