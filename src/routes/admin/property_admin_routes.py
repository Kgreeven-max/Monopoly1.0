from flask import Blueprint, jsonify, request
import logging
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)
property_admin_bp = Blueprint('property_admin', __name__, url_prefix='/properties')

# Initialize the admin controller
admin_controller = AdminController()

@property_admin_bp.route('/', methods=['GET'])
@admin_required
def get_all_properties():
    """
    Get all properties in the game.
    
    Query parameters:
    - owner_id: Filter by owner
    - type: Filter by property type
    - group: Filter by property group
    - min_value: Minimum property value
    - max_value: Maximum property value
    """
    try:
        # Get optional filter parameters
        filters = {}
        
        if 'owner_id' in request.args:
            filters['owner_id'] = int(request.args.get('owner_id'))
        
        if 'type' in request.args:
            filters['type'] = request.args.get('type')
        
        if 'group' in request.args:
            filters['group'] = request.args.get('group')
        
        if 'min_value' in request.args:
            filters['min_value'] = float(request.args.get('min_value'))
        
        if 'max_value' in request.args:
            filters['max_value'] = float(request.args.get('max_value'))
        
        # Call the controller method
        result = admin_controller.get_all_properties(filters)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting all properties: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/<int:property_id>', methods=['GET'])
@admin_required
def get_property(property_id):
    """
    Get details of a specific property.
    """
    try:
        result = admin_controller.get_property_details(property_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f"Error getting property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/<int:property_id>', methods=['PUT'])
@admin_required
def update_property(property_id):
    """
    Update property details.
    
    Request body may include:
    - name: New property name
    - value: New property value
    - rent: New rent amount
    - mortgage_value: New mortgage value
    - development_cost: New development cost
    - rent_multipliers: Updated rent multipliers
    - special_rules: Updated special rules
    """
    try:
        # Get update data from request
        update_data = request.json
        
        if not update_data:
            return jsonify({"success": False, "error": "Update data is required"}), 400
        
        # Call the controller method
        result = admin_controller.update_property(property_id, update_data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error updating property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/transfer', methods=['POST'])
@admin_required
def transfer_property():
    """
    Transfer property ownership between players.
    
    Request body:
    - property_id: ID of the property to transfer
    - from_player_id: Current owner ID (optional, can be null if unowned)
    - to_player_id: New owner ID (can be null to make property unowned)
    - transfer_amount: Amount of money exchanged (optional)
    - record_transaction: Whether to record this as a financial transaction (default: true)
    """
    try:
        # Get transfer data
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Transfer data is required"}), 400
        
        property_id = data.get('property_id')
        from_player_id = data.get('from_player_id')
        to_player_id = data.get('to_player_id')
        transfer_amount = data.get('transfer_amount')
        record_transaction = data.get('record_transaction', True)
        
        if property_id is None:
            return jsonify({"success": False, "error": "Property ID is required"}), 400
        
        if to_player_id is None:
            return jsonify({"success": False, "error": "Destination player ID is required"}), 400
        
        # Call the controller method
        result = admin_controller.transfer_property(
            property_id,
            from_player_id,
            to_player_id,
            transfer_amount,
            record_transaction
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error transferring property: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/reset-improvements/<int:property_id>', methods=['POST'])
@admin_required
def reset_property_improvements(property_id):
    """
    Reset all improvements on a property (remove houses/hotels).
    
    Request body (optional):
    - refund_amount: Amount to refund to the owner (default: property development cost)
    """
    try:
        data = request.json or {}
        refund_amount = data.get('refund_amount')
        
        # Call the controller method
        result = admin_controller.reset_property_improvements(property_id, refund_amount)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error resetting improvements for property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/mortgage/<int:property_id>', methods=['POST'])
@admin_required
def toggle_mortgage(property_id):
    """
    Mortgage or unmortgage a property.
    
    Request body:
    - action: Either "mortgage" or "unmortgage"
    - bypass_cost: Whether to bypass the cost (default: false)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Action data is required"}), 400
        
        action = data.get('action')
        bypass_cost = data.get('bypass_cost', False)
        
        if action not in ['mortgage', 'unmortgage']:
            return jsonify({"success": False, "error": "Action must be 'mortgage' or 'unmortgage'"}), 400
        
        # Call the controller method
        result = admin_controller.manage_property_mortgage(property_id, action, bypass_cost)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error toggling mortgage for property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/add-house/<int:property_id>', methods=['POST'])
@admin_required
def add_house(property_id):
    """
    Add a house to a property.
    
    Request body (optional):
    - bypass_cost: Whether to bypass the cost (default: false)
    - bypass_rules: Whether to bypass normal house building rules (default: false)
    """
    try:
        data = request.json or {}
        
        bypass_cost = data.get('bypass_cost', False)
        bypass_rules = data.get('bypass_rules', False)
        
        # Call the controller method
        result = admin_controller.add_house_to_property(property_id, bypass_cost, bypass_rules)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error adding house to property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/remove-house/<int:property_id>', methods=['POST'])
@admin_required
def remove_house(property_id):
    """
    Remove a house from a property.
    
    Request body (optional):
    - refund_amount: Amount to refund (default: half the property development cost)
    - bypass_rules: Whether to bypass normal house removing rules (default: false)
    """
    try:
        data = request.json or {}
        
        refund_amount = data.get('refund_amount')
        bypass_rules = data.get('bypass_rules', False)
        
        # Call the controller method
        result = admin_controller.remove_house_from_property(property_id, refund_amount, bypass_rules)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error removing house from property {property_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/values/adjust', methods=['POST'])
@admin_required
def adjust_property_values():
    """
    Adjust property values across the board.
    
    Request body:
    - adjustment_type: "percentage" or "fixed"
    - value: Percentage (e.g., 10 for 10% increase) or fixed amount to adjust by
    - property_type: Optional filter for property type
    - property_group: Optional filter for property group
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Adjustment data is required"}), 400
        
        adjustment_type = data.get('adjustment_type')
        value = data.get('value')
        property_type = data.get('property_type')
        property_group = data.get('property_group')
        
        if adjustment_type not in ['percentage', 'fixed']:
            return jsonify({"success": False, "error": "Adjustment type must be 'percentage' or 'fixed'"}), 400
        
        if value is None:
            return jsonify({"success": False, "error": "Adjustment value is required"}), 400
        
        # Call the controller method
        result = admin_controller.adjust_property_values(
            adjustment_type,
            value,
            property_type,
            property_group
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error adjusting property values: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@property_admin_bp.route('/market-analysis', methods=['GET'])
@admin_required
def get_property_market_analysis():
    """
    Get analysis of the property market.
    """
    try:
        result = admin_controller.get_property_market_analysis()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting property market analysis: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

# Add routes for admin actions like mortgage/unmortgage, develop properties later 

# Removed the registration function
# def register_property_admin_routes(app):
#     # Register the blueprint under /api/admin
#     app.register_blueprint(property_admin_bp, url_prefix='/api/admin') 