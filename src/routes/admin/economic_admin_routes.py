from flask import Blueprint, jsonify, request, current_app
from src.routes.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

economic_admin_bp = Blueprint('economic_admin', __name__)

@economic_admin_bp.route('/economic/state', methods=['GET'])
@admin_required
def get_economic_state():
    """Get the current economic state for admin view"""
    try:
        # Get the economic cycle manager from app config
        economic_manager = current_app.config.get('economic_manager')
        
        if not economic_manager:
            logger.error("Economic manager not found in app config")
            return jsonify({
                "success": False,
                "error": "Economic manager not initialized"
            }), 500
        
        # Get current economic state
        result = economic_manager.get_current_economic_state()
        
        if not result.get('success', False):
            logger.error(f"Error getting economic state: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
        
        # Add configuration info to result
        result['config'] = {
            'economic_cycle_enabled': current_app.config.get('ECONOMIC_CYCLE_ENABLED', True),
            'economic_cycle_interval': current_app.config.get('ECONOMIC_CYCLE_INTERVAL', 5),
            'property_values_follow_economy': current_app.config.get('PROPERTY_VALUES_FOLLOW_ECONOMY', True),
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_economic_state: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@economic_admin_bp.route('/economic/force-state', methods=['POST'])
@admin_required
def force_economic_state():
    """Force the economic cycle to a specific state (admin only)"""
    try:
        # Get the economic cycle manager from app config
        economic_manager = current_app.config.get('economic_manager')
        
        if not economic_manager:
            logger.error("Economic manager not found in app config")
            return jsonify({
                "success": False,
                "error": "Economic manager not initialized"
            }), 500
        
        # Get the requested state from the request body
        state = request.json.get('state')
        admin_key = request.json.get('admin_key')
        
        if not state:
            logger.warning("Missing state parameter in force_economic_state request")
            return jsonify({
                "success": False,
                "error": "Missing state parameter"
            }), 400
        
        # Validate state parameter
        valid_states = ["recession", "normal", "growth", "boom"]
        if state not in valid_states:
            logger.warning(f"Invalid state parameter in force_economic_state request: {state}")
            return jsonify({
                "success": False,
                "error": f"Invalid state parameter. Must be one of: {', '.join(valid_states)}"
            }), 400
        
        # Force the economic state
        result = economic_manager.force_economic_state(state, admin_key)
        
        if not result.get('success', False):
            logger.error(f"Error forcing economic state: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
        
        logger.info(f"Economic state forced to {state} by admin")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in force_economic_state: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@economic_admin_bp.route('/economic/toggle', methods=['POST'])
@admin_required
def toggle_economic_cycle():
    """Enable or disable the economic cycle (admin only)"""
    try:
        admin_key = request.json.get('admin_key')
        enabled = request.json.get('enabled')
        
        if enabled is None:
            logger.warning("Missing enabled parameter in toggle_economic_cycle request")
            return jsonify({
                "success": False,
                "error": "Missing enabled parameter"
            }), 400
        
        # Verify admin key
        if admin_key != current_app.config.get('ADMIN_KEY'):
            logger.warning("Invalid admin key in toggle_economic_cycle request")
            return jsonify({
                "success": False,
                "error": "Invalid admin key"
            }), 403
        
        # Update the configuration
        current_app.config['ECONOMIC_CYCLE_ENABLED'] = bool(enabled)
        
        logger.info(f"Economic cycle {'enabled' if enabled else 'disabled'} by admin")
        return jsonify({
            "success": True,
            "message": f"Economic cycle {'enabled' if enabled else 'disabled'}",
            "enabled": current_app.config['ECONOMIC_CYCLE_ENABLED']
        })
        
    except Exception as e:
        logger.error(f"Error in toggle_economic_cycle: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@economic_admin_bp.route('/economic/update-now', methods=['POST'])
@admin_required
def update_economic_cycle_now():
    """Trigger an immediate update of the economic cycle (admin only)"""
    try:
        # Get the economic cycle manager from app config
        economic_manager = current_app.config.get('economic_manager')
        
        if not economic_manager:
            logger.error("Economic manager not found in app config")
            return jsonify({
                "success": False,
                "error": "Economic manager not initialized"
            }), 500
        
        # Verify admin key
        admin_key = request.json.get('admin_key')
        if admin_key != current_app.config.get('ADMIN_KEY'):
            logger.warning("Invalid admin key in update_economic_cycle_now request")
            return jsonify({
                "success": False,
                "error": "Invalid admin key"
            }), 403
        
        # Update the economic cycle
        result = economic_manager.update_economic_cycle()
        
        if not result.get('success', False):
            logger.error(f"Error updating economic cycle: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
        
        logger.info("Economic cycle updated manually by admin")
        return jsonify({
            "success": True,
            "message": "Economic cycle updated manually",
            "new_state": result
        })
        
    except Exception as e:
        logger.error(f"Error in update_economic_cycle_now: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@economic_admin_bp.route('/economic/trigger-event', methods=['POST'])
@admin_required
def trigger_economic_event():
    """Trigger a random or specific economic event (admin only)"""
    try:
        # Get the economic controller from app config
        economic_controller = current_app.config.get('economic_controller')
        
        if not economic_controller:
            logger.error("Economic controller not found in app config")
            return jsonify({
                "success": False,
                "error": "Economic controller not initialized"
            }), 500
        
        # Get parameters from request body
        game_id = request.json.get('game_id')
        admin_key = request.json.get('admin_key')
        specific_event = request.json.get('specific_event')  # Optional
        
        if not game_id:
            logger.warning("Missing game_id parameter in trigger_economic_event request")
            return jsonify({
                "success": False,
                "error": "Missing game_id parameter"
            }), 400
        
        # Verify admin key
        if admin_key != current_app.config.get('ADMIN_KEY'):
            logger.warning("Invalid admin key in trigger_economic_event request")
            return jsonify({
                "success": False,
                "error": "Invalid admin key"
            }), 403
        
        # Trigger the economic event
        result = economic_controller.trigger_economic_event(game_id, admin_key, specific_event)
        
        if not result.get('success', False):
            logger.error(f"Error triggering economic event: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
        
        event_type = specific_event if specific_event else "random"
        logger.info(f"Economic event ({event_type}) triggered for game {game_id} by admin")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in trigger_economic_event: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500 