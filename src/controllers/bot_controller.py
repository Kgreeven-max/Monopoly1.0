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
            
            # Create the bot strategy object
            bot_instance = None
            if bot_type == 'aggressive':
                bot_instance = AggressiveBot(bot_player.id, difficulty)
            elif bot_type == 'strategic':
                bot_instance = StrategicBot(bot_player.id, difficulty)
            elif bot_type == 'opportunistic':
                bot_instance = OpportunisticBot(bot_player.id, difficulty)
            elif bot_type == 'shark':
                bot_instance = SharkBot(bot_player.id, difficulty)
            elif bot_type == 'investor':
                bot_instance = InvestorBot(bot_player.id, difficulty)
            else:  # default to conservative
                bot_instance = ConservativeBot(bot_player.id, difficulty)
            
            # Store in active bots dictionary
            if bot_instance:
                active_bots[bot_player.id] = bot_instance
            
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
        with self.app_config.get('app').app_context(): # Ensure app context for the whole turn
            self.logger.info(f"--- Bot Player {player_id} starting turn in Game {game_id} ---")
            time.sleep(random.uniform(0.5, 1.5)) # Simulate thinking time

            try:
                # Continuously check game state in case something changed (e.g., game ended)
                game_state = GameState.query.get(game_id)
                if not game_state or game_state.status != 'active':
                    self.logger.warning(f"Game {game_id} is not active. Bot {player_id} stopping turn.")
                    return
                if game_state.current_player_id != player_id:
                    self.logger.warning(f"Bot {player_id} attempted to take turn, but current player is {game_state.current_player_id}. Stopping.")
                    return

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
                             current_game_state = GameState.query.get(game_id)
                             if current_game_state.current_player_id == player_id: 
                                 self.game_controller._internal_end_turn(player_id, game_id)
                             return # End processing for this turn
                    # If jail_action_taken is False, it means bot got out and needs to proceed with roll
                    
                # 2. Main Turn Loop (Handles doubles)
                turn_active = True
                roll_count = 0
                max_rolls = 3 # Prevent infinite loop in case of unexpected state

                while turn_active and roll_count < max_rolls:
                    roll_count += 1
                    self.logger.info(f"Bot {player_id} performing roll #{roll_count}")
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Check game state again before rolling
                    game_state = GameState.query.get(game_id)
                    if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                         self.logger.warning(f"Game state changed mid-turn for bot {player_id}. Stopping.")
                         turn_active = False; break

                    # Validate expected action before rolling
                    if game_state.expected_action_type not in [None, 'roll_again']: 
                         self.logger.warning(f"Bot {player_id} expected action is '{game_state.expected_action_type}', cannot roll. Handling action first.")
                         self._handle_pending_action(player, game_state)
                         # Re-check state after handling pending action
                         game_state = GameState.query.get(game_id)
                         if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                              self.logger.warning(f"Game state changed after handling pending action for bot {player_id}. Stopping.")
                              turn_active = False; break
                         # If action resolved and turn didn't end, loop might continue if doubles occurred before pending action
                         if game_state.expected_action_type == 'roll_again': continue # Proceed to roll
                         else: turn_active = False; break # Turn ended or another action is now pending
                        
                    # Perform Roll
                    roll_result = self.game_logic.roll_dice_and_move(player_id, game_id)
                    if not roll_result or not roll_result.get('success'):
                        self.logger.error(f"Bot {player_id} failed to roll dice or move: {roll_result.get('error')}")
                        turn_active = False; break # End turn on critical roll error

                    # Process Landing Action
                    landing_action = roll_result.get('landing_action', {})
                    self._handle_landing_action(player, landing_action, game_state)

                    # Check if turn ended by landing action (e.g., go to jail, bankruptcy potential)
                    # Re-fetch game state as handlers might modify it
                    game_state = GameState.query.get(game_id)
                    if not game_state or game_state.status != 'active' or game_state.current_player_id != player_id:
                        self.logger.info(f"Turn ended for bot {player_id} after handling landing action.")
                        turn_active = False; break 
                       
                    # Check for doubles
                    if roll_result.get('next_action') != 'roll_again':
                        self.logger.info(f"Bot {player_id} did not roll doubles or turn ended. Finishing turn sequence.")
                        turn_active = False # End loop if not rolling again
                    else:
                         self.logger.info(f"Bot {player_id} rolled doubles, continuing turn.")
                         # Update expected state for roll_again if GameLogic didn't
                         if game_state.expected_action_type != 'roll_again':
                              game_state.expected_action_type = 'roll_again'
                              game_state.expected_action_details = None
                              db.session.add(game_state)
                              db.session.commit()

                # 3. End Turn (if not already ended)
                # Check final state after loop
                final_game_state = GameState.query.get(game_id)
                if final_game_state and final_game_state.status == 'active' and final_game_state.current_player_id == player_id:
                     self.logger.info(f"Bot {player_id} turn loop finished. Explicitly ending turn.")
                     self.game_controller._internal_end_turn(player_id, game_id)
                else:
                     self.logger.info(f"Bot {player_id} turn already ended or game state changed.")

            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Exception during bot {player_id} turn: {e}", exc_info=True)
                # Attempt to end turn gracefully if possible
                try:
                     current_game_state = GameState.query.get(game_id)
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
         self.logger.info(f"Bot {player.id} handling pending action: {action_type}")
         # This is essentially the same logic as _handle_landing_action but triggered pre-roll
         self._handle_landing_action(player, {"action": action_type, **(details or {})}, game_state)

    def _handle_landing_action(self, player, landing_action, game_state):
        """Processes the result of landing on a space."""
        action_type = landing_action.get('action')
        player_id = player.id
        game_id = game_state.game_id

        self.logger.info(f"Bot {player_id} handling landing action: {action_type}")
        time.sleep(random.uniform(0.3, 0.8))

        if action_type == 'buy_or_auction_prompt':
            property_id = landing_action.get('property_id')
            cost = landing_action.get('cost')
            if self._decide_buy_property(player, property_id, cost):
                self.logger.info(f"Bot {player_id} decided to BUY property {property_id}")
                # Call PlayerActionController's logic or a direct controller method
                # Assuming direct call to property controller for simplicity here
                buy_result = self.property_controller.buy_property(player_id, property_id)
                if not buy_result.get('success'):
                     self.logger.error(f"Bot {player_id} failed to buy property {property_id}: {buy_result.get('error')}")
                     # If buy fails, maybe decline and auction? Or just end turn?
                     self._decline_buy_action(player_id, property_id, game_id)
            else:
                self.logger.info(f"Bot {player_id} decided to DECLINE buy for property {property_id}")
                self._decline_buy_action(player_id, property_id, game_id)

        elif action_type == 'draw_chance_card':
            self.logger.info(f"Bot {player_id} drawing Chance card.")
            self.special_space_controller.process_chance_card(player_id, game_id)

        elif action_type == 'draw_community_chest_card':
            self.logger.info(f"Bot {player_id} drawing Community Chest card.")
            self.special_space_controller.process_community_chest_card(player_id, game_id)
        
        elif action_type == 'pay_tax':
             tax_details = landing_action.get('tax_details', {})
             amount = tax_details.get('amount') # Assuming amount is in details
             self.logger.info(f"Bot {player_id} needs to pay tax: {amount}")
             payment_result = self.banker.player_pays_bank(player_id, amount, f"Tax: {landing_action.get('space_name')}")
             if not payment_result['success']:
                  self.logger.warning(f"Bot {player_id} could not pay tax. Needs asset management.")
                  self._manage_assets(player, amount)
             else:
                  # Tax paid, clear expected state if it was set
                  current_game_state = GameState.query.get(game_id)
                  if current_game_state.expected_action_type == 'pay_tax':
                       current_game_state.expected_action_type = None
                       current_game_state.expected_action_details = None
                       db.session.commit()
       
        elif action_type in ['insufficient_funds_for_rent', 'manage_assets_or_bankrupt', 'manage_assets_for_jail_fine']:
             required_amount = landing_action.get('required', landing_action.get('rent_amount', 0))
             self.logger.warning(f"Bot {player_id} needs to manage assets. Required: {required_amount}")
             self._manage_assets(player, required_amount)
             # After managing assets, the original action (paying rent/fine) might need re-attempting
             # This needs more complex state handling - for now, assume manage_assets handles payment if possible.
       
        # Actions like 'paid_rent', 'went_to_jail', 'passive_space' require no bot decision.
        else:
             self.logger.debug(f"Bot {player_id} encountered landing action '{action_type}' requiring no specific decision.")

    def _decline_buy_action(self, player_id, property_id, game_id):
         """Handles the logic after a bot declines to buy."""
         # Need to check game settings if auction is required
         game_state = GameState.query.get(game_id)
         if game_state.auction_required:
              self.logger.info(f"Bot {player_id} triggering auction for property {property_id}")
              # Auction controller should handle the flow from here
              self.auction_controller.start_auction(property_id, game_id)
         else:
              self.logger.info(f"Bot {player_id} declined property {property_id}, no auction required. Turn should end.")
              # Clear expected state manually if GameController didn't already
              if game_state.expected_action_type == 'buy_or_auction_prompt':
                   game_state.expected_action_type = None
                   game_state.expected_action_details = None
                   db.session.commit()
              # Turn progression is handled by the main loop or GameController
              # No need to call end_turn here explicitly unless needed as fallback

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
            if player.cash >= fine:
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
        
        if player.cash >= cost + min_cash_after: # Check affordability first
        # if player.cash / affordable_threshold > cost: 
            # TODO: Add basic property evaluation (e.g., based on type or group)
            self.logger.debug(f"Bot {player.id} decides TRUE for buying property {property_id} (Cost: {cost}, Cash: {player.cash})")
            return True
        else:
            self.logger.debug(f"Bot {player.id} decides FALSE for buying property {property_id} (Cost: {cost}, Cash: {player.cash})")
            return False

    def _manage_assets(self, player, amount_needed):
        """Simple logic to raise funds by mortgaging properties."""
        player_id = player.id
        self.logger.info(f"Bot {player_id} attempting to manage assets to raise ${amount_needed}")
        
        # Fetch unmortgaged properties, ordered by value (ascending) to mortgage cheapest first
        # Use joinedload to avoid N+1 queries for owner check
        properties_to_mortgage = Property.query.options(joinedload(Property.owner))\
                                    .filter_by(owner_id=player_id, is_mortgaged=False)\
                                    .order_by(Property.price).all()

        amount_raised = 0
        for prop in properties_to_mortgage:
            if player.cash + amount_raised >= amount_needed:
                 break # Raised enough
            
            self.logger.info(f"Bot {player_id} attempting to mortgage {prop.name} (Value: {prop.mortgage_value})")
            time.sleep(random.uniform(0.2, 0.5))
            # Assuming mortgage_property exists and handles cash transfer
            mortgage_result = self.property_controller.mortgage_property(player_id, prop.id)
            if mortgage_result.get('success'):
                 amount_raised += prop.mortgage_value # Add mortgage value to potential cash
                 self.logger.info(f"Bot {player_id} successfully mortgaged {prop.name}. Raised ${amount_raised} so far.")
            else:
                 self.logger.warning(f"Bot {player_id} failed to mortgage {prop.name}: {mortgage_result.get('error')}")

        # Re-check cash after attempting mortgages
        db.session.refresh(player) # Refresh player object to get updated cash
        if player.cash >= amount_needed:
            self.logger.info(f"Bot {player_id} successfully raised enough funds (${player.cash}) after managing assets.")
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
            self.logger.warning(f"Bot {player_id} FAILED to raise sufficient funds (${amount_needed} needed, has ${player.cash}). Declaring bankruptcy.")
            # Declare bankruptcy
            self.game_controller.declare_bankruptcy(player_id)

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

            if current_bid < max_willing_bid and player.cash > current_bid + min_cash_after:
                # Bid slightly more than current bid
                bid_increment = max(1, int(current_bid * 0.05)) # Bid 5% more, min $1
                next_bid = min(current_bid + bid_increment, max_willing_bid) # Don't exceed max willing bid
                
                # Ensure bot can actually afford the next bid
                if player.cash >= next_bid + min_cash_after:
                    self.logger.info(f"Bot {player_id} decided to BID ${next_bid} on property {property_id} (Current: {current_bid}, Max: {max_willing_bid})")
                    return next_bid
                else:
                    self.logger.info(f"Bot {player_id} willing to bid ${next_bid} but cannot afford with reserve. Passing.")
                    return None
            else:
                self.logger.debug(f"Bot {player_id} will not bid on property {property_id} (Current: {current_bid}, Max: {max_willing_bid}, Cash: {player.cash})")
                return None

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
                    # time.sleep(10) 
                    # continue # Continue inside context before sleep
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
                            if current_player_id in active_bots:
                                bot = active_bots[current_player_id]
                                connection_status = core_socket_controller.get_player_connection_status(current_player_id)
                                if not connection_status.get('success', False):
                                    logger.info(f"Bot {bot.player.username} is currently marked disconnected, skipping turn.")
                                else:
                                    logger.info(f"Processing turn for bot: {bot.player.username}")
                                    # --- Pass necessary dependencies to take_turn --- 
                                    # Assuming BotPlayer's take_turn method is adapted to use these directly
                                    # or BotController instance has a method that uses them.
                                    # Example: bot_controller_instance.take_turn(current_player_id, current_game_state.id)
                                    bot_controller_instance.take_turn(current_player_id, current_game_state.id) # Use the BotController's method
                                    
                            # 2. Process bot responses to auctions (if any active)
                            # process_bot_auctions(socketio) # Needs update for app_config
                            
                            # 3. Process general bot decisions (e.g., property management)
                            # Needs careful context handling if modifying DB
                            # for bot_id, bot in list(active_bots.items()):
                            #     if bot.player.id != current_player_id:
                            #          bot.manage_assets(current_game_state, banker)
                                    
                            # 4. Process scheduled events (if any)
                            # handle_scheduled_event(socketio, app_config)

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