from flask import Blueprint, request, jsonify
# Remove incorrect SocialController import if present
# from src.controllers.social import SocialController 
# Import ReputationController if needed for type hints
from src.controllers.social.reputation_controller import ReputationController
import logging

logger = logging.getLogger(__name__)

# Modify function to accept reputation_controller
def register_reputation_routes(app, socketio, reputation_controller):
    """Register reputation-related API routes"""
    reputation_bp = Blueprint('reputation', __name__, url_prefix='/api/social/reputation')
    
    # Use the passed-in reputation_controller instance
    # social_controller = SocialController(socketio) # Remove if present
    
    @reputation_bp.route('/<int:player_id>', methods=['GET'])
    def get_reputation(player_id):
        """Get a player's reputation score"""
        result = reputation_controller.get_player_reputation(player_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @reputation_bp.route('/<player_id>/events', methods=['GET'])
    def get_reputation_events():
        """Get reputation events for a player"""
        player_id = request.view_args['player_id']
        
        # Optional parameters
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        
        result = reputation_controller.get_player_reputation_events(
            player_id=player_id,
            limit=limit,
            offset=offset,
            category=category
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @reputation_bp.route('/<player_id>/events', methods=['POST'])
    def record_reputation_event():
        """Record a reputation-affecting event"""
        player_id = request.view_args['player_id']
        data = request.json
        
        # Validate required parameters
        required_params = ['event_type', 'description', 'impact']
        for param in required_params:
            if param not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }), 400
        
        # Optional parameters
        category = data.get('category')
        game_id = data.get('game_id')
        
        result = reputation_controller.record_reputation_event(
            player_id=player_id,
            event_type=data['event_type'],
            description=data['description'],
            impact=data['impact'],
            category=category,
            game_id=game_id
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @reputation_bp.route('/<player_id>/credit', methods=['GET'])
    def get_credit_score():
        """Get a player's credit score (financial reputation)"""
        player_id = request.view_args['player_id']
        
        result = reputation_controller.get_credit_score(player_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    # Admin routes
    @reputation_bp.route('/admin/<player_id>/adjust', methods=['POST'])
    def adjust_reputation():
        """Admin function to manually adjust a player's reputation"""
        player_id = request.view_args['player_id']
        data = request.json
        
        # Validate required parameters
        if 'adjustment' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required parameter: adjustment"
            }), 400
        
        # Optional parameters
        reason = data.get('reason')
        admin_id = data.get('admin_id')
        
        # Check admin authorization
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key or admin_key != app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Unauthorized: Admin key required"
            }), 401
        
        result = reputation_controller.adjust_reputation(
            player_id=player_id,
            adjustment=data['adjustment'],
            reason=reason,
            admin_id=admin_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @reputation_bp.route('/admin/<player_id>/reset', methods=['POST'])
    def reset_reputation():
        """Admin function to reset a player's reputation to default values"""
        player_id = request.view_args['player_id']
        data = request.json
        
        # Optional parameters
        reason = data.get('reason')
        admin_id = data.get('admin_id')
        
        # Check admin authorization
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key or admin_key != app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Unauthorized: Admin key required"
            }), 401
        
        result = reputation_controller.reset_reputation(
            player_id=player_id,
            reason=reason,
            admin_id=admin_id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    # Register the blueprint
    app.register_blueprint(reputation_bp) 