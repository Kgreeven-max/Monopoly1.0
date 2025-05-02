from flask import jsonify, request, current_app, Blueprint
from src.controllers.game_controller import GameController
from functools import wraps
import logging
# Import shared decorator
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)

# Create Blueprint
game_bp = Blueprint('game', __name__)

# Store the game controller instance
game_controller = None

def init_game_controller(controller):
    """Initialize the game controller for the blueprint"""
    global game_controller
    game_controller = controller
    
# Add back the register_game_routes function for compatibility with the root app.py
def register_game_routes(app, game_controller_instance):
    """Register game-related routes with the Flask app"""
    # Store the game controller in the global variable
    global game_controller
    game_controller = game_controller_instance
    
    # Define routes directly on the app
    @app.route('/api/game/new', methods=['POST'])
    def new_game():
        """Create a new game with specified settings"""
        # Use get_json(silent=True) to avoid raising an error on empty/invalid body
        data = request.get_json(silent=True)
        if data is None:
            data = {} # Default to empty dict if body is empty or not valid JSON
            
        difficulty = data.get('difficulty', 'normal')
        lap_limit = data.get('lap_limit', 0)  # 0 for unlimited
        free_parking_fund = data.get('free_parking_fund', True)
        auction_required = data.get('auction_required', True)
        turn_timeout = data.get('turn_timeout', 60)
        
        result = game_controller.create_new_game(
            difficulty=difficulty,
            lap_limit=lap_limit,
            free_parking_fund=free_parking_fund,
            auction_required=auction_required,
            turn_timeout=turn_timeout
        )
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/join', methods=['POST'])
    def join_game():
        """Join an existing game as a player"""
        data = request.json
        username = data.get('username')
        pin = data.get('pin')
        
        if not username or not pin:
            return jsonify({'success': False, 'error': 'Username and PIN are required'}), 400
        
        result = game_controller.add_player(username, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/state', methods=['GET'])
    def get_game_state():
        """Get the current state of the game"""
        result = game_controller.get_game_state()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/start', methods=['POST'])
    @admin_required
    def start_game():
        """Start the game"""
        # Create data dictionary with admin_pin
        data = request.json or {}
        
        # Ensure admin_pin is passed from the request
        if 'admin_pin' not in data:
            # Get admin key from app config
            data['admin_pin'] = current_app.config.get('ADMIN_KEY')
        
        result = game_controller.start_game(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/end', methods=['POST'])
    @admin_required
    def end_game():
        """End the current game"""
        reason = request.json.get('reason', 'normal')
        result = game_controller.end_game(reason)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/players', methods=['GET'])
    def get_players():
        """Get a list of all players in the game"""
        result = game_controller.get_players()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/config', methods=['POST'])
    @admin_required
    def update_config():
        """Update game configuration"""
        config_data = request.json.get('config')
        result = game_controller.update_game_config(config_data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/game/history', methods=['GET'])
    def get_game_history():
        """Get history of completed games"""
        game_id = request.args.get('game_id')
        
        if game_id:
            # Get specific game history
            result = game_controller.get_game_history_by_id(int(game_id))
        else:
            # Get all game history
            limit = request.args.get('limit', 10, type=int)
            result = game_controller.get_all_game_history(limit)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

# Blueprint routes remain the same
@game_bp.route('/new', methods=['POST'])
def new_game():
    """Create a new game with specified settings"""
    # Use get_json(silent=True) to avoid raising an error on empty/invalid body
    data = request.get_json(silent=True)
    if data is None:
        data = {} # Default to empty dict if body is empty or not valid JSON
        
    difficulty = data.get('difficulty', 'normal')
    lap_limit = data.get('lap_limit', 0)  # 0 for unlimited
    free_parking_fund = data.get('free_parking_fund', True)
    auction_required = data.get('auction_required', True)
    turn_timeout = data.get('turn_timeout', 60)
    
    result = game_controller.create_new_game(
        difficulty=difficulty,
        lap_limit=lap_limit,
        free_parking_fund=free_parking_fund,
        auction_required=auction_required,
        turn_timeout=turn_timeout
    )
    
    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@game_bp.route('/join', methods=['POST'])
def join_game():
    """Join an existing game as a player"""
    data = request.json
    username = data.get('username')
    pin = data.get('pin')
    
    if not username or not pin:
        return jsonify({'success': False, 'error': 'Username and PIN are required'}), 400
    
    result = game_controller.add_player(username, pin)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/state', methods=['GET'])
def get_game_state():
    """Get the current state of the game"""
    result = game_controller.get_game_state()
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/start', methods=['POST'])
@admin_required
def start_game():
    """Start the game"""
    # Create data dictionary with admin_pin
    data = request.json or {}
    
    # Ensure admin_pin is passed from the request
    if 'admin_pin' not in data:
        # Get admin key from app config
        data['admin_pin'] = current_app.config.get('ADMIN_KEY')
    
    result = game_controller.start_game(data)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/end', methods=['POST'])
@admin_required
def end_game():
    """End the current game"""
    reason = request.json.get('reason', 'normal')
    result = game_controller.end_game(reason)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/players', methods=['GET'])
def get_players():
    """Get a list of all players in the game"""
    result = game_controller.get_players()
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/config', methods=['POST'])
@admin_required
def update_config():
    """Update game configuration"""
    config_data = request.json.get('config')
    result = game_controller.update_game_config(config_data)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_bp.route('/history', methods=['GET'])
def get_game_history():
    """Get history of completed games"""
    game_id = request.args.get('game_id')
    
    if game_id:
        # Get specific game history
        result = game_controller.get_game_history_by_id(int(game_id))
    else:
        # Get all game history
        limit = request.args.get('limit', 10, type=int)
        result = game_controller.get_all_game_history(limit)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400
            
# Removed /api/game/property/action route - Handled by socket events
# @app.route('/api/game/property/action', methods=['POST'])
# def property_action(): ... 