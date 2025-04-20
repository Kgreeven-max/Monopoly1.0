from flask import Blueprint, jsonify, request, current_app
import logging
from functools import wraps
from src.controllers.game_mode_controller import GameModeController
from src.models import db
from src.models.game_mode import GameMode

# Create blueprint
game_mode_bp = Blueprint('game_mode', __name__)
logger = logging.getLogger(__name__)

# Initialize controller
game_mode_controller = GameModeController()

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('key')
        if not admin_key or admin_key != current_app.config['ADMIN_KEY']:
            return jsonify({"error": "Unauthorized", "message": "Admin key required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def register_game_mode_routes(app):
    """Register game mode routes with the Flask app"""
    app.register_blueprint(game_mode_bp, url_prefix='/api/game-modes')
    logger.info("Game mode routes registered")

# Routes for game mode management
@game_mode_bp.route('/', methods=['GET'])
def get_available_modes():
    """Get list of available game modes"""
    try:
        modes = game_mode_controller.get_available_modes()
        
        if not modes:
            logger.warning("No game modes available from controller")
            # Return empty but valid structure
            modes = {"standard": [], "specialty": []}
        
        return jsonify({
            "success": True,
            "modes": modes
        })
    except Exception as e:
        logger.error(f"Error getting available game modes: {e}", exc_info=True)
        # Return empty but valid structure in case of error
        return jsonify({
            "success": False,
            "error": str(e),
            "modes": {"standard": [], "specialty": []}
        }), 500

@game_mode_bp.route('/select/<game_id>', methods=['POST'])
@admin_required
def select_game_mode(game_id):
    """Select and initialize a game mode for a game"""
    mode_id = request.json.get('mode_id')
    
    if not mode_id:
        return jsonify({
            "success": False,
            "error": "Missing required parameter: mode_id"
        }), 400
    
    result = game_mode_controller.initialize_game_mode(game_id, mode_id)
    
    if result.get("success", False):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_mode_bp.route('/check-win/<game_id>', methods=['GET'])
def check_win_condition(game_id):
    """Check if win condition is met for current game mode"""
    result = game_mode_controller.check_win_condition(game_id)
    
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 400
    
    return jsonify({
        "success": True,
        "result": result
    })

@game_mode_bp.route('/settings/<game_id>', methods=['GET'])
def get_game_mode_settings(game_id):
    """Get current game mode settings"""
    result = game_mode_controller.get_game_mode_settings(game_id)
    
    if result.get("success", False):
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@game_mode_bp.route('/update-settings/<game_id>', methods=['POST'])
@admin_required
def update_game_mode_settings(game_id):
    """Update specific game mode settings"""
    updated_settings = request.json.get('settings', {})
    
    # Don't allow changing the core mode type
    if "mode_type" in updated_settings:
        return jsonify({
            "success": False,
            "error": "Cannot change core game mode type. Create a new game with the desired mode."
        }), 400
    
    result = game_mode_controller.update_game_mode_settings(game_id, updated_settings)
    
    if result.get("success", False):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_mode_bp.route('/list-active', methods=['GET'])
@admin_required
def list_active_game_modes():
    """List all active game modes"""
    modes = GameMode.query.all()
    
    return jsonify({
        "success": True,
        "modes": [mode.to_dict() for mode in modes]
    }) 