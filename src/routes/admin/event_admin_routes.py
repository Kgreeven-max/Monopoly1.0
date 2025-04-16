from flask import Blueprint, jsonify, request, current_app
import logging
from src.models.game_state import GameState
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
event_admin_bp = Blueprint('event_admin', __name__, url_prefix='/events')

@event_admin_bp.route('/trigger', methods=['POST'])
@admin_required
def trigger_event():
    """Manually trigger a specific game event"""
    data = request.json
    event_type = data.get('event_type')
    params = data.get('params', {})
    reason = data.get('reason', 'Admin triggered event')
    
    if not event_type:
        return jsonify({'success': False, 'error': 'Event type is required'}), 400
    
    # Get event_system from app config
    event_system = current_app.config.get('event_system')
    if not event_system:
         return jsonify({'success': False, 'error': 'Event system not initialized'}), 500

    # TODO: Verify event_type exists in event_system and call appropriate method
    # For now, using a generic placeholder
    # result = event_system.trigger_event(event_type, params, reason)
    # Placeholder response:
    result = {"success": True, "message": f"Placeholder: Triggered event {event_type}"}
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@event_admin_bp.route('/list', methods=['GET'])
@admin_required
def list_events():
    """List available game events"""
    # Get event_system from app config
    event_system = current_app.config.get('event_system')
    if not event_system:
         return jsonify({'success': False, 'error': 'Event system not initialized'}), 500

    # TODO: Get available events from event_system
    # available_events = event_system.list_available_events()
    # Placeholder response:
    available_events = ["placeholder_event_1", "placeholder_event_2"]
    
    return jsonify({"success": True, "events": available_events}), 200

@event_admin_bp.route('/history', methods=['GET'])
@admin_required
def event_history():
    """Get history of triggered events"""
    # Get event_system from app config
    event_system = current_app.config.get('event_system')
    if not event_system:
         return jsonify({'success': False, 'error': 'Event system not initialized'}), 500

    # TODO: Get event history from event_system or a dedicated log/db table
    # history = event_system.get_event_history()
    # Placeholder response:
    history = [{"event": "placeholder_event_1", "timestamp": "2023-01-01T10:00:00Z"}]
    
    return jsonify({"success": True, "history": history}), 200 