import os, json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    creds_json = os.getenv("GOOGLE_CREDS_BASE64")
    creds_dict = json.loads(base64.b64decode(creds_json).decode())

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1_HYh2BXOGjuZ6ypovf7HUlb3GYuu033V66O6KtNmM2M/edit")
    return sheet.worksheet("SkyHustle")

