# bot/config.py

import os
import base64
import json

# Load environment variables
BASE64_CREDS = os.getenv("BASE64_CREDS")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")

# Decode base64 credentials
SERVICE_ACCOUNT_INFO = json.loads(base64.b64decode(BASE64_CREDS).decode('utf-8'))