
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import base64

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_data = os.getenv("GOOGLE_CREDS_BASE64")
if creds_data:
    creds_json = json.loads(base64.b64decode(creds_data))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
else:
    raise Exception("Missing Google credentials.")

SHEET_NAME = "SkyHustleSheet"
sheet = client.open(SHEET_NAME)

player_profile = sheet.worksheet("PlayerProfile")
army = sheet.worksheet("Army")
buildings = sheet.worksheet("Buildings")
research = sheet.worksheet("Research")
missions = sheet.worksheet("Missions")
