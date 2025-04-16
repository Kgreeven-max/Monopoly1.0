# src/models/bots/shark_bot.py

import random
from .base_bot import BotPlayer
from ..player import Player # Relative import
from ..property import Property # Relative import
import logging

logger = logging.getLogger(__name__)

class SharkBot(BotPlayer):
    """Shark bot that focuses on predatory strategies and player loans"""
    
    def __init__(self, player_id, difficulty='hard'):
        # Ensure superclass is initialized first
        super().__init__(player_id, difficulty)
        
        # Aggressively increase risk tolerance after decision_maker is initialized
        if hasattr(self.decision_maker, 'risk_tolerance'):
             # Increase risk tolerance significantly, but cap it
             self.decision_maker.risk_tolerance = min(self.decision_maker.risk_tolerance * 1.4, 0.95)
        else:
             logger.warning(f"SharkBot {self.player_id}: Could not adjust risk_tolerance on decision_maker.")
        
        # Modify other parameters for shark-like behavior if needed
        # Example: Lower cash reserve threshold further? Increase development aggression?
        if hasattr(self.decision_maker, 'value_estimation_error'):
            self.decision_maker.value_estimation_error *= 0.7  # More accurate valuation
        else:
             logger.warning(f"SharkBot {self.player_id}: Could not adjust value_estimation_error on decision_maker.")
    
    def _make_optimal_buy_decision(self, property_obj):
        """Shark buying strategy - focus on blocking others and high-traffic properties"""
        # Check if player has enough money
        if self.player.cash < property_obj.current_price:
            return {
                "buy": False,
                "reason": "Cannot afford property"
            }
            
        # Shark bots are willing to spend down to a very low reserve
        cash_after_purchase = self.player.cash - property_obj.current_price
        min_cash_reserve = 50  # Very low minimum cash reserve
        
        if cash_after_purchase < min_cash_reserve:
            return {
                "buy": False,
                "reason": "Would deplete minimal cash reserves"
            }
            
        # Check if property is in a high-traffic area (properties 1-3 past GO, near Jail, etc.)
        high_traffic_positions = [2, 3, 4, 5, 12, 15, 25, 28, 35, 38, 39]
        is_high_traffic = property_obj.position in high_traffic_positions
        
        # Check if property would block a monopoly for another player
        would_block_monopoly = self._would_block_monopoly(property_obj)
        
        # Base value calculation
        property_value = self._evaluate_property_value(property_obj)
        # Avoid division by zero
        value_ratio = property_value / property_obj.current_price if property_obj.current_price > 0 else float('inf')
        
        # Sharks value blocking and high-traffic properties more
        if would_block_monopoly:
            value_ratio *= 1.3
        if is_high_traffic:
            value_ratio *= 1.2
            
        # Decision factors
        should_buy = value_ratio > 0.9 or would_block_monopoly or is_high_traffic
        
        reason = "General acquisition"
        if would_block_monopoly:
            reason = "Blocks another player's monopoly"
        elif is_high_traffic:
            reason = "High-traffic property"
            
        return {
            "buy": should_buy,
            "value_ratio": value_ratio,
            "reason": reason
        }
    
    def _would_block_monopoly(self, property_obj):
        """Check if buying this property would block another player's monopoly"""
        # Get all properties in this group
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        if len(group_properties) <= 1:
            return False
            
        # Count ownership by player
        ownership_counts = {}
        for prop in group_properties:
            if prop.id == property_obj.id:
                continue  # Skip the property we're evaluating
            if prop.owner_id is not None:
                 # Ignore self when checking block potential
                if prop.owner_id == self.player_id: 
                    continue
                if prop.owner_id not in ownership_counts:
                    ownership_counts[prop.owner_id] = 0
                ownership_counts[prop.owner_id] += 1
                
        # Check if any other player is one property away from a monopoly
        for player_id, count in ownership_counts.items():
            if count == len(group_properties) - 1:
                return True
                
        return False
    
    def decide_auction_bid(self, auction_data):
        """Shark auction bidding strategy - competitive and positional"""
        property_id = auction_data["property_id"]
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"bid": False, "reason": "Property not found"}
            
        # Check if property would block a monopoly
        would_block_monopoly = self._would_block_monopoly(property_obj)
        
        # Base valuation
        property_value = self._evaluate_property_value(property_obj)
        max_bid_base = min(property_value, self.player.cash * 0.85)
        
        # Bid more for blocking monopolies
        if would_block_monopoly:
            max_bid = min(property_value * 1.4, self.player.cash * 0.95)
        else:
            max_bid = max_bid_base
            
        # Current high bid
        current_bid = auction_data["current_bid"]
        
        # Minimum bid required
        min_bid = max(current_bid + 1, auction_data.get("minimum_bid", 1))
        
        # Shark bots are aggressive bidders - they try to outbid by meaningful increments
        if current_bid > 0:
            bid_amount = current_bid * 1.15  # 15% more than current bid
        else:
            bid_amount = min_bid
            
        # Ensure minimum increment
        bid_amount = max(bid_amount, min_bid)
        
        # Bid if within max limit and affordable
        if bid_amount <= max_bid and bid_amount <= self.player.cash:
            return {
                "bid": True,
                "amount": int(bid_amount),
                "max_willing": int(max_bid),
                "reason": "Predatory acquisition" if would_block_monopoly else "Strategic position"
            }
        else:
            reason = "Exceeds valuation threshold" if current_bid >= max_bid else "Cannot afford bid increment"
            return {
                "bid": False,
                "reason": reason
            }
    
    def perform_pre_roll_actions(self):
        """Shark bots look for opportunities to offer loans or create events"""
        actions = super().perform_pre_roll_actions()
        
        # Look for players in financial distress
        distressed_players = self._find_distressed_players()
        
        # If there are distressed players, consider predatory actions
        if distressed_players and random.random() < 0.4:  # 40% chance
            # Select a random distressed player
            target_player = random.choice(distressed_players)
            
            # Record predatory opportunity (actual loan offers would be implemented via the
            # loan system, this just logs the intention)
            actions.append({
                "action": "identify_loan_target",
                "player_id": target_player.id,
                "player_name": target_player.username,
                "reason": "Financial distress detected"
            })
            
        return actions
    
    def _find_distressed_players(self):
        """Find players with low cash who might need loans"""
        all_players = Player.query.filter(Player.in_game == True, Player.id != self.player_id).all()
        distressed_players = []
        
        for player in all_players:
            # Consider a player distressed if they have less than $200 cash
            # and own at least one property
            if player.cash < 200 and Property.query.filter_by(owner_id=player.id).count() > 0:
                distressed_players.append(player)
                
        return distressed_players 