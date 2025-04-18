from flask import Blueprint, jsonify, request
import logging
from src.controllers.finance_controller import FinanceController
from src.routes.decorators import player_required

# Create blueprint
finance_player_bp = Blueprint('finance_player', __name__)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize controller in route registration rather than here
finance_controller = None

@finance_player_bp.route('/player/<int:player_id>/loans', methods=['GET'])
@player_required
def get_player_loans(player_id):
    """Get all loans for a player"""
    if not finance_controller:
        return jsonify({'success': False, 'error': 'Finance controller not initialized'}), 500
    
    result = finance_controller.get_player_loans(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@finance_player_bp.route('/player/<int:player_id>/cds', methods=['GET'])
@player_required
def get_player_cds(player_id):
    """Get all certificates of deposit for a player"""
    if not finance_controller:
        return jsonify({'success': False, 'error': 'Finance controller not initialized'}), 500
    
    result = finance_controller.get_player_cds(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@finance_player_bp.route('/player/<int:player_id>/helocs', methods=['GET'])
@player_required
def get_player_helocs(player_id):
    """Get all home equity lines of credit for a player"""
    if not finance_controller:
        return jsonify({'success': False, 'error': 'Finance controller not initialized'}), 500
    
    result = finance_controller.get_player_helocs(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@finance_player_bp.route('/player/<int:player_id>/financial-summary', methods=['GET'])
@player_required
def get_financial_summary(player_id):
    """Get a summary of player's financial status"""
    if not finance_controller:
        return jsonify({'success': False, 'error': 'Finance controller not initialized'}), 500
    
    result = finance_controller.get_player_financial_summary(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Initialize blueprint with app and controller
def init_finance_player_routes(app):
    """Initialize the finance player blueprint with controller instance"""
    global finance_controller
    
    # Get finance controller from app config
    finance_controller = FinanceController(
        socketio=app.config.get('socketio'),
        banker=app.config.get('banker'),
        game_state=app.config.get('game_state_instance')
    )
    
    logger.info(f"Finance player routes initialized with controller")
    return finance_player_bp 