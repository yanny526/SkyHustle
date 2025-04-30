import datetime
 from utils.ui_helpers import render_status_panel
 from utils import google_sheets
 

 # In-memory mining tracker
 player_mining = {}  # player_id: {resource: {amount: x, end_time: time}}
 

 # Resources per minute
 MINING_SPEEDS = {
  "metal": 100,
  "fuel": 60,
  "crystal": 30,
 }
 

 async def start_mining(update, context):
  pid = str(update.effective_user.id)
  panel = render_status_panel(pid)
  args = context.args or []
 

  if len(args) != 2:
  return await update.message.reply_text(
  "⛏️ Usage: /mine [resource] [amount]\\nExample: /mine metal 1000\\n\\n"
  + panel
  )
 

  res = args[0].lower()
  try:
  amt = int(args[1])
  except:
  return await update.message.reply_text(
  "⚡ Amount must be a number.\\n\\n" + panel
  )
 

  if res not in MINING_SPEEDS:
  return await update.message.reply_text(
  "❌ Invalid resource. Available: metal, fuel, crystal.\\n\\n"
  + panel
  )
 

  # Schedule
  speed = MINING_SPEEDS[res]
  mins = amt / speed
  delta = datetime.timedelta(minutes=mins)
  end_time = datetime.datetime.now() + delta
  end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
 

  pm = player_mining.get(pid, {})
  pm[res] = {"amount": amt, "end_time": end_str}
  player_mining[pid] = pm  # Update the player_mining dictionary
 

  await update.message.reply_text(
  f"⛏️ Mining {amt} {res.capitalize()}... (ends {end_str})\\n\\n" + panel
  )
 

 async def mining_status(update, context):
  pid = str(update.effective_user.id)
  panel = render_status_panel(pid)
  pm = player_mining.get(pid, {})
 

  if not pm:
  return await update.message.reply_text(
  "❌ Not currently mining anything.\\n\\n" + panel
  )
 

  lines = ["⛏️ Current Mining Operations:"]
  now = datetime.datetime.now()
  for res, info in pm.items():
  end_time = datetime.datetime.strptime(
  info["end_time"], "%Y-%m-%d %H:%M:%S"
  )
  rem = end_time - now
  if rem.total_seconds() <= 0:
  lines.append(
  f"✅ {res.capitalize()} ready to claim ({info['amount']})."
  )
  else:
  m, s = divmod(int(rem.total_seconds()), 60)
  lines.append(f"⏳ {res.capitalize()}: {m}m{s}s remaining.")
 

  await update.message.reply_text("\n".join(lines) + "\n\n" + panel)
 

 async def claim_mining(update, context):
  pid = str(update.effective_user.id)
  panel = render_status_panel(pid)
  pm = player_mining.get(pid, {})
 

  if not pm:
  return await update.message.reply_text(
  "❌ Nothing to claim.\\n\\n" + panel
  )
 

  now = datetime.datetime.now()
  claimed = {}
  for res, info in list(pm.items()):
  end_time = datetime.datetime.strptime(
  info["end_time"], "%Y-%m-%d %H:%M:%S"
  )
  if now >= end_time:
  claimed[res] = info["amount"]
  del pm[res]
 

  if not claimed:
  return await update.message.reply_text(
  "⏳ Still mining—no resources ready.\\n\\n" + panel
  )
 

  # Add to Google Sheets
  resources = google_sheets.load_resources(pid)
  for res, amt in claimed.items():
  resources[res] = resources.get(res, 0) + amt
  google_sheets.save_resources(pid, resources)
 

  claimed_str = ", ".join(
  f"{amt} {res.capitalize()}" for res, amt in claimed.items()
  )
  await update.message.reply_text(f"✅ Claimed: {claimed_str}\\n\\n" + panel)
