from telegram.ext import Application, CommandHandler
import handlers.start as start
import handlers.player as player
import handlers.resource as resource
import handlers.army as army
import handlers.zones as zones
import handlers.combat as combat
import handlers.research as research
import handlers.missions as missions
import handlers.ranking as ranking
import handlers.admin as admin  # 🔥 NEW import for Admin Tools

import os

TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(TOKEN).build()

# Existing Handlers
app.add_handler(CommandHandler("start", start.start))
app.add_handler(CommandHandler("status", player.status))
app.add_handler(CommandHandler("daily", resource.daily))
app.add_handler(CommandHandler("mine", resource.mine))
app.add_handler(CommandHandler("collect", resource.collect))
app.add_handler(CommandHandler("scan", zones.scan))
app.add_handler(CommandHandler("attack", combat.attack))
app.add_handler(CommandHandler("help", start.help))

# Army Handlers
app.add_handler(CommandHandler("forge", army.forge))
app.add_handler(CommandHandler("army", army.army))

# Research Handlers
app.add_handler(CommandHandler("research", research.research))
app.add_handler(CommandHandler("tech", research.tech))

# Zone Handlers
app.add_handler(CommandHandler("claim", zones.claim))
app.add_handler(CommandHandler("zone", zones.zone))
app.add_handler(CommandHandler("map", zones.map))

# Combat Handler
app.add_handler(CommandHandler("shield", combat.shield))

# Mission Handlers
app.add_handler(CommandHandler("missions", missions.missions))
app.add_handler(CommandHandler("claimmission", missions.claim))

# Ranking Handler
app.add_handler(CommandHandler("rank", ranking.rank))

# 🔥 Admin Tools Handlers
app.add_handler(CommandHandler("givegold", admin.givegold))
app.add_handler(CommandHandler("wipeplayer", admin.wipeplayer))
app.add_handler(CommandHandler("shieldforce", admin.shieldforce))

if __name__ == "__main__":
    app.run_polling()
