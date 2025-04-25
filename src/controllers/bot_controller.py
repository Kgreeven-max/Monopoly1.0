import logging
import random
import time
import threading
from flask_socketio import emit
from flask import request, current_app
from sqlalchemy.orm import joinedload # For eager loading
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property, PropertyType
from src.models.bots import (
    BotPlayer, ConservativeBot, AggressiveBot, StrategicBot, OpportunisticBot,
    SharkBot, InvestorBot
)
from src.controllers.bot_event_controller import handle_bot_event, handle_scheduled_event
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Dictionary to store active bots
active_bots = {}

# Process lock for bot actions
bot_action_lock = threading.Lock()

# Bot action thread
bot_action_thread = None
bot_action_running = False

class BotController:
    """Controller for managing AI bot players' actions and decisions."""
    
    # Assuming dependencies based on app.py instantiation
    def __init__(self, app_config):
        self.app_config = app_config
        self.logger = logging.getLogger("bot_controller")
        # Get dependencies from app_config (ensure they are registered in app.py)
        self.game_logic = app_config.get('game_logic')
        self.game_controller = app_config.get('game_controller')
        self.property_controller = app_config.get('property_controller')
        self.auction_controller = app_config.get('auction_controller')
        self.banker = app_config.get('banker')
        self.special_space_controller = app_config.get('special_space_controller')
        # self.trade_controller = app_config.get('trade_controller') # Needed for trading logic
        self.socketio = app_config.get('socketio')
        
        # Add the bot controller instance to app_config for the bot action thread
        app_config['bot_controller_instance'] = self
        
        # Store reference to Flask app instance - needed for app context in bot thread
        if not app_config.get('app'):
            app_config['app'] = current_app._get_current_object()
        
        if not all([self.game_logic, self.game_controller, self.property_controller, 
                     self.auction_controller, self.banker, self.special_space_controller, self.socketio]):
             self.logger.error("BotController missing one or more dependencies!")
             # Handle initialization error

        self.logger.info("BotController initialized.")

    def create_bot(self, bot_name, bot_type='conservative', difficulty='medium'):
        """Create a new bot player
        
        Args:
            bot_name: Name of the bot
            bot_type: Type of bot strategy (conservative, aggressive, strategic, opportunistic, shark, investor)
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Bot player object if creation successful, None otherwise
        """
        try:
            # Get game state and starting money
            game_state = GameState.query.first()  # Assuming game_id=1 for now
            if not game_state:
                self.logger.error("Cannot create bot: Game state not found.")
                return None
            
            # Get starting money from settings, default to 1500 if not found
            starting_money = game_state.settings.get('starting_money', 1500) if hasattr(game_state, 'settings') else 1500
            self.logger.info(f"Retrieved starting money for bot creation: {starting_money}")
            
            # Create bot player in database
            bot_player = Player(
                username=bot_name,
                is_bot=True,
                in_game=True,
                money=starting_money,
                position=0,
                game_id=game_state.id
            )
            
            # Generate a PIN for the bot
            bot_player.pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Commit to database to get ID
            db.session.add(bot_player)
            db.session.commit()
            self.logger.info(f"Committed new bot player {bot_player.username} with ID: {bot_player.id}")
            
            # Create the bot strategy object based on type
            if bot_type == 'aggressive':
                active_bots[bot_player.id] = AggressiveBot(bot_player.id, difficulty)
            elif bot_type == 'strategic':
                active_bots[bot_player.id] = StrategicBot(bot_player.id, difficulty)
            elif bot_type == 'opportunistic':
                active_bots[bot_player.id] = OpportunisticBot(bot_player.id, difficulty)
            elif bot_type == 'shark':
                active_bots[bot_player.id] = SharkBot(bot_player.id, difficulty)
            elif bot_type == 'investor':
                active_bots[bot_player.id] = InvestorBot(bot_player.id, difficulty)
            else:  # default to conservative
                active_bots[bot_player.id] = ConservativeBot(bot_player.id, difficulty)
            
            self.logger.info(f"Registered bot in active_bots dictionary with key {bot_player.id}")
            self.logger.info(f"Active bots: {list(active_bots.keys())}")
            
            # Start the bot action thread if not running
            start_bot_action_thread(self.socketio, self.app_config)
            
            # Broadcast bot created event if socketio is available
            if self.socketio:
                self.socketio.emit('bot_created', {
                    'bot_id': bot_player.id,
                    'name': bot_player.username,
                    'type': bot_type,
                    'difficulty': difficulty,
                    'money': bot_player.money,
                    'position': bot_player.position
                })
            
            self.logger.info(f"Created new bot: {bot_player.username} (ID: {bot_player.id}, Type: {bot_type}, Difficulty: {difficulty})")
            return bot_player
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating bot: {str(e)}", exc_info=True)
            return None

    def take_turn(self, player_id, game_id=1):
        """Determine and execute the bot's actions for its turn."""
        self.logger.info(f"--- Bot Player {player_id} starting turn in Game {game_id} ---")
        time.sleep(random.uniform(0.5, 1.5)) # Simulate thinking time

        try:
            # Get game state - handle both numeric and string UUIDs
            game_state = None
            
            # Try numeric ID first (used for integers)
            try:
                if isinstance(game_id, int) or (isinstance(game_id, str) and game_id.isdigit()):
                    game_state = GameState.query.get(int(game_id))
            except (ValueError, TypeError):
                pass
            
            # If not found and it's a string (potentially UUID), try by game_id column
            if not game_state and isinstance(game_id, str):
                self.logger.info(f"Looking up GameState by UUID in game_id column: {game_id}")
                game_state = GameState.query.filter_by(game_id=game_id).first()
                
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Game {game_id} is not active. Bot {player_id} stopping turn.")
                return
                
            if game_state.current_player_id != player_id:
                self.logger.warning(f"Bot {player_id} attempted to take turn, but current player is {game_state.current_player_id}. Stopping.")
                return

            # Use the game_state's game_id for all operations (the UUID string)
            game_id = game_state.game_id
            
            player = Player.query.get(player_id)
            if not player or player.is_bankrupt or not player.in_game:
                self.logger.warning(f"Bot player {player_id} is invalid or bankrupt. Ending turn.")
                self.game_controller._internal_end_turn(player_id, game_id)
                return

            # 1. Handle Jail
            if player.in_jail:
                jail_action_taken = self._handle_jail(player, game_state)
                if jail_action_taken: # If stayed in jail or managed assets
                    # Check if turn should end based on jail action result
                    if game_state.expected_action_type != 'roll_again': # If didn't roll doubles to get out
                         self.logger.info(f"Bot {player_id} finished jail action, ending turn.")
                         # End turn might have been called by GameLogic already if roll failed
                         # Ensure state is consistent before potentially ending turn again.
                         current_game_state = GameState.query.filter_by(game_id=game_id).first()
                         if current_game_state and current_game_state.current_player_id == player_id: 
                             self.game_controller._internal_end_turn(player_id, game_id)
                         return # End processing for this turn
                # If jail_action_taken is False, it means bot got out and needs to proceed with roll
                
            # 2. Main Turn Loop (Handles doubles)
            turn_active = True
            roll_count = 0
            max_rolls = 3 # Prevent infinite loop - 3 doubles sends to jail

            while turn_active and roll_count < max_rolls:
                roll_count += 1
                self.logger.info(f"Bot {player_id} performing roll #{roll_count}")
                
                # Safety check for too many rolls - shouldn't happen but protect against infinite loop
                if roll_count > 3:
                    self.logger.warning(f"Bot {player_id} has rolled too many times ({roll_count}). Forcing end of turn.")
                    break
                
                time.sleep(random.uniform(0.5, 1.0))
                
                # Check game state again before rolling
                game_state = GameState.query.filter_by(game_id=game_id).first()
                if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                     self.logger.warning(f"Game state changed mid-turn for bot {player_id}. Stopping.")
                     turn_active = False; break

                # Validate expected action before rolling
                if game_state.expected_action_type not in [None, 'roll_again']: 
                     self.logger.warning(f"Bot {player_id} expected action is '{game_state.expected_action_type}', cannot roll. Handling action first.")
                     self._handle_pending_action(player, game_state)
                     # Re-check state after handling pending action
                     game_state = GameState.query.filter_by(game_id=game_id).first()
                     if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                          self.logger.warning(f"Game state changed after handling pending action for bot {player_id}. Stopping.")
                          turn_active = False; break
                           
                # Roll the dice
                if not self.game_logic:
                     self.logger.error(f"GameLogic not found for bot {player_id}. Cannot roll dice.")
                     turn_active = False; break
                      
                # Roll dice and move the player
                roll_result = self.game_logic.roll_dice_and_move(player_id)
                
                if not roll_result or not roll_result.get("success"):
                     self.logger.warning(f"Bot {player_id} roll failed: {roll_result.get('error') if roll_result else 'Unknown error'}")
                     # End turn if roll fails
                     self.game_controller._internal_end_turn(player_id, game_id)
                     return
                
                # Check if we rolled doubles (to continue turn)
                rolled_doubles = roll_result.get("rolled_doubles", False)
                
                # Handle third doubles case - should send to jail
                if rolled_doubles and roll_count == 3:
                    self.logger.info(f"Bot {player_id} rolled doubles for the third time - should be sent to jail")
                    # The game logic should handle this automatically, but let's check
                    # Re-fetch player to see if they're in jail
                    db.session.refresh(player)
                    if player.in_jail:
                        self.logger.info(f"Bot {player_id} confirmed in jail after third doubles")
                        turn_active = False
                        break
                
                # Get updated game state for potential actions
                game_state = GameState.query.filter_by(game_id=game_id).first()
                
                # Process any landing actions
                if game_state and game_state.current_player_id == player_id and game_state.expected_action_type:
                     # Sleep to simulate thinking about the action
                     time.sleep(random.uniform(0.3, 0.8))
                     
                     # Handle the action
                     self.logger.info(f"Bot {player_id} performing landing action: {game_state.expected_action_type}")
                     action_result = self._handle_pending_action(player, game_state)
                     
                     # Re-check state
                     game_state = GameState.query.filter_by(game_id=game_id).first()
                     if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                          self.logger.warning(f"Game state changed after handling landing action for bot {player_id}. Stopping.")
                          turn_active = False; break
                
                # Should we continue the turn?
                if not rolled_doubles or roll_count >= max_rolls or game_state.expected_action_type == 'end_turn':
                     self.logger.info(f"Bot {player_id} did not roll doubles or turn ended. Finishing turn sequence.")
                     turn_active = False
                else:
                     self.logger.info(f"Bot {player_id} rolled doubles, continuing turn.")

            # 3. Consider doing financial management before ending turn
            # Only do this occasionally to avoid too many financial operations
            if random.random() < 0.25:  # 25% chance each turn
                self.logger.info(f"Bot {player_id} considering financial management")
                self.manage_investments(player_id, game_id)
                
            # 4. End Turn Explicitly
            self.logger.info(f"Bot {player_id} turn loop finished. Explicitly ending turn.")
            
            # Recheck current player
            game_state = GameState.query.filter_by(game_id=game_id).first()
            if game_state and game_state.current_player_id == player_id:
                self.game_controller._internal_end_turn(player_id, game_id)
            
        except Exception as e:
            self.logger.error(f"Error in bot {player_id} turn: {str(e)}", exc_info=True)
            
            # Attempt recovery - end turn if we're the current player
            try:
                current_game_state = GameState.query.filter_by(game_id=game_id).first()
                if current_game_state and current_game_state.current_player_id == player_id:
                     self.game_controller._internal_end_turn(player_id, game_id)
            except Exception as inner_e:
                 self.logger.error(f"Failed to gracefully end turn for bot {player_id} after error: {inner_e}")

        self.logger.info(f"--- Bot Player {player_id} finished turn --- ")
        return {'success': True} # Indicate completion

    def _handle_pending_action(self, player, game_state):
         """Handles actions that were pending at the start of the bot's turn decision."""
         action_type = game_state.expected_action_type
         details = game_state.expected_action_details
         player_id = player.id
         game_id = game_state.game_id
         
         self.logger.info(f"Bot {player_id} handling pending action: {action_type}")
         
         # Enhanced error handling for pending actions
         try:
             # Check if action type is valid 
             if not action_type:
                 self.logger.warning(f"Bot {player_id} has no pending action (expected_action_type is None)")
                 return False
             
             # Special handling for roll_dice action - bot should just roll the dice
             if action_type == "roll_dice":
                 self.logger.info(f"Bot {player_id} handling roll_dice action directly")
                 # Clear the expected action first to avoid recursion
                 game_state.expected_action_type = None
                 game_state.expected_action_details = None
                 db.session.commit()
                 
                 # Let the game_logic handle the dice roll
                 if self.game_logic:
                     roll_result = self.game_logic.roll_dice_and_move(player_id)
                     if roll_result and roll_result.get('success'):
                         return True
                 return False
             
             # Convert expected_action_type into a structured landing action
             landing_action = {
                 'action': action_type,
                 'game_id': game_id  # Use UUID instead of numeric ID
             }
             
             # Add details if available
             if details:
                 landing_action.update(details)
                 
             # Use the landing action handler with this structured action
             return self._handle_landing_action(player, landing_action, game_state)
             
         except Exception as e:
             self.logger.error(f"Error handling pending action for bot {player_id}: {str(e)}", exc_info=True)
             
             # Attempt to clear the action to prevent stuck state
             try:
                 game_state.expected_action_type = None
                 game_state.expected_action_details = None
                 db.session.commit()
                 self.logger.warning(f"Bot {player_id} action '{action_type}' wasn't cleared by handler. Clearing manually.")
             except Exception as recovery_error:
                 self.logger.error(f"Failed to recover from action error: {str(recovery_error)}")
             
             return False # Indicate action handling failed

    def _handle_landing_action(self, player, landing_action, game_state):
        """Processes the result of landing on a space."""
        action_type = landing_action.get('action')
        player_id = player.id
        game_id = game_state.game_id

        self.logger.info(f"Bot {player_id} handling landing action: {action_type}")
        time.sleep(random.uniform(0.3, 0.8))

        if action_type == 'buy_or_auction_prompt':
            # Handle property purchase decision
            property_id = landing_action.get('property_id')
            
            # First verify the player is actually on a property space
            player_position = player.position
            if player_position in [0, 2, 4, 7, 10, 17, 20, 22, 30, 33, 36, 38]:
                self.logger.info(f"Player is on a non-property space at position {player_position}")
                # Clear the action since we can't buy on non-property spaces
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.commit()
                return True  # Return true to indicate action was handled
            
            # Find the property at the player's current position - ALWAYS use position as source of truth
            correct_property = Property.query.filter_by(position=player_position, game_id=game_id).first()
            
            if not correct_property:
                self.logger.error(f"No property found at position {player_position} for game {game_id}")
                # Clear the action since we can't find the correct property
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.commit()
                return True  # Return true to indicate action was handled
            
            # Override any property_id from the landing_action with the correct one
            property_id = correct_property.id
            self.logger.info(f"Using property {correct_property.name} (ID: {property_id}) at player position {player_position}")
            
            # Check if property is already owned
            if correct_property.owner_id is not None:
                # If somehow the player has been prompted to buy a property that's already owned, clear the action
                self.logger.warning(f"Property {property_id} already owned by Player {correct_property.owner_id}")
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.commit()
                return True  # Return true to indicate action was handled
            
            # Extract cost from property_obj
            cost = correct_property.price if hasattr(correct_property, 'price') else correct_property.current_price
            
            # Use decision maker to determine whether to buy
            decision = self._decide_buy_property(player, property_id, cost)
            if decision:  # The method returns True/False, not a dictionary with a "buy" key
                # Bot decides to buy the property
                self.logger.info(f"Bot {player_id} decided to BUY property {property_id}")
                
                # Call game controller to purchase
                purchase_result = self.game_controller.handle_property_purchase(
                    {"player_id": player_id, "property_id": property_id, "game_id": game_id, "is_bot": True}
                )
                
                # Always clear the expected action after handling, regardless of success
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.commit()
                
                return purchase_result.get("success", False)
            else:
                # Bot decides to trigger auction
                self.logger.info(f"Bot {player_id} decided to DECLINE buy for property {property_id}")
                
                # Send the decline purchase request to the game controller
                decline_result = self.game_controller.handle_property_decline(
                    {"player_id": player_id, "property_id": property_id, "game_id": game_id, "is_bot": True}
                )
                
                # Always clear the expected action after handling, regardless of success
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.commit()
                
                # Auction handling if the decline was successful
                if decline_result.get("success", False):
                    self.logger.info(f"Successfully declined purchase, auction should be triggered automatically")
                    return True
                
                return decline_result.get("success", False)

        elif action_type == 'draw_chance_card':
            self.logger.info(f"Bot {player_id} drawing Chance card.")
            # Get game_id from landing_action if available, otherwise use from game_state
            card_game_id = landing_action.get('game_id', game_state.game_id)
            result = self.special_space_controller.process_chance_card(player_id, card_game_id)
            
            # Clear the expected action after handling
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.commit()
            
            return result.get("success", False)

        elif action_type == 'draw_community_chest_card':
            self.logger.info(f"Bot {player_id} drawing Community Chest card.")
            # Get game_id from landing_action if available, otherwise use from game_state
            card_game_id = landing_action.get('game_id', game_state.game_id)
            result = self.special_space_controller.process_community_chest_card(player_id, card_game_id)
            
            # Clear the expected action after handling
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.commit()
            
            return result.get("success", False)
        
        elif action_type == 'free_parking':
            self.logger.info(f"Bot {player_id} landed on Free Parking.")
            result = self.special_space_controller.handle_free_parking_space(game_state.id, player_id)
            
            # Clear the expected action after handling
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.commit()
            
            return result.get("success", False)
        
        elif action_type == 'market_fluctuation':
            self.logger.info(f"Bot {player_id} landed on Market Fluctuation.")
            result = self.special_space_controller.handle_market_fluctuation_space(game_state.id, player_id)
            
            # Clear the expected action after handling
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.commit()
            
            return result.get("success", False)
        
        elif action_type == 'pay_tax':
             tax_details = landing_action.get('tax_details', {})
             amount = tax_details.get('amount') # Assuming amount is in details
             space_name = landing_action.get('space_name', 'Tax Space')
             self.logger.info(f"Bot {player_id} needs to pay tax: {amount}")
             payment_result = self.banker.player_pays_community_fund(player_id, amount, f"Tax: {space_name}")
             
             # Clear expected state regardless of payment success
             game_state.expected_action_type = None
             game_state.expected_action_details = None
             db.session.commit()
             
             if not payment_result['success']:
                  self.logger.warning(f"Bot {player_id} could not pay tax. Needs asset management.")
                  return self._manage_assets(player, amount)
             
             return payment_result.get("success", False)
       
        elif action_type in ['insufficient_funds_for_rent', 'manage_assets_or_bankrupt', 'manage_assets_for_jail_fine']:
             required_amount = landing_action.get('required', landing_action.get('rent_amount', 0))
             self.logger.warning(f"Bot {player_id} needs to manage assets. Required: {required_amount}")
             
             # Clear expected state regardless of asset management success
             game_state.expected_action_type = None
             game_state.expected_action_details = None
             db.session.commit()
             
             return self._manage_assets(player, required_amount)
       
        elif action_type == 'jail_action_prompt':
            # Handle jail prompt directly when it comes through as a landing action
            self.logger.info(f"Bot {player_id} handling jail action prompt")
            # Pay the fine to get out rather than rolling for doubles in this case
            fine = 50  # Standard fine
            
            # Clear expected action state regardless of what happens next
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.commit()
            
            if player.money >= fine:
                self.logger.info(f"Bot {player_id} paying ${fine} fine to get out of jail.")
                pay_result = self.banker.player_pays_bank(player_id, fine, "Jail fine")
                if pay_result['success']:
                    player.in_jail = False
                    player.jail_turns = 0
                    db.session.commit()
                    return True
                else:
                    self.logger.warning(f"Bot {player_id} failed to pay jail fine: {pay_result.get('error')}. Managing assets.")
                    return self._manage_assets(player, fine)
            else:
                self.logger.info(f"Bot {player_id} cannot afford jail fine. Managing assets.")
                return self._manage_assets(player, fine)
       
        # Actions like 'paid_rent', 'went_to_jail', 'passive_space' require no bot decision.
        else:
             self.logger.debug(f"Bot {player_id} encountered landing action '{action_type}' requiring no specific decision.")
             
             # Clear the expected action for any action we don't specifically handle
             game_state.expected_action_type = None
             game_state.expected_action_details = None
             db.session.commit()
             
             return True  # Action was handled

    def _decline_buy_action(self, player_id, property_id, game_id):
         """Handles the logic after a bot declines to buy."""
         # Need to check game settings if auction is required
         # Try to get game state by id - first check if this is a UUID string
         game_state = None
         
         try:
             # First try to find game state by the game_id attribute (UUID)
             if isinstance(game_id, str) and '-' in game_id:
                 self.logger.info(f"Looking up GameState by UUID field: {game_id}")
                 game_state = GameState.query.filter_by(game_id=game_id).first()
             
             # If not found or ID is numeric, try by primary key
             if not game_state:
                 try:
                     # Convert to int only if it's numeric
                     if isinstance(game_id, int) or (isinstance(game_id, str) and game_id.isdigit()):
                         pk_id = int(game_id)
                         self.logger.info(f"Looking up GameState by primary key: {pk_id}")
                         game_state = GameState.query.get(pk_id)
                 except (ValueError, TypeError):
                     self.logger.warning(f"Could not convert game_id {game_id} to integer primary key")
             
             # Final fallback - get main game state
             if not game_state:
                 self.logger.warning(f"Could not find game_state for game ID {game_id}, falling back to primary game")
                 game_state = GameState.get_instance()
                 
                 # Update the instance if its game_id doesn't match
                 if game_state and game_state.game_id != game_id and isinstance(game_id, str):
                     self.logger.info(f"Refreshing game state instance to match requested game ID: {game_id}")
                     success = game_state.refresh_from_db(game_id=game_id)
                     if not success:
                         self.logger.error(f"Failed to refresh game state to match requested game ID: {game_id}")
         except Exception as e:
             self.logger.error(f"Error finding game state: {str(e)}", exc_info=True)
             return
         
         if not game_state:
             self.logger.error(f"Could not find game_state for game ID {game_id} in _decline_buy_action")
             return
             
         # Now handle the auction logic
         if game_state.auction_required:
             self.logger.info(f"Bot {player_id} triggering auction for property {property_id}")
             # Auction controller should handle the flow from here
             self.auction_controller.start_auction(property_id, game_state.id)
         else:
             self.logger.info(f"Bot {player_id} declined property {property_id}, no auction required. Turn should end.")
             # Clear expected state manually if GameController didn't already
             if game_state.expected_action_type == 'buy_or_auction_prompt':
                 game_state.expected_action_type = None
                 game_state.expected_action_details = None
                 db.session.commit()
             # Turn progression is handled by the main loop or GameController

    def _handle_jail(self, player, game_state):
        """Decides and performs action for a bot in jail."""
        player_id = player.id
        game_id = game_state.game_id
        action_taken = False # Flag if an action resolving the jail state was made
        
        self.logger.info(f"Bot {player_id} deciding jail action. Turns spent: {player.jail_turns}")
        # TODO: Check for Get Out of Jail Free cards
        
        # Simple Strategy: Try rolling first, pay on last turn if needed.
        if player.jail_turns < 2: # Try rolling on turn 0 and 1
            self.logger.info(f"Bot {player_id} attempting to roll for doubles.")
            # Roll is handled by the main loop calling roll_dice_and_move
            # No action needed here other than letting the main loop proceed
            action_taken = False # Let main loop handle roll
        else:
            # Pay fine on the 3rd turn if possible
            fine = 50 # Standard fine
            if player.money >= fine:
                self.logger.info(f"Bot {player_id} paying ${fine} fine to get out of jail.")
                pay_result = self.banker.player_pays_bank(player_id, fine, "Jail fine")
                if pay_result['success']:
                     player.in_jail = False
                     player.jail_turns = 0
                     # Clear expected action state
                     game_state.expected_action_type = None
                     game_state.expected_action_details = None
                     db.session.commit() 
                     action_taken = False # Got out, proceed to roll in main loop
                else:
                     self.logger.warning(f"Bot {player_id} failed to pay jail fine despite sufficient cash? Error: {pay_result.get('error')}. Managing assets.")
                     self._manage_assets(player, fine)
                     action_taken = True # Still needs to resolve payment/bankruptcy
            else:
                 self.logger.info(f"Bot {player_id} cannot afford jail fine. Managing assets.")
                 self._manage_assets(player, fine)
                 action_taken = True # Still needs to resolve payment/bankruptcy
        return action_taken

    def _decide_buy_property(self, player, property_id, cost):
        """Simple decision logic for buying property."""
        # Basic Strategy: Buy if affordable and has decent potential
        if cost is None: return False # Cannot buy if cost unknown
        affordable_threshold = 1.5 # Buy if cost is less than cash / threshold
        min_cash_after = 100 # Try to keep at least this much cash after buying
        
        if player.money >= cost + min_cash_after: # Check affordability first
        # if player.cash / affordable_threshold > cost: 
            # TODO: Add basic property evaluation (e.g., based on type or group)
            self.logger.debug(f"Bot {player.id} decides TRUE for buying property {property_id} (Cost: {cost}, Cash: {player.money})")
            return True
        else:
            self.logger.debug(f"Bot {player.id} decides FALSE for buying property {property_id} (Cost: {cost}, Cash: {player.money})")
            return False

    def _manage_assets(self, player, amount_needed):
        """Logic to raise funds by taking loans, HELOCs, and/or mortgaging properties."""
        player_id = player.id
        self.logger.info(f"Bot {player_id} attempting to manage assets to raise ${amount_needed}")
        
        # Get finance controller
        finance_controller = None
        if hasattr(self, 'app_config'):
            finance_controller = self.app_config.get('finance_controller')
        
        # First try to get a loan if the amount needed is substantial
        # and the player's credit score is decent
        loan_taken = False
        
        if amount_needed > 100 and player.credit_score >= 600:
            # If we have a finance controller, try to take a loan
            if finance_controller:
                self.logger.info(f"Bot {player_id} attempting to take a loan for ${amount_needed}")
                
                # Bots are conservative with loans - don't borrow way more than needed
                loan_amount = min(amount_needed * 1.5, 500)  # Maximum $500 loan, or 1.5x needed amount
                
                # Get a loan
                try:
                    loan_result = finance_controller.create_loan(player_id, player.pin, loan_amount)
                    if loan_result.get('success'):
                        self.logger.info(f"Bot {player_id} successfully took a loan of ${loan_amount}")
                        loan_taken = True
                        
                        # Refresh player object to get updated money
                        db.session.refresh(player)
                        
                        # If we have enough money now, we're done
                        if player.money >= amount_needed:
                            self.logger.info(f"Bot {player_id} now has enough money (${player.money}) after loan")
                            return
                    else:
                        error = loan_result.get('error', 'Unknown error')
                        self.logger.warning(f"Bot {player_id} failed to get a loan: {error}")
                except Exception as e:
                    self.logger.warning(f"Error while attempting to get loan for Bot {player_id}: {str(e)}")
        
        # If we still need money and finance controller is available, try HELOCs
        if player.money < amount_needed and finance_controller:
            # Calculate how much more we need
            amount_still_needed = amount_needed - player.money
            self.logger.info(f"Bot {player_id} still needs ${amount_still_needed} after loan attempt, trying HELOC")
            
            # Get bot's properties that are not mortgaged
            properties = Property.query.filter_by(
                owner_id=player_id, 
                is_mortgaged=False
            ).order_by(Property.current_price.desc()).all()
            
            # Try to get a HELOC on the most valuable property first
            heloc_taken = False
            for prop in properties:
                if prop.houses > 0 or prop.hotel:
                    # Skip properties with houses/hotels as they typically have higher value
                    continue
                    
                try:
                    # Determine a reasonable HELOC amount
                    heloc_amount = min(amount_still_needed * 1.2, prop.current_price * 0.5)
                    heloc_amount = max(int(heloc_amount), 50)  # Minimum $50 HELOC
                    
                    self.logger.info(f"Bot {player_id} attempting HELOC of ${heloc_amount} on {prop.name}")
                    
                    heloc_result = finance_controller.create_heloc(player_id, player.pin, prop.id, heloc_amount)
                    if heloc_result.get('success'):
                        self.logger.info(f"Bot {player_id} successfully got HELOC on {prop.name} for ${heloc_amount}")
                        heloc_taken = True
                        
                        # Refresh player object to get updated money
                        db.session.refresh(player)
                        
                        # If we have enough money now, we're done
                        if player.money >= amount_needed:
                            self.logger.info(f"Bot {player_id} now has enough money (${player.money}) after HELOC")
                            return
                            
                        # If we still need more, try another property
                        amount_still_needed = amount_needed - player.money
                    else:
                        error = heloc_result.get('error', 'Unknown error')
                        self.logger.warning(f"Bot {player_id} failed to get HELOC on {prop.name}: {error}")
                except Exception as e:
                    self.logger.warning(f"Error attempting HELOC for Bot {player_id} on {prop.name}: {str(e)}")
        
        # If we still need money, try mortgaging properties
        if player.money < amount_needed:
            # Calculate how much more we need
            amount_still_needed = amount_needed - player.money
            self.logger.info(f"Bot {player_id} still needs ${amount_still_needed} after loan/HELOC attempts")
            
            # Fetch unmortgaged properties, ordered by value (ascending) to mortgage cheapest first
            # Use joinedload to avoid N+1 queries for owner check
            properties_to_mortgage = Property.query.options(joinedload(Property.owner))\
                                        .filter_by(owner_id=player_id, is_mortgaged=False)\
                                        .order_by(Property.price).all()

            amount_raised = 0
            for prop in properties_to_mortgage:
                if player.money + amount_raised >= amount_needed:
                     break # Raised enough
                
                self.logger.info(f"Bot {player_id} attempting to mortgage {prop.name} (Value: {prop.mortgage_value})")
                time.sleep(random.uniform(0.2, 0.5))
                # Assuming mortgage_property exists and handles cash transfer
                mortgage_result = self.property_controller.mortgage_property(player_id, player.pin, prop.id)
                if mortgage_result.get('success'):
                     amount_raised += prop.mortgage_value # Add mortgage value to potential cash
                     self.logger.info(f"Bot {player_id} successfully mortgaged {prop.name}. Raised ${amount_raised} so far.")
                else:
                     self.logger.warning(f"Bot {player_id} failed to mortgage {prop.name}: {mortgage_result.get('error')}")

        # Re-check cash after attempting loans, HELOCs, and mortgages
        db.session.refresh(player) # Refresh player object to get updated cash
        if player.money >= amount_needed:
            self.logger.info(f"Bot {player_id} successfully raised enough funds (${player.money}) after managing assets.")
            # Now attempt the original payment again if possible (e.g., rent/fine)
            # This requires more state - knowing WHAT the original debt was for.
            # For now, assume the calling context might re-attempt payment or the next turn starts.
            # Clear the manage_assets state if it was set
            game_state = GameState.query.get(player.game_id)
            if game_state and game_state.expected_action_type and 'manage_assets' in game_state.expected_action_type:
                 game_state.expected_action_type = None # Or set to retry payment? 
                 game_state.expected_action_details = None
                 db.session.commit()
        else:
            self.logger.warning(f"Bot {player_id} FAILED to raise sufficient funds (${amount_needed} needed, has ${player.money}). Declaring bankruptcy.")
            # Declare bankruptcy
            self.game_controller.declare_bankruptcy(player_id)
            
    def manage_investments(self, player_id, game_id=1):
        """
        Manage a bot's investments and financial decisions at the end of their turn.
        Consider CDs, paying off loans, etc. based on the bot's strategy and economic conditions.
        
        Args:
            player_id: The ID of the bot player
            game_id: The ID of the game
            
        Returns:
            dict: Results of the investment decisions
        """
        self.logger.info(f"Bot {player_id} managing investments")
        
        try:
            # Get game state - handle both numeric and string UUIDs
            game_state = None
            
            # Try numeric ID first (used for integers)
            try:
                if isinstance(game_id, int) or (isinstance(game_id, str) and game_id.isdigit()):
                    game_state = GameState.query.get(int(game_id))
            except (ValueError, TypeError):
                pass
                
            # If not found and it's a string (potentially UUID), try by game_id column
            if not game_state and isinstance(game_id, str):
                self.logger.info(f"Looking up GameState by UUID in game_id column: {game_id}")
                game_state = GameState.query.filter_by(game_id=game_id).first()
                if game_state:
                    actual_game_id = game_state.id
                    
            if not game_state:
                self.logger.error(f"Game state {game_id} not found")
                return {'success': False, 'error': 'Game not found'}
            
            player = Player.query.get(player_id)
            if not player or player.is_bankrupt:
                return {"success": False, "error": "Player not found or bankrupt"}
                
            # Get finance controller
            finance_controller = None
            if hasattr(self, 'app_config'):
                finance_controller = self.app_config.get('finance_controller')
                
            if not finance_controller:
                return {"success": False, "error": "Finance controller not available"}
            
            # Get economic conditions from game state
            economic_state = game_state.economic_state if hasattr(game_state, 'economic_state') else "neutral"
            inflation_rate = game_state.inflation_rate if hasattr(game_state, 'inflation_rate') else 0.02
            interest_rate = game_state.base_interest_rate if hasattr(game_state, 'base_interest_rate') else 0.03
                
            self.logger.info(f"Bot {player_id} considering investments in {economic_state} economy (inflation: {inflation_rate:.2f}, interest: {interest_rate:.2f})")
                
            # Get the bot's financial summary
            try:
                financial_summary = finance_controller.get_player_financial_summary(player_id)
                if not financial_summary.get('success'):
                    return {"success": False, "error": "Failed to get financial summary"}
                    
                loans = financial_summary.get('loans', [])
                cds = financial_summary.get('cds', [])
                helocs = financial_summary.get('helocs', [])
                
                self.logger.info(f"Bot {player_id} financial status: ${player.money} cash, {len(loans)} loans, {len(cds)} CDs, {len(helocs)} HELOCs")
                
                actions_taken = []
                
                # Cash threshold for investments - keep this amount as reserve
                # During recession, keep more cash on hand
                min_cash_reserve = 200
                if economic_state == "recession":
                    min_cash_reserve = 300  # Keep more cash during recession
                elif economic_state == "boom":
                    min_cash_reserve = 150  # Can keep less cash during boom
                    
                excess_cash = player.money - min_cash_reserve
                
                # First, check if we should pay off any high-interest loans or HELOCs
                if excess_cash > 100:
                    # Sort loans/HELOCs by interest rate (highest first)
                    all_debts = []
                    for loan in loans:
                        all_debts.append({
                            'type': 'loan',
                            'id': loan['id'],
                            'interest_rate': loan['interest_rate'],
                            'current_value': loan['current_value'],
                            'original_amount': loan['amount']
                        })
                        
                    for heloc in helocs:
                        all_debts.append({
                            'type': 'heloc',
                            'id': heloc['id'],
                            'interest_rate': heloc['interest_rate'],
                            'current_value': heloc['current_value'],
                            'original_amount': heloc['amount']
                        })
                        
                    # Sort by interest rate (highest first)
                    all_debts.sort(key=lambda x: x['interest_rate'], reverse=True)
                    
                    # Log the debt situation
                    if all_debts:
                        self.logger.info(f"Bot {player_id} has {len(all_debts)} outstanding debts, highest rate: {all_debts[0]['interest_rate']:.2f}")
                    
                    # During recession, more aggressive debt payoff
                    min_interest_to_pay = 0.06  # Default - pay off debts with >6% interest
                    if economic_state == "recession":
                        min_interest_to_pay = 0.04  # More aggressive payoff during recession
                    elif economic_state == "boom":
                        min_interest_to_pay = 0.08  # Less aggressive during boom (invest instead)
                    
                    # Try to pay off high-interest debts
                    for debt in all_debts:
                        # Only pay off debts above the threshold
                        if debt['interest_rate'] < min_interest_to_pay:
                            continue
                            
                        # Determine payment amount - full payoff if possible, otherwise partial
                        payoff_amount = min(debt['current_value'], excess_cash)
                        if payoff_amount < 50:
                            continue  # Too small to bother with
                            
                        try:
                            if debt['type'] == 'loan':
                                result = finance_controller.repay_loan(player_id, player.pin, debt['id'], payoff_amount)
                                debt_type = 'loan'
                            else:  # heloc
                                # Assuming there's a repay_heloc method
                                if hasattr(finance_controller, 'repay_heloc'):
                                    result = finance_controller.repay_heloc(player_id, player.pin, debt['id'], payoff_amount)
                                else:
                                    continue
                                debt_type = 'HELOC'
                                
                            if result.get('success'):
                                self.logger.info(f"Bot {player_id} paid ${payoff_amount} toward {debt_type} #{debt['id']} (rate: {debt['interest_rate']:.2f})")
                                actions_taken.append(f"Paid ${payoff_amount} toward {debt_type}")
                                
                                # Update excess cash
                                excess_cash -= payoff_amount
                                if excess_cash <= 100:
                                    break  # Stop if reserve is getting low
                            else:
                                self.logger.warning(f"Bot {player_id} failed to pay {debt_type}: {result.get('error')}")
                        except Exception as e:
                            self.logger.warning(f"Error paying debt for Bot {player_id}: {str(e)}")
                
                # If we still have excess cash, consider investing in CDs
                if excess_cash > 200:
                    # Investment strategy based on economic conditions
                    invest_percentage = 0.7  # Default - invest 70% of excess
                    
                    if economic_state == "recession":
                        # During recession, be more conservative with investments
                        invest_percentage = 0.5  # Only invest 50% of excess
                    elif economic_state == "boom":
                        # During boom, more aggressive investment
                        invest_percentage = 0.8  # Invest 80% of excess
                    
                    # Amount to invest
                    invest_amount = int(excess_cash * invest_percentage)
                    
                    # Determine CD term length based on bot type, game state, and economy
                    current_lap = game_state.current_lap if game_state else 0
                    
                    # Default to short term (3 laps)
                    cd_term = 3
                    
                    # Adjust based on economic state
                    if economic_state == "recession":
                        cd_term -= 1  # Shorter terms during recession
                    elif economic_state == "boom":
                        cd_term += 1  # Longer terms during boom (higher rates)
                    
                    # Adjust based on bot type
                    bot = active_bots.get(player_id)
                    if bot and isinstance(bot, ConservativeBot):
                        cd_term += 2  # Longer term for conservative bots
                    elif bot and isinstance(bot, AggressiveBot):
                        cd_term -= 1  # Shorter term for aggressive bots
                    
                    # Ensure term is at least 1 lap
                    cd_term = max(1, cd_term)
                    
                    # Don't create CDs with terms that would extend beyond reasonable game length
                    max_reasonable_laps = 40  # Assume games don't go much beyond 40 laps
                    if current_lap + cd_term > max_reasonable_laps:
                        cd_term = max(1, max_reasonable_laps - current_lap)
                    
                    try:
                        result = finance_controller.create_cd(player_id, player.pin, invest_amount, cd_term)
                        if result.get('success'):
                            est_return = result.get('estimated_return', invest_amount * (1 + 0.03 * cd_term))
                            self.logger.info(f"Bot {player_id} invested ${invest_amount} in a {cd_term}-lap CD (est. return: ${est_return})")
                            actions_taken.append(f"Invested ${invest_amount} in {cd_term}-lap CD")
                        else:
                            self.logger.warning(f"Bot {player_id} failed to create CD: {result.get('error')}")
                    except Exception as e:
                        self.logger.warning(f"Error creating CD for Bot {player_id}: {str(e)}")
                
                # Log investment summary
                if actions_taken:
                    self.logger.info(f"Bot {player_id} completed {len(actions_taken)} financial actions: {', '.join(actions_taken)}")
                else:
                    self.logger.info(f"Bot {player_id} made no financial moves this turn")
                        
                return {
                    "success": True,
                    "player_id": player_id,
                    "actions": actions_taken,
                    "economic_state": economic_state,
                    "game_id": game_id,
                }
            except Exception as e:
                self.logger.error(f"Error managing investments for Bot {player_id}: {str(e)}")
                return {"success": False, "error": str(e)}
        except Exception as e:
            self.logger.error(f"Error in manage_investments for Bot {player_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def participate_in_auction(self, player_id, property_id, current_bid, current_high_bidder_id):
        """Determine if the bot should bid in an auction and return the bid amount or None."""
        with self.app_config.get('app').app_context(): # Ensure context
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            if not player or player.is_bankrupt or not property_obj:
                return None # Cannot participate
            
            if player.id == current_high_bidder_id:
                 return None # Don't bid against self

            # Simple Strategy: Bid up to 110% of property price if affordable
            max_bid_percentage = 1.10 
            max_willing_bid = int(property_obj.price * max_bid_percentage)
            min_cash_after = 50 # Keep some cash reserve

            if current_bid < max_willing_bid and player.money > current_bid + min_cash_after:
                # Bid slightly more than current bid
                bid_increment = max(1, int(current_bid * 0.05)) # Bid 5% more, min $1
                next_bid = min(current_bid + bid_increment, max_willing_bid) # Don't exceed max willing bid
                
                # Ensure bot can actually afford the next bid
                if player.money >= next_bid + min_cash_after:
                    self.logger.info(f"Bot {player_id} decided to BID ${next_bid} on property {property_id} (Current: {current_bid}, Max: {max_willing_bid})")
                    return next_bid
                else:
                    self.logger.info(f"Bot {player_id} willing to bid ${next_bid} but cannot afford with reserve. Passing.")
                    return None
            else:
                self.logger.debug(f"Bot {player_id} will not bid on property {property_id} (Current: {current_bid}, Max: {max_willing_bid}, Cash: {player.money})")
                return None
    
    def evaluate_bot_trade(self, trade_offer):
        """
        Evaluate a trade offer sent to a bot player.
        
        Args:
            trade_offer (dict): Trade offer details containing:
                - bot_id: ID of the bot player to evaluate the trade
                - requesting_player_id: ID of player making the offer
                - properties_offered: List of property IDs being offered
                - cash_offered: Cash amount being offered
                - properties_requested: List of property IDs being requested
                - cash_requested: Cash amount being requested
                
        Returns:
            dict: Bot's response to the trade offer
        """
        bot_id = trade_offer.get('bot_id')
        
        with self.app_config.get('app').app_context():
            # Find the bot in active_bots dictionary
            if bot_id not in active_bots:
                self.logger.warning(f"Trade offer evaluation requested for inactive bot {bot_id}")
                return {
                    "success": False, 
                    "error": f"Bot {bot_id} not active",
                    "bot_id": bot_id
                }
                
            bot = active_bots[bot_id]
            
            # Check if the bot exists in the database
            player = Player.query.get(bot_id)
            if not player or not player.is_bot or player.is_bankrupt:
                self.logger.warning(f"Trade offer evaluation requested for invalid bot {bot_id}")
                return {
                    "success": False, 
                    "error": f"Bot {bot_id} is invalid, bankrupt, or not a bot",
                    "bot_id": bot_id
                }
                
            # Evaluate the trade offer using the bot's logic
            self.logger.info(f"Evaluating trade offer for bot {bot_id} from player {trade_offer.get('requesting_player_id')}")
            
            # Add a small random delay to simulate thinking
            time.sleep(random.uniform(1.0, 3.0))
            
            # Use the bot's evaluate_trade_offer method
            try:
                decision = bot.evaluate_trade_offer(trade_offer)
                
                # Log the bot's decision
                if decision.get('accept', False):
                    self.logger.info(f"Bot {bot_id} accepted trade offer from player {trade_offer.get('requesting_player_id')}")
                else:
                    self.logger.info(f"Bot {bot_id} rejected trade offer from player {trade_offer.get('requesting_player_id')}")
                    if decision.get('counter_offer'):
                        self.logger.info(f"Bot {bot_id} proposed counter offer")
                
                # Return the decision with success indicator
                return {
                    "success": True,
                    "decision": decision,
                    "bot_id": bot_id
                }
                
            except Exception as e:
                self.logger.error(f"Error while evaluating trade offer for bot {bot_id}: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error evaluating trade: {str(e)}",
                    "bot_id": bot_id
                }

    def handle_economic_event(self, game_id, event_type, event_data):
        """
        Allow bots to respond to economic events in the game.
        
        Args:
            game_id (str): ID of the game where the event occurred
            event_type (str): Type of economic event (e.g., market_boom, interest_rate_change)
            event_data (dict): Additional data about the event
            
        Returns:
            dict: Responses from each bot
        """
        self.logger.info(f"Processing economic event '{event_type}' for bots in game {game_id}")
        
        try:
            # Get all active bots in this game
            bot_responses = {}
            
            # Find active bots in the specified game
            for bot_id, bot in active_bots.items():
                bot_player = Player.query.get(bot_id)
                
                # Skip if bot doesn't exist or isn't in this game
                if not bot_player or bot_player.game_id != game_id:
                    continue
                
                # Skip if bot is not active/in game
                if not bot_player.in_game or bot_player.is_bankrupt:
                    continue
                
                self.logger.info(f"Bot {bot_id} ({bot_player.username}) responding to {event_type} event")
                
                # Call the bot's response_to_economic_event method
                try:
                    response = bot.response_to_economic_event(event_type, event_data)
                    
                    # Log the response
                    if response.get('success', False):
                        actions = response.get('actions', [])
                        self.logger.info(f"Bot {bot_id} responded with {len(actions)} actions")
                        
                        # Record bot response for return
                        bot_responses[bot_id] = {
                            'bot_id': bot_id,
                            'bot_name': bot_player.username,
                            'actions': actions,
                            'success': True
                        }
                        
                        # Emit event for each bot response
                        self.socketio.emit('bot_economic_response', {
                            'bot_id': bot_id,
                            'bot_name': bot_player.username,
                            'event_type': event_type,
                            'actions': actions
                        }, room=game_id)
                    else:
                        self.logger.warning(f"Bot {bot_id} failed to respond to economic event: {response.get('error', 'Unknown error')}")
                        bot_responses[bot_id] = {
                            'bot_id': bot_id,
                            'bot_name': bot_player.username,
                            'success': False,
                            'error': response.get('error', 'Unknown error')
                        }
                except Exception as e:
                    self.logger.error(f"Error in bot {bot_id} economic event response: {str(e)}", exc_info=True)
                    bot_responses[bot_id] = {
                        'bot_id': bot_id,
                        'bot_name': bot_player.username,
                        'success': False,
                        'error': str(e)
                    }
            
            return {
                'success': True,
                'event_type': event_type,
                'bot_responses': bot_responses
            }
            
        except Exception as e:
            self.logger.error(f"Error handling economic event for bots: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

def register_bot_events(socketio, app_config):
    """Register socket event handlers for bot operations"""
    
    # Retrieve dependencies from app_config
    banker = app_config.get('banker')
    # Retrieve game_state instance if needed (already done in handlers via query)
    # game_state = app_config.get('game_state_instance') 
    
    if not banker:
        logger.error("Banker not found in app config during bot event registration.")
        # Decide if registration should halt
    
    @socketio.on('create_bot')
    def handle_create_bot(data):
        """Handle bot creation request"""
        # Validate admin access
        admin_pin = data.get('admin_pin')
        if not admin_pin or admin_pin != current_app.config.get('ADMIN_KEY'):
            emit('auth_error', {
                'error': 'Invalid admin credentials'
            })
            return

        bot_name = data.get('name', f"Bot_{random.randint(1000, 9999)}")
        bot_type = data.get('type', 'conservative')
        difficulty = data.get('difficulty', 'medium')
        
        # Get the bot controller from app config
        bot_controller = current_app.config.get('bot_controller')
        if not bot_controller:
            logger.error("Cannot create bot: BotController not found in app config.")
            emit('event_error', {'error': 'Internal server error: BotController not found'})
            return
        
        # Use the BotController create_bot method
        new_bot = bot_controller.create_bot(bot_name, bot_type, difficulty)
        
        if new_bot:
            # Return success response - the broadcast was already handled in create_bot
            emit('bot_event', {
                'success': True,
                'bot': {
                    'id': new_bot.id,
                    'name': new_bot.username,
                    'type': bot_type,
                    'difficulty': difficulty
                }
            })
        else:
            # Return failure
            emit('event_error', {'error': 'Failed to create bot player'})
            return
    
    @socketio.on('remove_bot')
    def handle_remove_bot(data):
        """Handle bot removal request"""
        # Validate admin access
        admin_pin = data.get('admin_pin')
        # game_state = GameState.query.first()
        if not admin_pin or admin_pin != current_app.config.get('ADMIN_KEY'):
            emit('auth_error', {
                'error': 'Invalid admin credentials'
            })
            return
        
        bot_id = data.get('bot_id')
        
        # Verify bot exists
        bot_player = Player.query.get(bot_id)
        if not bot_player or not bot_player.is_bot:
            emit('event_error', {
                'error': 'Bot not found'
            })
            return
        
        # Remove from active bots
        if bot_id in active_bots:
            del active_bots[bot_id]
        
        # Update database
        bot_player.in_game = False
        db.session.commit()
        
        # Broadcast bot removed event
        socketio.emit('bot_removed', {
            'bot_id': bot_id,
            'name': bot_player.username
        })
        
        logger.info(f"Removed bot: {bot_player.username} (ID: {bot_id})")
        
        return {
            'success': True,
            'message': f"Bot {bot_player.username} removed from the game"
        }
    
    @socketio.on('update_bot_settings')
    def handle_update_bot_settings(data):
        """Handle bot settings update request"""
        # Validate admin access
        admin_pin = data.get('admin_pin')
        game_state = GameState.query.first()
        if not game_state or game_state.admin_pin != admin_pin:
            emit('auth_error', {
                'error': 'Invalid admin credentials'
            })
            return
        
        bot_id = data.get('bot_id')
        new_name = data.get('name')
        new_type = data.get('type')
        new_difficulty = data.get('difficulty')
        
        # Verify bot exists
        bot_player = Player.query.get(bot_id)
        if not bot_player or not bot_player.is_bot:
            emit('event_error', {
                'error': 'Bot not found'
            })
            return
        
        # Update bot name if provided
        if new_name:
            bot_player.username = new_name
        
        # Update bot type and difficulty if provided
        if bot_id in active_bots and (new_type or new_difficulty):
            # Get current difficulty if not provided
            if not new_difficulty:
                new_difficulty = active_bots[bot_id].difficulty
            
            # Get current type if not provided
            if not new_type:
                current_bot = active_bots[bot_id]
                if isinstance(current_bot, AggressiveBot):
                    new_type = 'aggressive'
                elif isinstance(current_bot, StrategicBot):
                    new_type = 'strategic'
                elif isinstance(current_bot, OpportunisticBot):
                    new_type = 'opportunistic'
                elif isinstance(current_bot, SharkBot):
                    new_type = 'shark'
                elif isinstance(current_bot, InvestorBot):
                    new_type = 'investor'
                else:
                    new_type = 'conservative'
            
            # Create new bot with updated settings
            if new_type == 'aggressive':
                active_bots[bot_id] = AggressiveBot(bot_player.id, new_difficulty)
            elif new_type == 'strategic':
                active_bots[bot_id] = StrategicBot(bot_player.id, new_difficulty)
            elif new_type == 'opportunistic':
                active_bots[bot_id] = OpportunisticBot(bot_player.id, new_difficulty)
            elif new_type == 'shark':
                active_bots[bot_id] = SharkBot(bot_player.id, new_difficulty)
            elif new_type == 'investor':
                active_bots[bot_id] = InvestorBot(bot_player.id, new_difficulty)
            else:  # default to conservative
                active_bots[bot_id] = ConservativeBot(bot_player.id, new_difficulty)
        
        # Update database
        db.session.commit()
        
        # Broadcast bot updated event
        socketio.emit('bot_updated', {
            'bot_id': bot_id,
            'name': bot_player.username,
            'type': new_type,
            'difficulty': new_difficulty
        })
        
        logger.info(f"Updated bot: {bot_player.username} (ID: {bot_id})")
        
        return {
            'success': True,
            'message': f"Bot {bot_player.username} settings updated"
        }
    
    @socketio.on('get_active_bots')
    def handle_get_active_bots(data):
        """Handle request to retrieve the list of active bots."""
        # Validate admin access
        admin_pin = data.get('admin_pin')
        # game_state = GameState.query.first()
        if not admin_pin or admin_pin != current_app.config.get('ADMIN_KEY'):
            emit('auth_error', {'error': 'Invalid admin credentials'})
            return
        
        try:
            # Query active bot players from the database
            bot_players = Player.query.filter_by(is_bot=True, in_game=True).all()
            
            bots_data = []
            for bot_player in bot_players:
                # Attempt to get bot type and difficulty from active_bots dictionary
                # This might be inaccurate if the bot isn't in active_bots or if type/difficulty aren't stored there reliably.
                # TODO: Store bot type and difficulty directly on the Player model for better persistence.
                bot_instance = active_bots.get(bot_player.id)
                bot_type = "unknown"
                difficulty = "unknown"
                if bot_instance:
                    difficulty = getattr(bot_instance, 'difficulty', 'unknown')
                    # Infer type based on class - brittle
                    if isinstance(bot_instance, AggressiveBot):
                        bot_type = 'aggressive'
                    elif isinstance(bot_instance, StrategicBot):
                        bot_type = 'strategic'
                    elif isinstance(bot_instance, OpportunisticBot):
                        bot_type = 'opportunistic'
                    elif isinstance(bot_instance, SharkBot):
                        bot_type = 'shark'
                    elif isinstance(bot_instance, InvestorBot):
                        bot_type = 'investor'
                    elif isinstance(bot_instance, ConservativeBot):
                         bot_type = 'conservative' # Assuming this class exists
                    else:
                        bot_type = type(bot_instance).__name__ # Fallback to class name
                
                bots_data.append({
                    'id': bot_player.id,
                    'name': bot_player.username,
                    'money': bot_player.money,
                    'position': bot_player.position,
                    'bot_type': bot_type, 
                    'difficulty': difficulty
                })
            
            # Emit the list back to the requesting client
            emit('active_bots_list', {'success': True, 'bots': bots_data})
            
        except Exception as e:
            logger.error(f"Error fetching active bots: {str(e)}")
            emit('event_error', {'error': 'Failed to retrieve bot list.'})

    @socketio.on('evaluate_bot_trade')
    def handle_evaluate_bot_trade(data):
        """Handle request to evaluate a trade offer with a bot player."""
        # Validate player access - either the player making the trade or an admin
        player_id = data.get('player_id')
        player_pin = data.get('player_pin')
        admin_pin = data.get('admin_pin')
        
        is_authorized = False
        
        # Check if admin PIN is provided and valid
        if admin_pin and admin_pin == current_app.config.get('ADMIN_KEY'):
            is_authorized = True
            
        # Check if player PIN is provided and valid
        elif player_id and player_pin:
            player = Player.query.get(player_id)
            if player and player.pin == player_pin:
                is_authorized = True
                
        if not is_authorized:
            emit('auth_error', {'error': 'Invalid credentials for trade evaluation'})
            return
            
        try:
            # Extract trade details
            bot_id = data.get('bot_id')
            trade_offer = {
                'bot_id': bot_id,
                'requesting_player_id': player_id,
                'properties_offered': data.get('properties_offered', []),
                'cash_offered': data.get('cash_offered', 0),
                'properties_requested': data.get('properties_requested', []),
                'cash_requested': data.get('cash_requested', 0)
            }
            
            # Validate required fields
            if not bot_id:
                emit('event_error', {'error': 'Missing bot_id in trade offer'})
                return
                
            if (not trade_offer['properties_offered'] and trade_offer['cash_offered'] <= 0) or \
               (not trade_offer['properties_requested'] and trade_offer['cash_requested'] <= 0):
                emit('event_error', {'error': 'Trade must include at least one property or cash amount in each direction'})
                return
                
            # Get the bot controller from app config
            bot_controller = current_app.config.get('bot_controller_instance')
            if not bot_controller:
                emit('event_error', {'error': 'Bot controller not available'})
                return
                
            # Evaluate the trade
            trade_result = bot_controller.evaluate_bot_trade(trade_offer)
            
            # Emit result back to requesting client
            if trade_result.get('success', False):
                emit('bot_trade_response', {
                    'success': True,
                    'bot_id': bot_id,
                    'decision': trade_result.get('decision', {})
                })
                
                # If the bot accepted, also notify other players in the game
                bot_decision = trade_result.get('decision', {})
                if bot_decision.get('accept', False):
                    # Get game ID to emit to room
                    bot_player = Player.query.get(bot_id)
                    if bot_player and bot_player.game_id:
                        socketio.emit('bot_accepted_trade', {
                            'bot_id': bot_id,
                            'bot_name': bot_player.username,
                            'player_id': player_id,
                            'trade_details': {
                                'properties_offered': trade_offer['properties_offered'],
                                'cash_offered': trade_offer['cash_offered'],
                                'properties_requested': trade_offer['properties_requested'],
                                'cash_requested': trade_offer['cash_requested']
                            }
                        }, room=bot_player.game_id)
            else:
                emit('event_error', {'error': trade_result.get('error', 'Unknown error evaluating trade')})
                
        except Exception as e:
            logger.error(f"Error handling bot trade evaluation: {str(e)}", exc_info=True)
            emit('event_error', {'error': f'Error processing trade: {str(e)}'})

    @socketio.on('trigger_bot_market_timing')
    def handle_trigger_bot_market_timing(data):
        """Handle request to trigger a market timing event for testing"""
        # Validate admin access
        admin_pin = data.get('admin_pin')
        game_state = GameState.query.first()
        if not game_state or game_state.admin_pin != admin_pin:
            emit('auth_error', {
                'error': 'Invalid admin credentials'
            })
            return
        
        bot_id = data.get('bot_id')
        
        # Verify bot exists
        bot_player = Player.query.get(bot_id)
        if not bot_player or not bot_player.is_bot:
            emit('event_error', {
                'error': 'Bot not found'
            })
            return
        
        # Create and execute a market timing event
        # This likely needs access to GameState and Banker
        event_data = {
            'event_type': 'market_timing',
            'bot_id': bot_id,
            'description': "Admin triggered market timing event"
        }
        
        # Assuming handle_bot_event takes socketio and app_config now
        # Need to update handle_bot_event signature too
        handle_bot_event(socketio, app_config, event_data)
        
        return {'success': True, 'message': f'Market timing event triggered for bot {bot_player.username}'} 

    @socketio.on('economic_event_reaction')
    def handle_economic_event_reaction(data):
        """Handle request to trigger bot reactions to economic events"""
        logger.info(f"Received economic_event_reaction: {data}")
        
        # Extract data
        game_id = data.get('game_id')
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        # Validate data
        if not game_id or not event_type:
            emit('event_error', {'error': 'Missing required parameters: game_id and event_type'})
            return
        
        # Get bot controller from app config
        bot_controller = current_app.config.get('bot_controller')
        if not bot_controller:
            logger.error("Bot controller not found in app config")
            emit('event_error', {'error': 'Internal server error: Bot controller not found'})
            return
        
        # Process the economic event
        try:
            result = bot_controller.handle_economic_event(game_id, event_type, event_data)
            
            if result.get('success'):
                # The event already emits individual bot responses in the method
                # Just confirm the overall process was completed
                emit('event_success', {
                    'message': f'Economic event {event_type} processed successfully',
                    'event_type': event_type,
                    'bot_count': len(result.get('bot_responses', {}))
                })
            else:
                emit('event_error', {'error': result.get('error', 'Unknown error processing economic event')})
        
        except Exception as e:
            logger.error(f"Error handling economic event reaction: {str(e)}", exc_info=True)
            emit('event_error', {'error': f'Error processing economic event: {str(e)}'})

# --- Bot Processing Logic (Needs refactoring to use app_config) ---

def init_bots_from_database():
    """Initialize active_bots dictionary from existing bot players in DB"""
    bot_players = Player.query.filter_by(is_bot=True, in_game=True).all()
    for bot_player in bot_players:
        # Defaulting type and difficulty - could store these on Player model
        difficulty = 'medium' # Example default
        bot_type = 'conservative' # Example default 
        
        if bot_type == 'aggressive':
            bot = AggressiveBot(bot_player, difficulty)
        elif bot_type == 'strategic':
            bot = StrategicBot(bot_player, difficulty)
        # ... add other types ...
        else:
            bot = ConservativeBot(bot_player, difficulty)
            
        active_bots[bot_player.id] = bot
    logger.info(f"Initialized {len(active_bots)} active bots from database.")

def start_bot_action_thread(socketio, app_config):
    """Starts the background thread for processing bot actions"""
    global bot_action_thread, bot_action_running
    
    # Debug: Log active bots state
    logger.info(f"Current active bots: {list(active_bots.keys())}")
    
    # Also check if any bots exist in the database
    flask_app = app_config.get('app')
    if flask_app:
        with flask_app.app_context():
            bot_count = Player.query.filter_by(is_bot=True, in_game=True).count()
            logger.info(f"Found {bot_count} bots marked in_game in the database")
    
    if bot_action_thread is None or not bot_action_thread.is_alive():
        bot_action_running = True
        # Pass app_config to the thread target
        bot_action_thread = threading.Thread(target=process_bot_actions, args=(socketio, app_config), daemon=True)
        bot_action_thread.start()
        logger.info("Started bot action processing thread.")
    else:
        logger.info("Bot action processing thread already running.")

def process_bot_actions(socketio, app_config):
    """Background thread function to process bot actions periodically"""
    global bot_action_running
    logger.info("Bot action processor started.")
    
    # Retrieve necessary app components from app_config
    flask_app = app_config.get('app') # Get the Flask app instance
    if not flask_app:
        logger.error("Flask app instance not found in app_config for bot action thread. Stopping.")
        bot_action_running = False
        return
    
    # ... (retrieve other dependencies like banker, core_socket_controller etc. if needed outside context)
        
    while bot_action_running:
        try:
            # --- Add App Context --- 
            with flask_app.app_context():
                current_game_state = GameState.query.first() # Now safe to query
                if not current_game_state or not current_game_state.game_running:
                    logger.info("Game not running, bot actions paused.")
                    # No need for db access here, sleep outside context? Safer inside.
                    time.sleep(5) # Add a sleep here before continuing
                    continue # Continue inside context before sleep
                else: # Only process if game is running
                    # Acquire lock to prevent concurrent modifications
                    with bot_action_lock:
                        # Retrieve dependencies needing context OR pass them if retrieved outside
                        banker = app_config.get('banker') 
                        core_socket_controller = app_config.get('socket_controller')
                        game_controller = app_config.get('game_controller') # Assuming BotPlayer needs this
                        bot_controller_instance = app_config.get('bot_controller_instance') # If BotController instance is needed
                        
                        if not all([banker, core_socket_controller, game_controller, bot_controller_instance]):
                             logger.error("Missing dependencies inside app_context in bot thread.")
                        else:
                            # 1. Process whose turn it is
                            current_player_id = current_game_state.current_player_id
                            if current_player_id is None:
                                logger.warning("No current player ID set in game state.")
                                time.sleep(2)
                                continue
                            
                            logger.info(f"Current player ID: {current_player_id}, Active bots: {list(active_bots.keys())}")
                            
                            if current_player_id in active_bots:
                                # We found a bot whose turn it is
                                logger.info(f"Processing turn for bot player ID: {current_player_id}")
                                
                                # Bots don't need socket connections - they're automated players
                                # Skip connection status check and proceed with the turn
                                
                                # Use the BotController's method
                                try:
                                    bot_controller_instance.take_turn(current_player_id, current_game_state.id)
                                    logger.info(f"Bot {current_player_id} completed its turn")
                                except Exception as e:
                                    logger.error(f"Error during bot {current_player_id} turn: {str(e)}", exc_info=True)
                            else:
                                logger.info(f"Current player {current_player_id} is not a bot or not in active_bots dictionary")

            # --- End App Context ---

            # Sleep outside the context if no context-dependent ops needed here
            sleep_interval = app_config.get('BOT_ACTION_INTERVAL', 5.0)
            time.sleep(sleep_interval)
            
        except Exception as e:
            logger.error(f"Error in bot action processing loop: {e}", exc_info=True)
            time.sleep(10) # Longer sleep on error

    logger.info("Bot action processor stopped.")

def stop_bot_action_thread():
    """Signals the bot action processing thread to stop"""
    global bot_action_running
    bot_action_running = False
    logger.info("Stopping bot action processing thread...")
    if bot_action_thread and bot_action_thread.is_alive():
        bot_action_thread.join(timeout=5) # Wait for thread to finish
        logger.info("Bot action processing thread stopped.")
    else:
        logger.info("Bot action processing thread was not running.")


# Functions below might need refactoring based on how bot actions are handled
# e.g., moving logic into the Bot classes or the main process_bot_actions loop

def process_bot_turns(socketio):
    """Check if it's a bot's turn and execute actions"""
    game_state = GameState.query.first()
    if not game_state or not game_state.game_running:
        return

    current_player_id = game_state.current_player_id
    if current_player_id in active_bots:
        bot = active_bots[current_player_id]
        logger.info(f"Bot {bot.player.username}'s turn (ID: {current_player_id})")
        
        # Lock to prevent race conditions if multiple threads/processes interact
        with bot_action_lock:
            # Perform bot turn logic (simplified example)
            try:
                bot.take_turn(game_state)
                # TODO: Emit events based on bot actions
                # Example: socketio.emit('bot_action', {'bot_id': bot.player.id, 'action': 'rolled_dice', ...})
                
                # End bot turn automatically (replace with proper GameController interaction)
                # game_controller.end_turn(bot.player.id, bot.player.pin) 
                logger.warning("Automatic bot turn ending needs integration with GameController")
                
            except Exception as e:
                logger.error(f"Error during bot {bot.player.username}'s turn: {e}")

def process_bot_auctions(socketio):
    """Check active auctions and let bots participate"""
    auction_system = current_app.config.get('auction_system')
    if not auction_system:
        logger.error("AuctionSystem not available for bot auction processing.")
        return

    active_auctions = auction_system.get_active_auctions()
    if not active_auctions.get('success'):
        return # No active auctions or error

    for auction_data in active_auctions.get('auctions', []):
        auction_id = auction_data['id']
        # Lock to prevent race conditions
        with bot_action_lock:
            for bot_id, bot in list(active_bots.items()): # Iterate copy
                # Check if bot should participate (not already passed, etc.)
                if auction_system.can_participate(auction_id, bot_id):
                    try:
                        bid_decision = bot.decide_auction_bid(auction_data)
                        if bid_decision['action'] == 'bid':
                            auction_system.place_bid(auction_id, bot_id, bid_decision['amount'])
                        elif bid_decision['action'] == 'pass':
                            auction_system.pass_auction(auction_id, bot_id)
                    except Exception as e:
                        logger.error(f"Error during bot {bot.player.username}'s auction decision for {auction_id}: {e}") 