from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
game_admin_bp = Blueprint('game_admin', __name__, url_prefix='')

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
    
    # Call the implemented admin_controller method
    result = admin_controller.modify_game_state(state_changes, reason)
        
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
    """Reset the game to initial state"""
    try:
        # Call the implemented admin_controller method
        result = admin_controller.reset_game()
        
        logger.info(f"Game reset result: {result}")
        
        # Notify clients that bots have been reset
        if result.get('success'):
            # Get socketio from app config
            from flask import current_app
            socketio = current_app.config.get('socketio')
            if socketio:
                socketio.emit('bots_reset', {'message': 'All bots removed during game reset'})
                logger.info("Emitted bots_reset event to clients")
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error in admin_reset_game: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@game_admin_bp.route('/system-status', methods=['GET'])
@admin_required
def system_status():
    """Get server and game system status"""
    # Call the implemented admin_controller method
    result = admin_controller.get_system_status()
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_admin_bp.route('/system-health-trends', methods=['GET'])
@admin_required
def system_health_trends():
    """Get system health metrics and trends over time"""
    try:
        # Get the optional hours parameter
        hours = request.args.get('hours', default=24, type=int)
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # 1 hour to 7 days
            return jsonify({
                "success": False, 
                "error": "Hours parameter must be between 1 and 168"
            }), 400
        
        # Call the implemented admin_controller method
        result = admin_controller.get_system_health_trends(hours)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error in system_health_trends: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 