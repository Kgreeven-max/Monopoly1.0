# src/models/bots/aggressive_bot.py

import random
from .base_bot import BotPlayer

class AggressiveBot(BotPlayer):
    """Aggressive bot that prioritizes property acquisition and development"""
    
    def __init__(self, player_id, difficulty='normal'):
        super().__init__(player_id, difficulty)
        # Adjust parameters for aggressive strategy
        self.risk_tolerance *= 1.3  # Higher risk tolerance
    
    def _make_optimal_buy_decision(self, property_obj):
        """Aggressive buying strategy - focus on acquiring properties"""
        # Check if player has bare minimum money
        if self.player.cash < property_obj.current_price:
            return {
                "buy": False,
                "reason": "Cannot afford property"
            }
        
        # Aggressive bots are willing to spend down to a lower reserve
        cash_after_purchase = self.player.cash - property_obj.current_price
        min_cash_reserve = 50  # Lower minimum cash reserve
        
        if cash_after_purchase < min_cash_reserve:
            return {
                "buy": False,
                "reason": "Would deplete minimal cash reserves"
            }
        
        # Buy more readily, even if the value isn't optimal
        property_value = self._evaluate_property_value(property_obj)
        if property_value > property_obj.current_price * 0.8:
            return {
                "buy": True,
                "reason": "Property acquisition priority",
                "value_ratio": property_value / property_obj.current_price
            }
        else:
            return {
                "buy": False,
                "reason": "Property significantly undervalued",
                "value_ratio": property_value / property_obj.current_price
            }
    
    def decide_auction_bid(self, auction_data):
        """More aggressive auction bidding strategy"""
        result = super().decide_auction_bid(auction_data)
        
        # If parent says to bid, be more aggressive with amount
        if result.get("bid") and "amount" in result:
            # Need max_willing from the parent method's result dictionary
            max_willing = result.get("max_willing", result["amount"] * 1.5) # Estimate if missing
            result["amount"] = min(
                int(result["amount"] * 1.2),
                max_willing # Use the max_willing value from parent call if available
            )
        
        return result 