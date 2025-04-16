# src/models/bots/strategic_bot.py

import random
from .base_bot import BotPlayer
from ..property import Property # Relative import

class StrategicBot(BotPlayer):
    """Strategic bot that focuses on monopolies and property groups"""
    
    def __init__(self, player_id, difficulty='normal'):
        super().__init__(player_id, difficulty)
        # Adjust parameters for strategic focus
        self.planning_horizon += 1  # Longer planning horizon
    
    def _evaluate_property_value(self, property_obj):
        """Strategic bots value properties based on monopoly potential"""
        base_value = super()._evaluate_property_value(property_obj)
        
        # Check how many properties in this group we already own
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        owned_in_group = 0
        for prop in group_properties:
            if prop.owner_id == self.player_id:
                owned_in_group += 1
        
        # Calculate monopoly potential (0 to 1)
        monopoly_potential = owned_in_group / (len(group_properties) - 1) if len(group_properties) > 1 else 0
        
        # Strategic bots highly value properties that would complete a monopoly
        if owned_in_group == len(group_properties) - 1:
            # Last property to complete a monopoly is worth double
            return base_value * 2
        
        # Properties that advance toward a monopoly get a proportional boost
        return base_value * (1 + monopoly_potential)
    
    def _make_optimal_buy_decision(self, property_obj):
        """Strategic buying focused on completing monopolies"""
        # Check if player has enough money
        if self.player.cash < property_obj.current_price:
            return {
                "buy": False,
                "reason": "Cannot afford property"
            }
        
        # Check how many properties in this group we already own
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        owned_in_group = 0
        for prop in group_properties:
            if prop.owner_id == self.player_id:
                owned_in_group += 1
                
        # Strong preference for properties that would complete a monopoly
        if owned_in_group == len(group_properties) - 1:
            return {
                "buy": True,
                "reason": "Would complete a monopoly"
            }
        
        # Calculate monopoly potential
        monopoly_potential = owned_in_group / len(group_properties) if len(group_properties) > 0 else 0
        
        # Make decision based on monopoly potential and value
        property_value = self._evaluate_property_value(property_obj)
        # Avoid division by zero if price is 0 (though unlikely)
        value_ratio = property_value / property_obj.current_price if property_obj.current_price > 0 else float('inf')
        
        # Higher value ratio threshold for properties that don't advance monopolies
        buy_threshold = 1.1 - (monopoly_potential * 0.3)
        
        if value_ratio > buy_threshold:
            return {
                "buy": True,
                "reason": f"Advances monopoly strategy with potential {monopoly_potential:.2f}",
                "value_ratio": value_ratio
            }
        else:
            return {
                "buy": False,
                "reason": f"Doesn't fit strategic monopoly plan",
                "value_ratio": value_ratio
            }
    
    def decide_auction_bid(self, auction_data):
        """Strategic auction bidding focused on monopolies"""
        property_id = auction_data["property_id"]
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"bid": False, "reason": "Property not found"}
            
        # Check how many properties in this group we already own
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        owned_in_group = 0
        for prop in group_properties:
            if prop.owner_id == self.player_id:
                owned_in_group += 1
                
        # Base valuation
        property_value = self._evaluate_property_value(property_obj)
        max_bid_base = min(property_value, self.player.cash * 0.8)
        
        # Would complete a monopoly? Bid more aggressively
        if len(group_properties) > 0 and owned_in_group == len(group_properties) - 1:
            max_bid = min(property_value * 1.5, self.player.cash * 0.9)
        else:
            max_bid = max_bid_base # Use base valuation if not completing monopoly
            
        # Current high bid
        current_bid = auction_data["current_bid"]
        
        # Determine bid increment based on auction phase
        if property_obj.current_price > 0: # Avoid division by zero
            if current_bid < property_obj.current_price * 0.5:
                increment = property_obj.current_price * 0.1
            else:
                increment = property_obj.current_price * 0.05
            increment = max(10, increment) # Minimum increment
        else:
             increment = 10 # Default increment if price is 0
            
        # Calculate bid
        bid_amount = current_bid + increment
        
        # Bid if within max limit and affordable
        if bid_amount <= max_bid and bid_amount <= self.player.cash: # Ensure bot can afford the bid
            return {
                "bid": True,
                "amount": int(bid_amount),
                "max_willing": int(max_bid),
                "reason": f"Strategic value for monopoly: {owned_in_group}/{len(group_properties)}"
            }
        else:
            # Check if the current bid exceeds the calculated max_bid
            reason = "Exceeds strategic valuation" if current_bid >= max_bid else "Cannot afford bid increment"
            return {
                "bid": False,
                "reason": reason
            } 