# stub for telegram package
class Update:
    pass

class BotCommand:
    def __init__(self, command, description):
        self.command = command
        self.description = description

class InlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url

class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard):
        self.inline_keyboard = inline_keyboard
