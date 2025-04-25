from flask import Blueprint, request, jsonify, current_app
from src.controllers.auth_controller import AuthController
import logging

logger = logging.getLogger(__name__)

def register_auth_routes(app, auth_controller):
    """Register authentication related API routes."""
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

    @auth_bp.route('/register', methods=['POST'])
    def register():
        """Handle player registration requests."""
        # Import models DIRECTLY from their modules INSIDE the function
        from src.models import db # db is initialized in __init__
        from src.models.player import Player
        from src.models.game_state import GameState
        
        # Use get_json which handles content type and parsing errors
        data = request.get_json(silent=True)
        
        # Check if data is valid JSON
        if data is None:
            logger.warning("Registration attempt with invalid/missing JSON body or incorrect Content-Type.")
            return jsonify({'success': False, 'error': 'Invalid request format. JSON body required.'}), 400
            
        username = data.get('username')
        pin = data.get('pin')

        if not username or not pin:
            logger.warning("Registration attempt with missing username or PIN.")
            return jsonify({'success': False, 'error': 'Username and PIN are required'}), 400

        # Basic validation (can be enhanced)
        if not isinstance(pin, str) or not pin.isdigit() or not (4 <= len(pin) <= 6):
            logger.warning(f"Registration attempt failed for {username}: Invalid PIN format.")
            return jsonify({'success': False, 'error': 'PIN must be 4-6 digits'}), 400

        if Player.query.filter_by(username=username).first():
            logger.warning(f"Registration attempt failed: Username '{username}' already exists.")
            return jsonify({'success': False, 'error': 'Username already taken'}), 409 # Conflict

        # Assuming a single GameState instance for now (game_id=1)
        # TODO: Implement dynamic game joining/creation if needed
        game_state = GameState.query.get(1) 
        if not game_state:
            # Should we create one if it doesn't exist?
            logger.error("Registration failed: Default game state (ID=1) not found.")
            return jsonify({'success': False, 'error': 'Game setup error'}), 500 
        
        # --- Get starting money from game settings --- 
        starting_money = game_state.settings.get('starting_money', 1500) # Default to 1500 if not set
        logger.info(f"Using starting money: {starting_money} for new player {username}")
        # --- 
        
        try:
            new_player = Player(username=username, pin=pin, game_id=game_state.id, money=starting_money)
            db.session.add(new_player)
            db.session.commit()
            logger.info(f"Successfully registered player '{username}' with ID {new_player.id} in Game {game_state.id}")
            return jsonify({'success': True, 'message': 'Registration successful', 'player_id': new_player.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during registration for {username}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Registration failed due to server error'}), 500

    @auth_bp.route('/login', methods=['POST'])
    def login():
        """Handle player login requests."""
        # Import models DIRECTLY from their modules INSIDE the function
        from src.models.player import Player

        data = request.get_json(silent=True)
        logger.info(f"Received /login request data: {data}") # Log the raw data
        if data is None:
            logger.warning("Login attempt with invalid/missing JSON body or incorrect Content-Type.")
            return jsonify({'success': False, 'error': 'Invalid request format. JSON body required.'}), 400

        # Look for the 'identifier' key sent by the frontend
        identifier = data.get('identifier') 
        pin = data.get('pin')

        logger.info(f"Extracted identifier: {identifier}, pin: {pin}") # Log extracted values

        if not identifier or not pin:
            logger.warning("Login attempt with missing identifier or PIN.")
            return jsonify({'success': False, 'error': 'Username/Player ID and PIN are required'}), 400

        player = Player.query.filter_by(username=identifier).first()

        if player and player.pin == pin:
            logger.info(f"Player '{identifier}' (ID: {player.id}) successfully logged in.")
            # TODO: Add session management / JWT token generation if needed for more robust auth
            return jsonify({'success': True, 'player_id': player.id, 'username': player.username}), 200
        else:
            logger.warning(f"Login attempt failed for username: {identifier}. Invalid credentials.")
            return jsonify({'success': False, 'error': 'Invalid username or PIN'}), 401 # Unauthorized

    @auth_bp.route('/display/initialize', methods=['POST'])
    def initialize_display():
        """Validate the display key."""
        # No models needed here
        data = request.get_json(silent=True)
        if data is None:
            logger.warning("Display init attempt with invalid/missing JSON body.")
            return jsonify({'success': False, 'error': 'Invalid request format.'}), 400

        # Remove display key validation and always return success
        logger.info("Display initialized successfully (no key validation required).")
        return jsonify({'success': True, 'message': 'Display initialized.'}), 200

    @auth_bp.route('/admin/login', methods=['POST'])
    def admin_login():
        # No models needed here
        data = request.get_json()
        admin_key = data.get('admin_key')
        expected_admin_key = current_app.config.get('ADMIN_KEY')

        if not admin_key:
            logger.warning("Admin login attempt failed: Missing admin_key.")
            return jsonify({'success': False, 'error': 'Admin key is required'}), 400
        
        if not expected_admin_key:
            logger.error("Admin login failed: ADMIN_KEY not configured on the server.")
            return jsonify({'success': False, 'error': 'Server configuration error'}), 500

        if admin_key == expected_admin_key:
            logger.info("Admin successfully logged in.")
            # In a real app, you'd issue a session token/cookie here
            return jsonify({'success': True}), 200
        else:
            logger.warning("Admin login attempt failed: Invalid admin_key provided.")
            return jsonify({'success': False, 'error': 'Invalid admin key'}), 401 # Unauthorized

    # Register the blueprint with the Flask app
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered.") 