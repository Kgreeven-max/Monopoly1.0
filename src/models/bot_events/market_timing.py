# src/models/bot_events/market_timing.py

import random
import logging
from datetime import datetime
from .base_event import BotEvent
from .. import db # Relative import
from ..player import Player # Relative import
from ..property import Property # Relative import

logger = logging.getLogger(__name__)

class MarketTiming(BotEvent):
    """Event where a bot predicts market changes and creates an investment opportunity"""
    
    def __init__(self, game_state, player_id):
        self.game_state = game_state
        self.bot_id = player_id
        self.bot = Player.query.get(player_id)
        self.opportunity_type = None
        self.affected_groups = []
        self.price_change = 0.0
        self.duration = 0
        self.created_at = None

        if not self.bot or not self.game_state:
            logger.warning(f"MarketTiming initiated for non-existent player/game state: {player_id}")
            return

        # Determine if this is a buying or selling opportunity
        self.opportunity_type = self._determine_opportunity_type()
        
        # Select property group(s) that will be affected
        self.affected_groups = self._select_affected_groups()
        if not self.affected_groups:
             logger.info(f"MarketTiming: Could not select affected groups.")
             self.opportunity_type = None # Invalidate event
             return

        # Calculate price change percentage
        self.price_change = self._calculate_price_change()
        
        # Duration of the opportunity (in turns)
        self.duration = random.randint(2, 4)
        
        # Record creation time
        self.created_at = datetime.now().isoformat()
    
    @staticmethod
    def is_valid(game_state, player_id):
        """Check if this event is valid in the current game state"""
        # Event should only happen after at least 10 turns
        if game_state.current_lap < 2:
            return False
        
        # Need at least 3 properties owned by players
        owned_properties = Property.query.filter(Property.owner_id.isnot(None)).count()
        return owned_properties >= 3
    
    def _determine_opportunity_type(self):
        """Determine if this is a buying or selling opportunity"""
        # Check current economic state
        economic_state = self.game_state.inflation_state
        
        if economic_state in ["recession", "depression"]:
            # During recession, more likely to be a buying opportunity
            return "buy" if random.random() < 0.8 else "sell"
        elif economic_state in ["boom", "growth"]:
            # During boom, more likely to be a selling opportunity
            return "sell" if random.random() < 0.7 else "buy"
        else:
            # In normal state, equal chance
            return "buy" if random.random() < 0.5 else "sell"
    
    def _select_affected_groups(self):
        """Select property groups that will be affected by the market timing event"""
        # Get all property groups with at least one property owned
        owned_properties = Property.query.filter(Property.owner_id.isnot(None)).all()
        groups = set(p.group_name for p in owned_properties if p.group_name)
        if not groups:
            return []
        
        # Select 1-2 groups randomly
        num_groups = min(len(groups), random.randint(1, 2))
        return random.sample(list(groups), num_groups)
    
    def _calculate_price_change(self):
        """Calculate the price change percentage for the affected properties"""
        base_change = 0.0
        
        if self.opportunity_type == "buy":
            # For buying opportunities, prices will decrease then rise
            base_change = -random.uniform(0.15, 0.25)  # 15-25% price drop
        else:
            # For selling opportunities, prices will increase then fall
            base_change = random.uniform(0.15, 0.30)  # 15-30% price increase
        
        return base_change
    
    def get_event_data(self):
        """Return data about this event"""
        if not self.bot or not self.opportunity_type or not self.affected_groups:
            return {"success": False, "message": "Invalid MarketTiming event state."}

        return {
            "event_type": "market_timing",
            "success": True, # Indicate event data is valid
            "bot_id": self.bot_id,
            "bot_name": self.bot.username,
            "opportunity_type": self.opportunity_type,
            "affected_groups": self.affected_groups,
            "price_change": self.price_change,
            "duration": self.duration,
            "created_at": self.created_at,
            "message": self._generate_message()
        }
    
    def _generate_message(self):
        """Generate a message for the event"""
        if not self.bot or not self.opportunity_type or not self.affected_groups:
             return "Market timing event prediction failed."

        bot_name = self.bot.username
        
        if self.opportunity_type == "buy":
            action_phrase = "predicts a temporary downturn"
            advice = "now might be a good time to buy"
        else:
            action_phrase = "predicts a temporary boom"
            advice = "consider selling before the market adjusts"
            
        groups_text = ", ".join(self.affected_groups)
        percent = abs(int(self.price_change * 100))
        
        return f"{bot_name} {action_phrase} in the {groups_text} markets! " \
               f"Prices are expected to change by approximately {percent}% - {advice}."
    
    def execute(self):
        """Execute the market timing event"""
        if not self.bot or not self.opportunity_type or not self.affected_groups:
            return {"success": False, "message": "Cannot execute invalid MarketTiming event."}

        try:
            # Get all properties in the affected groups
            affected_properties = Property.query.filter(
                Property.group_name.in_(self.affected_groups)
            ).all()
            
            # Apply price changes
            property_updates = []
            for prop in affected_properties:
                original_price = prop.current_price
                
                # Apply price change
                new_price = int(original_price * (1 + self.price_change))
                
                # Ensure minimum price (e.g., 50% of base price)
                min_price = int(prop.base_price * 0.5) if prop.base_price else 10 # Default min if base is 0
                new_price = max(new_price, min_price)
                
                # Update property price
                prop.current_price = new_price
                
                # Record update
                property_updates.append({
                    "property_id": prop.id,
                    "property_name": prop.name,
                    "old_price": original_price,
                    "new_price": new_price,
                    "change_percent": int(self.price_change * 100)
                })
            
            # Create a temporary effect to restore prices later
            # Use game_state's temporary effects mechanism
            if self.game_state.temporary_effects is None:
                self.game_state.temporary_effects = [] # Initialize if needed
                
            # Add the restoration effect for later
            restoration_effect = {
                "type": "restore_property_prices",
                "affected_groups": self.affected_groups,
                "opportunity_type": self.opportunity_type,
                "remaining_turns": self.duration,
                "price_change": -self.price_change,  # Reverse the change when restoring
                "created_by": self.bot_id
            }
            
            # Store in game state (accessing property setter)
            temp_effects = self.game_state.temporary_effects # Get current list
            temp_effects.append(restoration_effect)
            self.game_state.temporary_effects = temp_effects # Trigger setter
            
            # Commit changes including temporary effects update
            db.session.add(self.game_state) # Add game_state to session if needed
            db.session.commit()
            
            return {
                "success": True,
                "affected_properties": len(property_updates),
                "opportunity_type": self.opportunity_type,
                "property_updates": property_updates,
                "message": self._generate_message()
            }
        except Exception as e:
             db.session.rollback()
             logger.error(f"Error executing MarketTiming event: {e}", exc_info=True)
             return {"success": False, "message": f"MarketTiming execution failed: {str(e)}"} 