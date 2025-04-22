from flask import Blueprint, jsonify, request, current_app
import logging
from functools import wraps
from src.controllers.game_mode_controller import GameModeController
from src.models import db
from src.models.game_mode import GameMode
from src.models.game_state import GameState

# Create blueprint
game_mode_bp = Blueprint('game_mode', __name__)
logger = logging.getLogger(__name__)

# Initialize controller
game_mode_controller = GameModeController()

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key') or request.args.get('key') or request.json.get('admin_pin')
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

# Fix the URL structure for the select endpoint
@game_mode_bp.route('/select/<string:mode_id>', methods=['POST'])
def select_game_mode(mode_id):
    """Select and initialize a game mode for a game"""
    try:
        # Get game_id from request body
        data = request.json
        game_id = data.get('game_id')
        admin_pin = data.get('admin_pin')
        
        # Check admin authorization
        if not admin_pin or admin_pin != current_app.config['ADMIN_KEY']:
            return jsonify({
                "success": False,
                "error": "Unauthorized. Admin PIN required."
            }), 401
        
        if not game_id:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: game_id"
            }), 400
        
        # Verify the game exists
        game = GameState.query.filter_by(game_id=game_id).first()
        if not game:
            logger.error(f"Game not found with ID: {game_id}")
            return jsonify({
                "success": False,
                "error": f"Game not found with ID: {game_id}"
            }), 404
        
        logger.info(f"Initializing game mode {mode_id} for game {game_id}")
        result = game_mode_controller.initialize_game_mode(game_id, mode_id)
        
        if result.get("success", False):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error selecting game mode: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to set game mode: {str(e)}"
        }), 500

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

@game_mode_bp.route('/update-advanced-settings/<string:game_id>', methods=['POST'])
@admin_required
def update_advanced_settings(game_id):
    """Update advanced game settings"""
    try:
        # Get settings from request body
        data = request.json
        settings = data.get('settings', {})
        
        if not settings:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: settings"
            }), 400
        
        # Verify the game exists
        game = GameState.query.filter_by(game_id=game_id).first()
        if not game:
            logger.error(f"Game not found with ID: {game_id}")
            return jsonify({
                "success": False,
                "error": f"Game not found with ID: {game_id}"
            }), 404
        
        logger.info(f"Updating advanced settings for game {game_id}: {settings}")
        
        # Save settings to game state
        # Handle property value factor
        if 'property_value_factor' in settings:
            game.property_value_factor = float(settings['property_value_factor'])
            
        # Handle property rent factor  
        if 'property_rent_factor' in settings:
            game.property_rent_factor = float(settings['property_rent_factor'])
            
        # Handle property injuries
        if 'enable_property_injuries' in settings:
            game.enable_property_injuries = bool(settings['enable_property_injuries'])
            
        # Handle inflation rate
        if 'inflation_rate' in settings:
            game.inflation_rate = float(settings['inflation_rate'])
            
        # Handle economic cycle interval
        if 'economic_cycle_interval' in settings:
            game.economic_cycle_interval = int(settings['economic_cycle_interval'])
            
        # Handle market crashes
        if 'enable_market_crashes' in settings:
            game.enable_market_crashes = bool(settings['enable_market_crashes'])
            
        # Handle turn timer seconds
        if 'turn_timer_seconds' in settings:
            game.turn_timer_seconds = int(settings['turn_timer_seconds'])
            
        # Handle max turns
        if 'max_turns' in settings:
            game.max_turns = int(settings['max_turns'])
            
        # Handle max time minutes
        if 'max_time_minutes' in settings:
            game.max_time_minutes = int(settings['max_time_minutes'])
        
        # Save changes to database
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Advanced settings updated successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error updating advanced settings: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to update advanced settings: {str(e)}"
        }), 500 