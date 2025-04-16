from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
game_admin_bp = Blueprint('game_admin', __name__, url_prefix='/game')

# Assumes AdminController instance is accessible
admin_controller = AdminController()

@game_admin_bp.route('/modify-state', methods=['POST'])
@admin_required
def modify_game_state():
    """Override current game state values"""
    data = request.json
    state_changes = data.get('state_changes')
    reason = data.get('reason', 'Admin adjustment')
    
    if not state_changes:
        return jsonify({'success': False, 'error': 'State changes are required'}), 400
    
    # TODO: Call the (currently placeholder) admin_controller method
    # result = admin_controller.modify_game_state(state_changes, reason)
    # Placeholder response:
    result = {"success": True, "message": "Placeholder: Modified game state"}
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_admin_bp.route('/status', methods=['GET'])
@admin_required
def admin_status():
    """Get current game status for admin dashboard"""
    # Delegate to controller (already refactored)
    result = admin_controller.get_admin_game_status()
    
    if result.get('success'):
        result.pop('success', None)
        return jsonify(result), 200
    else:
        return jsonify({"error": result.get('error', 'Failed to get admin status')}), 500

@game_admin_bp.route('/reset', methods=['POST'])
@admin_required
def admin_reset_game():
    """Reset the game to initial state (DISABLED)"""
    # DISABLED FOR SAFETY: Full database reset via API is too risky.
    # Use offline database management scripts or tools for resets.
    logger.warning("Attempted use of disabled admin reset route via game_admin_bp.")
    return jsonify({
        "success": False,
        "status": "disabled", 
        "message": "Game reset via API is disabled for safety. Use offline scripts."
    }), 403 # Return 403 Forbidden

@game_admin_bp.route('/system-status', methods=['GET'])
@admin_required
def system_status():
    """Get server and game system status"""
    # TODO: Call the (currently placeholder) admin_controller method
    # result = admin_controller.get_system_status()
    # Placeholder response:
    result = {"success": True, "message": "Placeholder: System status OK"}
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400 