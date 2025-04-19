from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# REMOVED Explicit imports - caused circular dependency
# from .player import Player
# from .game_state import GameState
# --- End REMOVED Explicit Imports ---

# Import models that might be needed at import time by other modules
# from .team import Team # Removed from top level

# Set up logger
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

# Global instances (Removed - Instances managed via app.config)
# _banker = None
# _auction_system = None

# def get_banker(): (Removed)
#     """Get the global banker instance"""
#     global _banker
#     if _banker is None:
#         from .banker import Banker
#         _banker = Banker() # Problem: needs socketio
#     return _banker

# def get_auction_system(): (Removed)
#     """Get the global auction system instance"""
#     global _auction_system
#     if _auction_system is None:
#         from .auction_system import AuctionSystem
#         from .banker import Banker
#         from flask import current_app
#         from flask_socketio import SocketIO
#         
#         # Get the banker instance (Problematic: relies on potentially uninitialized global)
#         banker = get_banker()
#         
#         # Get the socketio instance from the current app
#         socketio = current_app.extensions['socketio']
#         
#         # Initialize the auction system with required parameters
#         _auction_system = AuctionSystem(socketio, banker)
#         
#     return _auction_system

def init_db(app):
    """Initialize database and migrations"""
    db.init_app(app)
    Migrate(app, db)
    
    # Import all models to ensure they're registered with SQLAlchemy
    import_models()
    
    logger.info("Database models initialized")
    
    return db 

def import_models():
    """Import all models to register them with SQLAlchemy"""
    # Uncommented necessary imports
    from .player import Player
    from .game_state import GameState
    from .property import Property
    from .team import Team # Added back
    from .transaction import Transaction
    from .auction import Auction
    from .auction_system import AuctionSystem
    from .bot_events import (
        BotEvent, TradeProposal, PropertyAuction, MarketCrash, EconomicBoom, BotChallenge, MarketTiming
    )
    from .special_space import Card, SpecialSpace
    from .finance.loan import Loan
    from .game_mode import GameMode
    from .game import Game # Add this import
    from .game_settings import GameSettings # Add the GameSettings model

    # logger.info("Database models initialized") # Duplicate log, removed 

# Import social models if they exist
try:
    from .social.chat import Channel, Message, ChannelMember
    from .social.alliance import Alliance, AllianceMember, AllianceInvite
    from .social.reputation import Reputation
except ImportError:
    # Handle cases where social models might not be present (e.g., simpler setup)
    pass

# Import other models as needed
# from .some_other_model import SomeOtherModel 