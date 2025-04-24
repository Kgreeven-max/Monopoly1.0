from flask import jsonify, request, current_app
from src.controllers.board_controller import BoardController
from functools import wraps
import logging
# Import shared decorator
from src.routes.decorators import display_required

logger = logging.getLogger(__name__)

# --- Display Authentication Decorator ---
# def display_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         display_key = request.args.get('display_key')
#         if not display_key or display_key != current_app.config.get('DISPLAY_KEY'): 
#             logger.warning(f"Unauthorized display access attempt to {request.path}")
#             return jsonify({"success": False, "error": "Unauthorized: Missing or invalid display key"}), 401
#         return f(*args, **kwargs)
#     return decorated_function
# --- End Decorator ---

def register_board_routes(app):
    """Register board-related routes with the Flask app"""
    board_controller = BoardController()
    app.config['board_controller'] = board_controller
    
    @app.route('/api/board/state', methods=['GET'])
    @display_required
    def get_board_state():
        """Get the current board state for display"""
        result = board_controller.get_board_state()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/players', methods=['GET'])
    @display_required
    def get_player_positions():
        """Get player positions for the board display"""
        result = board_controller.get_player_positions()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/properties', methods=['GET'])
    @display_required
    def get_property_owners():
        """Get property ownership information for the board display"""
        result = board_controller.get_property_owners()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/events', methods=['GET'])
    @display_required
    def get_recent_events():
        """Get recent game events for the board display"""
        limit = request.args.get('limit', 10, type=int)
        result = board_controller.get_recent_events(limit)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/register', methods=['POST'])
    @display_required
    def register_display():
        """Register a display device for the board view"""
        data = request.json
        device_info = data.get('device_info')
        
        result = board_controller.register_display(device_info)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/economy', methods=['GET'])
    @display_required
    def get_economy_state():
        """Get the current economic state for the board display"""
        result = board_controller.get_economy_state()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/board/auctions', methods=['GET'])
    @display_required
    def get_active_auctions():
        """Get active auctions for the board display"""
        result = board_controller.get_active_auctions()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to retrieve auctions')}), 400
    
    @app.route('/api/board/auctions/<auction_id>', methods=['GET'])
    @display_required
    def get_auction_details(auction_id):
        """Get details for a specific auction"""
        result = board_controller.get_auction_details(auction_id)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Auction not found':
             return jsonify({"success": False, "error": "Auction not found"}), 404
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to retrieve auction details')}), 400
    
    @app.route('/api/board/property-development/requirements', methods=['GET'])
    @display_required
    def check_property_development_requirements():
        """Check development requirements for a specific property"""
        property_id = request.args.get('property_id', type=int)
        target_level = request.args.get('target_level', type=int)
        
        if not property_id:
            return jsonify({'success': False, 'error': 'Property ID is required'}), 400
            
        if target_level is None:
            return jsonify({'success': False, 'error': 'Target development level is required'}), 400
        
        result = board_controller.check_property_development_requirements(property_id, target_level)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Property not found':
             return jsonify({"success": False, "error": "Property not found"}), 404
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to check requirements')}), 400
    
    @app.route('/api/board/property-development', methods=['GET'])
    @display_required
    def get_property_development_info():
        """Get property development information for a specific group"""
        group_name = request.args.get('group_name')
        if not group_name:
            return jsonify({'success': False, 'error': 'Group name is required'}), 400
        
        result = board_controller.get_property_development_info(group_name)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Property group not found':
             return jsonify({"success": False, "error": "Property group not found"}), 404
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to get info')}), 400
    
    @app.route('/api/board/property-development/status', methods=['GET'])
    @display_required
    def get_property_development_status():
        """Get current status and development capabilities of a property"""
        property_id = request.args.get('property_id', type=int)
        
        if not property_id:
            return jsonify({'success': False, 'error': 'Property ID is required'}), 400
        
        result = board_controller.get_property_development_status(property_id)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Property not found':
            return jsonify({"success": False, "error": "Property not found"}), 404
        else:
            return jsonify({"success": False, "error": result.get('error', 'Failed to get status')}), 400 