# src/models/bots/opportunistic_bot.py

import random
from .base_bot import BotPlayer
from ..game_state import GameState # Relative import
from ..property import Property # Relative import
import logging

logger = logging.getLogger(__name__)

class OpportunisticBot(BotPlayer):
    """Opportunistic bot that focuses on timing-based strategies and market conditions"""
    
    def __init__(self, player_id, difficulty='normal'):
        super().__init__(player_id, difficulty)
        
        # Adjust parameters based on decision_maker attributes
        if hasattr(self.decision_maker, 'risk_tolerance'):
            self.decision_maker.risk_tolerance = min(self.decision_maker.risk_tolerance * 1.3, 0.9)
        else:
             logger.warning(f"OpportunisticBot {self.player_id}: Could not adjust risk_tolerance on decision_maker.")
             
        if hasattr(self.decision_maker, 'planning_horizon'):
            self.decision_maker.planning_horizon = max(1, self.decision_maker.planning_horizon - 1) # Focus on short-term gains
        else:
             logger.warning(f"OpportunisticBot {self.player_id}: Could not adjust planning_horizon on decision_maker.")
    
    def _make_optimal_buy_decision(self, property_obj):
        """Opportunistic bots base decisions on current game phase and economic state"""
        # Get game state to check economic phase
        game_state = GameState.query.first()
        # Ensure game_state is available
        if not game_state:
             # Fallback to base decision if game state is missing
             return super()._make_optimal_buy_decision(property_obj) 
        economic_phase = game_state.inflation_state
        
        # Base value calculation from parent class
        property_value = self._evaluate_property_value(property_obj)
        purchase_price = property_obj.current_price
        # Avoid division by zero
        value_ratio = property_value / purchase_price if purchase_price > 0 else float('inf') 
        
        # Adjust based on economic phase
        if economic_phase == "recession":
            # Buy aggressively during recession (prices are low)
            value_ratio *= 1.25
        elif economic_phase == "boom":
            # Be more cautious during boom phases (prices are high)
            value_ratio *= 0.85
        
        # Check player's cash position
        cash_ratio = self.player.cash / purchase_price if purchase_price > 0 else float('inf')
        
        # Opportunistic bot is more sensitive to cash position
        if cash_ratio < 2.0:
            value_ratio *= 0.8  # Be more conservative when cash is tight
        elif cash_ratio > 5.0:
            value_ratio *= 1.2  # Be more aggressive when cash is plentiful
        
        # Decision factors
        should_buy = value_ratio > (1.0 - self.risk_tolerance)
        
        # Include detailed reasoning for the decision
        return {
            "buy": should_buy,
            "value_ratio": value_ratio,
            "property_value": property_value,
            "economic_phase": economic_phase,
            "reason": f"Value ratio {value_ratio:.2f} with {economic_phase} economic phase"
        }
    
    def decide_auction_bid(self, auction_data):
        """Determine maximum bid for an auction"""
        # Use the base class implementation for auction bids
        # This bot's strength is in timing buy/sell, not specific auction logic yet
        # Return the dictionary format expected by the auction system
        base_decision = super().decide_auction_bid(auction_data)
        
        # Modify the base decision slightly based on opportunity
        if base_decision.get("bid"):
             game_state = GameState.query.first()
             if game_state and game_state.inflation_state == "recession":
                 # Slightly more willing to bid during recession
                 base_decision["amount"] = int(base_decision["amount"] * 1.05)
                 if "max_willing" in base_decision:
                      base_decision["max_willing"] = int(base_decision["max_willing"] * 1.05)

        return base_decision

    def response_to_economic_event(self, event_type, event_data):
        """
        Respond strategically to economic events in the game.
        
        Args:
            event_type (str): Type of economic event (e.g., "inflation_change", "market_boom", "market_bust")
            event_data (dict): Additional data about the event
            
        Returns:
            dict: Actions the bot decides to take in response to the event
        """
        actions = []
        
        # Log the event
        logger.info(f"OpportunisticBot {self.player_id} responding to economic event: {event_type}")
        
        if event_type == "inflation_change":
            new_state = event_data.get("new_state")
            
            if new_state == "recession":
                # During recession: Buy properties, hold cash for bargains
                actions.append({
                    "action": "adjust_strategy",
                    "strategy": "acquire_assets",
                    "reason": "Recession presents buying opportunities at reduced prices"
                })
                
                # Consider taking a loan for property acquisition
                if hasattr(self.decision_maker, 'risk_tolerance'):
                    old_risk_tolerance = self.decision_maker.risk_tolerance
                    # Temporarily increase risk tolerance to be more aggressive during recession
                    self.decision_maker.risk_tolerance = min(old_risk_tolerance * 1.25, 0.95)
                    logger.info(f"OpportunisticBot {self.player_id} increased risk tolerance from {old_risk_tolerance:.2f} to {self.decision_maker.risk_tolerance:.2f} due to recession")
                
            elif new_state == "boom":
                # During boom: Consider selling properties at premium, be cautious with purchases
                actions.append({
                    "action": "adjust_strategy",
                    "strategy": "sell_premium_assets",
                    "reason": "Boom market allows selling at higher prices"
                })
                
                # Be more conservative with risk during boom (avoid buying overpriced assets)
                if hasattr(self.decision_maker, 'risk_tolerance'):
                    old_risk_tolerance = self.decision_maker.risk_tolerance
                    # Temporarily decrease risk tolerance to be more cautious during boom
                    self.decision_maker.risk_tolerance = max(old_risk_tolerance * 0.8, 0.3)
                    logger.info(f"OpportunisticBot {self.player_id} decreased risk tolerance from {old_risk_tolerance:.2f} to {self.decision_maker.risk_tolerance:.2f} due to boom market")
                
            elif new_state == "normal":
                # Reset strategy to baseline during normal conditions
                actions.append({
                    "action": "adjust_strategy",
                    "strategy": "balanced",
                    "reason": "Normal market conditions suggest balanced approach"
                })
                
                # Reset risk tolerance to default for bot type and difficulty
                if hasattr(self.decision_maker, 'risk_tolerance'):
                    # Calculate default risk tolerance based on difficulty
                    default_risk = self.decision_maker.calculate_default_risk_tolerance()
                    # Apply opportunistic bot modifier (30% more risk-taking)
                    self.decision_maker.risk_tolerance = min(default_risk * 1.3, 0.9)
                    logger.info(f"OpportunisticBot {self.player_id} reset risk tolerance to {self.decision_maker.risk_tolerance:.2f} due to normal market")
        
        elif event_type == "market_boom":
            # Short-term market boom - consider development opportunities
            owned_properties = Property.query.filter_by(owner_id=self.player_id).all()
            developable_properties = [p for p in owned_properties if p.can_build_house]
            
            if developable_properties:
                # Prioritize development during booms
                actions.append({
                    "action": "prioritize_development",
                    "property_ids": [p.id for p in developable_properties],
                    "reason": "Market boom increases return on development investment"
                })
        
        elif event_type == "market_bust":
            # Market downturn - consider consolidating assets, hold cash
            actions.append({
                "action": "hold_cash",
                "reason": "Market downturn suggests holding liquid assets for future opportunities"
            })
            
            # Consider repaying loans during bust to reduce debt burden
            from src.models.finance.loan import Loan
            active_loans = Loan.query.filter_by(player_id=self.player.id, is_active=True).all()
            if active_loans and self.player.cash > 1000:  # If we have cash to spare
                actions.append({
                    "action": "prioritize_loan_repayment",
                    "loan_ids": [loan.id for loan in active_loans],
                    "reason": "Market downturn makes debt riskier, prioritizing repayment"
                })
        
        return {
            "bot_id": self.player_id,
            "event_type": event_type,
            "actions": actions
        }

        # Original simpler logic returning only amount:
        # property_id = auction_data["property_id"]
        # property_obj = Property.query.get(property_id)
        # if not property_obj:
        #     return 0 # Should return dict format expected by base
        
        # # Get base property value
        # property_value = self._evaluate_property_value(property_obj)
        
        # # Opportunistic bots bid higher when few players are left in the auction
        # eligible_players = auction_data.get("eligible_players", [])
        # players_passed = auction_data.get("players_passed", [])
        # active_bidders = len([p for p in eligible_players if p not in players_passed])
        # bidder_factor = max(0.8, min(1.2, 2.0 / active_bidders)) if active_bidders > 0 else 1.0
        
        # # Adjust based on current bid
        # current_bid = auction_data["current_bid"]
        # list_price = property_obj.current_price
        
        # # Opportunistic bot will bid higher if current bid is significantly below market
        # if list_price > 0 and current_bid < list_price * 0.7:
        #     bargain_factor = 1.2  # Willing to pay more for a bargain
        # else:
        #     bargain_factor = 0.9  # Less interested as price approaches list price
        
        # # Calculate max bid
        # max_bid = property_value * bidder_factor * bargain_factor
        
        # # Ensure we don't bid more than 90% of our cash
        # max_cash_bid = self.player.cash * 0.9
        # calculated_max_bid = min(max_bid, max_cash_bid)
        # # Return dict format
        # proposed_bid = min(current_bid + 10, calculated_max_bid) # Basic bid proposal
        # if proposed_bid > current_bid and proposed_bid <= max_cash_bid:
        #      return {"bid": True, "amount": int(proposed_bid), "max_willing": int(calculated_max_bid)}
        # else:
        #      return {"bid": False} 