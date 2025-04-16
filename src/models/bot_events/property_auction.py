# src/models/bot_events/property_auction.py

import random
import logging
from flask import current_app
from .base_event import BotEvent
from ..player import Player # Relative import
from ..property import Property # Relative import

logger = logging.getLogger(__name__)

class PropertyAuction(BotEvent):
    """Bot initiates an auction for one of its properties"""
    
    def __init__(self, game_state, player_id):
        self.game_state = game_state
        self.bot_id = player_id
        self.bot = Player.query.get(player_id)
        self.property = None
        self.minimum_bid = 0
        
        if not self.bot:
            logger.warning(f"PropertyAuction initiated for non-existent player_id: {player_id}")
            return

        # Select a property to auction
        self.property = self._select_property()
        if self.property:
            self.minimum_bid = self._calculate_minimum_bid()
        else:
            logger.info(f"PropertyAuction: Bot {self.bot.username} has no suitable properties to auction.")

    @staticmethod
    def is_valid(game_state, player_id):
        """Check if this event is valid in the current game state"""
        # Need at least 2 players in the game
        active_players = Player.query.filter_by(in_game=True).count()
        if active_players < 2:
            return False
        
        # Bot must have at least one property
        bot_properties = Property.query.filter_by(owner_id=player_id).count()
        return bot_properties > 0
    
    def _select_property(self):
        """Select a property for auction"""
        bot_properties = Property.query.filter_by(owner_id=self.bot_id).all()
        if not bot_properties:
            return None

        # Group properties by color group
        property_groups = {}
        for prop in bot_properties:
            if prop.group_name not in property_groups:
                property_groups[prop.group_name] = []
            property_groups[prop.group_name].append(prop)
        
        # Never auction properties in a monopoly
        monopoly_groups = []
        non_monopoly_groups = []
        
        for group_name, properties in property_groups.items():
            # Get all properties in this group
            all_in_group = Property.query.filter_by(group_name=group_name).all()
            
            # Check if bot owns all properties in the group
            if len(all_in_group) > 0 and len(properties) == len(all_in_group):
                monopoly_groups.append(group_name)
            else:
                non_monopoly_groups.append(group_name)
        
        # Select from non-monopoly properties
        auction_candidates = []
        for group in non_monopoly_groups:
            if group in property_groups:
                 auction_candidates.extend(property_groups[group])
        
        # If no suitable properties, return None
        if not auction_candidates:
            return None
        
        # Choose a property to auction
        return random.choice(auction_candidates)
    
    def _calculate_minimum_bid(self):
        """Calculate minimum bid for the property"""
        if not self.property:
            return 0
        
        # Base minimum bid on property value
        base_value = self.property.current_price
        
        # Add premium for developed properties
        if self.property.improvement_level > 0:
            base_value += self.property.improvement_level * 50
        
        # Set minimum slightly below market value to attract bidders
        minimum = int(base_value * 0.8)
        
        # Round to nearest 10
        return max(10, round(minimum / 10) * 10)
    
    def get_event_data(self):
        """Return data about this event"""
        if not self.property or not self.bot:
            bot_name = self.bot.username if self.bot else "A bot"
            return {
                "event_type": "property_auction",
                "success": False,
                "message": f"{bot_name} considered auctioning a property but changed their mind."
            }
        
        return {
            "event_type": "property_auction",
            "success": True,
            "bot_id": self.bot_id,
            "bot_name": self.bot.username,
            "property_id": self.property.id,
            "property_name": self.property.name,
            "minimum_bid": self.minimum_bid,
            "message": f"{self.bot.username} is auctioning {self.property.name} with a minimum bid of ${self.minimum_bid}!"
        }
    
    def execute(self):
        """Initiate the auction"""
        if not self.property:
            return {
                "success": False,
                "message": "No property selected for auction."
            }
        
        try:
            # Get the auction system
            auction_system = current_app.config.get('auction_system')
            if not auction_system:
                logger.error("Auction system not found in app config during PropertyAuction event.")
                return {
                    "success": False,
                    "message": "Auction system not available."
                }
            
            # Create an auction
            result = auction_system.create_auction(
                property_id=self.property.id,
                seller_id=self.bot_id,
                minimum_bid=self.minimum_bid,
                auction_type="bot_initiated"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error initiating auction: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to start auction: {str(e)}"
            } 