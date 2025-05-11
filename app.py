"""
Flask web application for SkyHustle dashboard.
Provides a web interface for viewing game statistics and admin controls.
"""
import os
import logging
import telegram
from flask import Flask, render_template, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Set the correct Telegram bot username
bot_username = "SkyHustle_bot"
logger.info(f"Using Telegram bot @{bot_username}")

# Routes
@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', bot_username=bot_username)

@app.route('/dashboard')
def dashboard():
    """Admin dashboard for game statistics."""
    return render_template('dashboard.html', bot_username=bot_username)

@app.route('/api/stats')
def get_stats():
    """API endpoint to retrieve game statistics."""
    from utils.sheets_service import get_stats
    try:
        stats = get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return jsonify({"error": str(e)}), 500

# Start the Flask app if run directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
