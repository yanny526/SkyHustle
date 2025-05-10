# telegram/ext/__init__.py

class Application:
    """Stub of the high-level Application builder."""
    @classmethod
    def builder(cls):
        return cls()
    def token(self, token: str):
        return self
    def build(self):
        return self
    def run_polling(self):
        # No-op in stub
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

# Simple filter stub so you can write filters.TEXT & ~filters.COMMAND
class _FilterStub:
    def __and__(self, other): return self
    def __invert__(self): return self

filters = type('filters', (), {'TEXT': _FilterStub(), 'COMMAND': _FilterStub()})()
