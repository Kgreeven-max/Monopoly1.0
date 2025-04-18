import logging
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

# --- Admin Authentication Decorator ---
def admin_required(f):
    """Decorator to ensure the request is authenticated with a valid admin key.
    
    Checks the 'X-Admin-Key' header against the ADMIN_KEY in app config.
    Returns 401 Unauthorized if the key is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        # Strict check against configured key, no fallback
        if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'): 
            logger.warning(f"Unauthorized admin access attempt to {request.path}")
            return jsonify({"success": False, "error": "Unauthorized: Missing or invalid admin key"}), 401
        return f(*args, **kwargs)
    return decorated_function
# --- End Decorator ---

# --- Display Authentication Decorator ---
# Moved from board_routes.py for shared use
def display_required(f):
    """Decorator to ensure the request is authenticated with a valid display key.
    
    Checks the 'display_key' query parameter against the DISPLAY_KEY in app config.
    Returns 401 Unauthorized if the key is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        display_key = request.args.get('display_key')
        # Strict check against configured key, no fallback
        if not display_key or display_key != current_app.config.get('DISPLAY_KEY'): 
            logger.warning(f"Unauthorized display access attempt to {request.path}")
            return jsonify({"success": False, "error": "Unauthorized: Missing or invalid display key"}), 401
        return f(*args, **kwargs)
    return decorated_function
# --- End Decorator ---

# --- Player Authentication Decorator ---
def player_required(f):
    """Decorator to ensure the request is accessing their own player data.
    
    Extracts the player_id from the route parameters and validates it against the 
    player_id in the request payload or query parameters.
    
    The player_id parameter must be included in the function's route parameters.
    """
    @wraps(f)
    def decorated_function(player_id, *args, **kwargs):
        # Get authentication details from request
        data = request.json if request.is_json else None
        auth_player_id = data.get('player_id') if data else None
        
        # If not in JSON body, check query parameters
        if auth_player_id is None:
            auth_player_id = request.args.get('player_id')
            
        # Convert to integers for comparison if both are provided
        try:
            if auth_player_id:
                auth_player_id = int(auth_player_id)
            player_id = int(player_id)
        except ValueError:
            logger.warning(f"Invalid player ID format in request to {request.path}")
            return jsonify({"success": False, "error": "Invalid player ID format"}), 400
            
        # Check if auth_player_id matches route player_id or if no auth_player_id was provided
        # This allows both player-authenticated routes and admin routes that specify player_id
        if auth_player_id is not None and auth_player_id != player_id:
            logger.warning(f"Player ID mismatch in request to {request.path}: {auth_player_id} vs {player_id}")
            return jsonify({"success": False, "error": "Unauthorized: Player ID mismatch"}), 401
            
        return f(player_id, *args, **kwargs)
    return decorated_function
# --- End Decorator ---

# Add other shared decorators here if needed (e.g., player_auth_required) 