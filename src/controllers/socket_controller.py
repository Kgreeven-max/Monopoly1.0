from flask_socketio import emit, join_room, leave_room
import logging
from datetime import datetime, timedelta
import uuid
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property
from src.models.event_system import EventSystem
from src.models.banker import Banker
from src.models.community_fund import CommunityFund
from src.controllers.auction_controller import register_auction_events
from src.controllers.property_controller import register_property_events
from src.controllers.bot_controller import register_bot_events
from src.controllers.bot_event_controller import register_bot_event_handlers
from src.controllers.special_space_controller import SpecialSpaceController
from src.controllers.social import SocialController
from src.controllers.social.socket_handlers import register_social_socket_handlers
# Import core handlers and controller
from .socket_core import register_core_socket_handlers, SocketController as CoreSocketController 
import eventlet
import random

# Set up logger
logger = logging.getLogger(__name__)

# Global dictionary to track connected players, can be imported by other modules
connected_players = {}

class SocketController:
    """Controller managing game-specific socket events (e.g., game actions, chat)."""
    
    def __init__(self, socketio_instance, app_config):
        self.socketio = socketio_instance
        self.app_config = app_config
        # Removed: self.connected_players = {}
        # Removed: self.player_reconnect_timers = {} 
        
        # Get shared services from app config (assuming they are stored there during setup)
        self.banker = app_config.get('banker')
        self.community_fund = app_config.get('community_fund')
        self.event_system = app_config.get('event_system')
        self.special_space_controller = app_config.get('special_space_controller')
        self.social_controller = app_config.get('social_controller')
        self.game_controller = app_config.get('game_controller') # Assuming game_controller is also stored
        self.property_controller = app_config.get('property_controller') # Assuming property_controller is stored
        self.auction_controller = app_config.get('auction_controller') # Assuming auction_controller is stored
        self.bot_controller = app_config.get('bot_controller') # Assuming bot_controller is stored
        
        # Validate essential components
        if not all([self.socketio, self.banker, self.community_fund, self.event_system, 
                    self.special_space_controller, self.social_controller, self.game_controller,
                    self.property_controller, self.auction_controller, self.bot_controller]):
            logger.error("SocketController initialized with missing components!")
            # Depending on severity, might raise an exception

    # --- Helper Methods --- 
    # Removed: _get_player_id_from_sid (Use self.core_controller._get_player_id_from_sid if needed)
    # Removed: _register_base_handlers (Managed by core controller)
    # Removed: _start_reconnect_timer (Managed by core controller)
    # Removed: cancel_reconnect_timer (Managed by core controller)
    # Removed: remove_connected_player_entry (Managed by core controller)
    # Removed: notify_all_player_removed (Managed by core controller)
    # Removed: get_player_connection_status (Managed by core controller)

    # --- Event Handlers --- 

    def register_event_handlers(self):
        """Registers game-specific socket event handlers with the SocketIO instance."""
        # NOTE: Most handlers are now registered via separate functions 
        # (register_player_action_handlers, register_property_events, etc.)
        # This method remains primarily for handlers tightly coupled with this controller's state,
        # or potentially for organizing sub-controller registrations if needed later.
        
        # Example (if needed):
        # @self.socketio.on('some_event_specific_to_socket_controller')
        # def handle_specific_event(data):
        #    pass
        
        logger.info("SocketController register_event_handlers called (currently minimal).")
        
        # Remove duplicate/conflicting handlers below this line:
        # Removed: @self.socketio.on('chat_message') - Handled by SocialController/Handlers
        # Removed: @self.socketio.on('end_turn') - Handled by PlayerActionController
        # Removed: @self.socketio.on('repair_property') - Handled by PlayerActionController/PropertyController
        # Removed: @self.socketio.on('draw_chance_card') - Handled by PlayerActionController
        # Removed: @self.socketio.on('draw_community_chest_card') - Handled by PlayerActionController
        # Removed: @self.socketio.on('land_on_special_space') - Handled by PlayerActionController
        # Removed: @self.socketio.on('join_channel') - Handled by SocialController/Handlers
        # Removed: @self.socketio.on('leave_channel') - Handled by SocialController/Handlers
        # Removed: @self.socketio.on('message_reaction') - Handled by SocialController/Handlers

# Updated registration function
def register_socket_events(app_socketio, app_config):
    """Register all socket event handlers using the controller classes."""
    
    # Register core handlers FIRST - this creates the core controller instance 
    # and stores it in app_config['socket_controller']
    core_socket_controller = register_core_socket_handlers(app_socketio, app_config)
    if not core_socket_controller:
        logger.critical("Failed to register core socket handlers. Aborting further registration.")
        return # Or raise an exception
    
    # Ensure the core controller instance is stored in app_config under the expected key
    app_config['core_socket_controller'] = core_socket_controller
        
    # Instantiate the game-specific socket controller 
    # It retrieves dependencies (including core_socket_controller) from app_config
    game_socket_controller = SocketController(app_socketio, app_config)
    
    # Store game controller instance if needed elsewhere (optional)
    app_config['game_socket_controller'] = game_socket_controller
    
    # Retrieve necessary controllers/services from app_config
    # These should have been initialized and stored in app.py
    banker = app_config.get('banker')
    social_controller = app_config.get('social_controller')
    # Note: No need to retrieve here if controllers get them from app_config

    # Validate dependencies used by other registration functions
    if not banker:
        logger.error("Banker instance not found in app config during socket event registration.")
        # Decide if this is fatal or if some handlers can still be registered
    if not social_controller:
        logger.error("SocialController instance not found in app config during socket event registration.")
        # Decide if this is fatal

    # Register events from other controllers 
    # Pass app_socketio and app_config so they can access necessary instances
    if banker:
        register_auction_events(app_socketio, app_config) # Pass app_config
        register_property_events(app_socketio, app_config) # Pass app_config
        register_bot_events(app_socketio, app_config) # Pass app_config
    else:
        logger.warning("Skipping auction, property, and bot event registration due to missing Banker.")
        
    register_bot_event_handlers(app_socketio, app_config) # Pass app_config
    
    if social_controller:
        register_social_socket_handlers(app_socketio, app_config) # Pass app_config
    else:
        logger.warning("Skipping social event registration due to missing SocialController.")
    
    # Register events handled directly by the game-specific SocketController
    game_socket_controller.register_event_handlers() 

    # --- Add Player Action Handlers Here (or in a dedicated registration function) ---
    @app_socketio.on('roll_dice')
    def handle_roll_dice(data, *args):
        player_id = data.get('playerId')
        sid = request.sid
        logger.info(f"[Socket] Received 'roll_dice' event from player ID: {player_id} (SID: {sid})")
        if args:
            logger.info(f"[Socket] roll_dice received extra args: {args}")
            
        game_logic = app_config.get('game_logic')
        if not game_logic:
            logger.error("GameLogic not found in app_config for handle_roll_dice")
            emit('game_error', {'error': 'Game logic unavailable'}, room=sid)
            return
            
        # Call the actual game logic method
        result = game_logic.roll_dice_and_move(player_id)
        
        if not result or not result.get('success'):
             error_message = result.get('error', 'Dice roll failed for unknown reason.') if result else 'Dice roll failed for unknown reason.'
             logger.warning(f"Dice roll failed for player {player_id}: {error_message}")
             emit('game_error', {'error': error_message, 'action': 'roll_dice'}, room=sid)
        else:
             # GameLogic method now emits specific events (dice_rolled, player_moved, etc.)
             # We might emit a final confirmation or the action required for the new space
             logger.info(f"Dice roll processed for player {player_id}. Action Required: {result.get('action_required')}")
             emit('roll_dice_result', result, room=sid) # Send detailed result back to the player who rolled
             # Broadcasting of game state updates should be handled within GameLogic or triggered by specific events

    @app_socketio.on('end_turn')
    def handle_end_turn(data, *args):
        player_id = data.get('playerId')
        sid = request.sid
        logger.info(f"[Socket] Received 'end_turn' event from player ID: {player_id} (SID: {sid})")
        if args:
            logger.info(f"[Socket] end_turn received extra args: {args}")
            
        game_logic = app_config.get('game_logic')
        if not game_logic:
            logger.error("GameLogic not found in app_config for handle_end_turn")
            emit('game_error', {'error': 'Game logic unavailable'}, room=sid)
            return
            
        # TODO: Call game_logic.end_turn(player_id) - Needs implementation in GameLogic
        logger.warning(f"End turn logic not fully implemented yet for player {player_id}.")
        emit('action_received', {'action': 'end_turn', 'status': 'pending_logic', 'message': 'End turn logic TBD'}, room=sid) # Placeholder response

    @app_socketio.on('start_game')
    def handle_start_game(data, *args):
        """Handles request to start the game. Only admin should be able to trigger this."""
        sid = request.sid
        admin_key = data.get('admin_key')
        expected_admin_key = app_config.get('ADMIN_KEY')
        
        logger.info(f"[Socket] Received 'start_game' event (SID: {sid})")
        if args:
             logger.info(f"[Socket] start_game received extra args: {args}")

        # --- Admin Authorization Check --- 
        if not admin_key or admin_key != expected_admin_key:
            logger.warning(f"Unauthorized 'start_game' attempt from SID {sid}.")
            emit('game_error', {'error': 'Unauthorized: Only admins can start the game.', 'action': 'start_game'}, room=sid)
            return
        # --- End Admin Authorization Check --- 

        # Get the CoreSocketController instance from app_config
        core_controller = app_config.get('core_socket_controller') 
        if not core_controller:
             logger.error("CoreSocketController not found in app_config for handle_start_game")
             emit('game_error', {'error': 'Internal server error'}, room=sid)
             return

        # Get specified game_id if provided
        game_id = data.get('game_id')
        
        game_logic = app_config.get('game_logic')
        if not game_logic:
            logger.error("GameLogic not found in app_config for handle_start_game")
            emit('game_error', {'error': 'Game logic unavailable'}, room=sid)
            return
            
        result = game_logic.start_game(data)

        if not result or not result.get('success'):
             error_message = result.get('error', 'Failed to start game.') if result else 'Failed to start game.'
             logger.warning(f"Start game failed: {error_message}")
             emit('game_error', {'error': error_message, 'action': 'start_game'}, room=sid)
        else:
             # Success is broadcast by GameLogic via game_started/game_state_update
             logger.info(f"Game start initiated successfully by admin (SID: {sid}).")
             # Optionally send confirmation back to requesting admin
             emit('game_started', {'success': True, 'game_id': result.get('game_id')}, room=sid)

    @app_socketio.on('create_game')
    def handle_create_game(data, *args):
        """Handles request to create a new game with specified settings."""
        sid = request.sid
        admin_key = data.get('admin_key')
        expected_admin_key = app_config.get('ADMIN_KEY')
        
        logger.info(f"[Socket] Received 'create_game' event (SID: {sid})")
        
        # Admin Authorization Check
        if not admin_key or admin_key != expected_admin_key:
            logger.warning(f"Unauthorized 'create_game' attempt from SID {sid}.")
            emit('game_error', {'error': 'Unauthorized: Only admins can create games.', 'action': 'create_game'}, room=sid)
            return
            
        # Get the game controller from app config
        game_controller = app_config.get('game_controller')
        if not game_controller:
            logger.error("GameController not found in app_config for handle_create_game")
            emit('game_error', {'error': 'Game controller unavailable'}, room=sid)
            return
            
        # Extract game settings from the request
        difficulty = data.get('difficulty', 'normal')
        mode = data.get('mode', 'classic')
        lap_limit = data.get('lap_limit', 0)
        free_parking_fund = data.get('free_parking_fund', True)
        auction_required = data.get('auction_required', True)
        turn_timeout = data.get('turn_timeout', 60)
        
        # Create new game
        result = game_controller.create_new_game(
            difficulty=difficulty,
            lap_limit=lap_limit,
            free_parking_fund=free_parking_fund,
            auction_required=auction_required,
            turn_timeout=turn_timeout
        )
        
        if not result or not result.get('success'):
            error_message = result.get('error', 'Failed to create game.') if result else 'Failed to create game.'
            logger.warning(f"Game creation failed: {error_message}")
            emit('game_error', {'error': error_message, 'action': 'create_game'}, room=sid)
            return
            
        game_id = result.get('game_id')
        logger.info(f"Game created successfully with ID: {game_id}")
        
        # Initialize game mode if not classic
        if mode != 'classic':
            game_mode_controller = app_config.get('game_mode_controller')
            if game_mode_controller:
                mode_result = game_mode_controller.initialize_game_mode(game_id, mode)
                if not mode_result.get('success'):
                    logger.warning(f"Failed to initialize game mode: {mode_result.get('error')}")
        
        # Send success response
        emit('game_created', {
            'success': True,
            'game_id': game_id,
            'mode': mode,
            'difficulty': difficulty
        }, room=sid)
        
    @app_socketio.on('add_player')
    def handle_add_player(data, *args):
        """Handles request to add a human player to the game."""
        sid = request.sid
        admin_key = data.get('admin_key')
        expected_admin_key = app_config.get('ADMIN_KEY')
        
        logger.info(f"[Socket] Received 'add_player' event (SID: {sid})")
        
        # Admin Authorization Check
        if not admin_key or admin_key != expected_admin_key:
            logger.warning(f"Unauthorized 'add_player' attempt from SID {sid}.")
            emit('game_error', {'error': 'Unauthorized: Only admins can add players.', 'action': 'add_player'}, room=sid)
            return
            
        # Get the game controller from app config
        game_controller = app_config.get('game_controller')
        if not game_controller:
            logger.error("GameController not found in app_config for handle_add_player")
            emit('game_error', {'error': 'Game controller unavailable'}, room=sid)
            return
            
        # Extract player data
        username = data.get('username')
        if not username:
            emit('game_error', {'error': 'Username is required', 'action': 'add_player'}, room=sid)
            return
            
        # Generate a PIN for the player
        pin = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        
        # Add player to the game
        result = game_controller.add_player(username, pin)
        
        if not result or not result.get('success'):
            error_message = result.get('error', 'Failed to add player.') if result else 'Failed to add player.'
            logger.warning(f"Player addition failed: {error_message}")
            emit('game_error', {'error': error_message, 'action': 'add_player'}, room=sid)
            return
            
        player_id = result.get('player_id')
        logger.info(f"Player {username} added successfully with ID: {player_id}")
        
        # Send success response
        emit('player_added', {
            'success': True,
            'player_id': player_id,
            'player_name': username,
            'pin': pin,
            'is_bot': False
        }, room=sid)

    @app_socketio.on('remove_player')
    def handle_remove_player(data, *args):
        """Handles request to remove a player from the game."""
        sid = request.sid
        admin_key = data.get('admin_key')
        expected_admin_key = app_config.get('ADMIN_KEY')
        
        logger.info(f"[Socket] Received 'remove_player' event (SID: {sid})")
        
        # Admin Authorization Check
        if not admin_key or admin_key != expected_admin_key:
            logger.warning(f"Unauthorized 'remove_player' attempt from SID {sid}.")
            emit('game_error', {'error': 'Unauthorized: Only admins can remove players.', 'action': 'remove_player'}, room=sid)
            return
            
        # Get the admin controller from app config
        admin_controller = app_config.get('admin_controller')
        if not admin_controller:
            logger.error("AdminController not found in app_config for handle_remove_player")
            emit('game_error', {'error': 'Admin controller unavailable'}, room=sid)
            return
            
        # Extract player data
        player_id = data.get('player_id')
        if not player_id:
            emit('game_error', {'error': 'Player ID is required', 'action': 'remove_player'}, room=sid)
            return
            
        # Remove player from the game
        result = admin_controller.remove_player(player_id, handle_properties='bank', reason='Admin removal')
        
        if not result or not result.get('success'):
            error_message = result.get('error', 'Failed to remove player.') if result else 'Failed to remove player.'
            logger.warning(f"Player removal failed: {error_message}")
            emit('game_error', {'error': error_message, 'action': 'remove_player'}, room=sid)
            return
            
        logger.info(f"Player {player_id} removed successfully")
        
        # Send success response
        emit('player_removed', {
            'success': True,
            'player_id': player_id,
            'message': 'Player removed successfully'
        }, room=sid)

    @app_socketio.on('request_game_state')
    def handle_request_game_state(data=None, *args):
        """Handles a client's request for the current game state."""
        sid = request.sid
        # Get the CoreSocketController instance from app_config
        core_controller = app_config.get('core_socket_controller') 
        if not core_controller:
             logger.error("CoreSocketController not found in app_config for handle_request_game_state")
             emit('game_error', {'error': 'Internal server error'}, room=sid)
             return
             
        player_id = core_controller._get_player_id_from_sid(sid) # Use method from core controller
        game_id = data.get('gameId', 1) if data else 1 # Allow requesting specific game ID later?
        logger.info(f"[Socket] Received 'request_game_state' for game {game_id} from player ID: {player_id} (SID: {sid})")
        if args:
            logger.info(f"[Socket] request_game_state received extra args: {args}")

        if not player_id:
            logger.warning("Received 'request_game_state' from unknown SID.")
            # Don't emit error, just ignore?
            return 

        game_logic = app_config.get('game_logic')
        if not game_logic:
            logger.error("GameLogic not found in app_config for handle_request_game_state")
            emit('game_error', {'error': 'Game logic unavailable'}, room=sid)
            return

        current_state = game_logic.get_game_state(game_id)
        if current_state:
            emit('game_state_update', current_state, room=sid)
            logger.info(f"Sent current game state to requesting player {player_id}")
        else:
            logger.error(f"Could not retrieve game state {game_id} for player {player_id}")
            emit('game_error', {'error': 'Could not retrieve game state'}, room=sid)

    @app_socketio.on('add_bot')
    def handle_add_bot(data, *args):
        """Handles request to add a bot player to the game."""
        sid = request.sid
        admin_key = data.get('admin_key')
        expected_admin_key = app_config.get('ADMIN_KEY')
        
        logger.info(f"[Socket] Received 'add_bot' event (SID: {sid})")
        
        # Admin Authorization Check
        if not admin_key or admin_key != expected_admin_key:
            logger.warning(f"Unauthorized 'add_bot' attempt from SID {sid}.")
            emit('game_error', {'error': 'Unauthorized: Only admins can add bots.', 'action': 'add_bot'}, room=sid)
            return
            
        # Get the bot controller from app config
        bot_controller = app_config.get('bot_controller')
        if not bot_controller:
            logger.error("BotController not found in app_config for handle_add_bot")
            emit('game_error', {'error': 'Bot controller unavailable'}, room=sid)
            return
            
        # Extract bot data
        bot_name = data.get('name', f"Bot_{random.randint(1000, 9999)}")
        bot_type = data.get('type', 'conservative')
        difficulty = data.get('difficulty', 'normal')
        
        # Create the bot
        result = bot_controller.create_bot(bot_name, bot_type, difficulty)
        
        if not result:
            logger.warning(f"Bot creation failed")
            emit('game_error', {'error': 'Failed to create bot player', 'action': 'add_bot'}, room=sid)
            return
            
        logger.info(f"Bot {bot_name} created successfully with ID: {result.id}")
        
        # Send success response
        emit('player_added', {
            'success': True,
            'player_id': result.id,
            'player_name': result.username,
            'is_bot': True,
            'bot_type': bot_type,
            'difficulty': difficulty
        }, room=sid)

    # --- End Player Action Handlers ---

    logger.info("All socket event handlers registered.")

# Removed: handle_remote_player_connect function (logic moved/redundant) 