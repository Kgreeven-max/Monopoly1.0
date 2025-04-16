from flask import Blueprint, jsonify, request, current_app, send_file
import logging
from functools import wraps
from src.controllers.remote_controller import RemoteController
from datetime import datetime
import qrcode
import io
from src.models.player import Player
from src.models.game_state import GameState

# Create blueprint
remote_bp = Blueprint('remote', __name__)
logger = logging.getLogger(__name__)

# Initialize controller
remote_controller = RemoteController()

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('key')
        if not admin_key or admin_key != current_app.config['ADMIN_KEY']:
            return jsonify({"error": "Unauthorized", "message": "Admin key required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def register_remote_routes(app):
    """Register remote play routes with the Flask app"""
    app.register_blueprint(remote_bp, url_prefix='/api/remote')
    logger.info("Remote routes registered")

# Routes for remote play setup
@remote_bp.route('/status', methods=['GET'])
@admin_required
def get_tunnel_status():
    """Get the status of the Cloudflare Tunnel"""
    status = remote_controller.get_tunnel_status()
    return jsonify(status)

@remote_bp.route('/check-installation', methods=['GET'])
@admin_required
def check_installation():
    """Check if cloudflared is installed"""
    installed = remote_controller.check_cloudflared_installed()
    version = remote_controller.get_cloudflared_version() if installed else None
    
    return jsonify({
        "installed": installed,
        "version": version
    })

@remote_bp.route('/create', methods=['POST'])
@admin_required
def create_tunnel():
    """Create a new Cloudflare Tunnel"""
    tunnel_name = request.json.get('tunnel_name', 'pinopoly')
    result = remote_controller.create_tunnel(tunnel_name)
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@remote_bp.route('/start', methods=['POST'])
@admin_required
def start_tunnel():
    """Start the Cloudflare Tunnel"""
    result = remote_controller.start_tunnel()
    
    if result["success"]:
        # Add tunnel URL to app config for use in templates
        current_app.config['TUNNEL_URL'] = result.get('tunnel_url')
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@remote_bp.route('/stop', methods=['POST'])
@admin_required
def stop_tunnel():
    """Stop the Cloudflare Tunnel"""
    result = remote_controller.stop_tunnel()
    
    if result["success"]:
        # Remove tunnel URL from app config
        current_app.config.pop('TUNNEL_URL', None)
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@remote_bp.route('/delete', methods=['DELETE'])
@admin_required
def delete_tunnel():
    """Delete the Cloudflare Tunnel"""
    result = remote_controller.delete_tunnel()
    
    if result["success"]:
        # Remove tunnel URL from app config
        current_app.config.pop('TUNNEL_URL', None)
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Public endpoint to get tunnel info (just the URL, if running)
@remote_bp.route('/info', methods=['GET'])
def get_tunnel_info():
    """Get public tunnel information (URL only)"""
    status = remote_controller.get_tunnel_status()
    
    return jsonify({
        "remote_enabled": status.get("running", False),
        "remote_url": status.get("url") if status.get("running", False) else None
    })

# Routes for remote player management
@remote_bp.route('/players', methods=['GET'])
@admin_required
def get_connected_players():
    """Get list of connected remote players"""
    players = remote_controller.get_connected_players()
    
    return jsonify({
        "success": True,
        "players": players
    })

@remote_bp.route('/players/ping/<player_id>', methods=['POST'])
@admin_required
def ping_player(player_id):
    """Ping a specific player to check connection quality"""
    # Get socket controller from app config
    socket_controller = current_app.config.get('socket_controller')
    socketio = current_app.config.get('socketio')
    if not socket_controller or not socketio:
        return jsonify({"success": False, "error": "Socket systems not initialized"}), 500

    # Use controller method to check status
    status_result = socket_controller.get_player_connection_status(player_id)
    
    if not status_result.get('success'):
        status_code = 404 if status_result.get('status') == 'never_connected' else 400
        return jsonify({"success": False, "error": status_result.get('message', 'Player not connected or disconnected')}), status_code

    # Send ping through socketio using player-specific room
    player_socket_id = status_result.get('socket_id')
    if not player_socket_id:
        return jsonify({"success": False, "error": "Could not find player socket ID"}), 500
        
    try:
        # Assuming ping_request is handled by the SocketController or directly
        socketio.emit('ping_request', {'timestamp': datetime.now().isoformat()}, room=player_socket_id) # Use room=socket_id if direct emit preferred
        return jsonify({"success": True, "message": f"Ping sent to player {player_id}"})
    except Exception as e:
        logger.error(f"Error emitting ping request to player {player_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to send ping request"}), 500

@remote_bp.route('/players/remove/<player_id>', methods=['DELETE'])
@admin_required
def remove_player(player_id):
    """Remove a player from the remote connections"""
    # Get socket controller from app config
    socket_controller = current_app.config.get('socket_controller')
    socketio = current_app.config.get('socketio')
    if not socket_controller or not socketio:
        return jsonify({"success": False, "error": "Socket systems not initialized"}), 500

    # Get player info for name and socket_id
    player = Player.query.get(player_id)
    if not player:
         return jsonify({"success": False, "error": "Player not found in database"}), 404
         
    status_result = socket_controller.get_player_connection_status(player_id)
    socket_id = status_result.get('socket_id') # Get socket ID if connected

    # Disconnect the client if currently connected via socket
    if socket_id and status_result.get('status') == 'connected':
        try:
            socketio.server.disconnect(socket_id)
            logger.info(f"Admin disconnected remote player {player_id} (Socket: {socket_id})")
        except Exception as e:
            logger.warning(f"Could not disconnect socket {socket_id} for player {player_id}: {e}")
    
    # Cancel any reconnection timer via controller
    socket_controller.cancel_reconnect_timer(player_id)
    
    # Remove player from tracking via controller
    removed = socket_controller.remove_connected_player_entry(player_id)
    
    # Notify others (assuming game_id is available)
    game_state = GameState.get_instance()
    if game_state:
         socket_controller.notify_all_player_removed(player_id, player.username, game_state.game_id)
    
    if removed:
        return jsonify({"success": True, "message": f"Player {player_id} removed from tracking"})
    else:
        # Player might not have been actively tracked anymore, but timer/disconnect was attempted
        return jsonify({"success": True, "message": f"Player {player_id} connection management finalized."}), 202 # Accepted

@remote_bp.route('/timeout', methods=['POST'])
@admin_required
def update_timeout():
    """Update the reconnect timeout setting for remote play"""
    timeout_seconds = request.json.get('timeout')
    
    try:
        timeout = int(timeout_seconds)
        if timeout < 10 or timeout > 300:
            return jsonify({"success": False, "error": "Timeout must be between 10 and 300 seconds"}), 400
        
        # Update app config
        current_app.config['REMOTE_PLAY_TIMEOUT'] = timeout
        
        # Return success
        return jsonify({
            "success": True,
            "message": f"Timeout updated to {timeout} seconds",
            "timeout": timeout
        })
        
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid timeout value"}), 400

# QR Code generator endpoint
@remote_bp.route('/qr', methods=['GET'])
@admin_required
def get_qr_code():
    """Generate QR code for tunnel URL"""
    # Get current tunnel status
    status = remote_controller.get_tunnel_status()
    
    if not status.get("running", False) or not status.get("url"):
        return jsonify({"error": "Tunnel not running or URL not available"}), 400
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    tunnel_url = status.get("url")
    connect_url = f"{tunnel_url}/connect"
    qr.add_data(connect_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes IO
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Return as image
    return send_file(img_bytes, mimetype='image/png') 