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

# Set up logger
logger = logging.getLogger(__name__)

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
             
        # Removed player_id identification, only admin key matters now.
        # player_id = core_controller._get_player_id_from_sid(sid) 

        game_logic = app_config.get('game_logic')
        if not game_logic:
            logger.error("GameLogic not found in app_config for handle_start_game")
            emit('game_error', {'error': 'Game logic unavailable'}, room=sid)
            return
            
        result = game_logic.start_game() # Assuming game_id=1 for now

        if not result or not result.get('success'):
             error_message = result.get('error', 'Failed to start game.') if result else 'Failed to start game.'
             logger.warning(f"Start game failed: {error_message}")
             emit('game_error', {'error': error_message, 'action': 'start_game'}, room=sid)
        else:
             # Success is broadcast by GameLogic via game_started/game_state_update
             logger.info(f"Game start initiated successfully by admin (SID: {sid}).")
             # Optionally send confirmation back to requesting admin
             emit('start_game_initiated', {'success': True}, room=sid)

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

    # --- End Player Action Handlers ---

    logger.info("All socket event handlers registered.")

# Removed: handle_remote_player_connect function (logic moved/redundant) 