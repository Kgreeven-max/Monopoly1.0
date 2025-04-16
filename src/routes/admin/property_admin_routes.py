from flask import Blueprint, jsonify
import logging
from src.models import db
from src.models.property import Property
from src.models.player import Player
from src.routes.decorators import admin_required
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)
property_admin_bp = Blueprint('property_admin', __name__, url_prefix='/properties')

@property_admin_bp.route('/', methods=['GET'], strict_slashes=False)
@admin_required
def get_all_properties():
    """Get a list of all properties with details for the admin panel."""
    try:
        # Eager load the owner relationship to avoid N+1 queries
        properties = Property.query.options(joinedload(Property.owner)).order_by(Property.id).all()
        
        properties_data = []
        for prop in properties:
            owner_name = prop.owner.username if prop.owner else "Bank"
            
            # --- Debugging Log --- 
            logger.debug(f"Inspecting property ID {prop.id} ({prop.name}) before calculate_rent. Attributes: {vars(prop)}")
            # --- End Debugging Log ---
            
            current_rent = prop.calculate_rent() # Assuming calculate_rent exists on Property model
            
            properties_data.append({
                'id': prop.id,
                'name': prop.name,
                'type': prop.property_type.value, # Assumes PropertyType is an Enum
                'price': prop.price,
                'rent': prop.rent,
                'rent_with_monopoly': prop.rent_with_monopoly,
                'rent_with_1_house': prop.rent_with_1_house,
                'rent_with_2_houses': prop.rent_with_2_houses,
                'rent_with_3_houses': prop.rent_with_3_houses,
                'rent_with_4_houses': prop.rent_with_4_houses,
                'rent_with_hotel': prop.rent_with_hotel,
                'mortgage_value': prop.mortgage_value,
                'house_cost': prop.house_cost,
                'hotel_cost': prop.hotel_cost,
                'is_mortgaged': prop.is_mortgaged,
                'houses': prop.houses,
                'hotel': prop.hotel,
                'color': prop.color,
                'owner_id': prop.owner_id,
                'owner_name': owner_name,
                'current_rent': current_rent 
            })
            
        return jsonify({"success": True, "properties": properties_data})
        
    except Exception as e:
        logger.error(f"Error fetching all properties for admin: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to retrieve property list."}), 500

# Add routes for admin actions like mortgage/unmortgage, develop properties later 

# Removed the registration function
# def register_property_admin_routes(app):
#     # Register the blueprint under /api/admin
#     app.register_blueprint(property_admin_bp, url_prefix='/api/admin') 