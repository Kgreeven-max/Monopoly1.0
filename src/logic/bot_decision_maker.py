import random
import logging
from ..models.property import Property
from ..models.player import Player

logger = logging.getLogger(__name__)

class BotDecisionMaker:
    """Handles decision-making logic for AI players.
    
    Takes bot parameters and game state information to make decisions like
    buying property, bidding in auctions, managing assets, etc.
    Does not directly modify game state.
    """

    def __init__(self, player: Player, difficulty: str, decision_params: dict):
        """Initializes the decision maker for a specific bot.
        
        Args:
            player: The Player object this decision maker is for.
            difficulty: The difficulty level ('easy', 'normal', 'hard').
            decision_params: A dict containing parameters like 
                             'decision_accuracy', 'value_estimation_error', 
                             'risk_tolerance', 'planning_horizon'.
        """
        self.player = player
        self.difficulty = difficulty
        self.decision_accuracy = decision_params.get('decision_accuracy', 0.85)
        self.value_estimation_error = decision_params.get('value_estimation_error', 0.1)
        self.risk_tolerance = decision_params.get('risk_tolerance', 0.5)
        self.planning_horizon = decision_params.get('planning_horizon', 4)
        
        logger.info(f"Initialized BotDecisionMaker for Player {self.player.id} with difficulty '{self.difficulty}'")

    def decide_buy_property(self, property_obj: Property):
        """Decide whether to buy an unowned property."""
        if not property_obj:
            logger.warning(f"Player {self.player.id}: decide_buy_property called with invalid property object.")
            return {"buy": False, "reason": "Invalid property data"}
            
        logger.debug(f"Player {self.player.id} deciding whether to buy {property_obj.name}")
        
        # Make optimal decision based purely on value vs price
        optimal_decision = self._make_optimal_buy_decision(property_obj)
        
        # Factor in bot's accuracy (random chance to deviate)
        if random.random() < self.decision_accuracy:
            final_decision = optimal_decision["buy"]
            reason = optimal_decision["reason"]
        else:
            final_decision = not optimal_decision["buy"] # Flip the decision
            reason = "Inaccurate assessment (random deviation)" if final_decision else "Overly cautious (random deviation)"
            logger.debug(f"Player {self.player.id} deviated from optimal buy decision due to inaccuracy.")

        # Check affordability *after* making the decision to buy/not buy
        can_afford = self.player.cash >= property_obj.current_price
        
        result = {
            "buy": final_decision and can_afford, # Can only buy if decided yes AND can afford
            "can_afford": can_afford,
            "reason": reason if final_decision else ("Decided not to buy" if not final_decision else "Cannot afford"), # Clarify reason
            "estimated_value": optimal_decision.get("estimated_value", None) # Pass along evaluation details
        }
        
        if final_decision and not can_afford:
            result["reason"] = "Decided to buy but cannot afford"
            # Logged as warning previously in BaseBot, decision maker just returns the decision
            # logger.warning(f"Bot {self.player.id} decided to buy {property_obj.name} but lacks funds.")

        logger.debug(f"Buy decision for {property_obj.name}: {result}")
        return result

    def _make_optimal_buy_decision(self, property_obj: Property):
        """Make the 'optimal' buy/pass decision based on estimated value vs price."""
        estimated_value = self._evaluate_property_value(property_obj)
        price = property_obj.current_price
        
        # Threshold logic considering risk tolerance:
        # Higher tolerance means willing to pay closer to (or even slightly above) estimated value.
        # Lower tolerance demands a bigger discount.
        # Factor ranges roughly from 0.9 (low risk) to 1.1 (high risk)
        buy_threshold_factor = 1.0 + (self.risk_tolerance - 0.5) * 0.2 
        
        should_buy = estimated_value >= (price * buy_threshold_factor)
        
        reason = f"Estimated value ({estimated_value:.0f}) vs Price ({price}) comparison."
        if not should_buy:
            reason += f" (Price exceeds risk-adjusted value threshold: {price} > {estimated_value:.0f} / {buy_threshold_factor:.2f})"
        else:
             reason += f" (Price within risk-adjusted value threshold: {price} <= {estimated_value:.0f} / {buy_threshold_factor:.2f})"
            
        return {
            "buy": should_buy,
            "reason": reason,
            "estimated_value": estimated_value
            }

    def _evaluate_property_value(self, property_obj: Property):
        """Estimate the long-term value of a property. (Placeholder)."""
        # TODO: Implement a more sophisticated valuation model
        # Needs access to game state, other player holdings etc.
        # For now, keeps the simple placeholder logic.
        
        if not property_obj or not property_obj.rent_level:
            logger.warning(f"Cannot evaluate property value: Invalid property data or rent levels for {property_obj}")
            return 0

        # Simple placeholder: Value = Base Rent * Multiplier + Monopoly Bonus
        base_rent = property_obj.rent_level[0]
        base_value = base_rent * 15 # Arbitrary multiplier
        
        # Crude monopoly potential bonus
        # TODO: Check actual monopoly status/potential more accurately (needs game state access)
        monopoly_bonus = 0
        if property_obj.monopoly_group not in ["Railroad", "Utility"]:
           # Check if owning this would complete/advance monopoly for the player
           # This requires knowing player's current holdings - passed via self.player
           # Placeholder: Just add a flat bonus for non-RR/Utility
           monopoly_bonus = base_value * 0.5 # Add 50% bonus for potential standard monopoly

        estimated_value = base_value + monopoly_bonus

        # Introduce error based on difficulty's value_estimation_error parameter
        error_margin = estimated_value * self.value_estimation_error
        valuation_error = random.uniform(-error_margin, error_margin)
        final_estimated_value = max(0, round(estimated_value + valuation_error)) # Ensure non-negative
        
        logger.debug(f"Estimated value for {property_obj.name}: {final_estimated_value} (Base: {base_value}, Bonus: {monopoly_bonus:.0f}, Error: {valuation_error:.2f})")
        return final_estimated_value

    def decide_auction_bid(self, property_obj: Property, current_bid: int):
        """Decide how much to bid in an auction."""
        if not property_obj:
            logger.warning(f"Cannot decide auction bid: Property object is invalid.")
            return {"bid_amount": 0, "reason": "Invalid property data"}

        logger.debug(f"Player {self.player.id} deciding auction bid for {property_obj.name}. Current bid: {current_bid}")

        estimated_value = self._evaluate_property_value(property_obj)
        
        # Determine max bid based on estimated value, risk tolerance, and cash
        # Lower risk tolerance -> bid further below estimated value
        # risk_tolerance=0 -> 80%, risk_tolerance=0.5 -> 100%, risk_tolerance=1 -> 120%
        max_willing_bid_factor = 0.8 + self.risk_tolerance * 0.4 
        max_willing_bid = estimated_value * max_willing_bid_factor
        
        # Keep a small cash buffer (e.g., $50 or 10% of cash, whichever is smaller?)
        cash_buffer = min(50, self.player.cash * 0.1) 
        max_affordable_bid = self.player.cash - cash_buffer
        
        max_bid = min(max_willing_bid, max_affordable_bid)
        logger.debug(f"Auction bid params: Est.Value={estimated_value:.0f}, MaxWillingFactor={max_willing_bid_factor:.2f}, MaxWillingBid={max_willing_bid:.0f}, Cash={self.player.cash}, Buffer={cash_buffer:.0f}, MaxAffordable={max_affordable_bid:.0f}, FinalMaxBid={max_bid:.0f}")
        
        bid_amount = 0
        reason = ""

        # Simple bidding strategy: Bid slightly above current bid if below max
        if max_bid > current_bid:
            # Add a small increment, maybe random amount or percentage?
            increment = max(10, round(current_bid * 0.05) + random.randint(1, 5)) 
            potential_bid = current_bid + increment
            
            if potential_bid <= max_bid:
                bid_amount = potential_bid
                reason = f"Bidding {bid_amount}. (Est.Val={estimated_value:.0f}, MaxBid={max_bid:.0f})"
            else:
                 # If close to max_bid, maybe bid exactly max_bid? Add randomness/risk factor.
                 if max_bid > current_bid and (self.risk_tolerance > 0.6 or random.random() > 0.5): # Chance to bid max if close
                     bid_amount = round(max_bid)
                     reason = f"Bidding max {bid_amount}. (Est.Val={estimated_value:.0f})"
                 else:
                     bid_amount = 0 # Drop out
                     reason = f"Potential bid ({potential_bid}) exceeds max ({max_bid:.0f}). Dropping out. (Est.Val={estimated_value:.0f})"
        else:
            bid_amount = 0 # Drop out
            reason = f"Current bid ({current_bid}) >= max bid ({max_bid:.0f}). Dropping out. (Est.Val={estimated_value:.0f})"

        # Accuracy check - random chance to make a suboptimal bid (bid 0 or bid too high)
        if random.random() > self.decision_accuracy:
             if random.random() < 0.5 and bid_amount > 0: # Chance to drop out unexpectedly
                 logger.debug(f"Player {self.player.id} deviating from optimal auction bid (dropping out). Original reason: {reason}")
                 bid_amount = 0
                 reason = "Suboptimal: Dropped out unexpectedly"
             # Could also add logic for accidentally bidding too high (more complex)
        
        final_bid = round(max(0, bid_amount)) # Ensure bid is non-negative and integer
        logger.debug(f"Auction bid decision for {property_obj.name}: Bid {final_bid}. Reason: {reason}")
        return {"bid_amount": final_bid, "reason": reason}

    # TODO: Add other decision methods as needed:
    # - decide_mortgage_property(property_obj)
    # - decide_unmortgage_property(property_obj)
    # - decide_build_house(property_obj)
    # - decide_sell_house(property_obj)
    # - decide_propose_trade(other_player)
    # - decide_respond_to_trade(trade_offer)
    # - decide_jail_action(options: list) # e.g. ['pay', 'card', 'roll']

# Removed extraneous closing tag