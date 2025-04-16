from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController # Needed for trigger_audit
from src.controllers.crime_controller import CrimeController # Needed for pardon, stats
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
crime_admin_bp = Blueprint('crime_admin', __name__, url_prefix='/crime')

# Assumes AdminController and CrimeController instances are accessible
admin_controller = AdminController()
crime_controller = CrimeController()

@crime_admin_bp.route('/trigger-audit', methods=['POST'])
@admin_required
def trigger_audit():
    """Trigger a tax audit for a player"""
    data = request.json
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'success': False, 'error': 'Player ID is required'}), 400
    
    # TODO: Call the (currently placeholder) admin_controller method
    # result = admin_controller.trigger_player_audit(player_id)
    # Placeholder response:
    result = {"success": True, "message": f"Placeholder: Triggered audit for player {player_id}"}
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@crime_admin_bp.route('/police-activity', methods=['POST'])
@admin_required
def set_police_activity():
    """Set the police activity level (affects crime detection rates)"""
    data = request.json
    activity_level = data.get('activity_level')

    if activity_level is None:
        return jsonify({'success': False, 'error': 'Activity level is required'}), 400
        
    try:
        activity_level = float(activity_level)
        if activity_level < 0.1 or activity_level > 3.0:
            raise ValueError("Activity level must be between 0.1 and 3.0")
    except (ValueError, TypeError):
         return jsonify({'success': False, 'error': 'Invalid activity level'}), 400

    # TODO: Call the (currently placeholder) crime_controller method?
    # Or directly modify GameState if simple enough?
    # result = crime_controller.set_police_activity(activity_level)
    # Placeholder response:
    result = {"success": True, "message": f"Placeholder: Set police activity to {activity_level}"}

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@crime_admin_bp.route('/pardon', methods=['POST'])
@admin_required
def pardon_player():
    """Pardon a player for a specific crime or all crimes"""
    data = request.json
    player_id = data.get('player_id')
    crime_id = data.get('crime_id') # Optional
    
    if not player_id:
        return jsonify({'success': False, 'error': 'Player ID is required'}), 400
    
    # TODO: Call the (currently placeholder) crime_controller method?
    # result = crime_controller.pardon_player(player_id, crime_id)
    # Placeholder response:
    result = {"success": True, "message": f"Placeholder: Pardoned player {player_id} (crime: {crime_id or 'all'})"}
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@crime_admin_bp.route('/statistics', methods=['GET'])
@admin_required
def admin_crime_statistics():
    """Get detailed crime statistics for admin dashboard"""
    # TODO: Call the (currently placeholder) crime_controller method?
    # stats = crime_controller.get_crime_statistics()
    # Placeholder response:
    stats = {"theft_attempts": 0, "vandalism_incidents": 0}

    return jsonify({"success": True, "statistics": stats}) 