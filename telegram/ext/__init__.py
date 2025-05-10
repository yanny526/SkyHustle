
# stub
class Application:
    @classmethod
    def builder(cls): return cls()
    def token(self, token): return self
    def build(self): return self
    def run_polling(self): pass
class CommandHandler: pass
class MessageHandler: pass
filters = type('flt', (), {'TEXT': None, 'COMMAND': None})()
class ContextTypes: DEFAULT_TYPE = None
