#!/usr/bin/env python3
"""
SkyHustle Telegram Bot - Main Entry Point
A Telegram-based strategy RPG where players build aerial bases, train armies,
research technologies, and engage in battles via chat commands.
"""
import os
import logging
import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify
from bot.telegram_bot import setup_bot
from utils.logger import setup_logging
from utils.sheets import initialize_sheets, get_sheet_stats, get_recent_activity

# Create Flask app
app = Flask(__name__)

# Global variables to store app start time
start_time = datetime.now()

# Dashboard routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', 
                          version="1.0.0")

@app.route('/simple')
def simple():
    """Simple text-based dashboard"""
    return render_template('simple.html')

@app.route('/api/stats')
def get_stats():
    """API endpoint for dashboard stats"""
    # Calculate uptime
    uptime_seconds = int((datetime.now() - start_time).total_seconds())
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    # Get stats from Google Sheets asynchronously
    try:
        # Create event loop if not exists
        loop = asyncio.new_event_loop()
        
        # Initialize sheets if needed
        loop.run_until_complete(initialize_sheets())
        
        # Get stats
        stats = loop.run_until_complete(get_sheet_stats())
        
        # Get recent activity
        recent_activity = loop.run_until_complete(get_recent_activity(10))
        
        loop.close()
    except Exception as e:
        logging.error(f"Error getting sheet data: {e}", exc_info=True)
        # Fallback stats
        stats = {
            "players": 0,
            "alliances": 0,
            "battles": 0
        }
        recent_activity = []
    
    # Return JSON data
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": uptime_str,
        "stats": stats,
        "recent_activity": recent_activity
    })

def main():
    """Main entry point for the SkyHustle bot application."""
    # Setup logging
    setup_logging()
    
    # Get environment variables
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logging.critical("BOT_TOKEN environment variable not set. Exiting.")
        return
    
    # Validate other required environment variables
    if not os.getenv('BASE64_CREDS'):
        logging.critical("BASE64_CREDS environment variable not set. Exiting.")
        return
    
    if not os.getenv('SHEET_ID'):
        logging.critical("SHEET_ID environment variable not set. Exiting.")
        return
        
    # Initialize Google Sheets (try once at startup)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(initialize_sheets())
        loop.close()
        logging.info("Google Sheets initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Google Sheets: {e}", exc_info=True)
        # Continue anyway, we'll try again later
    
    # Setup and run the bot
    logging.info("Starting SkyHustle Telegram Bot...")
    
    try:
        # Run the bot
        asyncio.run(setup_bot(bot_token))
    except Exception as e:
        logging.critical(f"Failed to start bot: {e}", exc_info=True)
        
if __name__ == "__main__":
    main()
