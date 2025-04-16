from flask import jsonify, request, current_app
from src.controllers.crime_controller import CrimeController
from src.models.player import Player
import logging
from functools import wraps
# Import shared decorator
from src.routes.decorators import admin_required

# Set up logger
logger = logging.getLogger(__name__)

# Initialize the controller
crime_controller = None

# --- Admin Authentication Decorator --- (REMOVED)
# def admin_required(f): ...
# --- End Decorator ---

def register_crime_routes(app, socketio=None):
    """Register crime-related routes with the Flask app
    
    Args:
        app: Flask app
        socketio: Flask-SocketIO instance for real-time notifications
    """
    global crime_controller
    crime_controller = CrimeController(socketio)
    
    @app.route('/api/crime/commit', methods=['POST'])
    def commit_crime():
        """Commit a crime"""
        try:
            data = request.get_json()
            
            # Validate required parameters
            player_id = data.get('player_id')
            player_pin = data.get('player_pin')
            crime_type = data.get('crime_type')
            
            if not player_id or not player_pin or not crime_type:
                return jsonify({
                    "success": False,
                    "message": "Missing required parameters (player_id, player_pin, crime_type)"
                }), 400
                
            # Validate player credentials
            player = Player.query.get(player_id)
            if not player or player.pin != player_pin:
                return jsonify({
                    "success": False,
                    "message": "Invalid player credentials"
                }), 401
                
            # Check valid crime types
            valid_crime_types = ['theft', 'property_vandalism', 'rent_evasion', 'forgery', 'tax_evasion']
            if crime_type not in valid_crime_types:
                return jsonify({
                    "success": False,
                    "message": f"Invalid crime type. Valid types: {', '.join(valid_crime_types)}"
                }), 400
                
            # Extract additional parameters
            params = {}
            if crime_type == 'theft':
                params['target_player_id'] = data.get('target_player_id')
                params['amount'] = data.get('amount')
            elif crime_type == 'property_vandalism':
                params['target_property_id'] = data.get('target_property_id')
                params['amount'] = data.get('amount')
            elif crime_type == 'rent_evasion':
                params['target_property_id'] = data.get('target_property_id')
                params['amount'] = data.get('amount')
            elif crime_type == 'forgery':
                params['amount'] = data.get('amount')
            elif crime_type == 'tax_evasion':
                params['amount'] = data.get('amount')
                
            # Commit the crime
            result = crime_controller.commit_crime(player_id, crime_type, **params)
            
            # Log the attempt
            if result.get('success'):
                logger.info(f"Crime attempt: {crime_type} by Player {player.username} (ID: {player_id}) - {'Detected' if result.get('detected') else 'Undetected'}")
            else:
                logger.warning(f"Failed crime attempt: {crime_type} by Player {player.username} (ID: {player_id}) - {result.get('message')}")
                
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in commit_crime route: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            }), 500
    
    @app.route('/api/crime/history/<int:player_id>', methods=['GET'])
    def get_player_crime_history(player_id):
        """Get a player's crime history"""
        try:
            # Verify player PIN
            player_pin = request.args.get('player_pin')
            
            if not player_pin:
                return jsonify({
                    "success": False,
                    "message": "Player PIN is required"
                }), 400
                
            # Validate player credentials
            player = Player.query.get(player_id)
            if not player or player.pin != player_pin:
                return jsonify({
                    "success": False,
                    "message": "Invalid player credentials"
                }), 401
                
            # Get crime history
            result = crime_controller.get_player_crimes(player_id)
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in get_player_crime_history route: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            }), 500
    
    @app.route('/api/crime/police-patrol', methods=['POST'])
    @admin_required
    def trigger_police_patrol():
        """Trigger a police patrol (admin only)"""
        try:
            # data = request.get_json() # No longer needed for admin key
            
            # Validate admin key # Removed - Handled by decorator
            # admin_key = data.get('admin_key') # Removed
            # if admin_key != app.config.get('ADMIN_KEY', 'pinopoly-admin'): # Removed
            #     return jsonify({ # Removed
            #         "success": False, # Removed
            #         "message": "Unauthorized" # Removed
            #     }), 403 # Removed
                
            # Trigger patrol
            result = crime_controller.check_for_police_patrol()
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in trigger_police_patrol route: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            }), 500
    
    @app.route('/api/crime/statistics', methods=['GET'])
    @admin_required
    def get_crime_statistics():
        """Get crime statistics (admin only)"""
        try:
            # Validate admin key # Removed - Handled by decorator
            # admin_key = request.args.get('admin_key') # Removed
            # if admin_key != app.config.get('ADMIN_KEY', 'pinopoly-admin'): # Removed
            #     return jsonify({ # Removed
            #         "success": False, # Removed
            #         "message": "Unauthorized" # Removed
            #     }), 403 # Removed
                
            # Get statistics
            # Validate admin key
            admin_key = request.args.get('admin_key')
            if admin_key != app.config.get('ADMIN_KEY', 'pinopoly-admin'):
                return jsonify({
                    "success": False,
                    "message": "Unauthorized"
                }), 403
                
            # Get statistics
            result = crime_controller.get_crime_statistics()
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in get_crime_statistics route: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            }), 500
    
    @app.route('/api/crime/types', methods=['GET'])
    def get_crime_types():
        """Get available crime types and their descriptions"""
        try:
            return jsonify({
                "success": True,
                "crime_types": [
                    {
                        "id": "theft",
                        "name": "Theft",
                        "description": "Steal money from another player",
                        "risk": "Medium",
                        "params": ["target_player_id", "amount (optional)"],
                        "consequences": "Go to jail if caught"
                    },
                    {
                        "id": "property_vandalism",
                        "name": "Property Vandalism",
                        "description": "Damage a property to reduce its value and rent",
                        "risk": "Medium",
                        "params": ["target_property_id", "amount (optional)"],
                        "consequences": "Go to jail if caught"
                    },
                    {
                        "id": "rent_evasion",
                        "name": "Rent Evasion",
                        "description": "Avoid paying rent when landing on a property",
                        "risk": "Low",
                        "params": ["target_property_id", "amount"],
                        "consequences": "Pay rent plus 50% penalty if caught"
                    },
                    {
                        "id": "forgery",
                        "name": "Forgery",
                        "description": "Forge bank notes for immediate cash",
                        "risk": "High",
                        "params": ["amount (optional)"],
                        "consequences": "Pay double the amount as fine and go to jail if caught"
                    },
                    {
                        "id": "tax_evasion",
                        "name": "Tax Evasion",
                        "description": "Avoid paying taxes",
                        "risk": "Medium-High",
                        "params": ["amount (optional)"],
                        "consequences": "Pay double tax amount if caught"
                    }
                ]
            })
                
        except Exception as e:
            logger.error(f"Error in get_crime_types route: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            }), 500 