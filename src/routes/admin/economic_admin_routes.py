from flask import Blueprint, jsonify, request, current_app
import logging
from src.models.game_state import GameState
from src.routes.decorators import admin_required
from src.models.economic_cycle_manager import EconomicCycleManager
from datetime import datetime

logger = logging.getLogger(__name__)
economic_admin_bp = Blueprint('economic_admin', __name__, url_prefix='/economic')

# Get or create economic manager
def get_economic_manager():
    """Get or create the economic cycle manager"""
    economic_manager = current_app.config.get('economic_manager')
    if not economic_manager:
        economic_manager = EconomicCycleManager(
            socketio=current_app.config.get('socketio'),
            banker=current_app.config.get('banker')
        )
        current_app.config['economic_manager'] = economic_manager
    return economic_manager

@economic_admin_bp.route('/state', methods=['GET'])
@admin_required
def get_economic_state():
    """Get the current economic state of the game."""
    try:
        # Get game state
        game_state = GameState.query.first()
        if not game_state:
            return jsonify({
                "success": False, 
                "error": "Game state not found"
            }), 404
            
        # Get economic state data
        economic_state = {
            "current_state": game_state.inflation_state if hasattr(game_state, 'inflation_state') else "normal",
            "inflation_rate": game_state.inflation_rate if hasattr(game_state, 'inflation_rate') else 0.0,
            "base_interest_rate": game_state.base_interest_rate if hasattr(game_state, 'base_interest_rate') else 0.05,
            "cycle_position": 0.5,  # Default to middle position
            "last_cycle_update": datetime.utcnow().isoformat()  # Current time as placeholder
        }
        
        # Add descriptions for economic states
        state_descriptions = {
            "recession": "Economic downturn. Property values decrease, interest rates increase.",
            "normal": "Stable economy. Standard property values and interest rates.",
            "growth": "Growing economy. Property values increase slightly, interest rates decrease slightly.",
            "boom": "Economic boom. Property values increase significantly, interest rates decrease significantly."
        }
        
        economic_state["state_description"] = state_descriptions.get(economic_state["current_state"], "Unknown economic state")
        
        # Add cycle timing information
        economic_controller = current_app.config.get('economic_controller')
        if economic_controller:
            economic_state["auto_cycle_enabled"] = getattr(economic_controller, 'auto_cycle_enabled', True)
            economic_state["cycle_interval_minutes"] = current_app.config.get('ECONOMIC_CYCLE_INTERVAL', 5)
            
        return jsonify({
            "success": True,
            "economic_state": economic_state
        })
    
    except Exception as e:
        logger.error(f"Error getting economic state: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@economic_admin_bp.route('/state', methods=['POST'])
@admin_required
def update_economic_state():
    """Force the economic cycle to a specific state"""
    try:
        data = request.json
        if not data or 'state' not in data:
            return jsonify({"success": False, "error": "Missing required parameter: state"}), 400
            
        state = data['state']
        admin_key = request.headers.get('X-Admin-Key')
        
        economic_manager = get_economic_manager()
        result = economic_manager.force_economic_state(state, admin_key)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating economic state: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@economic_admin_bp.route('/cycle', methods=['POST'])
@admin_required
def cycle_economy():
    """Manually trigger an economic cycle update"""
    try:
        economic_manager = get_economic_manager()
        result = economic_manager.update_economic_cycle()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error cycling economy: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@economic_admin_bp.route('/history', methods=['GET'])
@admin_required
def get_economic_history():
    """Get the economic phase change history"""
    try:
        from src.models.economic_phase_change import EconomicPhaseChange
        
        # Get phase change history
        phase_changes = EconomicPhaseChange.query.order_by(EconomicPhaseChange.timestamp.desc()).limit(20).all()
        
        history = []
        for change in phase_changes:
            history.append({
                "id": change.id,
                "lap_number": change.lap_number,
                "old_state": change.old_state,
                "new_state": change.new_state,
                "inflation_factor": change.inflation_factor,
                "total_cash": change.total_cash,
                "total_property_value": change.total_property_value,
                "timestamp": change.timestamp.isoformat(),
                "description": change.description
            })
        
        return jsonify({
            "success": True,
            "history": history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting economic history: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@economic_admin_bp.route('/toggle', methods=['POST'])
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

@economic_admin_bp.route('/update-now', methods=['POST'])
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

@economic_admin_bp.route('/trigger-event', methods=['POST'])
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