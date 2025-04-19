from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
crime_admin_bp = Blueprint('crime_admin', __name__, url_prefix='/crime')

# Initialize the admin controller
admin_controller = AdminController()

@crime_admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_crime_settings():
    """
    Get current crime system settings.
    """
    try:
        # Call a controller method to get crime settings
        # We need to implement this method in admin_controller.py
        result = admin_controller.get_crime_settings()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting crime settings: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_crime_settings():
    """
    Update crime system settings.
    
    Request body:
    - frequency: How often crimes occur (value between 0.0 and 1.0)
    - severity: How severe crimes are (value between 0.0 and 1.0)
    - enabled: Whether the crime system is enabled
    - jail_time: Default jail time in turns
    - bail_amount: Default bail amount
    """
    try:
        # Get settings data from request body
        settings_data = request.json
        
        if not settings_data:
            return jsonify({"success": False, "error": "Settings data is required"}), 400
        
        # Call the controller method
        result = admin_controller.manage_crime_settings(settings_data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error updating crime settings: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_crime_statistics():
    """
    Get statistics on crimes for the admin dashboard.
    """
    try:
        # We need to implement this method in admin_controller.py
        result = admin_controller.get_crime_statistics()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting crime statistics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/trigger-random', methods=['POST'])
@admin_required
def trigger_random_crime():
    """
    Trigger a random crime event.
    
    Request body (optional):
    - severity: Force a specific severity level (LOW, MEDIUM, HIGH)
    - target_player_id: Force a specific player to be targeted
    """
    try:
        data = request.json or {}
        
        severity = data.get('severity')
        target_player_id = data.get('target_player_id')
        
        # We need to implement this method in admin_controller.py
        result = admin_controller.trigger_random_crime(severity, target_player_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error triggering random crime: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/jail/release/<int:player_id>', methods=['POST'])
@admin_required
def release_from_jail(player_id):
    """
    Release a player from jail.
    """
    try:
        # We need to implement this method in admin_controller.py
        result = admin_controller.release_player_from_jail(player_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error releasing player {player_id} from jail: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/jail/send/<int:player_id>', methods=['POST'])
@admin_required
def send_to_jail(player_id):
    """
    Send a player to jail.
    
    Request body (optional):
    - turns: Number of turns to spend in jail
    - reason: Reason for sending to jail
    """
    try:
        data = request.json or {}
        
        turns = data.get('turns')
        reason = data.get('reason', 'Admin action')
        
        # We need to implement this method in admin_controller.py
        result = admin_controller.send_player_to_jail(player_id, turns, reason)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error sending player {player_id} to jail: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/history', methods=['GET'])
@admin_required
def get_crime_history():
    """
    Get history of crimes.
    
    Query parameters:
    - player_id: Filter by player
    - start_date: Filter by date >= start_date
    - end_date: Filter by date <= end_date
    - limit: Limit the number of results
    """
    try:
        # Get optional filter parameters
        filters = {}
        
        if 'player_id' in request.args:
            filters['player_id'] = int(request.args.get('player_id'))
        
        if 'start_date' in request.args:
            filters['start_date'] = request.args.get('start_date')
        
        if 'end_date' in request.args:
            filters['end_date'] = request.args.get('end_date')
        
        limit = int(request.args.get('limit', 50))
        
        # We need to implement this method in admin_controller.py
        result = admin_controller.get_crime_history(filters, limit)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting crime history: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@crime_admin_bp.route('/jail/status', methods=['GET'])
@admin_required
def get_jail_status():
    """
    Get current jail status (who is in jail).
    """
    try:
        # We need to implement this method in admin_controller.py
        result = admin_controller.get_jail_status()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting jail status: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 