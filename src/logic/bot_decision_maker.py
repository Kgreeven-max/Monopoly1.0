import random
import logging
from ..models.property import Property
from ..models.player import Player
from ..models.finance.loan import Loan
from ..models.game_state import GameState
from datetime import datetime

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

    def decide_repay_loan(self, loan_id):
        """
        Decide whether to repay a specific loan and how much to repay.
        
        Args:
            loan_id (int): The ID of the loan to consider repaying
            
        Returns:
            dict: Decision information including:
                - repay (bool): Whether to repay the loan
                - loan_id (int): ID of the loan to repay
                - amount (int): Amount to repay (partial or full)
                - reason (str): Reasoning behind the decision
        """
        try:
            # Get the specific loan
            loan = Loan.query.get(loan_id)
            if not loan:
                logger.error(f"Cannot make loan repayment decision: Loan {loan_id} not found")
                return {"repay": False, "loan_id": loan_id, "reason": "Loan not found"}
            
            # Get game state to check economic conditions
            game_state = GameState.query.first()
            economic_state = game_state.economic_state if hasattr(game_state, 'economic_state') else 'stable'
            
            # Calculate base probability for repayment
            base_probability = 0.5  # Default 50% chance
            
            # Factor 1: Loan urgency (due date, interest rate)
            urgency_factor = 0.0
            
            # Check if loan has a due date and is approaching
            if hasattr(loan, 'due_date') and loan.due_date:
                days_until_due = (loan.due_date - datetime.utcnow()).days
                if days_until_due <= 1:  # Due tomorrow or today
                    urgency_factor = 0.9
                elif days_until_due <= 3:  # Due in 2-3 days
                    urgency_factor = 0.7
                elif days_until_due <= 7:  # Due within a week
                    urgency_factor = 0.5
                elif days_until_due <= 14:  # Due within two weeks
                    urgency_factor = 0.3
            
            # High interest rates increase urgency
            interest_urgency = min(loan.interest_rate / 20.0, 0.5)  # 10% interest = 0.5 factor
            urgency_factor = max(urgency_factor, interest_urgency)
            
            # Factor 2: Economic conditions
            economic_factor = 0.0
            if economic_state == 'boom':
                economic_factor = 0.3  # Good time to repay during boom
            elif economic_state == 'growth' or economic_state == 'stable':
                economic_factor = 0.2  # Also good during growth/stable economy
            elif economic_state == 'recession':
                economic_factor = -0.1  # May want to hold cash during recession
            elif economic_state == 'depression':
                economic_factor = -0.2  # Definitely hold cash during depression
            
            # Factor 3: Cash availability
            cash_factor = 0.0
            loan_to_cash_ratio = loan.amount / self.player.cash if self.player.cash > 0 else float('inf')
            
            if loan_to_cash_ratio < 0.3:
                cash_factor = 0.4  # Can easily afford to repay
            elif loan_to_cash_ratio < 0.5:
                cash_factor = 0.3  # Can comfortably repay
            elif loan_to_cash_ratio < 0.7:
                cash_factor = 0.1  # Can repay but it's a significant portion of cash
            else:
                cash_factor = -0.3  # Too expensive to repay now
            
            # Calculate final probability
            repayment_probability = base_probability + urgency_factor + economic_factor + cash_factor
            repayment_probability = max(0.1, min(0.9, repayment_probability))  # Bound between 10% and 90%
            
            # Apply bot's difficulty level to adjust decision making
            # Higher difficulty = better financial decisions
            if self.difficulty == 'easy':
                decision_accuracy = 0.7
            elif self.difficulty == 'medium' or self.difficulty == 'normal':
                decision_accuracy = 0.85
            else:  # hard
                decision_accuracy = 0.95
            
            # Reason for decision
            reason = ""
            
            # Occasionally override the calculated probability based on bot difficulty
            if random.random() > decision_accuracy:
                # Bot makes a sub-optimal decision
                repayment_probability = random.random()
                reason = "Strategic decision (influenced by randomness)"
            else:
                # Normal reason based on factors
                reasons = []
                if urgency_factor > 0.3:
                    reasons.append("urgent repayment needed")
                if economic_factor > 0.1:
                    reasons.append("favorable economic conditions")
                elif economic_factor < -0.1:
                    reasons.append(f"preserving cash during {economic_state}")
                if cash_factor > 0.2:
                    reasons.append("sufficient cash available")
                
                if not reasons:
                    reasons.append("strategic financial planning")
                    
                reason = ", ".join(reasons)
            
            # Decide whether to repay
            will_repay = random.random() < repayment_probability
            
            if will_repay:
                # Decide how much to repay
                if self.player.cash >= loan.amount * 1.2:  # Can afford full repayment with buffer
                    repay_amount = loan.amount
                    repay_reason = f"Full repayment: {reason}"
                else:
                    # Partial repayment - between 20% and 70% of loan or available cash
                    min_payment = max(int(loan.amount * 0.2), 100)  # At least 20% or $100
                    max_payment = min(int(loan.amount * 0.7), int(self.player.cash * 0.7))  # Up to 70% of loan or cash
                    
                    if max_payment < min_payment:  # Can't afford minimum payment
                        return {"repay": False, "loan_id": loan_id, "reason": "Insufficient funds for meaningful payment"}
                    
                    repay_amount = random.randint(min_payment, max_payment)
                    repay_reason = f"Partial repayment (${repay_amount}): {reason}"
                
                return {
                    "repay": True,
                    "loan_id": loan_id,
                    "amount": repay_amount,
                    "reason": repay_reason
                }
            else:
                # Decision not to repay
                if loan_to_cash_ratio > 0.8:
                    no_repay_reason = "Preserving cash reserves"
                elif economic_state in ['recession', 'depression']:
                    no_repay_reason = f"Holding cash during {economic_state}"
                else:
                    no_repay_reason = "Strategic decision to maintain liquidity"
                
                return {
                    "repay": False,
                    "loan_id": loan_id,
                    "reason": no_repay_reason
                }
                
        except Exception as e:
            logger.error(f"Error in decide_repay_loan for player {self.player.id}: {str(e)}", exc_info=True)
            return {
                "repay": False,
                "loan_id": loan_id,
                "reason": f"Error in decision making: {str(e)}"
            }

    def decide_trade_offer(self, trade_offer):
        """
        Decide whether to accept a trade offer from another player.
        
        Args:
            trade_offer (dict): The trade offer with details like:
                - requesting_player_id: ID of player making the offer
                - properties_offered: List of properties being offered
                - cash_offered: Cash amount being offered
                - properties_requested: List of properties being requested
                - cash_requested: Cash amount being requested
                
        Returns:
            dict: Decision details with:
                - accept (bool): Whether to accept the trade
                - counter_offer (dict, optional): Counter offer if not accepting
                - reason (str): Reason for the decision
        """
        logger.debug(f"Evaluating trade offer for player {self.player.id}: {trade_offer}")
        
        # Extract offer details
        requesting_player_id = trade_offer.get('requesting_player_id')
        properties_offered = trade_offer.get('properties_offered', [])
        cash_offered = trade_offer.get('cash_offered', 0)
        properties_requested = trade_offer.get('properties_requested', [])
        cash_requested = trade_offer.get('cash_requested', 0)
        
        # Validate basic offer structure
        if not requesting_player_id or (not properties_offered and cash_offered <= 0) or (not properties_requested and cash_requested <= 0):
            return {
                "accept": False,
                "reason": "Invalid trade offer structure"
            }
        
        # 1. Calculate value of what we're getting
        value_getting = cash_offered
        for prop_id in properties_offered:
            prop = Property.query.get(prop_id)
            if prop:
                # Evaluate the property value (using our evaluation method)
                prop_value = self._evaluate_property_value(prop)
                value_getting += prop_value
        
        # 2. Calculate value of what we're giving up
        value_giving = cash_requested
        for prop_id in properties_requested:
            prop = Property.query.get(prop_id)
            if prop:
                # Check if we own the property
                if prop.owner_id != self.player.id:
                    return {
                        "accept": False,
                        "reason": f"Don't own requested property {prop.name}"
                    }
                
                # Evaluate the property value with a premium for our owned properties
                prop_value = self._evaluate_property_value(prop) * 1.2  # 20% premium on properties we own
                
                # Check if this would break a monopoly
                monopoly_group = prop.monopoly_group
                if monopoly_group not in ["Railroad", "Utility"]:
                    all_in_group = Property.query.filter_by(monopoly_group=monopoly_group).all()
                    owned_in_group = [p for p in all_in_group if p.owner_id == self.player.id]
                    
                    # If we own all properties in this group, add a monopoly premium
                    if len(owned_in_group) == len(all_in_group):
                        prop_value *= 2.0  # Double value for monopoly properties
                
                value_giving += prop_value
        
        # 3. Check if we can afford the cash part
        if cash_requested > self.player.cash:
            return {
                "accept": False,
                "reason": "Insufficient funds for trade"
            }
        
        # 4. Evaluate strategic value of the trade
        # Check if offered properties would complete a monopoly for us
        monopoly_bonus = 0
        properties_by_group = {}
        
        # Group our existing properties by monopoly group
        my_properties = Property.query.filter_by(owner_id=self.player.id).all()
        for prop in my_properties:
            group = prop.monopoly_group
            if group not in properties_by_group:
                properties_by_group[group] = []
            properties_by_group[group].append(prop)
        
        # Check if offered properties would complete a monopoly
        for prop_id in properties_offered:
            prop = Property.query.get(prop_id)
            if prop and prop.monopoly_group not in ["Railroad", "Utility"]:
                group = prop.monopoly_group
                all_in_group = Property.query.filter_by(monopoly_group=group).all()
                
                # Count how many we would own after the trade
                would_own = 0
                for group_prop in all_in_group:
                    if group_prop.owner_id == self.player.id or group_prop.id == prop.id:
                        would_own += 1
                
                # If we would own all properties in the group, add a big bonus
                if would_own == len(all_in_group):
                    monopoly_bonus += 500  # Arbitrary high value for completing a monopoly
        
        # 5. Make the decision
        # Basic formula: accept if what we're getting + strategic value > what we're giving up
        adjusted_value_getting = value_getting + monopoly_bonus
        
        # Apply risk tolerance: more risk-tolerant bots will accept less favorable trades
        risk_factor = 0.8 + (self.risk_tolerance * 0.4)  # Range: 0.8 to 1.2
        min_value_ratio = 1.0 / risk_factor  # Higher risk tolerance = lower required value ratio
        
        # Calculate value ratio of what we're getting vs giving
        value_ratio = adjusted_value_getting / value_giving if value_giving > 0 else float('inf')
        
        # Make decision based on value ratio
        if value_ratio >= min_value_ratio:
            reason = f"Trade accepted: Value ratio {value_ratio:.2f} >= {min_value_ratio:.2f}"
            if monopoly_bonus > 0:
                reason += f" with monopoly bonus of {monopoly_bonus}"
            
            return {
                "accept": True,
                "reason": reason
            }
        else:
            # Propose a counter offer if the trade wasn't terrible
            counter_offer = None
            if value_ratio >= 0.8:
                # Simple counter: ask for more cash to make up value difference
                cash_adjustment = int(value_giving - adjusted_value_getting)
                if cash_adjustment > 0:
                    counter_offer = {
                        "properties_offered": properties_requested,
                        "cash_offered": cash_requested,
                        "properties_requested": properties_offered,
                        "cash_requested": cash_offered + cash_adjustment
                    }
            
            return {
                "accept": False,
                "reason": f"Trade rejected: Value ratio {value_ratio:.2f} < required {min_value_ratio:.2f}",
                "counter_offer": counter_offer
            }

    # TODO: Add other decision methods as needed:
    # - decide_mortgage_property(property_obj)
    # - decide_unmortgage_property(property_obj)
    # - decide_build_house(property_obj)
    # - decide_sell_house(property_obj)
    # - decide_propose_trade(other_player)
    # - decide_respond_to_trade(trade_offer) - Implemented as decide_trade_offer
    # - decide_jail_action(options: list) # e.g. ['pay', 'card', 'roll']

# Removed extraneous closing tag