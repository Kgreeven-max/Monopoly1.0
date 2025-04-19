from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
audit_admin_bp = Blueprint('audit_admin', __name__, url_prefix='/audit')

# Initialize the admin controller
admin_controller = AdminController()

@audit_admin_bp.route('/economic', methods=['POST'])
@admin_required
def audit_economic_system():
    """
    Trigger a comprehensive audit of the economic system.
    Returns detailed analysis of economic health, property values, transactions,
    and market trends with actionable recommendations.
    """
    try:
        # Call the implemented admin_controller method
        result = admin_controller.audit_economic_system()
        
        if result.get('success'):
            logger.info("Economic system audit completed successfully")
            return jsonify(result), 200
        else:
            logger.error(f"Economic system audit failed: {result.get('error')}")
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error in audit_economic_system route: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@audit_admin_bp.route('/game-state', methods=['POST'])
@admin_required
def audit_game_state():
    """
    Trigger a comprehensive audit of the entire game state.
    Returns detailed analysis of players, properties, rule compliance,
    game progression, and balance with actionable recommendations.
    """
    try:
        # Call the implemented admin_controller method
        result = admin_controller.audit_game_state()
        
        if result.get('success'):
            logger.info("Game state audit completed successfully")
            return jsonify(result), 200
        else:
            logger.error(f"Game state audit failed: {result.get('error')}")
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error in audit_game_state route: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@audit_admin_bp.route('/player/<int:player_id>', methods=['POST'])
@admin_required
def audit_player(player_id):
    """
    Trigger a comprehensive audit of a specific player.
    This reuses the existing player audit functionality.
    """
    try:
        # Call the implemented admin_controller method
        result = admin_controller.trigger_player_audit(player_id)
        
        if result.get('success'):
            logger.info(f"Player audit for player {player_id} completed successfully")
            return jsonify(result), 200
        else:
            logger.error(f"Player audit failed: {result.get('error')}")
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error in audit_player route for player {player_id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@audit_admin_bp.route('/summary', methods=['GET'])
@admin_required
def get_audit_summary():
    """
    Get a summary of all available audit capabilities and recent audit results.
    """
    try:
        # In a real implementation, this might retrieve information from a database
        # of recent audit results. For now, we'll just return static information.
        summary = {
            "success": True,
            "available_audits": [
                {
                    "id": "economic",
                    "name": "Economic System Audit",
                    "description": "Comprehensive analysis of economic health, property values, and market trends",
                    "endpoint": "/api/admin/audit/economic"
                },
                {
                    "id": "game-state",
                    "name": "Game State Audit",
                    "description": "Complete analysis of game rules, player status, and game progression",
                    "endpoint": "/api/admin/audit/game-state"
                },
                {
                    "id": "player",
                    "name": "Player Audit",
                    "description": "Detailed analysis of player finances, properties, and transaction history",
                    "endpoint": "/api/admin/audit/player/{player_id}"
                }
            ],
            "recent_audits": []  # Would be populated from audit history in a real implementation
        }
        
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error in get_audit_summary route: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 