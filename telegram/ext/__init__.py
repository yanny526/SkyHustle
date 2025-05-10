# telegram/ext/__init__.py

class Application:
    """Stub of the high-level Application builder."""
    def __init__(self):
        # In real life app.bot is the Bot instance
        self.bot = self

    @classmethod
    def builder(cls):
        # Builder pattern: Application.builder().token(...).build()
        class Builder:
            def __init__(self):
                self._token = None
            def token(self, token: str):
                self._token = token
                return self
            def build(self):
                return Application()
        return Builder()

    def run_polling(self):
        # No-op stub
        pass

    def add_handler(self, handler):
        # Stub for registering handlers
        pass

    def set_my_commands(self, commands):
        # Stub for setting bot commands
        pass

class CommandHandler:
    """Stub for handling slash commands."""
    def __init__(self, command: str, callback):
        self.command = command
        self.callback = callback

class CallbackQueryHandler:
    """Stub for callback query handlers."""
    def __init__(self, callback, pattern=None):
        self.callback = callback
        self.pattern = pattern

class MessageHandler:
    """Stub for message handlers."""
    def __init__(self, filters, callback):
        self.filters = filters
        self.callback = callback

class JobQueue:
    """Stub for scheduling jobs."""
    pass

class ContextTypes:
    """Stub for context types."""
    DEFAULT_TYPE = None

# Simple filter stub to allow `filters.TEXT & ~filters.COMMAND`
class _FilterStub:
    def __and__(self, other): return self
    def __invert__(self): return self

filters = type('filters', (), {'TEXT': _FilterStub(), 'COMMAND': _FilterStub()})()
