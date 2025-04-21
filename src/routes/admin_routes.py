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
from src.routes.admin.economic_admin_routes import economic_admin_bp
import logging

logger = logging.getLogger(__name__)

# Main admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Register all admin blueprints - improved to prevent re-registration issues
def register_admin_routes(app):
    """Register all admin routes with Flask app"""
    
    # Create the main admin blueprint
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
    
    # Register main admin blueprint with app
    app.register_blueprint(admin_bp)
    logger.info("Main admin blueprint 'admin' registered")
    
    # Import and register admin sub-blueprints
    from src.routes.admin.game_admin_routes import game_admin_bp
    from src.routes.admin.player_admin_routes import player_admin_bp
    from src.routes.admin.bot_admin_routes import bot_admin_bp
    from src.routes.admin.event_admin_routes import event_admin_bp
    from src.routes.admin.crime_admin_routes import crime_admin_bp
    from src.routes.admin.finance_admin_routes import finance_admin_bp
    from src.routes.admin.property_admin_routes import property_admin_bp
    from src.routes.admin.auction_admin_routes import auction_admin_bp
    from src.routes.admin.audit_admin_routes import audit_admin_bp
    from src.routes.admin.economic_admin_routes import economic_admin_bp
    
    # Register sub-blueprints with appropriate prefixes
    app.register_blueprint(game_admin_bp, url_prefix='/api/admin')
    logger.info(f"Admin sub-blueprint 'game_admin' registered with prefix '/api/admin'")
    
    app.register_blueprint(player_admin_bp, url_prefix='/api/admin/players')
    logger.info(f"Admin sub-blueprint 'player_admin' registered with prefix '/api/admin/players'")
    
    app.register_blueprint(bot_admin_bp, url_prefix='/api/admin/bots')
    logger.info(f"Admin sub-blueprint 'bot_admin' registered with prefix '/api/admin/bots'")
    
    app.register_blueprint(event_admin_bp, url_prefix='/api/admin/events')
    logger.info(f"Admin sub-blueprint 'event_admin' registered with prefix '/api/admin/events'")
    
    app.register_blueprint(crime_admin_bp, url_prefix='/api/admin/crime')
    logger.info(f"Admin sub-blueprint 'crime_admin' registered with prefix '/api/admin/crime'")
    
    app.register_blueprint(finance_admin_bp, url_prefix='/api/admin/finance')
    logger.info(f"Admin sub-blueprint 'finance_admin' registered with prefix '/api/admin/finance'")
    
    app.register_blueprint(property_admin_bp, url_prefix='/api/admin/properties')
    logger.info(f"Admin sub-blueprint 'property_admin' registered with prefix '/api/admin/properties'")
    
    app.register_blueprint(auction_admin_bp, url_prefix='/api/admin/auctions')
    logger.info(f"Admin sub-blueprint 'auction_admin' registered with prefix '/api/admin/auctions'")
    
    app.register_blueprint(audit_admin_bp, url_prefix='/api/admin/audit')
    logger.info(f"Admin sub-blueprint 'audit_admin' registered with prefix '/api/admin/audit'")
    
    app.register_blueprint(economic_admin_bp, url_prefix='/api/admin/economic')
    logger.info(f"Admin sub-blueprint 'economic_admin' registered with prefix '/api/admin/economic'")
    
    logger.info("Admin routes registration complete")