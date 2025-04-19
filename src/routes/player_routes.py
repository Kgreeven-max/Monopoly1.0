import logging
from flask import Blueprint, jsonify, request, current_app
from src.controllers.player_controller import PlayerController
from src.models.player import Player
from src.utils.token_validation import validate_token

logger = logging.getLogger(__name__)
player_bp = Blueprint('player_bp', __name__, url_prefix='/api/player')

def register_player_routes(app, player_controller):
    """Register player-related routes with the Flask app"""
    # Retrieve the existing PlayerController instance from app config
    # player_controller = current_app.config['player_controller'] # Removed - Passed as argument
    
    @player_bp.route('/<int:player_id>/status', methods=['GET'])
    def get_status(player_id):
        """API endpoint to get a player's status."""
        # TODO: Add authentication/authorization check here later
        # For now, allow fetching any player status if ID is valid
        
        result, status_code = player_controller.get_player_status(player_id)
        return jsonify(result), status_code
    
    @app.route('/api/player/roll', methods=['POST'])
    def roll_dice():
        """Roll dice for a player's turn"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = player_controller.roll_dice(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/player/end-turn', methods=['POST'])
    def end_turn():
        """End the current player's turn"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = player_controller.end_turn(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/player/report-income', methods=['POST'])
    def report_income():
        """Report income when landing on or passing GO"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        income = data.get('income')
        
        if not player_id or not pin or income is None:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and income are required'}), 400
        
        result = player_controller.report_income(player_id, pin, income)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/player/jail-action', methods=['POST'])
    def jail_action():
        """Handle jail options (pay fine, use card, roll)"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        action = data.get('action')  # 'pay', 'card', 'roll'
        
        if not player_id or not pin or not action:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and action are required'}), 400
        
        result = player_controller.handle_jail_action(player_id, pin, action)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/player/properties', methods=['GET'])
    def get_player_properties():
        """Get a list of properties owned by a player"""
        player_id = request.args.get('player_id')
        pin = request.args.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = player_controller.get_player_properties(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    @player_bp.route('/credit_score/<player_id>', methods=['GET'])
    def get_credit_score(player_id):
        """
        Get a player's credit score.
        
        Args:
            player_id (str): The ID of the player.
            
        Returns:
            A JSON response containing the player's credit score and credit rating.
        """
        try:
            # Validate player exists
            player = Player.query.get(player_id)
            if not player:
                return jsonify({"success": False, "error": "Player not found"}), 404
            
            # Get credit score and determine credit rating
            credit_score = player.credit_score
            
            credit_rating = "Poor"
            if credit_score >= 800:
                credit_rating = "Excellent"
            elif credit_score >= 700:
                credit_rating = "Good"
            elif credit_score >= 600:
                credit_rating = "Fair"
            
            return jsonify({
                "success": True,
                "player_id": player_id,
                "player_name": player.name,
                "credit_score": credit_score,
                "credit_rating": credit_rating,
                "bankruptcy_count": player.bankruptcy_count
            }), 200
            
        except Exception as e:
            logging.error(f"Error getting credit score for player {player_id}: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/player/bankruptcy', methods=['POST'])
    def player_declare_bankruptcy():
        """Handle player bankruptcy declaration"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        player_controller = current_app.config.get('player_controller')
        if not player_controller:
            return jsonify({'success': False, 'error': 'Server configuration error'}), 500
            
        result = player_controller.handle_bankruptcy(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    app.register_blueprint(player_bp)
    logger.info("Player routes registered.") 
    return app 