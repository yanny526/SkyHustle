"""
Scheduler for SkyHustle.
Manages game ticks, timed events, and periodic tasks.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any 