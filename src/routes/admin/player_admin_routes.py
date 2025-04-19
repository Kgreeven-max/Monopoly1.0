from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
player_admin_bp = Blueprint('player_admin', __name__, url_prefix='/players')

# Assumes AdminController instance is accessible, e.g., via app context or passed during registration
# For simplicity, instantiate directly here for now, but consider better DI patterns.
admin_controller = AdminController()

@player_admin_bp.route('/modify-cash', methods=['POST'])
@admin_required
def modify_cash():
    """Modify a player's cash balance"""
    data = request.json
    player_id = data.get('player_id')
    amount = data.get('amount')
    reason = data.get('reason', 'Admin adjustment')
    
    if not player_id or amount is None:
        return jsonify({'success': False, 'error': 'Player ID and amount are required'}), 400
    
    # Call the implemented admin_controller method
    result = admin_controller.modify_player_cash(player_id, amount, reason)
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@player_admin_bp.route('/transfer-property', methods=['POST'])
@admin_required
def transfer_property():
    """Transfer property ownership between players or to/from bank"""
    data = request.json
    property_id = data.get('property_id')
    from_player_id = data.get('from_player_id')  # null for bank
    to_player_id = data.get('to_player_id')  # null for bank
    reason = data.get('reason', 'Admin transfer')
    
    if not property_id:
        return jsonify({'success': False, 'error': 'Property ID is required'}), 400
    
    # Call the implemented admin_controller method
    result = admin_controller.transfer_property(property_id, from_player_id, to_player_id, reason)
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@player_admin_bp.route('/<int:player_id>', methods=['GET'])
@admin_required
def admin_get_player(player_id):
    """Get detailed player info"""
    # Delegate to controller (already refactored)
    result = admin_controller.get_admin_player_details(player_id)
    
    if result.get('success'):
        result.pop('success', None) 
        return jsonify(result), 200
    elif result.get('error') == 'Player not found':
        return jsonify({"error": "Player not found"}), 404
    else:
        return jsonify({"error": result.get('error', 'Failed to get player details')}), 500

@player_admin_bp.route('/audit/<int:player_id>', methods=['POST'])
@admin_required
def audit_player(player_id):
    """Trigger an audit of player's activities and finances"""
    # Call the implemented admin_controller method
    result = admin_controller.trigger_player_audit(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    elif result.get('error') == 'Player not found':
        return jsonify({"error": "Player not found"}), 404
    else:
        return jsonify({"error": result.get('error', 'Failed to audit player')}), 500

@player_admin_bp.route('/remove', methods=['POST'])
@admin_required
def remove_player():
    """Remove a player from the game"""
    data = request.json
    player_id = data.get('player_id')
    handle_properties = data.get('handle_properties', 'bank')  # 'bank' or 'auction'
    reason = data.get('reason', 'Admin removal')
    
    if not player_id:
        return jsonify({'success': False, 'error': 'Player ID is required'}), 400
    
    # Call the implemented admin_controller method
    result = admin_controller.remove_player(player_id, handle_properties, reason)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400 