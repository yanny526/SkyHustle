"""
Logging setup for the SkyHustle Telegram bot.
Configures logging for the application.
"""
import logging
import os
import json
import sys
from datetime import datetime

def setup_logging():
    """
    Configure logging for the application.
    
    Sets up console and file logging with appropriate formatting.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/skyhustle_{timestamp}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set more verbose logging for certain modules
    logging.getLogger('modules.sheets_service').setLevel(logging.DEBUG)
    
    # Reduce logging verbosity for some libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('gspread').setLevel(logging.WARNING)
    
    # Log startup information
    logging.info("Logging initialized")
    logging.info(f"Log file: {log_file}")
    
    # Log environment information (excluding sensitive data)
    env_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "has_bot_token": bool(os.getenv("BOT_TOKEN")),
        "has_base64_creds": bool(os.getenv("BASE64_CREDS")),
        "has_sheet_id": bool(os.getenv("SHEET_ID"))
    }
    
    logging.info(f"Environment: {json.dumps(env_info)}")

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Formats log records as JSON objects.
    """
    def format(self, record):
        """Format a log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "command"):
            log_data["command"] = record.command
        
        return json.dumps(log_data)

def get_logger(name):
    """
    Get a logger with the given name.
    
    Args:
        name: Name of the logger
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Add a JSON handler if not already present
    has_json_handler = any(isinstance(h.formatter, JSONFormatter) for h in logger.handlers)
    
    if not has_json_handler and os.getenv("JSON_LOGGING", "").lower() == "true":
        json_handler = logging.FileHandler("logs/json_logs.log")
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)
    
    return logger
