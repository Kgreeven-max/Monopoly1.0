# src/models/bots/__init__.py

# Make bot classes available for easier import
from .base_bot import BotPlayer
from .conservative_bot import ConservativeBot
from .aggressive_bot import AggressiveBot
from .strategic_bot import StrategicBot
from .opportunistic_bot import OpportunisticBot
from .shark_bot import SharkBot
from .investor_bot import InvestorBot

__all__ = [
    'BotPlayer',
    'ConservativeBot',
    'AggressiveBot',
    'StrategicBot',
    'OpportunisticBot',
    'SharkBot',
    'InvestorBot'
] 