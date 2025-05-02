from flask import Flask, jsonify, request
import sys
import os

# Add the parent directory to sys.path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.routes.game_routes import game_bp, init_game_controller
from src.routes.player_routes import player_bp
from src.routes.admin_routes import admin_bp
from src.routes.admin.finance_admin_routes import finance_admin_bp
from src.routes.admin.economic_admin_routes import economic_admin_bp
from src.routes.admin.property_admin_routes import property_admin_bp
from src.routes.admin.bot_admin_routes import bot_admin_bp
from src.routes.view_routes import view_routes
from src.routes.auth_routes import register_auth_routes
from src.routes.admin.game_admin_routes import game_admin_bp
from src.controllers.game_controller import GameController
from src.controllers.auth_controller import AuthController
from flask_socketio import SocketIO
from src.game_logic.game_logic import GameLogic
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monopoly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", path="/ws/socket.io")

# Initialize GameLogic
game_logic = GameLogic(app)

# Create app_config dictionary to hold shared components
app_config = {
    'socketio': socketio,
    'game_logic': game_logic,
    # Other configurations can be added here
}

# Initialize controllers
game_controller = GameController(app_config)
auth_controller = AuthController()
init_game_controller(game_controller)

# Register blueprints
app.register_blueprint(game_bp, url_prefix='/api/game')
app.register_blueprint(player_bp, url_prefix='/api/player')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(finance_admin_bp, url_prefix='/api/admin/finance')
app.register_blueprint(economic_admin_bp, url_prefix='/api/admin/economic')
app.register_blueprint(property_admin_bp, url_prefix='/api/admin/property')
app.register_blueprint(bot_admin_bp, url_prefix='/api/admin/bots')
app.register_blueprint(view_routes)
# Register auth routes using the registration function
register_auth_routes(app, auth_controller)
app.register_blueprint(game_admin_bp, url_prefix='/api/admin')

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

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080) 