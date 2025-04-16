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

# Add other shared decorators here if needed (e.g., player_auth_required) 