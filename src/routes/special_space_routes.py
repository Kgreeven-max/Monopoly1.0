from flask import Blueprint, jsonify, request, current_app
from flask_socketio import emit
import json
from functools import wraps
import logging

from src.models import db
from src.models.special_space import Card, SpecialSpace
from src.models.player import Player
from src.controllers.special_space_controller import SpecialSpaceController
# Import shared decorator
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)

def register_special_space_routes(app):
    """Register special space routes with Flask application
    
    Args:
        app: Flask application instance
    """
    # Create controllers
    banker = app.config.get('banker')
    community_fund = app.config.get('community_fund')
    socketio = app.config.get('socketio')
    economic_controller = app.config.get('economic_controller')
    
    # Create special space controller
    special_space_controller = SpecialSpaceController(socketio=socketio, game_controller=None, economic_controller=economic_controller)
    app.config['special_space_controller'] = special_space_controller
    
    # Get routes
    @app.route('/api/board/special-spaces', methods=['GET'])
    def get_special_spaces():
        """Get all special spaces on the board"""
        spaces = SpecialSpace.query.all()
        return jsonify({
            "success": True,
            "spaces": [space.to_dict() for space in spaces]
        })
    
    @app.route('/api/board/special-spaces/<int:space_id>', methods=['GET'])
    def get_special_space(space_id):
        """Get a specific special space by ID"""
        space = SpecialSpace.query.get(space_id)
        
        if not space:
            return jsonify({
                "success": False,
                "error": "Special space not found"
            }), 404
        
        return jsonify({
            "success": True,
            "space": space.to_dict()
        })
    
    @app.route('/api/board/special-spaces/position/<int:position>', methods=['GET'])
    def get_special_space_by_position(position):
        """Get a specific special space by board position"""
        space = SpecialSpace.query.filter_by(position=position).first()
        
        if not space:
            return jsonify({
                "success": False,
                "error": "No special space at position"
            }), 404
        
        return jsonify({
            "success": True,
            "space": space.to_dict()
        })
    
    @app.route('/api/board/special-spaces/action', methods=['POST'])
    def handle_special_space_action():
        """Handle action when player lands on a special space"""
        data = request.json
        player_id = data.get('player_id')
        position = data.get('position')
        pin = data.get('pin')
        
        # Validate parameters
        if not player_id or position is None:
            return jsonify({
                "success": False,
                "error": "Missing required parameters"
            }), 400
        
        # Verify player PIN
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return jsonify({
                "success": False,
                "error": "Invalid player or PIN"
            }), 403
        
        # Handle the space action
        result = special_space_controller.handle_special_space(player_id, position)
        
        return jsonify(result)
    
    @app.route('/api/cards', methods=['GET'])
    def get_cards():
        """Get all cards"""
        card_type = request.args.get('type')
        
        if card_type:
            cards = Card.query.filter_by(card_type=card_type, is_active=True).all()
        else:
            cards = Card.query.filter_by(is_active=True).all()
        
        return jsonify({
            "success": True,
            "cards": [card.to_dict() for card in cards]
        })
    
    @app.route('/api/cards/<int:card_id>', methods=['GET'])
    def get_card(card_id):
        """Get a specific card by ID"""
        card = Card.query.get(card_id)
        
        if not card:
            return jsonify({
                "success": False,
                "error": "Card not found"
            }), 404
        
        return jsonify({
            "success": True,
            "card": card.to_dict()
        })
    
    @app.route('/api/admin/special-spaces/initialize', methods=['POST'])
    @admin_required
    def initialize_special_spaces():
        """Initialize special spaces (admin only)"""
        # data = request.json # Removed
        # admin_key = data.get('admin_key') # Removed
        
        # Verify admin key # Removed
        # if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'): # Removed
        #     return jsonify({ # Removed
        #         "success": False, # Removed
        #         "error": "Unauthorized" # Removed
        #     }), 403 # Removed
        
        # Initialize special spaces
        result = special_space_controller.initialize_special_spaces()
        
        return jsonify(result)
    
    @app.route('/api/admin/cards/initialize', methods=['POST'])
    @admin_required
    def initialize_cards():
        """Initialize cards (admin only)"""
        # data = request.json # Removed
        # admin_key = data.get('admin_key') # Removed
        
        # Verify admin key # Removed
        # if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'): # Removed
        #     return jsonify({ # Removed
        #         "success": False, # Removed
        #         "error": "Unauthorized" # Removed
        #     }), 403 # Removed
        
        # Initialize cards
        result = special_space_controller.initialize_cards()
        
        return jsonify(result)
    
    @app.route('/api/admin/cards', methods=['POST'])
    @admin_required
    def create_card():
        """Create a new card (admin only)"""
        data = request.json
        
        # Validate required keys (controller will perform deeper validation)
        required_keys = ['card_type', 'title', 'description', 'action_type', 'action_data']
        if not all(key in data for key in required_keys):
            return jsonify({
                "success": False,
                "error": f"Missing one or more required fields: {required_keys}"
            }), 400
            
        # Delegate to controller
        result = special_space_controller.create_card(data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            # Controller should provide appropriate error message
            return jsonify(result), 400
    
    @app.route('/api/admin/cards/<int:card_id>', methods=['PUT'])
    @admin_required
    def update_card(card_id):
        """Update an existing card (admin only)"""
        data = request.json
        # Remove admin key if present, not needed for controller
        update_data = {k: v for k, v in data.items() if k != 'admin_key'}

        if not update_data:
            return jsonify({"success": False, "error": "No update data provided"}), 400
            
        # Delegate to controller
        result = special_space_controller.update_card(card_id, update_data)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Card not found':
            return jsonify(result), 404
        else:
            # Controller should provide appropriate error message
            return jsonify(result), 400
    
    @app.route('/api/admin/cards/<int:card_id>', methods=['DELETE'])
    @admin_required
    def delete_card(card_id):
        """Delete a card (admin only)"""
        # Delegate to controller
        result = special_space_controller.delete_card(card_id)
        
        if result.get('success'):
            return jsonify(result), 200
        elif result.get('error') == 'Card not found':
            return jsonify(result), 404
        else:
            return jsonify(result), 400
    
    @app.route('/api/admin/special-spaces', methods=['POST'])
    @admin_required
    def create_special_space():
        """Create a new special space (admin only)"""
        data = request.json

        # Basic validation in route
        required_keys = ['position', 'space_type', 'name']
        if not all(key in data for key in required_keys):
            return jsonify({
                "success": False,
                "error": f"Missing one or more required fields: {required_keys}"
            }), 400
        
        # Delegate to controller (currently placeholder)
        result = special_space_controller.create_special_space(data)

        if result.get('success'):
            return jsonify(result), 201
        else:
            # Controller should provide appropriate error message
            return jsonify(result), 400
    
    return app 