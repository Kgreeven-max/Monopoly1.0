from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
bot_admin_bp = Blueprint('bot_admin', __name__, url_prefix='/bots')

# Assumes AdminController instance is accessible
admin_controller = AdminController()

@bot_admin_bp.route('/add', methods=['POST'])
@admin_required
def add_bot():
    """Add an AI player to the game"""
    data = request.json
    bot_type = data.get('bot_type', 'strategic') # Default type if not provided
    bot_name = data.get('bot_name')
    
    if not bot_name:
        return jsonify({'success': False, 'error': 'Bot name is required'}), 400
    
    # Call the implemented admin_controller method
    result = admin_controller.add_bot_player(bot_name, bot_type)
        
    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@bot_admin_bp.route('/bots/types', methods=['GET'])
@admin_required
def get_bot_types():
    """Get list of available bot types and difficulty levels"""
    try:
        # This logic seems self-contained and doesn't need a controller method
        # TODO: Consider moving descriptions to config or a dedicated model/service
        return jsonify({
            "success": True,
            "bot_types": [
                {
                    "id": "conservative", "name": "Conservative Bot",
                    "description": "Focuses on safe investments and steady growth. Maintains high cash reserves."
                },
                {
                    "id": "aggressive", "name": "Aggressive Bot",
                    "description": "Rapid expansion and high-risk investments. Willing to spend nearly all cash on properties."
                },
                {
                    "id": "strategic", "name": "Strategic Bot",
                    "description": "Balanced approach focusing on completing property monopolies and strategic development."
                },
                {
                    "id": "opportunistic", "name": "Opportunistic Bot",
                    "description": "Uses market timing strategy to buy during recession and sell during boom cycles."
                },
                {
                    "id": "shark", "name": "Shark Bot",
                    "description": "Predatory focus on blocking monopolies and targeting players in financial distress."
                },
                {
                    "id": "investor", "name": "Investor Bot",
                    "description": "Financial instrument focus over properties. Highly selective with strict ROI requirements."
                }
            ],
            "difficulty_levels": [
                {
                    "id": "easy", "name": "Easy",
                    "description": "70% optimal decisions, 20% property valuation error, shorter planning horizon."
                },
                {
                    "id": "medium", "name": "Medium",
                    "description": "85% optimal decisions, 10% property valuation error, moderate planning horizon."
                },
                {
                    "id": "hard", "name": "Hard",
                    "description": "95% optimal decisions, 5% property valuation error, extended planning horizon."
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error getting bot types: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@bot_admin_bp.route('/adaptive-difficulty/assessment', methods=['POST'])
@admin_required
def assess_game_balance():
    """Assess the current game balance between human and bot players"""
    try:
        # This requires AdaptiveDifficultyController, should be instantiated appropriately
        from src.controllers.adaptive_difficulty_controller import AdaptiveDifficultyController
        from flask import current_app
        socketio = current_app.config.get('socketio')
        if not socketio:
             return jsonify({"success": False, "error": "SocketIO not available"}), 500
             
        controller = AdaptiveDifficultyController(socketio)
        assessment = controller.assess_game_balance()
        return jsonify(assessment)
    except Exception as e:
        logger.error(f"Error assessing game balance: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
        
@bot_admin_bp.route('/adaptive-difficulty/adjust', methods=['POST'])
@admin_required
def adjust_bot_difficulty():
    """Manually adjust bot difficulty"""
    try:
        data = request.get_json()
        bot_id = data.get('bot_id')
        difficulty_adjustment = data.get('difficulty_adjustment')
        
        if bot_id is None or difficulty_adjustment is None:
            return jsonify({"success": False, "error": "Missing bot_id or difficulty_adjustment"}), 400
            
        # Requires AdaptiveDifficultyController
        from src.controllers.adaptive_difficulty_controller import AdaptiveDifficultyController
        from flask import current_app
        socketio = current_app.config.get('socketio')
        if not socketio:
             return jsonify({"success": False, "error": "SocketIO not available"}), 500
             
        controller = AdaptiveDifficultyController(socketio)
        result = controller.manually_adjust_difficulty(bot_id, difficulty_adjustment)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error adjusting bot difficulty: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
        
@bot_admin_bp.route('/adaptive-difficulty/auto-adjust', methods=['POST'])
@admin_required
def auto_adjust_bot_difficulty():
    """Automatically assess and adjust bot difficulty"""
    try:
        # Requires AdaptiveDifficultyController
        from src.controllers.adaptive_difficulty_controller import AdaptiveDifficultyController
        from flask import current_app
        socketio = current_app.config.get('socketio')
        if not socketio:
             return jsonify({"success": False, "error": "SocketIO not available"}), 500
             
        controller = AdaptiveDifficultyController(socketio)
        result = controller.auto_adjust_difficulty()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error auto-adjusting bot difficulty: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500 