# config.py

import os
import json
from base64 import b64decode

# Environment variables
BASE64_CREDS = os.getenv('BASE64_CREDS')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SHEET_ID = os.getenv('SHEET_ID')

# Decode the base64-encoded service account JSON
SERVICE_ACCOUNT_INFO = json.loads(b64decode(BASE64_CREDS).decode())
