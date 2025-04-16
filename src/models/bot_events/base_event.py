# src/models/bot_events/base_event.py

import random
import logging
# Use relative imports within the module
from ..player import Player
from ..game_state import GameState

# Import subclasses for get_random_event
# Need to use try/except or check if defined later to avoid circular import at startup
# Or define events list later after all classes are defined
# from .trade_proposal import TradeProposal
# from .property_auction import PropertyAuction
# from .market_crash import MarketCrash
# from .economic_boom import EconomicBoom
# from .bot_challenge import BotChallenge
# from .market_timing import MarketTiming

logger = logging.getLogger(__name__)

class BotEvent:
    """Base class for special events that can be triggered by bots"""
    
    @staticmethod
    def get_random_event(game_state, player_id, bot_type_name=None):
        """Return a random event appropriate for the current game state"""
        
        # Import subclasses here to avoid circular import issues at module load time
        from .trade_proposal import TradeProposal
        from .property_auction import PropertyAuction
        from .market_crash import MarketCrash
        from .economic_boom import EconomicBoom
        from .bot_challenge import BotChallenge
        from .market_timing import MarketTiming
        
        # List of available events with their weights
        events = [
            (TradeProposal, 30),
            (PropertyAuction, 20),
            (MarketCrash, 10),
            (EconomicBoom, 15),
            (BotChallenge, 25),
            (MarketTiming, 20)  # Add the new MarketTiming event
        ]
        
        # Check if the bot is an OpportunisticBot using the passed type name
        player = Player.query.get(player_id)
        is_opportunistic = False
        # Ensure player exists, is a bot, and bot_type_name was provided
        if player and player.is_bot and bot_type_name == 'OpportunisticBot':
            is_opportunistic = True
        
        # Filter events based on current game state
        valid_events = []
        for event_class, weight in events:
            if event_class.is_valid(game_state, player_id):
                # Increase weight for MarketTiming if the bot is opportunistic
                if is_opportunistic and event_class == MarketTiming:
                    valid_events.append((event_class, weight * 3))  # Triple the weight
                else:
                    valid_events.append((event_class, weight))
        
        if not valid_events:
            return None
        
        # Calculate total weight
        total_weight = sum(weight for _, weight in valid_events)
        
        # Random selection based on weights
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for event_class, weight in valid_events:
            cumulative_weight += weight
            if r <= cumulative_weight:
                # Instantiate the selected event class
                return event_class(game_state, player_id)
        
        return None 