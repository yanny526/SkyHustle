"""
Google Sheets Manager for SkyHustle 2
Handles connection, tab creation, and all game data operations
"""

import os
import json
import base64
import time
import logging
import functools
from typing import List, Dict, Optional, Any, Union, Callable
from google.oauth2.service_account import Credentials
import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
CACHE_TTL = 300  # 5 minutes
BATCH_SIZE = 100

# Required fields for each sheet
REQUIRED_FIELDS = {
    'Players': ['player_id', 'name'],
    'Alliances': ['alliance_id', 'name', 'leader'],
    'AllianceWars': ['war_id', 'attacker_id', 'defender_id'],
    'ShopTransactions': ['transaction_id', 'player_id', 'item_id'],
    'BlackMarketTransactions': ['transaction_id', 'player_id', 'item_id'],
    'DailyRewards': ['claim_id', 'player_id'],
    'Achievements': ['achievement_id', 'player_id'],
    'Logs': ['log_id', 'timestamp']
}

SHEET_TABS = {
    'Players': [
        'player_id', 'name', 'level', 'xp', 'resources', 'army', 'alliance', 'hustlecoins', 'achievements', 'last_active', 'bag'
    ],
    'Alliances': [
        'alliance_id', 'name', 'level', 'xp', 'members', 'leader', 'created_at', 'perks', 'war_history', 'diplomacy', 'resources'
    ],
    'AllianceWars': [
        'war_id', 'attacker_id', 'defender_id', 'start_time', 'end_time', 'result', 'score', 'details'
    ],
    'ShopTransactions': [
        'transaction_id', 'player_id', 'item_id', 'item_name', 'quantity', 'cost', 'currency', 'timestamp'
    ],
    'BlackMarketTransactions': [
        'transaction_id', 'player_id', 'item_id', 'item_name', 'quantity', 'cost', 'currency', 'timestamp'
    ],
    'DailyRewards': [
        'claim_id', 'player_id', 'date', 'reward', 'claimed_at'
    ],
    'Achievements': [
        'achievement_id', 'player_id', 'achievement', 'date', 'details'
    ],
    'Logs': [
        'log_id', 'timestamp', 'level', 'event', 'details'
    ]
}

# Define expected data types for each column
SHEET_DATA_TYPES = {
    'Players': {
        'player_id': str,
        'name': str,
        'level': int,
        'xp': int,
        'resources': str,  # JSON string
        'army': str,  # JSON string
        'alliance': str,
        'hustlecoins': int,
        'achievements': str,  # JSON string
        'last_active': float,
        'bag': str  # JSON string
    },
    'Alliances': {
        'alliance_id': str,
        'name': str,
        'level': int,
        'xp': int,
        'members': str,  # JSON string
        'leader': str,
        'created_at': float,
        'perks': str,  # JSON string
        'war_history': str,  # JSON string
        'diplomacy': str,  # JSON string
        'resources': str  # JSON string
    },
    'AllianceWars': {
        'war_id': str,
        'attacker_id': str,
        'defender_id': str,
        'start_time': float,
        'end_time': float,
        'result': str,
        'score': str,  # JSON string
        'details': str  # JSON string
    },
    'ShopTransactions': {
        'transaction_id': str,
        'player_id': str,
        'item_id': str,
        'item_name': str,
        'quantity': int,
        'cost': str,  # JSON string
        'currency': str,
        'timestamp': float
    },
    'BlackMarketTransactions': {
        'transaction_id': str,
        'player_id': str,
        'item_id': str,
        'item_name': str,
        'quantity': int,
        'cost': str,  # JSON string
        'currency': str,
        'timestamp': float
    },
    'DailyRewards': {
        'claim_id': str,
        'player_id': str,
        'date': str,
        'reward': str,  # JSON string
        'claimed_at': float
    },
    'Achievements': {
        'achievement_id': str,
        'player_id': str,
        'achievement': str,
        'date': str,
        'details': str  # JSON string
    },
    'Logs': {
        'log_id': str,
        'timestamp': float,
        'level': str,
        'event': str,
        'details': str  # JSON string
    }
}

def retry_on_api_error(func: Callable) -> Callable:
    """Decorator to retry operations on API errors"""
    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: logger.error(f"Failed after {retry_state.attempt_number} attempts")
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class GoogleSheetsManager:
    def __init__(self):
        self._setup_credentials()
        self.sheet = None
        self._worksheets = {}
        self._cache = {}
        self._cache_timestamps = {}

    def _setup_credentials(self):
        """Setup Google Sheets credentials"""
        creds_b64 = os.getenv('BASE64_CREDS')
        self.sheet_id = os.getenv('SHEET_ID')
        if not creds_b64 or not self.sheet_id:
            raise ValueError("Missing BASE64_CREDS or SHEET_ID in environment variables.")
        
        try:
            creds_json = base64.b64decode(creds_b64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            self.gc = gspread.authorize(creds)
        except Exception as e:
            logger.error(f"Failed to setup credentials: {str(e)}")
            raise

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if key in self._cache and time.time() - self._cache_timestamps.get(key, 0) < CACHE_TTL:
            return self._cache[key]
        return None

    def _set_cached_data(self, key: str, value: Any):
        """Set data in cache with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def _sanitize_value(self, value: Any) -> str:
        """Sanitize value for Google Sheets"""
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def _validate_required_fields(self, tab: str, data: Dict[str, Any]) -> None:
        """Validate required fields are present"""
        required = REQUIRED_FIELDS.get(tab, [])
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Missing required fields for {tab}: {', '.join(missing)}")

    def _validate_and_convert_data(self, tab: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert data types according to schema"""
        self._validate_required_fields(tab, data)
        validated_data = {}
        expected_types = SHEET_DATA_TYPES[tab]
        
        for key, expected_type in expected_types.items():
            value = data.get(key)
            if value is None:
                validated_data[key] = ''
                continue
                
            try:
                if expected_type == str and isinstance(value, (dict, list)):
                    validated_data[key] = json.dumps(value)
                elif expected_type == int:
                    validated_data[key] = int(value)
                elif expected_type == float:
                    validated_data[key] = float(value)
                else:
                    validated_data[key] = str(value)
            except (ValueError, TypeError) as e:
                logger.error(f"Data validation error for {key} in {tab}: {str(e)}")
                raise ValueError(f"Invalid data type for {key} in {tab}: {str(e)}")
                
        return validated_data

    @retry_on_api_error
    def get_sheet(self):
        """Get the Google Sheet with retry logic"""
        if self.sheet is None:
            self.sheet = self.gc.open_by_key(self.sheet_id)
        return self.sheet

    @retry_on_api_error
    def get_worksheet(self, tab: str) -> gspread.Worksheet:
        """Get worksheet with retry logic and header validation"""
        headers = SHEET_TABS[tab]
        if tab not in self._worksheets:
            sheet = self.get_sheet()
            try:
                ws = sheet.worksheet(tab)
                current_headers = ws.row_values(1)
                if current_headers != headers:
                    logger.info(f"Updating headers for {tab}")
                    ws.delete_rows(1)
                    ws.insert_row(headers, 1)
            except WorksheetNotFound:
                logger.info(f"Creating new worksheet: {tab}")
                ws = sheet.add_worksheet(title=tab, rows=1000, cols=len(headers))
                ws.insert_row(headers, 1)
            self._worksheets[tab] = ws
        return self._worksheets[tab]

    def _batch_update(self, tab: str, rows: List[List[Any]]):
        """Perform batch update for better performance"""
        ws = self.get_worksheet(tab)
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            ws.append_rows(batch)

    # --- CRUD for Players ---
    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players with caching"""
        cache_key = 'all_players'
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        ws = self.get_worksheet('Players')
        data = ws.get_all_records()
        self._set_cached_data(cache_key, data)
        return data

    def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player by ID with caching"""
        cache_key = f'player_{player_id}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        ws = self.get_worksheet('Players')
        for row in ws.get_all_records():
            if str(row.get('player_id')) == str(player_id):
                self._set_cached_data(cache_key, row)
                return row
        return None

    @retry_on_api_error
    def upsert_player(self, player_data: Dict[str, Any]):
        """Upsert player with validation and retry logic"""
        ws = self.get_worksheet('Players')
        validated_data = self._validate_and_convert_data('Players', player_data)
        player_id = str(validated_data['player_id'])
        
        # Clear cache
        self._cache.pop('all_players', None)
        self._cache.pop(f'player_{player_id}', None)
        
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get('player_id')) == player_id:
                cell_list = ws.range(f'A{idx}:K{idx}')
                for i, key in enumerate(SHEET_TABS['Players']):
                    cell_list[i].value = validated_data.get(key, '')
                ws.update_cells(cell_list)
                return
        values = [validated_data.get(key, '') for key in SHEET_TABS['Players']]
        ws.append_row(values)

    # --- CRUD for Alliances ---
    def get_all_alliances(self) -> List[Dict[str, Any]]:
        """Get all alliances with caching"""
        cache_key = 'all_alliances'
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        ws = self.get_worksheet('Alliances')
        data = ws.get_all_records()
        self._set_cached_data(cache_key, data)
        return data

    def get_alliance(self, alliance_id: str) -> Optional[Dict[str, Any]]:
        """Get alliance by ID with caching"""
        cache_key = f'alliance_{alliance_id}'
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        ws = self.get_worksheet('Alliances')
        for row in ws.get_all_records():
            if str(row.get('alliance_id')) == str(alliance_id):
                self._set_cached_data(cache_key, row)
                return row
        return None

    @retry_on_api_error
    def upsert_alliance(self, alliance_data: Dict[str, Any]):
        """Upsert alliance with validation and retry logic"""
        ws = self.get_worksheet('Alliances')
        validated_data = self._validate_and_convert_data('Alliances', alliance_data)
        alliance_id = str(validated_data['alliance_id'])
        
        # Clear cache
        self._cache.pop('all_alliances', None)
        self._cache.pop(f'alliance_{alliance_id}', None)
        
        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get('alliance_id')) == alliance_id:
                cell_list = ws.range(f'A{idx}:K{idx}')
                for i, key in enumerate(SHEET_TABS['Alliances']):
                    cell_list[i].value = validated_data.get(key, '')
                ws.update_cells(cell_list)
                return
        values = [validated_data.get(key, '') for key in SHEET_TABS['Alliances']]
        ws.append_row(values)

    # --- CRUD for AllianceWars ---
    @retry_on_api_error
    def log_alliance_war(self, war_data: Dict[str, Any]):
        """Log alliance war with validation and retry logic"""
        ws = self.get_worksheet('AllianceWars')
        validated_data = self._validate_and_convert_data('AllianceWars', war_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['AllianceWars']]
        ws.append_row(values)

    # --- CRUD for ShopTransactions ---
    @retry_on_api_error
    def log_shop_transaction(self, tx_data: Dict[str, Any]):
        """Log shop transaction with validation and retry logic"""
        ws = self.get_worksheet('ShopTransactions')
        validated_data = self._validate_and_convert_data('ShopTransactions', tx_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['ShopTransactions']]
        ws.append_row(values)

    # --- CRUD for BlackMarketTransactions ---
    @retry_on_api_error
    def log_blackmarket_transaction(self, tx_data: Dict[str, Any]):
        """Log black market transaction with validation and retry logic"""
        ws = self.get_worksheet('BlackMarketTransactions')
        validated_data = self._validate_and_convert_data('BlackMarketTransactions', tx_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['BlackMarketTransactions']]
        ws.append_row(values)

    # --- CRUD for DailyRewards ---
    @retry_on_api_error
    def log_daily_reward(self, reward_data: Dict[str, Any]):
        """Log daily reward with validation and retry logic"""
        ws = self.get_worksheet('DailyRewards')
        validated_data = self._validate_and_convert_data('DailyRewards', reward_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['DailyRewards']]
        ws.append_row(values)

    # --- CRUD for Achievements ---
    @retry_on_api_error
    def log_achievement(self, achievement_data: Dict[str, Any]):
        """Log achievement with validation and retry logic"""
        ws = self.get_worksheet('Achievements')
        validated_data = self._validate_and_convert_data('Achievements', achievement_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['Achievements']]
        ws.append_row(values)

    # --- CRUD for Logs ---
    @retry_on_api_error
    def log_event(self, log_data: Dict[str, Any]):
        """Log event with validation and retry logic"""
        ws = self.get_worksheet('Logs')
        validated_data = self._validate_and_convert_data('Logs', log_data)
        values = [validated_data.get(key, '') for key in SHEET_TABS['Logs']]
        ws.append_row(values)

    def ensure_headers(self, tab: str, headers: list):
        """Ensure worksheet has correct headers"""
        self.get_worksheet(tab)

    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._cache_timestamps.clear() 