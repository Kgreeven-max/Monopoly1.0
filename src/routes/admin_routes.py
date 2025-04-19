from flask import Blueprint
from src.routes.admin.game_admin_routes import game_admin_bp
from src.routes.admin.player_admin_routes import player_admin_bp
from src.routes.admin.bot_admin_routes import bot_admin_bp
from src.routes.admin.event_admin_routes import event_admin_bp
from src.routes.admin.crime_admin_routes import crime_admin_bp
from src.routes.admin.finance_admin_routes import finance_admin_bp
from src.routes.admin.property_admin_routes import property_admin_bp
from src.routes.admin.auction_admin_routes import auction_admin_bp
from src.routes.admin.audit_admin_routes import audit_admin_bp
import logging

logger = logging.getLogger(__name__)

# Main admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Register all admin blueprints - improved to prevent re-registration issues
def register_admin_routes(app, app_config=None):
    """Register admin routes while preserving the blueprint structure.
    Directly register all sub-blueprints with the main Flask app to avoid nested blueprint issues.
    
    Args:
        app: Flask application instance
        app_config: Optional application config dictionary
    """
    logger.info("Registering admin routes with Flask app while maintaining blueprint structure")
    
    # Register the main admin blueprint for its own routes
    if admin_bp.name not in app.blueprints:
        app.register_blueprint(admin_bp)
        logger.info(f"Main admin blueprint '{admin_bp.name}' registered")
    
    # Register each admin sub-blueprint directly with the Flask app
    # We maintain the correct URL prefixes to preserve the route structure
    blueprint_registrations = [
        (game_admin_bp, '/api/admin'),
        (player_admin_bp, '/api/admin/players'),
        (bot_admin_bp, '/api/admin/bots'),
        (event_admin_bp, '/api/admin/events'),
        (crime_admin_bp, '/api/admin/crime'),
        (finance_admin_bp, '/api/admin/finance'),
        (property_admin_bp, '/api/admin/properties'),
        (auction_admin_bp, '/api/admin/auctions'),
        (audit_admin_bp, '/api/admin/audit')
    ]
    
    # Register each blueprint directly with app if not already registered
    for blueprint, url_prefix in blueprint_registrations:
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            logger.info(f"Admin sub-blueprint '{blueprint.name}' registered with prefix '{url_prefix}'")
        else:
            logger.info(f"Admin sub-blueprint '{blueprint.name}' already registered, skipping")
    
    logger.info("Admin routes registration complete")