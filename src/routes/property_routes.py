from flask import jsonify, request, current_app
import logging
from src.routes.decorators import player_auth_required

logger = logging.getLogger(__name__)

def register_property_routes(app):
    """Register property-related routes with the Flask app"""
    
    @app.route('/api/property/develop', methods=['POST'])
    @player_auth_required
    def improve_property():
        """Develop a property by adding an improvement (house/hotel)"""
        data = request.json
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        improvement_type = data.get('improvement_type', 'house')  # 'house' or 'hotel'
        game_id = data.get('game_id', 1)  # Default to 1 for now
        
        if not all([player_id, property_id]):
            logger.warning(f"Missing required parameters for property development")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Get the game controller
        game_controller = current_app.config.get('game_controller')
        if not game_controller:
            logger.error("Game controller not found in app config")
            return jsonify({
                'success': False,
                'error': 'Game controller not available'
            }), 500
        
        # Call the game controller's method
        result = game_controller.handle_improve_property({
            'player_id': player_id,
            'property_id': property_id,
            'improvement_type': improvement_type,
            'game_id': game_id
        })
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/property/sell-improvement', methods=['POST'])
    @player_auth_required
    def sell_improvement():
        """Sell an improvement (house/hotel) from a property"""
        data = request.json
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        improvement_type = data.get('improvement_type', 'house')  # 'house' or 'hotel'
        game_id = data.get('game_id', 1)  # Default to 1 for now
        
        if not all([player_id, property_id]):
            logger.warning(f"Missing required parameters for selling improvement")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Get the game controller
        game_controller = current_app.config.get('game_controller')
        if not game_controller:
            logger.error("Game controller not found in app config")
            return jsonify({
                'success': False,
                'error': 'Game controller not available'
            }), 500
        
        # Call the game controller's method
        result = game_controller.handle_sell_improvement({
            'player_id': player_id,
            'property_id': property_id,
            'improvement_type': improvement_type,
            'game_id': game_id
        })
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/property/<int:property_id>/details', methods=['GET'])
    def get_property_details(property_id):
        """Get detailed information about a specific property"""
        from src.models.property import Property
        
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        # Get property details including development status
        details = property_obj.to_dict()
        
        return jsonify({
            'success': True,
            'property': details
        }), 200
    
    @app.route('/api/property/group/<group_name>', methods=['GET'])
    def get_properties_by_group(group_name):
        """Get all properties in a specific group"""
        from src.models.property import Property
        
        properties = Property.query.filter_by(group=group_name).all()
        
        properties_data = [prop.to_dict() for prop in properties]
        
        return jsonify({
            'success': True,
            'group': group_name,
            'properties': properties_data
        }), 200
    
    @app.route('/api/property/request-approval', methods=['POST'])
    @player_auth_required
    def request_community_approval():
        """Request community approval for property development"""
        data = request.json
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        pin = data.get('pin')
        
        if not all([player_id, property_id, pin]):
            logger.warning(f"Missing required parameters for community approval request")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Get the property controller
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            return jsonify({
                'success': False,
                'error': 'Property controller not available'
            }), 500
        
        # Call the controller method
        result = property_controller.request_community_approval(player_id, pin, property_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    @app.route('/api/property/commission-study', methods=['POST'])
    @player_auth_required
    def commission_environmental_study():
        """Commission an environmental study for property development"""
        data = request.json
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        pin = data.get('pin')
        
        if not all([player_id, property_id, pin]):
            logger.warning(f"Missing required parameters for environmental study")
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # Get the property controller
        property_controller = current_app.config.get('property_controller')
        if not property_controller:
            logger.error("Property controller not found in app config")
            return jsonify({
                'success': False,
                'error': 'Property controller not available'
            }), 500
        
        # Call the controller method
        result = property_controller.commission_environmental_study(player_id, pin, property_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    logger.info("Property routes registered") 