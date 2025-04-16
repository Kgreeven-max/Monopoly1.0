# src/models/bot_events/market_crash.py

import random
import logging
from datetime import datetime
from .base_event import BotEvent
from .. import db # Relative import
from ..player import Player # Relative import
from ..property import Property # Relative import
from ..game_state import GameState # Relative import

logger = logging.getLogger(__name__)

class MarketCrash(BotEvent):
    """Economic event that reduces property values temporarily"""
    
    def __init__(self, game_state, player_id):
        self.game_state = game_state
        self.bot_id = player_id
        self.bot = Player.query.get(player_id)
        self.crash_percentage = 0
        self.affected_groups = []

        if not self.bot:
            logger.warning(f"MarketCrash initiated for non-existent player_id: {player_id}")
            return

        self.crash_percentage = random.randint(10, 30)  # 10-30% reduction
        self.affected_groups = self._select_affected_groups()
    
    @staticmethod
    def is_valid(game_state, player_id):
        """Check if this event is valid in the current game state"""
        # This event is rare and should only happen when game has progressed
        if random.random() > 0.1:  # 10% chance when checked
            return False
        
        # Only trigger after several rounds
        return game_state.current_lap > 2
    
    def _select_affected_groups(self):
        """Select property groups affected by the market crash"""
        # Get all property groups
        all_groups = db.session.query(Property.group_name).distinct().all()
        all_groups = [g[0] for g in all_groups if g[0]]  # Filter out None
        if not all_groups:
            return []

        # Select a random subset of groups (1-3)
        num_affected = min(random.randint(1, 3), len(all_groups))
        
        return random.sample(all_groups, num_affected)
    
    def get_event_data(self):
        """Return data about this event"""
        if not self.bot or not self.affected_groups:
            bot_name = self.bot.username if self.bot else "A bot"
            return {
                "event_type": "market_crash",
                "success": False,
                "message": f"{bot_name} could not trigger a market crash."
            }

        groups_text = ", ".join(self.affected_groups)
        
        return {
            "event_type": "market_crash",
            "success": True,
            "bot_id": self.bot_id,
            "bot_name": self.bot.username,
            "crash_percentage": self.crash_percentage,
            "affected_groups": self.affected_groups,
            "message": f"{self.bot.username} reports economic troubles! Market crash affects {groups_text} properties. Values decreased by {self.crash_percentage}%."
        }
    
    def execute(self):
        """Apply the market crash effects"""
        if not self.affected_groups:
             return {"success": False, "message": "No groups selected for market crash."}
        
        try:
            # Apply discount to all properties in affected groups
            for group_name in self.affected_groups:
                properties = Property.query.filter_by(group_name=group_name).all()
                
                for prop in properties:
                    # Record original price before discount
                    original_price = prop.current_price
                    
                    # Apply discount
                    prop.discount_percentage = self.crash_percentage
                    
                    # Calculate new price
                    new_price = original_price * (1 - prop.discount_percentage / 100)
                    
                    # Store reduction for history/UI
                    prop.discount_amount = original_price - new_price
                    # TODO: Consider using turn count instead of timestamp for expiration?
                    prop.discount_expires_at = datetime.now().timestamp() + (3 * 60)  # 3 minutes
            
            db.session.commit()
            
            # Schedule a cleanup to restore prices
            # TODO: Move scheduling logic to a central event processor?
            game_state = GameState.get_instance()
            if hasattr(game_state, 'schedule_event'): # Check if method exists
                 game_state.schedule_event(
                     "restore_market_prices", 
                     {"affected_groups": self.affected_groups},
                     3  # 3 turns later
                 )
            else:
                 logger.warning("GameState does not have schedule_event method. Cannot schedule price restoration.")
            
            return {
                "success": True,
                "message": f"Market crash affecting {', '.join(self.affected_groups)} properties has occurred!"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing market crash: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Market crash failed due to an error: {str(e)}"
            } 