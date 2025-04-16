from flask import Blueprint, request, jsonify
# Remove incorrect SocialController import if present
# from src.controllers.social import SocialController 
# Import AllianceController if needed for type hints
from src.controllers.social.alliance_controller import AllianceController
import logging

logger = logging.getLogger(__name__)

# Modify function to accept alliance_controller
def register_alliance_routes(app, socketio, alliance_controller):
    """Register alliance-related API routes"""
    alliance_bp = Blueprint('alliance', __name__, url_prefix='/api/social/alliance')
    
    # Use the passed-in alliance_controller instance
    # social_controller = SocialController(socketio) # Remove if present
    
    @alliance_bp.route('', methods=['GET'])
    def get_player_alliances():
        """Get all alliances for a player"""
        player_id = request.args.get('player_id')
        if not player_id:
            return jsonify({
                "success": False,
                "error": "Missing player_id parameter"
            }), 400
        
        result = alliance_controller.get_player_alliances(player_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('', methods=['POST'])
    def create_alliance():
        """Create a new alliance"""
        data = request.json
        
        # Validate required parameters
        required_params = ['creator_id', 'name']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        # Optional parameters
        description = data.get('description')
        is_public = data.get('is_public', True)
        
        result = alliance_controller.create_alliance(
            creator_id=data['creator_id'],
            name=data['name'],
            description=description,
            is_public=is_public
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/<alliance_id>', methods=['GET'])
    def get_alliance_details():
        """Get details of an alliance"""
        alliance_id = request.view_args['alliance_id']
        player_id = request.args.get('player_id')
        
        result = alliance_controller.get_alliance_details(
            alliance_id=alliance_id,
            player_id=player_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/<alliance_id>', methods=['PUT'])
    def update_alliance():
        """Update alliance information"""
        alliance_id = request.view_args['alliance_id']
        data = request.json
        
        # Validate required parameters
        if 'updater_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: updater_id"
            }), 400
        
        # Extract updater ID from data
        updater_id = data.pop('updater_id')
        
        result = alliance_controller.update_alliance(
            alliance_id=alliance_id,
            updater_id=updater_id,
            update_data=data
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/<alliance_id>/invite', methods=['POST'])
    def invite_player():
        """Invite a player to join an alliance"""
        alliance_id = request.view_args['alliance_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['inviter_id', 'invitee_id']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        result = alliance_controller.invite_player(
            alliance_id=alliance_id,
            inviter_id=data['inviter_id'],
            invitee_id=data['invitee_id']
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/invites/<invite_id>/respond', methods=['POST'])
    def respond_to_invite():
        """Accept or decline an alliance invitation"""
        invite_id = request.view_args['invite_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['player_id', 'accept']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        result = alliance_controller.respond_to_invite(
            invite_id=invite_id,
            player_id=data['player_id'],
            accept=data['accept']
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/<alliance_id>/leave', methods=['POST'])
    def leave_alliance():
        """Leave an alliance"""
        alliance_id = request.view_args['alliance_id']
        data = request.json
        
        # Validate required parameters
        if 'player_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: player_id"
            }), 400
        
        result = alliance_controller.leave_alliance(
            alliance_id=alliance_id,
            player_id=data['player_id']
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/<alliance_id>/members/<member_id>/role', methods=['PUT'])
    def update_member_role():
        """Update a member's role within an alliance"""
        alliance_id = request.view_args['alliance_id']
        member_id = request.view_args['member_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['updater_id', 'new_role']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        result = alliance_controller.update_member_role(
            alliance_id=alliance_id,
            updater_id=data['updater_id'],
            member_id=member_id,
            new_role=data['new_role']
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @alliance_bp.route('/benefits', methods=['GET'])
    def calculate_alliance_benefits():
        """Calculate alliance benefits between two players"""
        player1_id = request.args.get('player1_id')
        player2_id = request.args.get('player2_id')
        
        if not player1_id or not player2_id:
            return jsonify({
                "success": False,
                "error": "Missing player1_id or player2_id parameter"
            }), 400
        
        result = alliance_controller.calculate_alliance_benefits(
            player1_id=player1_id,
            player2_id=player2_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    # Register the blueprint
    app.register_blueprint(alliance_bp) 