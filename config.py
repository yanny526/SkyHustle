import os
from base64 import b64decode
import json

BASE64_CREDS = os.getenv('BASE64_CREDS')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SHEET_ID = os.getenv('SHEET_ID')

# Decode service account
SERVICE_ACCOUNT_INFO = json.loads(b64decode(BASE64_CREDS).decode())
