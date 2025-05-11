"""
Constants for the SkyHustle Telegram bot.
Defines game constants, messages, and configuration.
"""

# Game version
VERSION = "1.0.0"

# Tutorial states
TUTORIAL_STATES = [
    "start",
    "status",
    "build",
    "train",
    "setname",
    "completed"
]

# Default resource values for new players
DEFAULT_RESOURCES = {
    "credits": 500,
    "minerals": 200,
    "energy": 100,
    "skybucks": 0
}

# Experience levels
XP_LEVELS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 1000,
    6: 2000,
    7: 4000,
    8: 8000,
    9: 16000,
    10: 32000
}

# Message templates
WELCOME_MESSAGE = """
Welcome to SkyHustle, {username}! 🚀

In this strategy game, you'll build futuristic aerial bases, train armies, research technologies, and engage in epic battles!

Would you like to begin the tutorial?
"""

HELP_MESSAGE = """
*SkyHustle Command Reference*

📊 *Base Management*
/status - Show your base stats and resources
/build <structure> [qty] - Build structures
/train <unit> [count] - Train units
/research [tech_id] - Research new technologies
/defensive - Manage your defensive structures

⚔️ *Combat*
/scan - Find potential targets
/attack <player_id> - Attack another player
/unit_evolution - Upgrade your units

🛡️ *Alliance*
/alliance <subcmd> - Alliance management
/war <subcmd> - Alliance war commands

🏆 *Progression*
/daily - Claim daily rewards
/achievements - Track your achievements
/events - View current game events
/leaderboard [scope] - View rankings

⚙️ *Settings*
/setname <name> - Set your display name
/notifications - Manage notifications
/tutorial - Restart tutorial
/weather - View ambient weather messages

Use /help <command> for detailed info on a specific command.
"""

# Weather messages
WEATHER_MESSAGES = [
    "☀️ Clear skies above your aerial base. Perfect for reconnaissance missions!",
    "🌤️ Scattered clouds at high altitude. Visibility remains optimal for operations.",
    "⛈️ Electrical storm approaching! Defensive systems receiving 15% power boost.",
    "🌧️ Light rain showers. Resource collectors operating at 105% efficiency.",
    "🌪️ Warning: Turbulence detected in sector 7. Consider relocating sensitive equipment.",
    "🌫️ Dense fog surrounding lower levels. Stealth units gaining 10% evasion bonus.",
    "🌅 Sunrise detected. Solar arrays charging at maximum capacity.",
    "🌙 Nightfall approaching. Stealth operations receiving 8% efficiency bonus."
]

# Response prefixes
RESPONSE_SUCCESS = "✅ "
RESPONSE_ERROR = "❌ "
RESPONSE_INFO = "ℹ️ "

# Command cooldowns (in seconds)
COOLDOWNS = {
    "scan": 30,
    "attack": 300,  # 5 minutes
    "daily": 86400  # 24 hours
}

# Queue limits
MAX_BUILD_QUEUE = 5
MAX_TRAINING_QUEUE = 5

# Auto-save interval (in seconds)
AUTO_SAVE_INTERVAL = 300  # 5 minutes

# Image URLs for base components (SVG format)
BASE_IMAGES = {
    "command_center": "https://example.com/command_center.svg",
    "barracks": "https://example.com/barracks.svg",
    "factory": "https://example.com/factory.svg",
    "generator": "https://example.com/generator.svg",
    "lab": "https://example.com/lab.svg",
    "turret": "https://example.com/turret.svg",
    "refinery": "https://example.com/refinery.svg",
    "shield": "https://example.com/shield.svg"
}

# Unit images (SVG format)
UNIT_IMAGES = {
    "drone": "https://example.com/drone.svg",
    "fighter": "https://example.com/fighter.svg",
    "bomber": "https://example.com/bomber.svg",
    "interceptor": "https://example.com/interceptor.svg",
    "gunship": "https://example.com/gunship.svg",
    "titan": "https://example.com/titan.svg"
}

# Technology images (SVG format)
TECH_IMAGES = {
    "advanced_materials": "https://example.com/advanced_materials.svg",
    "energy_efficiency": "https://example.com/energy_efficiency.svg",
    "advanced_propulsion": "https://example.com/advanced_propulsion.svg",
    "weapons_research": "https://example.com/weapons_research.svg",
    "defensive_systems": "https://example.com/defensive_systems.svg",
    "mineral_processing": "https://example.com/mineral_processing.svg",
    "economy_optimization": "https://example.com/economy_optimization.svg",
    "advanced_shield_tech": "https://example.com/advanced_shield_tech.svg"
}
