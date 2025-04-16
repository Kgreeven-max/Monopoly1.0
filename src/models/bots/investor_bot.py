# src/models/bots/investor_bot.py

import random
from .base_bot import BotPlayer
from ..property import Property # Relative import
from ..game_state import GameState # Relative import
import logging # Import logging

logger = logging.getLogger(__name__) # Add logger

class InvestorBot(BotPlayer):
    """Investor bot that focuses on financial instruments over properties"""
    
    def __init__(self, player_id, difficulty='normal'):
        super().__init__(player_id, difficulty)
        # Adjust parameters for financial focus
        if hasattr(self.decision_maker, 'value_estimation_error'):
             self.decision_maker.value_estimation_error *= 0.6  # Much more accurate valuation
        else:
             logger.warning(f"Bot {self.player_id}: Could not adjust value_estimation_error on decision_maker.")
             
        if hasattr(self.decision_maker, 'planning_horizon'):
             self.decision_maker.planning_horizon += 2  # Long-term planning
        else:
             logger.warning(f"Bot {self.player_id}: Could not adjust planning_horizon on decision_maker.")
    
    def _make_optimal_buy_decision(self, property_obj):
        """Investor buying strategy - focus on ROI and property value growth"""
        # Check if player has enough money
        if self.player.cash < property_obj.current_price:
            return {
                "buy": False,
                "reason": "Cannot afford property"
            }
            
        # Calculate expected ROI
        expected_roi = self._calculate_property_roi(property_obj)
        
        # Investors maintain a larger cash reserve for financial instruments
        cash_after_purchase = self.player.cash - property_obj.current_price
        min_cash_reserve = 400  # Higher cash reserve for investments
        
        if cash_after_purchase < min_cash_reserve:
            return {
                "buy": False,
                "reason": "Would deplete investment reserves"
            }
            
        # Investors are selective and only buy properties with high ROI
        if expected_roi > 0.15:  # 15% ROI threshold
            return {
                "buy": True,
                "reason": f"High ROI investment: {expected_roi:.1%}",
                "roi": expected_roi
            }
        else:
            return {
                "buy": False,
                "reason": f"Insufficient ROI: {expected_roi:.1%}",
                "roi": expected_roi
            }
    
    def _calculate_property_roi(self, property_obj):
        """Calculate expected Return on Investment for a property"""
        # Base rent is the primary income
        annual_income = property_obj.current_rent * 3  # Estimate landing 3 times per game cycle
        
        # Factor in improvement potential
        if self._can_improve_property(property_obj):
            # Improvement increases rent substantially
            improved_rent = property_obj.current_rent * 3.5  # Typical rent multiplier
            annual_income = improved_rent * 3
            
            # Factor in improvement costs
            improvement_cost = property_obj.current_price * 0.5  # Typical improvement cost
            total_investment = property_obj.current_price + improvement_cost
        else:
            total_investment = property_obj.current_price
            
        # Calculate ROI
        # Avoid division by zero
        roi = annual_income / total_investment if total_investment > 0 else 0 
        
        # Adjust for economic phase
        game_state = GameState.query.first()
        if game_state:
            if game_state.inflation_state == "recession":
                roi *= 0.8  # Lower ROI during recession
            elif game_state.inflation_state == "boom":
                roi *= 1.2  # Higher ROI during boom
            
        return roi
    
    def _can_improve_property(self, property_obj):
        """Check if a property could be improved (has a complete color set)"""
        # Get all properties in this group
        group_properties = Property.query.filter_by(group_name=property_obj.group_name).all()
        
        # Check if all are owned by this player or would be after this purchase
        for prop in group_properties:
            if prop.id == property_obj.id:
                continue  # This is the property we're considering buying
            if prop.owner_id != self.player_id:
                return False
                
        return True
    
    def decide_auction_bid(self, auction_data):
        """Investor auction bidding strategy - ROI focused"""
        property_id = auction_data["property_id"]
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"bid": False, "reason": "Property not found"}
            
        # Calculate expected ROI
        expected_roi = self._calculate_property_roi(property_obj)
            
        # Base ROI valuation - investors are willing to pay more for high ROI properties
        # but have a strict upper limit based on calculated value
        if expected_roi > 0.2:  # Excellent ROI
            roi_multiplier = 1.2
        elif expected_roi > 0.15:  # Good ROI
            roi_multiplier = 1.1
        elif expected_roi > 0.1:  # Average ROI
            roi_multiplier = 1.0
        else:  # Below average ROI
            roi_multiplier = 0.8
            
        # Calculate maximum bid based on property value and ROI
        property_value = self._evaluate_property_value(property_obj)
        max_bid = min(property_value * roi_multiplier, self.player.cash * 0.7)
        
        # Current high bid
        current_bid = auction_data["current_bid"]
        
        # Minimum bid required
        min_bid = max(current_bid + 1, auction_data.get("minimum_bid", 1))
        
        # Calculate bid amount - investors bid incrementally and precisely
        if current_bid > 0 and property_value > 0: # Avoid division by zero
            # Calculate how far along the auction is relative to property value
            auction_progress = current_bid / property_value
            
            if auction_progress < 0.5:  # Early in auction
                bid_amount = current_bid * 1.1  # 10% increment
            elif auction_progress < 0.8:  # Middle of auction
                bid_amount = current_bid * 1.05  # 5% increment
            else:  # Late in auction
                bid_amount = current_bid + max(10, int(property_value * 0.02))  # Small fixed increment
        else:
            # Initial bid - investors start low
            bid_amount = property_obj.current_price * 0.6
            
        # Ensure minimum bid
        bid_amount = max(bid_amount, min_bid)
        
        # Bid if within max limit and ROI is acceptable
        if bid_amount <= max_bid and expected_roi > 0.08:  # Minimum acceptable ROI
            return {
                "bid": True,
                "amount": int(bid_amount),
                "max_willing": int(max_bid),
                "reason": f"Investment opportunity with {expected_roi:.1%} ROI"
            }
        else:
            reason = f"Insufficient ROI ({expected_roi:.1%}) or exceeds valuation" if expected_roi <= 0.08 else "Cannot afford bid increment"
            return {
                "bid": False,
                "reason": reason
            }
    
    def perform_pre_roll_actions(self):
        """Investor bots look for financial instrument opportunities"""
        actions = super().perform_pre_roll_actions()
        
        # Check if we should save cash for CDs or other investments
        if self.player.cash > 800 and random.random() < 0.3:  # 30% chance with sufficient cash
            actions.append({
                "action": "reserve_for_investment",
                "amount": min(500, self.player.cash - 300),
                "investment_type": random.choice(["CD", "HELOC", "Stock"]),
                "reason": "Investment opportunity"
            })
            
        return actions 