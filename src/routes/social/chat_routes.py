from flask import Blueprint, request, jsonify, current_app
from src.controllers.social.chat_controller import ChatController
import logging

logger = logging.getLogger(__name__)

def register_chat_routes(app, socketio, chat_controller):
    """Register chat-related API routes"""
    chat_bp = Blueprint('chat', __name__)
    
    @chat_bp.route('/channels', methods=['GET'])
    def get_player_channels():
        """Get all chat channels for a player"""
        player_id = request.args.get('player_id')
        if not player_id:
            return jsonify({
                "success": False,
                "error": "Missing player_id parameter"
            }), 400
        
        result = chat_controller.get_player_channels(player_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels', methods=['POST'])
    def create_channel():
        """Create a new chat channel"""
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
        members = data.get('members', [])
        channel_type = data.get('type', 'public')
        
        result = chat_controller.create_channel(
            creator_id=data['creator_id'],
            name=data['name'],
            description=description,
            members=members,
            channel_type=channel_type
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/messages', methods=['GET'])
    def get_channel_messages():
        """Get messages for a chat channel"""
        channel_id = request.view_args['channel_id']
        player_id = request.args.get('player_id')
        limit = int(request.args.get('limit', 50))
        before_message_id = request.args.get('before_message_id')
        
        result = chat_controller.get_channel_history(
            channel_id=channel_id,
            player_id=player_id,
            limit=limit,
            before_message_id=before_message_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/messages', methods=['POST'])
    def send_message():
        """Send a message to a chat channel"""
        channel_id = request.view_args['channel_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['sender_id', 'content']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        # Optional parameters
        message_type = data.get('type', 'text')
        
        result = chat_controller.send_message(
            sender_id=data['sender_id'],
            channel_id=channel_id,
            content=data['content'],
            message_type=message_type
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/messages/<message_id>/reactions', methods=['POST'])
    def add_reaction():
        """Add a reaction to a message"""
        channel_id = request.view_args['channel_id']
        message_id = request.view_args['message_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['player_id', 'emoji']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        result = chat_controller.add_reaction(
            player_id=data['player_id'],
            message_id=message_id,
            emoji=data['emoji']
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/messages/<message_id>/reactions', methods=['DELETE'])
    def remove_reaction():
        """Remove a reaction from a message"""
        channel_id = request.view_args['channel_id']
        message_id = request.view_args['message_id']
        
        player_id = request.args.get('player_id')
        emoji = request.args.get('emoji')
        
        if not player_id or not emoji:
            return jsonify({
                "success": False,
                "error": "Missing player_id or emoji parameter"
            }), 400
        
        result = chat_controller.remove_reaction(
            player_id=player_id,
            message_id=message_id,
            emoji=emoji
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/join', methods=['POST'])
    def join_channel():
        """Join a chat channel"""
        channel_id = request.view_args['channel_id']
        data = request.json
        
        # Validate required parameters
        if 'player_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: player_id"
            }), 400
        
        result = chat_controller.join_channel(
            player_id=data['player_id'],
            channel_id=channel_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @chat_bp.route('/channels/<channel_id>/leave', methods=['POST'])
    def leave_channel():
        """Leave a chat channel"""
        channel_id = request.view_args['channel_id']
        data = request.json
        
        # Validate required parameters
        if 'player_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: player_id"
            }), 400
        
        result = chat_controller.leave_channel(
            player_id=data['player_id'],
            channel_id=channel_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    # Register the blueprint
    app.register_blueprint(chat_bp, url_prefix='/api/social/chat') 