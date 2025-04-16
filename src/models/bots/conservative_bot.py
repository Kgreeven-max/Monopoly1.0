# src/models/bots/conservative_bot.py

import random
from .base_bot import BotPlayer
import logging

logger = logging.getLogger(__name__)

class ConservativeBot(BotPlayer):
    """Conservative bot that prioritizes cash reserves and safe investments"""
    
    def __init__(self, player_id, difficulty='normal'):
        super().__init__(player_id, difficulty)
        # Adjust parameters for conservative strategy
        # Modify the risk tolerance within the decision_maker
        if hasattr(self.decision_maker, 'risk_tolerance'): # Check if attribute exists
             self.decision_maker.risk_tolerance *= 0.7  # Lower risk tolerance
        else:
             # Log a warning if the attribute doesn't exist for some reason
             logger.warning(f"Bot {self.player_id}: Could not adjust risk_tolerance on decision_maker.")
    
    def _make_optimal_buy_decision(self, property_obj):
        """Conservative buying strategy - more cautious with money"""
        # Check if player has enough money with higher reserve
        if self.player.cash < property_obj.current_price * 1.5:
            return {
                "buy": False,
                "reason": "Insufficient funds for conservative strategy"
            }
        
        # Conservative bots want higher cash reserves
        cash_after_purchase = self.player.cash - property_obj.current_price
        min_cash_reserve = 200  # Higher minimum cash reserve
        
        if cash_after_purchase < min_cash_reserve:
            return {
                "buy": False,
                "reason": "Would deplete strategic cash reserves"
            }
        
        # Only buy if the property seems very valuable
        property_value = self._evaluate_property_value(property_obj)
        if property_value > property_obj.current_price * 1.2:
            return {
                "buy": True,
                "reason": "Property is a safe investment",
                "value_ratio": property_value / property_obj.current_price
            }
        else:
            return {
                "buy": False,
                "reason": "Property not valuable enough for conservative strategy",
                "value_ratio": property_value / property_obj.current_price
            }
    
    def decide_auction_bid(self, auction_data):
        """More conservative auction bidding strategy"""
        result = super().decide_auction_bid(auction_data)
        
        # If parent says to bid, be more conservative with amount
        # Ensure 'amount' key exists before modifying
        if result.get("bid") and "amount" in result:
            result["amount"] = int(result["amount"] * 0.8)
        
        return result 