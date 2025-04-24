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

    def decide_take_loan(self, cash_needed: int = 0):
        """Decide whether to take a loan and for how much.
        
        Args:
            cash_needed: Optional amount of cash needed for immediate expenses.
                         If 0, bot decides based on general financial situation.
        
        Returns:
            Dictionary with loan decision and parameters
        """
        logger.debug(f"Player {self.player.id} considering taking a loan. Cash needed: {cash_needed}")
        
        # Check current cash and property assets
        current_cash = self.player.cash
        owned_properties = Property.query.filter_by(owner_id=self.player.id).all()
        property_value = sum(prop.current_price for prop in owned_properties)
        net_worth = current_cash + property_value
        
        # If no properties, don't take a loan
        if len(owned_properties) == 0:
            return {
                "take_loan": False,
                "reason": "No properties to secure loan"
            }
        
        # Calculate maximum viable loan amount (80% of net worth)
        max_loan_amount = int(net_worth * 0.8)
        
        # Determine if loan is needed and for how much
        loan_amount = 0
        take_loan = False
        reason = ""
        
        if cash_needed > 0:
            # Specific need case
            if current_cash >= cash_needed:
                # No loan needed
                take_loan = False
                reason = f"Sufficient cash available (${current_cash})"
            else:
                # Take loan for the shortfall plus buffer
                shortfall = cash_needed - current_cash
                buffer = int(shortfall * 0.5)  # Add 50% buffer
                loan_amount = min(shortfall + buffer, max_loan_amount)
                take_loan = True
                reason = f"Need ${shortfall} with buffer (total: ${loan_amount})"
        else:
            # General financial strategy case
            # Higher risk tolerance -> more likely to take opportunistic loans
            if current_cash < 200 and property_value > 500:
                # Low cash situation
                loan_amount = min(300, max_loan_amount)
                take_loan = random.random() < self.risk_tolerance
                reason = f"Low cash situation (${current_cash}), risk assessment: {take_loan}"
            elif self.risk_tolerance > 0.7 and len(owned_properties) >= 3:
                # Strategic loan for expansion (high risk bot)
                loan_amount = min(500, max_loan_amount)
                take_loan = random.random() < (self.risk_tolerance - 0.5)
                reason = f"Strategic expansion opportunity, risk assessment: {take_loan}"
        
        # Apply difficulty factor
        if self.difficulty == 'hard':
            # Hard bots make better loan decisions
            if take_loan and loan_amount > max_loan_amount * 0.7:
                # Reduce loan amount to safer level
                loan_amount = int(max_loan_amount * 0.7)
                reason += f" (adjusted to safer amount: ${loan_amount})"
        elif self.difficulty == 'easy':
            # Easy bots might take excessive loans
            if take_loan and random.random() < 0.3:
                loan_amount = int(max_loan_amount * 0.9)
                reason += f" (easy bot taking larger loan: ${loan_amount})"
        
        # Decision accuracy factor - chance to make a random decision
        if random.random() > self.decision_accuracy:
            # Make a random loan decision
            prev_decision = take_loan
            take_loan = random.random() < 0.5
            if take_loan != prev_decision:
                reason += f" (Accuracy deviation, original decision: {prev_decision})"
                if take_loan and loan_amount == 0:
                    loan_amount = min(200, max_loan_amount)
        
        return {
            "take_loan": take_loan,
            "loan_amount": loan_amount if take_loan else 0,
            "max_loan_amount": max_loan_amount,
            "reason": reason
        }

    # TODO: Add other decision methods as needed:
    # - decide_mortgage_property(property_obj)
    # - decide_unmortgage_property(property_obj)
    # - decide_build_house(property_obj)
    # - decide_sell_house(property_obj)
    # - decide_propose_trade(other_player)
    # - decide_respond_to_trade(trade_offer)
    # - decide_jail_action(options: list) # e.g. ['pay', 'card', 'roll']

# Removed extraneous closing tag