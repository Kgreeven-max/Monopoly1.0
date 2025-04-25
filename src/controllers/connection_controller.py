# src/controllers/connection_controller.py

import logging
from flask_socketio import emit, join_room # Import join_room
from flask import request, current_app
from datetime import datetime
import eventlet # Required for timer
from src.models import db # Assuming db is needed
from src.models.game_state import GameState
from src.models.player import Player

logger = logging.getLogger(__name__)

# This dictionary will store connected player info (move from SocketController)
# Key: PlayerID, Value: Dict{username, socket_id, connected, last_connect, last_disconnect, device_info}
connected_players = {}
# This dictionary will store reconnect timers (move from SocketController)
# Key: PlayerID, Value: Eventlet Timer
player_reconnect_timers = {}

# Helper function to get player ID (needs access to connected_players)
def _get_player_id_from_sid(sid):
    """Find the player ID associated with a given socket ID."""
    for player_id, info in connected_players.items():
        if info.get('socket_id') == sid and info.get('connected', False):
            return player_id
    logger.warning(f"Could not find connected player for SID: {sid}")
    return None

# Helper function to cancel timer (needs access to player_reconnect_timers)
def cancel_reconnect_timer(player_id):
    """Cancels the reconnection timer for a specific player."""
    if player_id in player_reconnect_timers:
        try:
            player_reconnect_timers[player_id].cancel()
            logger.info(f"Cancelled reconnect timer for player {player_id}")
        except Exception as e:
            logger.error(f"Error cancelling timer for player {player_id}: {e}")
        finally:
             player_reconnect_timers.pop(player_id, None)
        return True
    return False

# Helper function to start timer (needs access to connected_players and player_reconnect_timers)
def _start_reconnect_timer(player_id, timeout_seconds):
    """Starts or resets the reconnection timer for a player."""
    # Cancel any existing timer
    cancel_reconnect_timer(player_id)
    
    # Nested function needs access to socketio, maybe pass it in?
    # For now, assume access via current_app or pass socketio instance
    socketio = current_app.extensions['socketio'] 

    def handle_timeout(pid):
        # Check if player is still in connected_players and still disconnected
        if pid in connected_players and not connected_players[pid].get('connected', False):
            player_name = connected_players[pid].get('username', "Unknown")
            logger.info(f"Player {player_name} timed out after {timeout_seconds}s")
            game_state = GameState.get_instance()
            
            # Notify all players of the timeout
            if game_state:
                socketio.emit('player_timed_out', {
                    'player_id': pid,
                    'player_name': player_name,
                    'disconnected_for': timeout_seconds,
                    'timestamp': datetime.now().isoformat()
                }, room=game_state.game_id)
                
                # Check if this is the current player and auto-end their turn if needed
                if game_state.current_player_id == pid:
                    logger.info(f"Auto-ending turn for timed out player {pid}")
                    # Need GameController instance - how to get?
                    # Maybe emit an event that GameController listens for?
                    # Or use app context if GameController is registered?
                    # For now, log error - requires further refactoring
                    logger.error("Auto-end turn on timeout needs GameController access.")
                    # from src.controllers.game_controller import GameController
                    # try:
                    #     gc = GameController()
                    #     gc.end_turn(pid, None, is_timeout=True) # Pass is_timeout flag
                    # except Exception as e:
                    #      logger.error(f"Error auto-ending turn for {pid} on timeout: {e}", exc_info=True)
                         
            # Remove timer reference after handling
            player_reconnect_timers.pop(pid, None)

    # Schedule the timeout handler
    player_reconnect_timers[player_id] = eventlet.spawn_after(
        timeout_seconds, handle_timeout, player_id)

def register_connection_handlers(socketio):
    """Registers connection-related socket event handlers."""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_success', {
            'message': 'Connected to server',
            'socketId': request.sid,
            'timestamp': datetime.now().isoformat()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
        game_state = GameState.get_instance()
        player_id_disconnected = None
        player_name = "Unknown"
        
        # Find player associated with this socket ID
        for pid, info in list(connected_players.items()): # Iterate over a copy
            if info.get('socket_id') == request.sid:
                player_id_disconnected = pid
                player_name = info.get('username', "Unknown")
                logger.info(f"Player {player_name} (ID: {pid}) disconnected")
                
                # Mark as disconnected but keep the record
                connected_players[pid]['connected'] = False
                connected_players[pid]['last_disconnect'] = datetime.now()
                
                # If remote play is enabled, start a reconnection timer
                app_config = current_app.config
                if app_config.get('REMOTE_PLAY_ENABLED', False):
                    timeout_seconds = app_config.get('REMOTE_PLAY_TIMEOUT', 60)
                    _start_reconnect_timer(pid, timeout_seconds)
                break # Found the player, exit loop
        
        # Notify if a known player disconnected
        if player_id_disconnected and game_state:
             socketio.emit('player_disconnected', {
                'player_id': player_id_disconnected,
                'player_name': player_name,
                'timestamp': datetime.now().isoformat(),
                'reconnect_timeout': current_app.config.get('REMOTE_PLAY_TIMEOUT', 60) if current_app.config.get('REMOTE_PLAY_ENABLED', False) else None
            }, room=game_state.game_id) 

    @socketio.on('register_device')
    def handle_register_device(data):
        device_type = data.get('type')
        logger.info(f"Registering device: {request.sid} as {device_type}")
        game_state = GameState.get_instance()
        was_reconnect = False
        app_config = current_app.config # Get app config

        if device_type == 'player':
            player_id = data.get('player_id')
            pin = data.get('pin')
            player = Player.query.get(player_id)

            if not player or player.pin != pin:
                emit('device_registered', {'status': 'error', 'error': 'Invalid player credentials'})
                return

            # Check if reconnecting
            if player_id in connected_players and not connected_players[player_id].get('connected', True):
                logger.info(f"Player {player.username} reconnected.")
                cancel_reconnect_timer(player_id)
                was_reconnect = True
            
            # Update connection status (uses module-level connected_players)
            device_info_str = data.get('client', 'web') # Or get more details if provided
            connected_players[player_id] = {
                'username': player.username,
                'socket_id': request.sid,
                'connected': True,
                'last_connect': datetime.now(),
                'last_disconnect': connected_players.get(player_id, {}).get('last_disconnect'), # Keep last disconnect time
                'device_info': device_info_str
            }

            join_room(request.sid) # Join self room
            join_room(f"player_{player_id}")
            if game_state:
                join_room(game_state.game_id)
            try:
                # TODO: Decouple social room joining - maybe emit event?
                from src.models.social.chat import ChannelMember
                for m in ChannelMember.query.filter_by(player_id=player_id).all(): join_room(f"channel_{m.channel_id}")
                from src.models.social.alliance import AllianceMember
                for m in AllianceMember.query.filter_by(player_id=player_id, status='active').all(): join_room(f"alliance_{m.alliance_id}")
            except Exception as e: logger.error(f"Error joining social rooms for {player_id}: {e}")
            
            emit('device_registered', {
                'status': 'success', 'device_type': 'player', 'player': player.to_dict(),
                'was_reconnect': was_reconnect
            })
            logger.info(f"Player {player.username} ({player_id}) registered device: {request.sid}")
            
            # Notify others
            if game_state:
                socketio.emit('player_connected', {
                     'player_id': player_id, 'player_name': player.username,
                     'timestamp': datetime.now().isoformat()
                }, room=game_state.game_id, skip_sid=request.sid)

        elif device_type == 'admin':
            admin_key = data.get('admin_key')
            if not admin_key or admin_key != app_config.get('ADMIN_KEY'):
                emit('device_registered', {'status': 'error', 'error': 'Invalid admin key'})
                return
            join_room("admin")
            emit('device_registered', {'status': 'success', 'device_type': 'admin'})
            logger.info(f"Admin registered device: {request.sid}")

        elif device_type == 'tv':
            # Remove display key validation
            join_room("tv")
            emit('device_registered', {'status': 'success', 'device_type': 'tv'})
            logger.info(f"TV display registered device: {request.sid}")

        elif device_type == 'spectator':
            join_room("spectators") # General room for non-authenticated viewers
            logger.info(f"Spectator registered device: {request.sid}")
            emit('device_registered', {'status': 'success', 'device_type': 'spectator'})
        else:
            emit('device_registered', {'status': 'error', 'error': 'Invalid device type'})

    # Add other connection-related handlers here (e.g., heartbeat, get_connection_status)
    @socketio.on('heartbeat')
    def handle_heartbeat():
        emit('heartbeat_response', {'timestamp': datetime.now().isoformat()})
    
    @socketio.on('get_connection_status') # Primarily for admin/debug?
    def handle_get_connection_status():
        players_status = {}
        for pid, info in connected_players.items():
            disconnect_duration = None
            if not info.get('connected', False) and 'last_disconnect' in info:
                disconnect_duration = (datetime.now() - info['last_disconnect']).total_seconds()
            players_status[pid] = {
                'connected': info.get('connected', False), 'username': info.get('username', 'Unknown'),
                'last_connect': info.get('last_connect', None).isoformat() if info.get('last_connect') else None,
                'last_disconnect': info.get('last_disconnect', None).isoformat() if info.get('last_disconnect') else None,
                'disconnect_duration': disconnect_duration, 'device_info': info.get('device_info', 'Unknown')
            }
        # Emit back to the requesting client (assumed admin or specific user)
        emit('connection_status_update', players_status)

    # Ping handlers could go here too, but consider if they are truly connection management
    @socketio.on('ping') # Generic client ping
    def handle_ping(data):
        logger.debug(f"Received ping from {request.sid} with data: {data}")
        emit('pong', data) # Echo back data

# Add helper methods that were previously in SocketController if needed by these handlers,
# ensuring they use the module-level dictionaries (connected_players, player_reconnect_timers)
# Example:
def get_player_connection_status(player_id):
    # ... (implementation using module-level connected_players) ...
    pass

def remove_connected_player_entry(player_id):
     # ... (implementation using module-level connected_players) ...
    pass 