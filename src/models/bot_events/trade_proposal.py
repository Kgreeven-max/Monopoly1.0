# src/models/bot_events/trade_proposal.py

import random
import logging
from .base_event import BotEvent
from .. import db # Relative import
from ..player import Player # Relative import
from ..property import Property # Relative import
from ..transaction import Transaction # Relative import

logger = logging.getLogger(__name__)

class TradeProposal(BotEvent):
    """Bot proposes a trade to another player"""
    
    def __init__(self, game_state, player_id):
        self.game_state = game_state
        self.bot_id = player_id
        self.bot = Player.query.get(player_id)
        self.target_player = None
        self.offered_properties = []
        self.requested_properties = []
        self.cash_amount = 0
        self.direction = "pay"
        
        if not self.bot:
            logger.warning(f"TradeProposal initiated for non-existent player_id: {player_id}")
            return

        # Find trade target (another player with properties)
        potential_targets = Player.query.filter(
            Player.in_game == True,
            Player.id != player_id
        ).all()
        
        # Filter to players who have properties
        potential_targets = [p for p in potential_targets if p.get_properties()]
        
        if not potential_targets:
             logger.info(f"TradeProposal: Bot {self.bot.username} found no valid trade targets.")
             return # Cannot initiate trade without targets

        self.target_player = random.choice(potential_targets)
        
        # If we found a target, set up the trade
        # Select properties to offer and request
        self.offered_properties = self._select_properties_to_offer()
        self.requested_properties = self._select_properties_to_request()
        
        # If either list is empty, the trade is pointless
        if not self.offered_properties and not self.requested_properties:
             logger.info(f"TradeProposal: Bot {self.bot.username} could not form a meaningful trade.")
             self.target_player = None # Invalidate the trade
             return

        # Determine cash adjustment
        self.cash_amount = self._calculate_cash_adjustment()
        
        # Set trade direction (positive = bot pays, negative = bot receives)
        if self.cash_amount < 0:
            self.direction = "receive"
            self.cash_amount = abs(self.cash_amount)
        else:
            self.direction = "pay"
    
    @staticmethod
    def is_valid(game_state, player_id):
        """Check if this event is valid in the current game state"""
        # Bot must have properties to trade
        bot = Player.query.get(player_id)
        if not bot or not bot.get_properties():
            return False
        
        # Need at least one other player with properties
        other_players_with_props = Player.query.filter(
            Player.in_game == True,
            Player.id != player_id
        ).all()
        
        return any(p.get_properties() for p in other_players_with_props)
    
    def _select_properties_to_offer(self):
        """Select properties that the bot will offer"""
        bot_properties = Property.query.filter_by(owner_id=self.bot_id).all()
        if not bot_properties:
            return []

        # Group properties by color group
        property_groups = {}
        for prop in bot_properties:
            if prop.group_name not in property_groups:
                property_groups[prop.group_name] = []
            property_groups[prop.group_name].append(prop)
        
        # Don't break monopolies unless desperate
        complete_groups = []
        incomplete_groups = []
        
        for group_name, properties in property_groups.items():
            # Get all properties in this group
            all_in_group = Property.query.filter_by(group_name=group_name).all()
            
            # Check if bot owns all properties in the group
            if len(properties) == len(all_in_group):
                complete_groups.append(group_name)
            else:
                incomplete_groups.append(group_name)
        
        # Decide which properties to offer
        offered_properties = []
        
        # Prefer offering from incomplete groups
        if incomplete_groups:
            chosen_group = random.choice(incomplete_groups)
            # Offer 1-2 properties from this group
            num_to_offer = min(random.randint(1, 2), len(property_groups[chosen_group]))
            offered_properties = random.sample(property_groups[chosen_group], num_to_offer)
        # If desperate, might offer from a complete group
        elif complete_groups and random.random() < 0.2:  # 20% chance when desperate
            chosen_group = random.choice(complete_groups)
            # Only offer 1 property from a complete group
            offered_properties = [random.choice(property_groups[chosen_group])]
        
        return offered_properties
    
    def _select_properties_to_request(self):
        """Select properties that the bot will request"""
        if not self.target_player:
             return []
        target_properties = Property.query.filter_by(owner_id=self.target_player.id).all()
        if not target_properties:
             return []

        # Look for properties that would complete a group for the bot
        bot_properties = Property.query.filter_by(owner_id=self.bot_id).all()
        bot_groups = {}
        
        for prop in bot_properties:
            if prop.group_name not in bot_groups:
                bot_groups[prop.group_name] = []
            bot_groups[prop.group_name].append(prop)
        
        # Find groups where bot is close to a monopoly
        strategic_properties = []
        for prop in target_properties:
            if prop.group_name in bot_groups:
                # Count how many properties in this group
                all_in_group = Property.query.filter_by(group_name=prop.group_name).all()
                bot_owned = len(bot_groups[prop.group_name])
                
                # If this property would complete or advance a monopoly
                if len(all_in_group) > 0 and (bot_owned + 1 == len(all_in_group) or bot_owned >= len(all_in_group) / 2):
                    strategic_properties.append(prop)
        
        # If we found strategic properties, prioritize those
        if strategic_properties:
            # Request 1-2 strategic properties
            num_to_request = min(random.randint(1, 2), len(strategic_properties))
            return random.sample(strategic_properties, num_to_request)
        
        # Otherwise, request random properties
        num_to_request = min(random.randint(1, 2), len(target_properties))
        return random.sample(target_properties, num_to_request)
    
    def _calculate_cash_adjustment(self):
        """Calculate cash adjustment for the trade"""
        offered_value = sum(p.current_price for p in self.offered_properties)
        requested_value = sum(p.current_price for p in self.requested_properties)
        
        # Base adjustment on property value difference
        difference = requested_value - offered_value
        
        # Add some randomness to make trades interesting
        randomness = random.uniform(-0.2, 0.2)  # +/- 20%
        adjustment = difference * (1 + randomness)
        
        # Round to nearest 10
        return round(adjustment / 10) * 10
    
    def get_event_data(self):
        """Return data about this event"""
        if not self.target_player or not self.bot: # Ensure bot and target exist
            bot_name = self.bot.username if self.bot else "A bot"
            return {
                "event_type": "trade_proposal",
                "success": False,
                "message": f"{bot_name} wanted to trade but couldn't find a suitable player or trade."
            }
        
        return {
            "event_type": "trade_proposal",
            "success": True,
            "bot_id": self.bot_id,
            "bot_name": self.bot.username,
            "target_player_id": self.target_player.id,
            "target_player_name": self.target_player.username,
            "offered_properties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "value": p.current_price
                } for p in self.offered_properties
            ],
            "requested_properties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "value": p.current_price
                } for p in self.requested_properties
            ],
            "cash_amount": self.cash_amount,
            "cash_direction": self.direction,
            "message": self._generate_message()
        }
    
    def _generate_message(self):
        """Generate a message describing the trade"""
        if not self.bot or not self.target_player:
             return "Invalid trade proposal."

        # List properties being offered
        if self.offered_properties:
            offered_list = ", ".join(p.name for p in self.offered_properties)
        else:
            offered_list = "nothing"
        
        # List properties being requested
        if self.requested_properties:
            requested_list = ", ".join(p.name for p in self.requested_properties)
        else:
            requested_list = "nothing"
        
        # Add cash details
        if self.cash_amount > 0:
            if self.direction == "pay":
                cash_text = f" plus ${self.cash_amount}"
            else:
                cash_text = f" and requests ${self.cash_amount}"
        else:
            cash_text = ""
        
        return f"{self.bot.username} offers {offered_list}{cash_text} in exchange for {requested_list}."
    
    def execute(self, accept=False):
        """Execute the trade if accepted"""
        if not accept or not self.target_player or not self.bot:
            bot_name = self.bot.username if self.bot else "A bot"
            return {
                "success": False,
                "message": f"Trade offer from {bot_name} was declined or became invalid."
            }
        
        try:
            # Validate cash amounts before proceeding
            if self.direction == "pay" and self.bot.cash < self.cash_amount:
                 return {"success": False, "message": f"{self.bot.username} does not have enough cash (${self.cash_amount}) for the trade."}
            if self.direction == "receive" and self.target_player.cash < self.cash_amount:
                 return {"success": False, "message": f"{self.target_player.username} does not have enough cash (${self.cash_amount}) for the trade."}

            # Transfer properties
            for prop in self.offered_properties:
                prop.owner_id = self.target_player.id
            
            for prop in self.requested_properties:
                prop.owner_id = self.bot_id
            
            # Transfer cash
            if self.cash_amount > 0:
                if self.direction == "pay":
                    # Bot pays target
                    self.bot.cash -= self.cash_amount
                    self.target_player.cash += self.cash_amount
                    from_id, to_id = self.bot_id, self.target_player.id
                    description = f"Trade payment to {self.target_player.username}"
                else:
                    # Target pays bot
                    self.target_player.cash -= self.cash_amount
                    self.bot.cash += self.cash_amount
                    from_id, to_id = self.target_player.id, self.bot_id
                    description = f"Trade payment to {self.bot.username}"
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=from_id,
                    to_player_id=to_id,
                    amount=self.cash_amount,
                    transaction_type="trade",
                    description=description
                )
                db.session.add(transaction)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Trade between {self.bot.username} and {self.target_player.username} completed successfully."
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing trade: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Trade failed due to an error: {str(e)}"
            } 