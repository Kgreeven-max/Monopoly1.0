from flask_socketio import emit, join_room, leave_room
import logging
from datetime import datetime, timedelta
import uuid
from flask import request, current_app
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
import eventlet

# Set up logger
logger = logging.getLogger(__name__)

class SocketController:
    """Controller managing core socket connections, authentication, and status."""
    
    def __init__(self, socketio_instance, app_config):
        self.socketio = socketio_instance
        self.app_config = app_config
        self.connected_players = {} # PlayerID -> {username, socket_id, connected, last_connect, last_disconnect, device_info}
        self.player_reconnect_timers = {} # PlayerID -> Eventlet Timer
        
        # Simplified dependencies for core logic
        self.game_controller = app_config.get('game_controller') # Needed for auto-end turn on timeout
        
        if not self.socketio:
            logger.error("SocketController initialized without SocketIO instance!")
        # Note: GameController might not be strictly necessary if timeout logic is adjusted
        # but keep for now for compatibility with original timeout handler
        if not self.game_controller and self.app_config.get('REMOTE_PLAY_ENABLED', False):
             logger.warning("SocketController initialized without GameController, auto-end turn on timeout might fail.")

    # --- Helper Methods --- 
    def _get_player_id_from_sid(self, sid):
        """Find the player ID associated with a given socket ID."""
        for player_id, info in self.connected_players.items():
            if info.get('socket_id') == sid and info.get('connected', False):
                return player_id
        logger.warning(f"Could not find connected player for SID: {sid}")
        return None
        
    def _register_base_handlers(self):
        """Register core connection handlers."""
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            emit('connection_success', {
                'message': 'Connected to server',
                'socketId': request.sid,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
            game_state = GameState.get_instance()
            player_id_disconnected = None
            player_name = "Unknown"
            
            # Find player associated with this socket ID
            for pid, info in list(self.connected_players.items()): # Iterate over a copy
                if info.get('socket_id') == request.sid:
                    player_id_disconnected = pid
                    player_name = info.get('username', "Unknown")
                    logger.info(f"Player {player_name} (ID: {pid}) disconnected (SID: {request.sid})")
                    
                    # Mark as disconnected but keep the record
                    self.connected_players[pid]['connected'] = False
                    self.connected_players[pid]['last_disconnect'] = datetime.now()
                    
                    # Leave the game room explicitly
                    if game_state:
                        leave_room(game_state.game_id, sid=request.sid)
                        logger.info(f"Player {pid} SID {request.sid} removed from game room {game_state.game_id}")
                    else:
                        logger.warning(f"Could not leave game room for SID {request.sid} - GameState not found.")
                        
                    # If remote play is enabled, start a reconnection timer
                    if self.app_config.get('REMOTE_PLAY_ENABLED', False):
                        timeout_seconds = self.app_config.get('REMOTE_PLAY_TIMEOUT', 60)
                        self._start_reconnect_timer(pid, timeout_seconds)
                    break # Found the player, exit loop
            
            # Notify if a known player disconnected
            if player_id_disconnected and game_state:
                 self.socketio.emit('player_disconnected', {
                    'player_id': player_id_disconnected,
                    'player_name': player_name,
                    'timestamp': datetime.now().isoformat(),
                    'reconnect_timeout': self.app_config.get('REMOTE_PLAY_TIMEOUT', 60) if self.app_config.get('REMOTE_PLAY_ENABLED', False) else None
                }, room=game_state.game_id)
                
    def _start_reconnect_timer(self, player_id, timeout_seconds):
        """Starts or resets the reconnection timer for a player."""
        # Cancel any existing timer
        self.cancel_reconnect_timer(player_id)
        
        def handle_timeout(pid):
            # Check if player is still in connected_players and still disconnected
            if pid in self.connected_players and not self.connected_players[pid].get('connected', False):
                player_name = self.connected_players[pid].get('username', "Unknown")
                logger.info(f"Player {player_name} timed out after {timeout_seconds}s")
                game_state = GameState.get_instance()
                
                # Notify all players of the timeout
                if game_state:
                    self.socketio.emit('player_timed_out', {
                        'player_id': pid,
                        'player_name': player_name,
                        'disconnected_for': timeout_seconds,
                        'timestamp': datetime.now().isoformat()
                    }, room=game_state.game_id)
                    
                    # Check if this is the current player and auto-end their turn if needed
                    if game_state.current_player_id == pid:
                        logger.info(f"Auto-ending turn for timed out player {pid}")
                        # Access GameController instance stored during init
                        if self.game_controller:
                            try:
                                # Use the existing instance, don't create a new one
                                self.game_controller.end_turn(pid, None, is_timeout=True) # Pass is_timeout flag
                            except Exception as e:
                                 logger.error(f"Error auto-ending turn for {pid} on timeout: {e}", exc_info=True)
                        else:
                            logger.error(f"Cannot auto-end turn for {pid}: GameController instance not available.")
                             
                        # Remove timer reference after handling
                        self.player_reconnect_timers.pop(pid, None)

        # Schedule the timeout handler
        self.player_reconnect_timers[player_id] = eventlet.spawn_after(
            timeout_seconds, handle_timeout, player_id)
            
    def cancel_reconnect_timer(self, player_id):
        """Cancels the reconnection timer for a specific player."""
        if player_id in self.player_reconnect_timers:
            try:
                self.player_reconnect_timers[player_id].cancel()
                logger.info(f"Cancelled reconnect timer for player {player_id}")
            except Exception as e:
                logger.error(f"Error cancelling timer for player {player_id}: {e}")
            finally:
                 self.player_reconnect_timers.pop(player_id, None)
            return True
        return False

    def remove_connected_player_entry(self, player_id):
        """Removes a player's entry from the connected_players dictionary."""
        if player_id in self.connected_players:
            removed_info = self.connected_players.pop(player_id, None)
            if removed_info:
                logger.info(f"Removed connection entry for player {player_id} ({removed_info.get('username')})")
                return True
        return False

    def notify_all_player_removed(self, player_id, player_name, game_id):
        """Emits a notification that a player was removed."""
        if self.socketio:
             self.socketio.emit('player_removed', {
                'player_id': player_id,
                'player_name': player_name,
                'removed_by': 'admin', # Assume admin for now, could be parameterized
                'timestamp': datetime.now().isoformat()
            }, room=game_id)
             return True
        return False

    def get_player_connection_status(self, player_id):
        """Checks the connection status of a specific player."""
        if player_id not in self.connected_players:
            return {
                "success": False,
                "status": "never_connected",
                "message": "Player never connected"
            }
        
        info = self.connected_players[player_id]
        if not info.get('connected', False):
            disconnect_time = info.get('last_disconnect')
            disconnect_duration = None
            if disconnect_time:
                disconnect_duration = (datetime.now() - disconnect_time).total_seconds()
            
            return {
                "success": False,
                "status": "disconnected",
                "disconnect_duration": disconnect_duration,
                "message": f"Player disconnected for {int(disconnect_duration)} seconds" if disconnect_duration else "Player disconnected"
            }
            
        # Player is considered connected
        return {
            "success": True,
            "status": "connected",
            "message": "Player is connected",
            "last_connect": info.get('last_connect', None).isoformat() if info.get('last_connect') else None,
            "socket_id": info.get('socket_id')
        }

    # --- Core Event Handlers --- 

    def handle_authenticate_socket(self, data):
        """Associates an authenticated player ID with the current socket connection."""
        player_id = data.get('player_id')
        sid = request.sid
        
        if not player_id:
            logger.warning(f"[AuthSocket] Received authenticate request without player_id from SID: {sid}")
            emit('auth_socket_response', {'success': False, 'error': 'Player ID missing'}, room=sid)
            return

        player = Player.query.get(player_id)
        if not player:
            logger.error(f"[AuthSocket] Invalid player_id {player_id} received for authentication from SID: {sid}")
            emit('auth_socket_response', {'success': False, 'error': 'Invalid player ID'}, room=sid)
            return
            
        logger.info(f"[AuthSocket] Authenticating SID {sid} for Player ID: {player_id} ({player.username})")

        # Cancel reconnect timer if player was previously disconnected
        was_reconnect = self.cancel_reconnect_timer(player_id)
        if was_reconnect:
             logger.info(f"[AuthSocket] Player {player.username} reconnected and authenticated.")

        # Update/Store connection info
        # Preserve last disconnect time if available
        last_disconnect = self.connected_players.get(player_id, {}).get('last_disconnect')
        self.connected_players[player_id] = {
            'username': player.username,
            'socket_id': sid,
            'connected': True,
            'last_connect': datetime.now(),
            'last_disconnect': last_disconnect, 
            'device_info': 'web_authenticated' # Simple marker
        }

        # Join essential rooms
        game_state = GameState.get_instance() # Assumes singleton or correct retrieval
        join_room(sid) # Self room
        join_room(f"player_{player_id}") # Player-specific room
        if game_state:
            join_room(game_state.game_id) # Game room
            logger.info(f"[AuthSocket] Player {player_id} SID {sid} joined game room {game_state.game_id}")
            # Notify game room that player has connected/reconnected fully
            self.socketio.emit('player_connected', {
                'player_id': player_id,
                'player_name': player.username,
                'reconnected': was_reconnect,
                'timestamp': datetime.now().isoformat()
            }, room=game_state.game_id)
        else:
             logger.warning(f"[AuthSocket] Could not join game room for SID {sid} - GameState not found.")

        # Send confirmation back to the client
        emit('auth_socket_response', {'success': True, 'player_id': player_id}, room=sid)
        
    def register_event_handlers(self):
        """Registers all core socket event handlers with the SocketIO instance."""
        self._register_base_handlers()
        
        # Register the new authentication handler
        self.socketio.on('authenticate_socket')(self.handle_authenticate_socket)

        @self.socketio.on('register_device')
        def handle_register_device(data):
            device_type = data.get('type')
            logger.info(f"Registering device: {request.sid} as {device_type}")
            game_state = GameState.get_instance()
            was_reconnect = False

            if device_type == 'player':
                player_id = data.get('player_id')
                pin = data.get('pin')
                player = Player.query.get(player_id)

                if not player or player.pin != pin:
                    emit('device_registered', {'status': 'error', 'error': 'Invalid player credentials'})
                    return

                # Check if reconnecting
                if player_id in self.connected_players and not self.connected_players[player_id].get('connected', True):
                    logger.info(f"Player {player.username} reconnected.")
                    self.cancel_reconnect_timer(player_id)
                    was_reconnect = True
                
                # Update connection status
                device_info_str = data.get('client', 'web') # Or get more details if provided
                self.connected_players[player_id] = {
                    'username': player.username,
                    'socket_id': request.sid,
                    'connected': True,
                    'last_connect': datetime.now(),
                    'last_disconnect': self.connected_players.get(player_id, {}).get('last_disconnect'), # Keep last disconnect time
                    'device_info': device_info_str
                }

                join_room(request.sid) # Join self room
                join_room(f"player_{player_id}")
                if game_state:
                    join_room(game_state.game_id)
                # Try joining social rooms - requires Social models
                try:
                    from src.models.social.chat import ChannelMember
                    for m in ChannelMember.query.filter_by(player_id=player_id).all(): join_room(f"channel_{m.channel_id}")
                    from src.models.social.alliance import AllianceMember
                    for m in AllianceMember.query.filter_by(player_id=player_id, status='active').all(): join_room(f"alliance_{m.alliance_id}")
                except Exception as e: logger.error(f"Error joining social rooms for {player_id}: {e}")
                
                emit('device_registered', {
                    'status': 'success', 'device_type': 'player', 
                    'player': player.to_dict(), # Send basic player info
                    'was_reconnect': was_reconnect
                })
                logger.info(f"Player {player.username} ({player_id}) registered device: {request.sid}")

                # --- Emit initial game state to the connecting player --- 
                if game_state:
                    game_controller = current_app.config.get('game_controller')
                    if game_controller:
                        current_state = game_controller.get_game_state() # Fetch current state
                        if current_state.get('success'):
                            logger.info(f"Sending initial game state to player {player_id}")
                            emit('game_state_update', current_state['game_state'], room=request.sid)
                        else:
                            logger.error(f"Failed to get game state for player {player_id}")
                            emit('game_error', {'error': 'Failed to retrieve initial game state.'}, room=request.sid)
                    else:
                        logger.error("GameController not found in app config, cannot send initial state.")

                # Notify others
                if game_state:
                    self.socketio.emit('player_connected', {
                         'player_id': player_id, 'player_name': player.username,
                         'timestamp': datetime.now().isoformat()
                    }, room=game_state.game_id, skip_sid=request.sid)

            elif device_type == 'admin':
                admin_key = data.get('admin_key')
                if not admin_key or admin_key != self.app_config.get('ADMIN_KEY'):
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

        @self.socketio.on('heartbeat')
        def handle_heartbeat():
            emit('heartbeat_response', {'timestamp': datetime.now().isoformat()})
            
        @self.socketio.on('join_game') # Note: Might be redundant due to register_device
        def handle_join_game(data):
             player_id = data.get('player_id'); pin = data.get('pin')
             player = Player.query.get(player_id)
             if not player or player.pin != pin: emit('auth_error', {'error': 'Invalid player credentials'}); return
             logger.info(f"Player {player.username} re-emitted join_game (potentially redundant)")
             # Maybe re-join rooms just in case?
             game_state = GameState.get_instance()
             if game_state: join_room(game_state.game_id)
             join_room(f"player_{player_id}")
             emit('join_success', { 'message': f"Re-joined game, {player.username}!", 'player_id': player_id})

        @self.socketio.on('get_connection_status')
        def handle_get_connection_status():
            players_status = {}
            for pid, info in self.connected_players.items():
                disconnect_duration = None
                if not info.get('connected', False) and 'last_disconnect' in info:
                    disconnect_duration = (datetime.now() - info['last_disconnect']).total_seconds()
                players_status[pid] = {
                    'connected': info.get('connected', False), 'username': info.get('username', 'Unknown'),
                    'last_connect': info.get('last_connect', None).isoformat() if info.get('last_connect') else None,
                    'last_disconnect': info.get('last_disconnect', None).isoformat() if info.get('last_disconnect') else None,
                    'disconnect_duration': disconnect_duration, 'device_info': info.get('device_info', 'Unknown')
                }
            timeout_seconds = self.app_config.get('REMOTE_PLAY_TIMEOUT', 60)
            emit('connection_status', {
                'players': players_status, 'timeout_seconds': timeout_seconds,
                'remote_play_enabled': self.app_config.get('REMOTE_PLAY_ENABLED', False),
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('ping_player') # Admin initiated - Recommended to use HTTP route instead
        def handle_ping_player(data):
             logger.warning("'ping_player' socket event received. Recommend using HTTP route /api/remote/players/ping/<id> instead.")
             admin_key = data.get('admin_key')
             if admin_key != self.app_config.get('ADMIN_KEY'): emit('ping_error', {'error': 'Unauthorized'}); return
             player_id = data.get('player_id')
             status = self.get_player_connection_status(player_id)
             if status['success']:
                 socket_id = status.get('socket_id')
                 if socket_id: 
                     self.socketio.emit('ping_request', {'timestamp': datetime.now().isoformat()}, to=socket_id)
                     emit('ping_result', {'success': True, 'message': 'Ping sent'})
                 else: emit('ping_error', {'error': 'Could not find socket ID'})
             else: emit('ping_result', status)

        @self.socketio.on('ping_response')
        def handle_ping_response(data):
            player_id = data.get('player_id')
            pin = data.get('pin') # Player should include PIN for auth
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                 logger.warning(f"Invalid ping response auth from {player_id}"); return
                 
            if player_id in self.connected_players:
                latency = data.get('latency')
                # Optionally update internal latency tracking if needed
                # Emit response back to admin room
                self.socketio.emit('player_ping_response', {
                    'player_id': player_id,
                    'player_name': self.connected_players[player_id].get('username'),
                    'latency': latency 
                }, room="admin") 
            else: logger.warning(f"Received ping response from untracked player {player_id}")

        @self.socketio.on('remove_player') # Admin initiated - Recommended to use HTTP route instead
        def handle_remove_player(data):
             logger.warning("'remove_player' socket event received. Recommend using HTTP route /api/remote/players/remove/<id> instead.")
             admin_key = data.get('admin_key')
             if admin_key != self.app_config.get('ADMIN_KEY'): emit('remove_error', {'error': 'Unauthorized'}); return
             player_id = data.get('player_id'); player = Player.query.get(player_id)
             if not player: emit('remove_error', {'error': 'Player not found'}); return
             
             # Try disconnecting socket first (might fail if already gone)
             status_result = self.get_player_connection_status(player_id)
             socket_id = status_result.get('socket_id')
             if socket_id:
                 try: self.socketio.server.disconnect(socket_id); logger.info(f"Disconnected socket {socket_id} via admin remove event.")
                 except Exception as e: logger.warning(f"Could not disconnect socket {socket_id} on remove event: {e}")
                 
             self.cancel_reconnect_timer(player_id)
             removed = self.remove_connected_player_entry(player_id)
             game_state = GameState.get_instance()
             if game_state: self.notify_all_player_removed(player_id, player.username, game_state.game_id)
             emit('remove_result', {'success': True, 'player_id': player_id, 'player_name': player.username})

        @self.socketio.on('ping') # Generic client ping
        def handle_ping(data):
            emit('pong', {'ts': data.get('ts', 0), 'server_time': datetime.now().isoformat()})
            if not data.get('silent', False): logger.debug(f"Ping from {request.sid}")


def register_core_socket_handlers(app_socketio, app_config):
    """Register core connection/auth/status socket event handlers."""
    
    socket_controller = SocketController(app_socketio, app_config)
    
    # Store the controller instance in app config for potential access elsewhere 
    # (e.g., admin routes needing connection status)
    if 'socket_controller' not in app_config:
        app_config['socket_controller'] = socket_controller
    else:
        # If it already exists, log a warning - should ideally only be created once.
        # Or, decide if this registration function should *retrieve* an existing
        # controller instead of creating one.
        logger.warning("'socket_controller' already exists in app_config during core handler registration. Overwriting may not be intended.")
        app_config['socket_controller'] = socket_controller # Overwrite for now
        
    # Register events handled directly by SocketController
    socket_controller.register_event_handlers()
    logger.info("Core socket handlers registered.")
    
    # Return the instance if needed by the caller (e.g., the main registration function)
    return socket_controller

# Note: The GameController dependency in handle_timeout needs to be resolved.
# It currently relies on being passed via app_config.
# Ensure GameController is initialized and added to app_config *before*
# this registration function is called if REMOTE_PLAY_ENABLED is True. 