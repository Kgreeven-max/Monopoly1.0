from flask import Blueprint, jsonify, request, current_app
import logging
from src.models.game_state import GameState
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required
from src.models.event import EventType

logger = logging.getLogger(__name__)
event_admin_bp = Blueprint('event_admin', __name__, url_prefix='/events')

# Initialize the admin controller
admin_controller = AdminController()

@event_admin_bp.route('/trigger', methods=['POST'])
@admin_required
def manual_trigger_event():
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

@event_admin_bp.route('/', methods=['GET'])
@admin_required
def get_events():
    """
    Get all game events with optional filtering.
    
    Query parameters:
    - status: Filter by event status (active, scheduled, completed, etc.)
    - type: Filter by event type
    - start_time: Return events after this time
    - end_time: Return events before this time
    - limit: Maximum number of events to return (default: 50)
    - offset: Offset for pagination (default: 0)
    """
    try:
        # Get filter parameters
        filters = {}
        
        if 'status' in request.args:
            filters['status'] = request.args.get('status')
        
        if 'type' in request.args:
            filters['type'] = request.args.get('type')
        
        if 'start_time' in request.args:
            filters['start_time'] = request.args.get('start_time')
        
        if 'end_time' in request.args:
            filters['end_time'] = request.args.get('end_time')
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Call the controller method
        result = admin_controller.get_events(filters, limit, offset)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/<int:event_id>', methods=['GET'])
@admin_required
def get_event(event_id):
    """
    Get details for a specific event.
    """
    try:
        result = admin_controller.get_event_details(event_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/', methods=['POST'])
@admin_required
def create_event():
    """
    Create a new game event.
    
    Request body:
    - name: Event name
    - type: Event type (market_crash, bonus_day, tax_holiday, etc.)
    - description: Event description
    - start_time: When the event starts (timestamp)
    - end_time: When the event ends (timestamp)
    - targets: Array of affected targets (all, properties, players, specific IDs)
    - parameters: Object containing event-specific parameters
    - is_recurring: Whether this is a recurring event
    - recurrence_pattern: If recurring, the pattern (daily, weekly, etc.)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Event data is required"}), 400
        
        required_fields = ['name', 'type']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Call the controller method
        result = admin_controller.create_event(data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error creating event: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/<int:event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """
    Update an existing game event.
    
    Request body may include:
    - name: Event name
    - description: Event description
    - start_time: When the event starts (timestamp)
    - end_time: When the event ends (timestamp)
    - targets: Array of affected targets
    - parameters: Object containing event-specific parameters
    - status: Event status (scheduled, active, canceled, completed)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Update data is required"}), 400
        
        # Call the controller method
        result = admin_controller.update_event(event_id, data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/<int:event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    """
    Delete or cancel an event.
    
    Query parameters:
    - cancel_only: If true, only cancel the event instead of deleting it (default: false)
    """
    try:
        cancel_only = request.args.get('cancel_only', 'false').lower() == 'true'
        
        # Call the controller method
        result = admin_controller.delete_event(event_id, cancel_only)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/<int:event_id>/trigger', methods=['POST'])
@admin_required
def trigger_event(event_id):
    """
    Manually trigger an event to start immediately.
    
    Request body (optional):
    - force: Whether to force the event to start even if conditions aren't met (default: false)
    - duration_override: Override the event duration in minutes (optional)
    """
    try:
        data = request.json or {}
        force = data.get('force', False)
        duration_override = data.get('duration_override')
        
        # Call the controller method
        result = admin_controller.trigger_event_now(event_id, force, duration_override)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error triggering event {event_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/<int:event_id>/end', methods=['POST'])
@admin_required
def end_event(event_id):
    """
    Manually end an active event.
    
    Request body (optional):
    - force: Whether to force the event to end even if there are issues (default: false)
    """
    try:
        data = request.json or {}
        force = data.get('force', False)
        
        # Call the controller method
        result = admin_controller.end_event(event_id, force)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error ending event {event_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/types', methods=['GET'])
@admin_required
def get_event_types():
    """
    Get a list of all available event types and their parameters.
    """
    try:
        result = admin_controller.get_event_types()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting event types: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/schedule', methods=['GET'])
@admin_required
def get_event_schedule():
    """
    Get the schedule of upcoming events.
    
    Query parameters:
    - days: Number of days to include in the schedule (default: 7)
    """
    try:
        days = int(request.args.get('days', 7))
        
        # Call the controller method
        result = admin_controller.get_event_schedule(days)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting event schedule: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/active', methods=['GET'])
@admin_required
def get_active_events():
    """
    Get all currently active events.
    """
    try:
        result = admin_controller.get_active_events()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting active events: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/random', methods=['POST'])
@admin_required
def trigger_random_event():
    """
    Trigger a random event.
    
    Request body (optional):
    - category: Limit to a specific event category
    - min_severity: Minimum severity level (1-5)
    - max_severity: Maximum severity level (1-5)
    - duration: Event duration in minutes
    - exclude_types: Array of event types to exclude
    """
    try:
        data = request.json or {}
        
        # Call the controller method
        result = admin_controller.trigger_random_event(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error triggering random event: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/history', methods=['GET'])
@admin_required
def get_event_history():
    """
    Get history of past events.
    
    Query parameters:
    - limit: Maximum number of events to return (default: 50)
    - offset: Offset for pagination (default: 0)
    - type: Filter by event type
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    """
    try:
        # Get filter parameters
        filters = {}
        
        if 'type' in request.args:
            filters['type'] = request.args.get('type')
        
        if 'start_date' in request.args:
            filters['start_date'] = request.args.get('start_date')
        
        if 'end_date' in request.args:
            filters['end_date'] = request.args.get('end_date')
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Call the controller method
        result = admin_controller.get_event_history(filters, limit, offset)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting event history: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/templates', methods=['GET'])
@admin_required
def get_event_templates():
    """
    Get all saved event templates.
    """
    try:
        result = admin_controller.get_event_templates()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting event templates: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/templates', methods=['POST'])
@admin_required
def create_event_template():
    """
    Create a new event template.
    
    Request body:
    - name: Template name
    - description: Template description
    - event_type: Type of event
    - parameters: Default parameters for the event
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Template data is required"}), 400
        
        required_fields = ['name', 'event_type']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Call the controller method
        result = admin_controller.create_event_template(data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error creating event template: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@admin_required
def delete_event_template(template_id):
    """
    Delete an event template.
    """
    try:
        result = admin_controller.delete_event_template(template_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error deleting event template {template_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@event_admin_bp.route('/impact-analysis', methods=['POST'])
@admin_required
def analyze_event_impact():
    """
    Analyze the potential impact of an event before creating it.
    
    Request body:
    - event_data: Complete event data object
    """
    try:
        data = request.json
        
        if not data or 'event_data' not in data:
            return jsonify({"success": False, "error": "Event data is required"}), 400
        
        # Call the controller method
        result = admin_controller.analyze_event_impact(data['event_data'])
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error analyzing event impact: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 