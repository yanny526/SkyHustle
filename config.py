# bot/config.py

import os
import base64
import json

# Load environment variables
BASE64_CREDS = os.getenv("BASE64_CREDS")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")

# Safely decode base64 credentials if provided
SERVICE_ACCOUNT_INFO = None
if BASE64_CREDS:
    try:
        decoded = base64.b64decode(BASE64_CREDS)
        SERVICE_ACCOUNT_INFO = json.loads(decoded.decode('utf-8'))
    except Exception as e:
        raise RuntimeError('Invalid BASE64_CREDS environment variable') from e
else:
    # BASE64_CREDS not set; SERVICE_ACCOUNT_INFO remains None
    pass

# Decode base64 credentials
