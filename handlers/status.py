# handlers/status.py

from telegram import Update
from telegram.ext import ContextTypes
import time
from datetime import datetime

from modules.save_system import load_player_data, load_buildings_data, load_units_data
from handlers.chaos_events import active_events
from modules.endgame import endgame_challenges
from modules.weather import get_current_weather
from utils.format import section_header

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    # Load player data
    player_data = load_player_data(uid)
    buildings_data = load_buildings_data(uid)
    units_data = load_units_data(uid)

    # Format last login
    last_login = datetime.fromtimestamp(player_data["last_login"]).strftime('%Y-%m-%d %H:%M')

    # Format active chaos events
    events_text = "None"
    if active_events:
        events_text = "\n".join([f"• {event.name}: {event.description}" for event in active_events])

    # Format endgame challenges
    challenges_text = "\n".join([
        f"• {challenge.name}: {'✅' if challenge.completed else '❌'}" for challenge in endgame_challenges
    ])

    # Get current weather
    weather = get_current_weather()
    weather_text = f"**Current Weather**: {weather.name}\n{weather.description}\nCombat Modifier: {weather.combat_modifier:.1f}x\nProduction Modifier: {weather.production_modifier:.1f}x"

    # Determine player's faction
    player_faction = "None"
    for faction_id, faction in factions.items():
        if uid in faction.members:
            player_faction = faction.name
            break

    # Retrieve defensive structures
    defensive_structures = get_rows("DefensiveStructures")
    defense_info = "None"
    for row in defensive_structures[1:]:
        if row[0] == uid:
            defense_info = f"{row[1]} - Level {row[2]} (Defense: {row[3]}x)"
            break

    # Retrieve unlocked research items
    unlocked_research = [item.name for item in research_items.values() if item.unlocked]
    research_text = "Unlocked Research:\n" + "\n".join(unlocked_research) if unlocked_research else "No research unlocked yet"

    # Retrieve current alliance war status
    war_status = "No active alliance war"
    current_war = get_current_war()
    if current_war:
        status = current_war.get_status()
        time_left = (status["end_time"] - datetime.now()).total_seconds() / 3600
        war_status = (
            f"Alliance War: {status['alliance1']} vs {status['alliance2']}\n"
            f"Score: {status['score'][status['alliance1']]} - {status['score'][status['alliance2']]}\n"
            f"Time Left: {time_left:.1f} hours"
        )

    # Retrieve evolved units
    evolved_units = []
    for evo in evolutions:
        if evo.unlocked:
            evolved_units.append(evo.name)
    evolved_units_text = "Evolved Units:\n" + "\n".join(evolved_units) if evolved_units else "No units evolved yet"

    # Check if user is an admin
    admins = get_rows("Admins")
    is_admin = any(row[0] == uid for row in admins[1:])

    await update.message.reply_text(
        f"{section_header('WAR ROOM BRIEFING', '🏰')}\n\n"
        f"Commander: {player_data['name']}\n"
        f"Faction: {player_faction}\n"
        f"Alliance: {player_data['alliance']}\n"
        f"Global Rank: #{player_data['global_rank']}\n"
        f"Level: {player_data['level']}⭐ (Exp: {player_data['experience']})\n"
        f"Last Login: {last_login}\n\n"
        f"{section_header('RESOURCES', '💰')}\n"
        f"Credits: {player_data['credits']}💰 | Minerals: {player_data['minerals']}⛏️ | Energy: {player_data['energy']}⚡\n"
        f"SkyBucks: {player_data['skybucks']}\n\n"
        f"{section_header('BASE DEFENSES', '🛡️')}\n"
        f"{defense_info}\n\n"
        f"{section_header('RESEARCH', '🔬')}\n"
        f"{research_text}\n\n"
        f"{section_header('EVOLVED UNITS', '✨')}\n"
        f"{evolved_units_text}\n\n"
        f"{section_header('ALLIANCE WAR', '⚔️')}\n"
        f"{war_status}\n\n"
        f"{section_header('BASE STATUS', '🏭')}\n"
        f"Barracks: Level {buildings_data.get('barracks', {'level': 1})['level']} ({buildings_data.get('barracks', {'production': 10})['production']}/min)\n"
        f"Factory: Level {buildings_data.get('factory', {'level': 1})['level']} ({buildings_data.get('factory', {'production': 15})['production']}/min)\n"
        f"Research Lab: Level {buildings_data.get('research_lab', {'level': 1})['level']} ({buildings_data.get('research_lab', {'production': 20})['production']}/min)\n\n"
        f"{section_header('FORCES', '⚔️')}\n"
        f"Infantry: {units_data.get('infantry', 0)}/50 👨‍✈️\n"
        f"Tanks: {units_data.get('tanks', 0)}/30 🛡️\n"
        f"Artillery: {units_data.get('artillery', 0)}/20 🚀\n\n"
        f"{section_header('CURRENT WEATHER', '🌤️')}\n"
        f"{weather_text}\n\n"
        f"{section_header('ACTIVE CHAOS EVENTS', '🌪️')}\n"
        f"{events_text}\n\n"
        f"{section_header('ENDGAME CHALLENGES', '🎯')}\n"
        f"{challenges_text}\n\n"
        f"{section_header('ACHIEVEMENTS', '🏅')}\n"
        "Use /achievements to view your progress!\n\n"
        "Use /build to construct buildings!\n"
        "Use /train to train units!\n"
        "Use /specialize to enhance your units with special abilities!\n"
        "Use /attack to conquer territories!\n"
        "Use /shop for useful items!\n"
        "Use /blackmarket for premium items!\n"
        "Use /alliance to manage alliances!\n"
        "Use /leaderboard to view rankings!\n"
        "Use /daily for daily rewards!\n"
        "Use /events to see current events!\n"
        "Use /notifications to set up notifications!\n"
        "Use /msg to send private messages!\n"
        "Use /save to save your progress!\n"
        "Use /faction to join a faction!\n"
        "Use /chaos to view or trigger chaos events!\n"
        "Use /endgame for endgame challenges!\n"
        "Use /tutorial to access the game tutorial!\n"
        "Use /weather to check current weather conditions!\n"
        "Use /evolve to evolve your units!\n"
        "Use /defensive to build defensive structures!\n"
        "Use /research to unlock advanced technologies!\n"
        "Use /war to participate in alliance wars!\n"
        f"Use /admin to access admin commands!{'' if is_admin else ' (Not an admin)'}",
        parse_mode="Markdown"
    )
