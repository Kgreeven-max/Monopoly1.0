from datetime import datetime
import random
import logging
import json
from flask import current_app
from .. import db # Relative import for db
from ..player import Player # Relative import for Player
from ..property import Property # Relative import for Property
from ..game_state import GameState # Relative import for GameState
from ..transaction import Transaction # Relative import for Transaction
from ..bot_events.base_event import BotEvent
from ..special_space import SpecialSpace # Import for special spaces
# New import for the handler
from ...services.bot_action_handler import BotActionHandler 
# New import for the decision maker
from ...logic.bot_decision_maker import BotDecisionMaker
# Import finance controller
from ...controllers.finance_controller import FinanceController
from ...models.finance.loan import Loan
from ...controllers.property_controller import PropertyController

logger = logging.getLogger(__name__)

class BotPlayer:
    """Base class for AI players with different strategies.
    Orchestrates the bot's turn by interacting with decision logic and action handlers.
    """
    
    def __init__(self, player_id, difficulty='normal'):
        self.player_id = player_id
        self.difficulty = difficulty
        
        # Load player object
        self.player = Player.query.get(player_id)
        if not self.player:
            # Log error and raise
            logger.error(f"Failed to initialize BotPlayer: Invalid player_id {player_id}")
            raise ValueError(f"Invalid player_id: {player_id}")
        
        # Instantiate handlers and decision makers
        self.action_handler = BotActionHandler()
        
        # Set up decision parameters based on difficulty (used by DecisionMaker later)
        if difficulty == 'easy':
            decision_params = {
                'decision_accuracy': 0.7,
                'value_estimation_error': 0.2,
                'risk_tolerance': 0.3,
                'planning_horizon': 2
            }
        elif difficulty == 'normal':
            decision_params = {
                'decision_accuracy': 0.85,
                'value_estimation_error': 0.1,
                'risk_tolerance': 0.5,
                'planning_horizon': 4
            }
        else:  # hard
            decision_params = {
                'decision_accuracy': 0.95,
                'value_estimation_error': 0.05,
                'risk_tolerance': 0.7,
                'planning_horizon': 6
            }
            
        # Instantiate the decision maker
        self.decision_maker = BotDecisionMaker(self.player, self.difficulty, decision_params)
        
        logger.info(f"Initialized BotPlayer for Player {self.player_id} ({self.player.username}) with difficulty '{self.difficulty}'.")

    
    def execute_turn(self):
        """Execute a full turn for the bot, coordinating actions and decisions."""
        logger.info(f"Executing turn for Bot Player {self.player_id}")
        turn_summary = {
            "player_id": self.player_id,
            "pre_roll_actions": [],
            "roll_result": None,
            "move_result": None,
            "post_roll_actions": []
        }

        try:
            # Pre-roll actions (e.g., manage properties, trigger events)
            turn_summary["pre_roll_actions"] = self.perform_pre_roll_actions()
            
            # --- Roll Dice ---
            roll_result = self.action_handler.roll_dice()
            turn_summary["roll_result"] = roll_result
            logger.debug(f"Player {self.player_id} rolled {roll_result['total']} ({roll_result['dice1']}, {roll_result['dice2']})")

            # --- Process Move ---
            move_result = self.action_handler.process_move(self.player, roll_result["total"])
            turn_summary["move_result"] = move_result
            logger.debug(f"Player {self.player_id} moved from {move_result['old_position']} to {move_result['new_position']}. Passed GO: {move_result['passed_go']}")

            # --- Post-roll actions based on landing space ---
            turn_summary["post_roll_actions"] = self.perform_post_roll_actions(move_result)
            
            # --- End Turn ---
            # Decision whether to end turn might depend on doubles, jail status etc.
            # The action_handler.end_turn() is more of a cleanup/logging step now.
            self.action_handler.end_turn(self.player)
            logger.info(f"Finished turn execution for Bot Player {self.player_id}")

        except Exception as e:
            logger.error(f"Error during Bot Player {self.player_id} turn execution: {e}", exc_info=True)
            # Add error information to the summary
            turn_summary["error"] = str(e)
            # Depending on the error, might need recovery logic or state reset

        return turn_summary

    # _roll_dice removed - handled by BotActionHandler
    
    # process_move removed - handled by BotActionHandler
    
    def perform_pre_roll_actions(self):
        """Perform optional pre-roll actions (e.g., unmortgage, build).
        
        Returns:
            list: The actions taken by the bot.
        """
        logger.debug(f"Bot {self.player_id} performing pre-roll actions")
        actions = []
        
        try:
            # First, check for any loans that need to be repaid
            player_loans = Loan.query.filter_by(player_id=self.player_id).all()
            
            if player_loans:
                # Get game state to evaluate economic conditions
                game_state = GameState.query.first()
                economic_state = game_state.economic_state if hasattr(game_state, 'economic_state') else 'stable'
                
                logger.info(f"Bot {self.player_id} has {len(player_loans)} loans to consider during {economic_state} economy")
                
                # Sort loans based on economic conditions and interest rates
                if economic_state in ['boom', 'growth', 'stable']:
                    # During good economy, prioritize high interest loans first
                    player_loans.sort(key=lambda loan: loan.interest_rate, reverse=True)
                    logger.info(f"Economic conditions favorable ({economic_state}). Prioritizing high interest loans.")
                else:
                    # During recession/depression, prioritize smallest loans to reduce count
                    player_loans.sort(key=lambda loan: loan.amount)
                    logger.info(f"Economic conditions unfavorable ({economic_state}). Prioritizing smallest loans.")
                
                # Consider repaying loans
                for loan in player_loans:
                    # Use decision maker to determine if/how much to repay
                    repay_decision = self.decision_maker.decide_repay_loan(loan.id)
                    
                    if repay_decision.get('repay', False) and repay_decision.get('amount', 0) > 0:
                        loan_id = repay_decision.get('loan_id')
                        repay_amount = repay_decision.get('amount')
                        
                        logger.info(f"Bot {self.player_id} decided to repay ${repay_amount} on loan {loan_id}. Reason: {repay_decision.get('reason')}")
                        
                        # Call controller to repay the loan
                        finance_controller = FinanceController()
                        repay_result = finance_controller.repay_loan(self.player_id, self.player.pin, loan_id, repay_amount)
                        
                        if repay_result.get('success', False):
                            logger.info(f"Bot {self.player_id} successfully repaid ${repay_amount} on loan {loan_id}")
                            actions.append({
                                "action": "repaid_loan",
                                "loan_id": loan_id,
                                "amount": repay_amount,
                                "remaining": repay_result.get('remaining_amount', 0)
                            })
                            # Update player data after loan repayment
                            self.player = Player.query.get(self.player_id)
                        else:
                            logger.warning(f"Bot {self.player_id} failed to repay loan: {repay_result.get('error', 'Unknown error')}")
            
            # Next, manage properties (unmortgage/build houses)
            owned_properties = Property.query.filter_by(owner_id=self.player_id).all()
            
            if owned_properties:
                # Get current economic state if we don't already have it
                if 'economic_state' not in locals():
                    game_state = GameState.query.first()
                    economic_state = game_state.economic_state if hasattr(game_state, 'economic_state') else 'stable'
                
                logger.debug(f"Bot {self.player_id} managing {len(owned_properties)} properties during {economic_state} economy")
                
                # Adjust property strategy based on economic conditions
                develop_aggressively = economic_state in ['boom', 'growth']
                unmortgage_aggressively = economic_state == 'boom'
                conserve_cash = economic_state in ['recession', 'depression']
                
                if conserve_cash:
                    logger.info(f"Bot {self.player_id} conserving cash during {economic_state}")
                    # During economic downturns, maintain higher cash reserves
                    min_cash_buffer = 500  # Higher buffer during recessions
                else:
                    min_cash_buffer = 200  # Normal buffer
                
                # First, consider unmortgaging properties that complete monopolies
                property_controller = PropertyController()
                
                # Identify monopoly groups 
                monopoly_groups = {}
                for prop in owned_properties:
                    if prop.monopoly_group not in monopoly_groups:
                        monopoly_groups[prop.monopoly_group] = []
                    monopoly_groups[prop.monopoly_group].append(prop)
                
                # Prioritize unmortgaging properties in monopoly groups
                for group, props in monopoly_groups.items():
                    # Skip utility and railroad groups
                    if group in ["Railroad", "Utility"]:
                        continue
                        
                    # Check if we have a complete or near-complete monopoly
                    all_in_group = Property.query.filter_by(monopoly_group=group).all()
                    owned_count = len(props)
                    total_count = len(all_in_group)
                    
                    # Focus on groups where we own all or most properties
                    if owned_count == total_count or (owned_count >= total_count - 1 and total_count > 2):
                        # Look for mortgaged properties in this group
                        for prop in props:
                            if prop.is_mortgaged:
                                # Calculate unmortgage cost
                                unmortgage_cost = int(prop.mortgage_value * 1.1)  # 10% interest
                                
                                # Determine cash buffer based on economic conditions
                                cash_buffer = min_cash_buffer
                                if unmortgage_aggressively:
                                    cash_buffer = min_cash_buffer * 0.5  # Lower buffer during boom
                                
                                # Check if we can afford it with appropriate buffer
                                if self.player.cash > unmortgage_cost + cash_buffer:
                                    logger.info(f"Bot {self.player_id} attempting to unmortgage {prop.name} to complete monopoly in {economic_state} economy")
                                    
                                    # Call the unmortgage method
                                    unmortgage_result = property_controller.unmortgage_property(
                                        self.player.id,
                                        self.player.pin,
                                        prop.id
                                    )
                                    
                                    if unmortgage_result.get('success', False):
                                        logger.info(f"Bot {self.player_id} successfully unmortgaged {prop.name}")
                                        actions.append({
                                            "action": "unmortgaged_property",
                                            "property_id": prop.id,
                                            "property_name": prop.name,
                                            "cost": unmortgage_cost
                                        })
                                        # Update cash after unmortgage
                                        self.player = Player.query.get(self.player.id)  # Refresh player data
                                    else:
                                        logger.warning(f"Bot {self.player_id} failed to unmortgage {prop.name}: {unmortgage_result.get('error', 'Unknown error')}")
                    
                    # Next, consider building houses on monopolies, but only if it makes economic sense
                    if not conserve_cash or develop_aggressively:
                        # Organize properties by monopoly group
                        properties_by_group = {}
                        for prop in owned_properties:
                            if prop.monopoly_group not in ["Railroad", "Utility"]:
                                if prop.monopoly_group not in properties_by_group:
                                    properties_by_group[prop.monopoly_group] = []
                                properties_by_group[prop.monopoly_group].append(prop)
                        
                        # Check each group to see if we have a monopoly
                        for group, props in properties_by_group.items():
                            all_in_group = Property.query.filter_by(monopoly_group=group).all()
                            
                            # If we own all properties in the group, consider building
                            if len(props) == len(all_in_group):
                                # Sort properties by current development level (to maintain even development)
                                props.sort(key=lambda p: p.houses)
                                
                                # Determine cash buffer based on economic conditions
                                if develop_aggressively:
                                    development_cash_buffer = 200  # Lower buffer when developing aggressively
                                else:
                                    development_cash_buffer = 300  # Normal buffer
                                
                                # Prioritize the least developed property
                                for prop in props:
                                    # Check if this property can be improved and we can afford it
                                    if prop.houses < 5:  # Maximum of 5 houses (hotel)
                                        # Get improvement cost
                                        improvement_cost = prop.house_cost
                                        if improvement_cost and self.player.cash > improvement_cost + development_cash_buffer:
                                            logger.info(f"Bot {self.player_id} attempting to build a house on {prop.name} during {economic_state} economy")
                                            
                                            # Call the improve property method
                                            improvement_result = property_controller.handle_property_improvement(
                                                game_state.id,
                                                self.player.id,
                                                prop.id,
                                                "house"  # Assuming "house" is the improvement type
                                            )
                                            
                                            if improvement_result.get('success', False):
                                                logger.info(f"Bot {self.player_id} successfully built a house on {prop.name}")
                                                actions.append({
                                                    "action": "built_house",
                                                    "property_id": prop.id,
                                                    "property_name": prop.name,
                                                    "houses": prop.houses + 1,
                                                    "cost": improvement_cost
                                                })
                                                # Update cash after building
                                                self.player = Player.query.get(self.player.id)  # Refresh player data
                                                
                                                # If developing aggressively in boom, consider building multiple houses
                                                if develop_aggressively and self.difficulty == 'hard':
                                                    continue  # Continue building on other properties
                                                else:
                                                    # Only build one house per turn to spread investments
                                                    break
                                            else:
                                                logger.warning(f"Bot {self.player_id} failed to build a house on {prop.name}: {improvement_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error during Bot {self.player_id} property management: {str(e)}", exc_info=True)
            
        return actions
    
    def check_for_special_event(self):
        """Check if the bot should trigger a special event based on chance and difficulty."""
        # Base chance of triggering an event
        event_chance = 0.15 # TODO: Make this configurable?
        
        # Adjust based on difficulty
        if self.difficulty == 'easy':
            event_chance *= 0.5
        elif self.difficulty == 'hard':
            event_chance *= 1.5
            
        if random.random() < event_chance:
            logger.debug(f"Attempting to generate special event for Bot {self.player_id}")
            # Try to generate a random event appropriate for the current game state
            # TODO: Get GameState more cleanly
            game_state = GameState.query.first()
            if not game_state:
                logger.warning("Cannot generate bot event: GameState not found.")
                return None

            # Pass bot's type name to the event generator
            event = BotEvent.get_random_event(game_state, self.player_id, bot_type_name=type(self).__name__)
            
            if event:
                logger.info(f"Generated event '{event.name}' for Bot {self.player_id}")
                # TODO: Consider triggering the event execution here or returning data for GameController
                # event.execute() # Or similar method if event handles its own execution
                return {
                    "action": "special_event_triggered",
                    "event": event.get_event_data() # Return data describing the event
                }
            else:
                logger.debug(f"No suitable event generated for Bot {self.player_id}")
                
        return None
    
    def perform_post_roll_actions(self, move_result):
        """Perform actions after moving, based on the landing space."""
        new_position = move_result["new_position"]
        logger.debug(f"Bot {self.player_id} performing post-roll actions for position {new_position}")
        
        # First, check if the space is a special space
        special_space = SpecialSpace.query.filter_by(position=new_position).first()
        
        if special_space:
            logger.debug(f"Landed on Special Space: {special_space.name} (Type: {special_space.space_type})")
            
            # Handle different types of special spaces
            if special_space.space_type == "chance":
                logger.info(f"Bot {self.player_id} landed on Chance space")
                return self.action_handler.handle_chance_space(self.player)
                
            elif special_space.space_type == "community_chest":
                logger.info(f"Bot {self.player_id} landed on Community Chest space")
                return self.action_handler.handle_community_chest_space(self.player)
                
            elif special_space.space_type == "tax":
                logger.info(f"Bot {self.player_id} landed on Tax space")
                # Get tax details from the special space
                tax_details = None
                try:
                    tax_details = json.loads(special_space.action_data) if special_space.action_data else {}
                except:
                    tax_details = {"amount": 100, "name": special_space.name}  # Default if parsing fails
                    
                return self.action_handler.handle_tax_space(self.player, tax_details)
                
            elif special_space.space_type == "go_to_jail":
                logger.info(f"Bot {self.player_id} landed on Go To Jail space")
                return self.action_handler.handle_go_to_jail_space(self.player)
                
            elif special_space.space_type == "free_parking":
                logger.info(f"Bot {self.player_id} landed on Free Parking space")
                return self.action_handler.handle_free_parking_space(self.player)
                
            elif special_space.space_type == "market_fluctuation":
                logger.info(f"Bot {self.player_id} landed on Market Fluctuation space")
                return self.action_handler.handle_market_fluctuation_space(self.player)
                
            elif special_space.space_type in ["go", "jail"]:
                logger.info(f"Bot {self.player_id} landed on {special_space.name} (passive space)")
                # No action needed for these spaces
                return [{"action": "passive_space", "space_name": special_space.name}]
                
            else:
                logger.warning(f"Bot {self.player_id} landed on unhandled special space type: {special_space.space_type}")
                return []
                
        # If not a special space, check if it's a property
        property_obj = Property.query.filter_by(position=new_position).first()
        
        if property_obj:
            logger.debug(f"Landed on Property: {property_obj.name} (ID: {property_obj.id})")
            # Decision needed first: Buy? (handled by decision logic)
            # Delegate decision to the BotDecisionMaker
            buy_decision_result = self.decision_maker.decide_buy_property(property_obj)
            
            # Execute action via handler, passing the decision
            property_actions = self.action_handler.handle_property_space(
                self.player, 
                property_obj, 
                buy_decision_result["buy"] # Pass the boolean decision
            )
            logger.debug(f"Property actions result: {property_actions}")
            return property_actions

        logger.warning(f"Bot {self.player_id} landed on position {new_position} that is neither a special space nor a property!")
        return [] # Return empty list if no space is defined at this position

    # handle_property_space removed - handled by BotActionHandler

    # _calculate_rent removed - handled by BotActionHandler (as helper)

    # --- Decision Logic Methods (To be moved to BotDecisionMaker) ---
    
    # Decision logic methods removed - delegated to BotDecisionMaker

    # end_turn removed - Handled by BotActionHandler / GameController

    def end_turn(self):
        """Actions to take at the end of the turn (e.g., manage properties)"""
        # Placeholder for future logic like building houses, mortgaging
        pass 

    def evaluate_trade_offer(self, trade_offer):
        """
        Evaluate a trade offer from another player and decide to accept or reject it.
        
        Args:
            trade_offer (dict): Dictionary containing trade details:
                - requesting_player_id: ID of player making the offer
                - properties_offered: List of property IDs being offered
                - cash_offered: Cash amount being offered
                - properties_requested: List of property IDs being requested
                - cash_requested: Cash amount being requested
                
        Returns:
            dict: Response with decision and details
        """
        logger.info(f"Bot {self.player_id} evaluating trade offer: {trade_offer}")
        
        try:
            # Use decision maker to evaluate the trade
            decision = self.decision_maker.decide_trade_offer(trade_offer)
            
            # Log the decision
            if decision.get('accept', False):
                logger.info(f"Bot {self.player_id} ACCEPTING trade offer. Reason: {decision.get('reason')}")
            else:
                logger.info(f"Bot {self.player_id} REJECTING trade offer. Reason: {decision.get('reason')}")
                if decision.get('counter_offer'):
                    logger.info(f"Bot {self.player_id} proposing counter offer: {decision.get('counter_offer')}")
            
            # Return the decision with additional metadata
            return {
                "player_id": self.player_id,
                "accept": decision.get('accept', False),
                "reason": decision.get('reason', "No reason provided"),
                "counter_offer": decision.get('counter_offer'),
                "original_offer": trade_offer
            }
            
        except Exception as e:
            logger.error(f"Error evaluating trade offer for Bot {self.player_id}: {str(e)}", exc_info=True)
            return {
                "player_id": self.player_id,
                "accept": False,
                "reason": f"Error evaluating trade: {str(e)}",
                "error": True
            } 

    def response_to_economic_event(self, event_type, event_data):
        """
        Respond to economic events in the game with appropriate actions.
        
        Args:
            event_type (str): Type of economic event (e.g., "market_boom", "market_crash", "interest_rate_change")
            event_data (dict): Additional data about the event
            
        Returns:
            dict: Actions the bot decides to take in response to the event
        """
        actions = []
        
        # Log the event
        logger.info(f"Bot {self.player_id} responding to economic event: {event_type}")
        
        try:
            # Get the bot's current financial state
            cash = self.player.cash
            owned_properties = Property.query.filter_by(owner_id=self.player_id).all()
            property_value = sum(prop.price for prop in owned_properties)
            net_worth = cash + property_value
            
            if event_type == "market_boom":
                # During market boom: Consider developing properties
                logger.info(f"Bot {self.player_id} responding to market boom event. Current cash: ${cash}")
                
                # If we have significant cash reserves, consider investing in property development
                if cash > 500 and owned_properties:
                    # Flag for property development in next turn
                    actions.append({
                        "action": "adjust_strategy",
                        "strategy": "develop_properties",
                        "reason": "Market boom provides good opportunity for property development"
                    })
                    
                    # Temporarily increase risk tolerance for the next few decisions
                    if hasattr(self.decision_maker, 'risk_tolerance'):
                        old_risk_tolerance = self.decision_maker.risk_tolerance
                        self.decision_maker.risk_tolerance = min(old_risk_tolerance * 1.2, 0.95)
                        logger.info(f"Bot {self.player_id} increased risk tolerance from {old_risk_tolerance:.2f} to {self.decision_maker.risk_tolerance:.2f} due to market boom")
                        
                        # Schedule to reset the risk tolerance after a few turns
                        # (Implementation would depend on your turn tracking mechanism)
                
            elif event_type == "market_crash":
                # During market crash: Preserve cash, be cautious with investments
                logger.info(f"Bot {self.player_id} responding to market crash event. Current cash: ${cash}")
                
                # Be more conservative with spending
                actions.append({
                    "action": "adjust_strategy",
                    "strategy": "preserve_cash",
                    "reason": "Market crash increases risk of financial difficulties"
                })
                
                # Decrease risk tolerance temporarily
                if hasattr(self.decision_maker, 'risk_tolerance'):
                    old_risk_tolerance = self.decision_maker.risk_tolerance
                    self.decision_maker.risk_tolerance = max(old_risk_tolerance * 0.8, 0.3)
                    logger.info(f"Bot {self.player_id} decreased risk tolerance from {old_risk_tolerance:.2f} to {self.decision_maker.risk_tolerance:.2f} due to market crash")
            
            elif event_type == "interest_rate_change":
                new_rate = event_data.get("new_rate", 0)
                old_rate = event_data.get("old_rate", 0)
                
                # Check if it's an increase or decrease
                if new_rate > old_rate:
                    # Interest rates increased - consider repaying loans
                    player_loans = Loan.query.filter_by(player_id=self.player_id).all()
                    
                    if player_loans:
                        actions.append({
                            "action": "adjust_strategy",
                            "strategy": "prioritize_loan_repayment",
                            "reason": f"Interest rates increased from {old_rate:.1%} to {new_rate:.1%}"
                        })
                        logger.info(f"Bot {self.player_id} prioritizing loan repayment due to interest rate increase to {new_rate:.1%}")
                else:
                    # Interest rates decreased - consider taking loans for investment
                    if net_worth > 1000 and owned_properties and cash < 300:
                        actions.append({
                            "action": "adjust_strategy",
                            "strategy": "consider_loans_for_investment",
                            "reason": f"Interest rates decreased from {old_rate:.1%} to {new_rate:.1%}, good opportunity for financing"
                        })
                        logger.info(f"Bot {self.player_id} considering loans for investment due to interest rate decrease to {new_rate:.1%}")
            
            elif event_type == "inflation_change":
                new_inflation = event_data.get("new_rate", 0)
                
                # High inflation - focus on property acquisition to hedge against inflation
                if new_inflation > 0.05:  # 5% inflation threshold
                    actions.append({
                        "action": "adjust_strategy",
                        "strategy": "acquire_assets",
                        "reason": f"High inflation ({new_inflation:.1%}) makes real estate a better investment than cash"
                    })
                    logger.info(f"Bot {self.player_id} focusing on property acquisition due to high inflation ({new_inflation:.1%})")
                
                # Deflation - cash becomes more valuable
                elif new_inflation < 0:
                    actions.append({
                        "action": "adjust_strategy",
                        "strategy": "preserve_cash",
                        "reason": f"Deflation ({new_inflation:.1%}) increases the value of cash holdings"
                    })
                    logger.info(f"Bot {self.player_id} preserving cash due to deflation ({new_inflation:.1%})")
            
            elif event_type == "economic_cycle_change":
                new_state = event_data.get("new_state")
                
                if new_state == "boom":
                    # During boom: Develop properties, consider selling at premium
                    actions.append({
                        "action": "adjust_strategy",
                        "strategy": "develop_and_sell",
                        "reason": "Economic boom provides opportunity for property development and sales at premium"
                    })
                    logger.info(f"Bot {self.player_id} adjusting strategy for boom economy")
                
                elif new_state in ["recession", "depression"]:
                    # During recession/depression: Buy undervalued properties, hold cash
                    actions.append({
                        "action": "adjust_strategy",
                        "strategy": "buy_undervalued",
                        "reason": f"{new_state.capitalize()} creates buying opportunities at reduced prices"
                    })
                    logger.info(f"Bot {self.player_id} adjusting strategy for {new_state} economy")
            
            # Return the planned actions
            return {
                "success": True,
                "actions": actions,
                "player_id": self.player_id
            }
            
        except Exception as e:
            logger.error(f"Error in Bot {self.player_id} economic event response: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": str(e),
                "player_id": self.player_id
            } 