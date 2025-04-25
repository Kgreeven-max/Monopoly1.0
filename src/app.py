# Register blueprints
from src.routes.game_routes import game_bp
from src.routes.player_routes import player_bp
from src.routes.admin.admin_routes import admin_bp
from src.routes.admin.finance_admin_routes import finance_admin_bp
from src.routes.admin.economic_admin_routes import economic_admin_bp
from src.routes.admin.property_admin_routes import property_admin_bp
from src.routes.admin.bot_admin_routes import bot_admin_bp

app.register_blueprint(game_bp, url_prefix='/api/game')
app.register_blueprint(player_bp, url_prefix='/api/player')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(finance_admin_bp, url_prefix='/api/admin/finance')
app.register_blueprint(economic_admin_bp, url_prefix='/api/admin/economic')
app.register_blueprint(property_admin_bp, url_prefix='/api/admin/property')
app.register_blueprint(bot_admin_bp, url_prefix='/api/admin/bots')

# Initialize economic cycle manager
from src.models.economic_cycle_manager import EconomicCycleManager
if 'economic_manager' not in app.config:
    app.config['economic_manager'] = EconomicCycleManager(
        socketio=socketio,
        banker=app.config.get('banker')
    )
    app.logger.info("Economic cycle manager initialized")

# Initialize economic controller for automated cycles if needed
from src.controllers.economic_cycle_controller import EconomicCycleController
if 'economic_controller' not in app.config:
    app.config['economic_controller'] = EconomicCycleController(socketio=socketio, app=app)
    app.config['economic_controller'].auto_cycle_enabled = True
    app.logger.info("Economic controller initialized")

# Set default economic cycle interval if not already set
if 'ECONOMIC_CYCLE_INTERVAL' not in app.config:
    app.config['ECONOMIC_CYCLE_INTERVAL'] = 5  # 5 minutes between cycle updates

# Set economic cycle enabled flag if not already set
if 'ECONOMIC_CYCLE_ENABLED' not in app.config:
    app.config['ECONOMIC_CYCLE_ENABLED'] = True 