from datetime import datetime
import random
import logging
from flask import current_app
from .. import db # Relative import for db
from ..player import Player # Relative import for Player
from ..property import Property # Relative import for Property
from ..game_state import GameState # Relative import for GameState
from ..transaction import Transaction # Relative import for Transaction
from ..bot_events.base_event import BotEvent
# New import for the handler
from ...services.bot_action_handler import BotActionHandler 
# New import for the decision maker
from ...logic.bot_decision_maker import BotDecisionMaker
# Import finance controller
from ...controllers.finance_controller import FinanceController

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
        """Perform actions before rolling (e.g., check events, manage properties)."""
        # To be implemented/refined by subclasses or decision maker
        actions = []
        
        # Check if the bot should trigger a special event
        event_action = self.check_for_special_event()
        if event_action:
            logger.info(f"Bot {self.player_id} triggered special event: {event_action.get('event', {}).get('name', 'Unknown')}")
            actions.append(event_action)
        
        # Consider taking a loan based on financial situation
        if random.random() < 0.3:  # 30% chance to consider a loan each turn
            loan_decision = self.decision_maker.decide_take_loan()
            
            if loan_decision.get('take_loan', False) and loan_decision.get('loan_amount', 0) > 0:
                logger.info(f"Bot {self.player_id} deciding to take a loan of ${loan_decision['loan_amount']}. Reason: {loan_decision['reason']}")
                
                # Execute the loan application
                try:
                    finance_controller = current_app.config.get('finance_controller')
                    if finance_controller:
                        loan_result = finance_controller.create_loan(
                            player_id=self.player_id,
                            pin=self.player.pin,
                            amount=loan_decision['loan_amount']
                        )
                        
                        if loan_result.get('success', False):
                            logger.info(f"Bot {self.player_id} successfully took a loan of ${loan_decision['loan_amount']}")
                            actions.append({
                                "action": "took_loan",
                                "amount": loan_decision['loan_amount'],
                                "loan_id": loan_result.get('loan', {}).get('id'),
                                "reason": loan_decision['reason']
                            })
                        else:
                            logger.warning(f"Bot {self.player_id} loan application failed: {loan_result.get('error', 'Unknown error')}")
                    else:
                        logger.warning(f"Bot {self.player_id} could not take loan: Finance controller not available")
                except Exception as e:
                    logger.error(f"Error while Bot {self.player_id} was taking a loan: {str(e)}")
        
        # TODO: Add calls to decision maker for property management (mortgage, build houses)
        # property_management_actions = self.decision_maker.manage_properties()
        # actions.extend(property_management_actions)
            
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
        
        # Check space type and delegate to appropriate handler method
        # TODO: Get board layout/space info from GameState or Board model
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

        # TODO: Handle other space types by calling specific methods in BotActionHandler
        # Example:
        # elif is_chance_card_space(new_position):
        #     return self.action_handler.handle_chance_card_space(self.player)
        # elif is_tax_space(new_position):
        #     return self.action_handler.handle_tax_space(self.player, new_position)
        # elif new_position == GO_TO_JAIL_POS:
        #     return self.action_handler.go_to_jail(self.player)
            
        else:
            logger.debug(f"Landed on non-property space {new_position}. No specific bot action implemented yet.")
            return [] # Return empty list if no action defined for the space

    # handle_property_space removed - handled by BotActionHandler

    # _calculate_rent removed - handled by BotActionHandler (as helper)

    # --- Decision Logic Methods (To be moved to BotDecisionMaker) ---
    
    # Decision logic methods removed - delegated to BotDecisionMaker

    # end_turn removed - Handled by BotActionHandler / GameController

    def end_turn(self):
        """Actions to take at the end of the turn (e.g., manage properties)"""
        # Placeholder for future logic like building houses, mortgaging
        pass 