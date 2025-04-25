from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import logging
from datetime import datetime
import eventlet
from src.models import init_db
# Import models from their specific files
from src.models.property import Property 
from src.models.player import Player
from src.routes.player_routes import register_player_routes
from src.routes.game_routes import register_game_routes
from sqlalchemy.orm import joinedload
from src.routes.decorators import admin_required
from src.routes.property_routes import register_property_routes
# from src.routes.auction_routes import register_auction_routes # File not found
from src.routes.admin.game_admin_routes import game_admin_bp
from src.routes.admin.player_admin_routes import player_admin_bp
from src.routes.admin.bot_admin_routes import bot_admin_bp
from src.routes.admin.event_admin_routes import event_admin_bp
from src.routes.admin.crime_admin_routes import crime_admin_bp
from src.routes.admin.finance_admin_routes import finance_admin_bp
# Import the blueprint variable directly
from src.routes.admin.property_admin_routes import property_admin_bp
from src.routes.admin.economic_admin_routes import economic_admin_bp
from src.routes.admin.auction_admin_routes import auction_admin_bp
from src.routes.admin_routes import register_admin_routes
# from src.routes.bot_event_routes import register_bot_event_routes # File not found
from src.routes.special_space_routes import register_special_space_routes
from src.routes.finance_routes import register_finance_routes
from src.routes.player.finance_player_routes import finance_player_bp, init_finance_player_routes  # Import finance player blueprint and initialization function
from src.routes.community_fund_routes import register_community_fund_routes
from src.routes.crime_routes import register_crime_routes
# Import remote_routes with error handling
try:
    from src.routes.remote_routes import register_remote_routes
except ImportError as e:
    logging.warning(f"Could not import remote_routes: {str(e)}. Remote play will be disabled.")
    register_remote_routes = None
from src.routes.game_mode_routes import register_game_mode_routes
from src.routes.social import register_social_routes
from src.controllers.socket_controller import register_socket_events
from src.controllers.adaptive_difficulty_controller import AdaptiveDifficultyController
from src.controllers.crime_controller import CrimeController
from src.controllers.remote_controller import RemoteController
from src.controllers.game_mode_controller import GameModeController
from src.controllers.social.chat_controller import ChatController
from src.controllers.social.alliance_controller import AllianceController
from src.controllers.social.reputation_controller import ReputationController
# Import core services/models needed for initialization
from src.models.banker import Banker
from src.models.community_fund import CommunityFund
from src.models.event_system import EventSystem
from src.controllers.special_space_controller import SpecialSpaceController
from src.models.game_state import GameState # Needed for CommunityFund init
# Import missing controllers/systems
from src.controllers.game_controller import GameController
# Import PlayerController
from src.controllers.player_controller import PlayerController
# Import AuthController
from src.controllers.auth_controller import AuthController
# Removed: from src.controllers.property_controller import PropertyController
# Removed: from src.controllers.auction_controller import AuctionController
# Removed: from src.controllers.bot_controller import BotController
from src.models.auction_system import AuctionSystem # Assuming this exists
import uuid # Needed for game_id generation
# Import route registration functions
# from src.routes.auth_routes import register_auth_routes # Moved down
from src.controllers.social import SocialController # Corrected import path
from src.controllers.property_controller import PropertyController # Import PropertyController
from src.controllers.auction_controller import AuctionController # Import AuctionController
from src.controllers.bot_controller import BotController # Import BotController
from src.game_logic.game_logic import GameLogic # Import GameLogic
from src.controllers.economic_cycle_controller import EconomicCycleController, register_economic_events # Import EconomicCycleController
# Import database migration
from src.migrations.add_free_parking_fund import run_migration
from src.migrations.add_credit_score import run_migration as run_credit_score_migration
from src.migrations.add_updated_at_column import run_migration as run_updated_at_migration
from src.migrations.add_inflation_rate import run_migration as run_inflation_rate_migration
from src.migrations.add_started_at_column import run_migration as run_started_at_migration
from src.migrations.fix_cash_to_money import run_migration as run_fix_cash_to_money_migration
from src.migrations.add_community_chest_cards import run_migration as run_community_chest_cards_migration
from src.migrations.add_game_id_to_auction import run_migration as run_add_game_id_to_auction_migration
from src.migrations.add_game_id_to_loan import run_migration as run_add_game_id_to_loan_migration
from src.migrations.add_fields_to_cd import run_migration as run_add_fields_to_cd_migration
from src.migrations.add_history_to_loan import run_migration as run_add_history_to_loan_migration
from src.migrations.add_times_passed_go import run_migration as run_add_times_passed_go_migration
from src.migrations.add_economic_cycle_columns import run_migration as run_add_economic_cycle_columns_migration
from src.controllers.trade_controller import TradeController # Import TradeController
from src.routes.trade_routes import trade_routes # Import trade routes

# Import our new configuration system
from src.utils.flask_config import (
    configure_flask_app, 
    get_environment, 
    get_secret_key,
    is_debug_mode,
    get_port
)

# Initialize Flask app
app = Flask(__name__)

# Use our configuration system to configure the Flask app
environment = get_environment()
configure_flask_app(app, environment)

# Set up logging
logging.basicConfig(
    level=logging.INFO if is_debug_mode() else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinopoly.log"),
        logging.StreamHandler()
    ]
)

# Initialize SocketIO with eventlet
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    path="/ws"
)

# Initialize database
db = init_db(app)

# Initialize core services and controllers
with app.app_context(): # Use app context to access db/config safely
    # Create database tables if they don't exist
    db.create_all()
    logging.info('Ensured database tables exist.')
    
    # Run migration to add free_parking_fund and other missing columns
    try:
        migration_result = run_migration()
        if migration_result:
            logging.info('Successfully ran free_parking_fund migration.')
        else:
            logging.warning('Failed to run free_parking_fund migration.')
    except Exception as e:
        logging.error(f'Error running free_parking_fund migration: {str(e)}', exc_info=True)
    
    # Run migration to add credit_score
    try:
        credit_score_migration_result = run_credit_score_migration()
        if credit_score_migration_result:
            logging.info('Successfully ran credit_score migration.')
        else:
            logging.warning('Failed to run credit_score migration.')
    except Exception as e:
        logging.error(f'Error running credit_score migration: {str(e)}', exc_info=True)
    
    # Run migration to add updated_at column to players table
    try:
        updated_at_migration_result = run_updated_at_migration()
        if updated_at_migration_result:
            logging.info('Successfully ran updated_at column migration.')
        else:
            logging.warning('Failed to run updated_at column migration.')
    except Exception as e:
        logging.error(f'Error running updated_at column migration: {str(e)}', exc_info=True)
    
    # Run migration to add inflation_rate and base_interest_rate columns to game_state table
    try:
        inflation_rate_migration_result = run_inflation_rate_migration()
        if inflation_rate_migration_result:
            logging.info('Successfully ran inflation_rate and base_interest_rate migration.')
        else:
            logging.warning('Failed to run inflation_rate and base_interest_rate migration.')
    except Exception as e:
        logging.error(f'Error running inflation_rate and base_interest_rate migration: {str(e)}', exc_info=True)
    
    # Run migration to add started_at and ended_at columns to game_state table
    try:
        started_at_migration_result = run_started_at_migration()
        if started_at_migration_result:
            logging.info('Successfully ran started_at and ended_at migration.')
        else:
            logging.warning('Failed to run started_at and ended_at migration.')
    except Exception as e:
        logging.error(f'Error running started_at and ended_at migration: {str(e)}', exc_info=True)
        
    # Run migration to fix cash to money references and add current_price/current_rent columns
    try:
        fix_cash_migration_result = run_fix_cash_to_money_migration()
        if fix_cash_migration_result:
            logging.info('Successfully ran cash to money fix migration.')
        else:
            logging.warning('Failed to run cash to money fix migration.')
    except Exception as e:
        logging.error(f'Error running cash to money fix migration: {str(e)}', exc_info=True)
    
    # Run migration to add _community_chest_cards_json and game_log columns
    try:
        community_chest_cards_migration_result = run_community_chest_cards_migration()
        if community_chest_cards_migration_result:
            logging.info('Successfully ran community chest cards migration.')
        else:
            logging.warning('Failed to run community chest cards migration.')
    except Exception as e:
        logging.error(f'Error running community chest cards migration: {str(e)}', exc_info=True)
    
    # Run migration to add game_id column to auctions table
    try:
        auction_game_id_migration_result = run_add_game_id_to_auction_migration()
        if auction_game_id_migration_result:
            logging.info('Successfully ran add_game_id_to_auction migration.')
        else:
            logging.warning('Failed to run add_game_id_to_auction migration.')
    except Exception as e:
        logging.error(f'Error running add_game_id_to_auction migration: {str(e)}', exc_info=True)
    
    # Run migration to add game_id column to loans table
    try:
        loan_game_id_migration_result = run_add_game_id_to_loan_migration()
        if loan_game_id_migration_result:
            logging.info('Successfully ran add_game_id_to_loan migration.')
        else:
            logging.warning('Failed to run add_game_id_to_loan migration.')
    except Exception as e:
        logging.error(f'Error running add_game_id_to_loan migration: {str(e)}', exc_info=True)
    
    # Run migration to add required fields to CD model
    try:
        cd_fields_migration_result = run_add_fields_to_cd_migration()
        if cd_fields_migration_result:
            logging.info('Successfully ran add_fields_to_cd migration.')
        else:
            logging.warning('Failed to run add_fields_to_cd migration.')
    except Exception as e:
        logging.error(f'Error running add_fields_to_cd migration: {str(e)}', exc_info=True)
    
    # Run migration to add history column to loan table
    try:
        loan_history_migration_result = run_add_history_to_loan_migration()
        if loan_history_migration_result:
            logging.info('Successfully ran add_history_to_loan migration.')
        else:
            logging.warning('Failed to run add_history_to_loan migration.')
    except Exception as e:
        logging.error(f'Error running add_history_to_loan migration: {str(e)}', exc_info=True)
    
    # Run migration to add times_passed_go column to players table
    try:
        times_passed_go_migration_result = run_add_times_passed_go_migration()
        if times_passed_go_migration_result:
            logging.info('Successfully ran add_times_passed_go migration.')
        else:
            logging.warning('Failed to run add_times_passed_go migration.')
    except Exception as e:
        logging.error(f'Error running add_times_passed_go migration: {str(e)}', exc_info=True)
        # Add a direct SQL migration as fallback for times_passed_go
        try:
            logging.info('Attempting direct SQL migration for times_passed_go column')
            from sqlalchemy import text
            # Check if column exists
            result = db.session.execute(text("SELECT 1 FROM pragma_table_info('players') WHERE name='times_passed_go'")).fetchone()
            if not result:
                # Add the column if it doesn't exist
                db.session.execute(text("ALTER TABLE players ADD COLUMN times_passed_go INTEGER DEFAULT 0"))
                db.session.commit()
                logging.info('Successfully added times_passed_go column using direct SQL')
            else:
                logging.info('times_passed_go column already exists')
        except Exception as fallback_error:
            logging.error(f'Fallback migration for times_passed_go also failed: {str(fallback_error)}', exc_info=True)
    
    # Ensure GameState instance exists and has a game_id
    # Use a direct SQL query instead of ORM to avoid issues with missing columns
    try:
        logging.info('Checking for existing GameState using direct SQL')
        from sqlalchemy import text
        result = db.session.execute(text("SELECT id, game_id FROM game_state LIMIT 1")).fetchone()
        
        if result:
            game_state_id, game_state_game_id = result
            logging.info(f'Found existing GameState with ID: {game_state_id} and game_id: {game_state_game_id}')
            
            # If game_id is missing, update it
            if not game_state_game_id:
                new_game_id = str(uuid.uuid4())
                db.session.execute(text(f"UPDATE game_state SET game_id = '{new_game_id}' WHERE id = {game_state_id}"))
                db.session.commit()
                logging.info(f'Updated game_id to: {new_game_id}')
                game_state_game_id = new_game_id
                
            # Create a GameState instance from the database row
            game_state = GameState()
            game_state.id = game_state_id
            game_state.game_id = game_state_game_id
        else:
            # Create a new GameState if one doesn't exist
            logging.info('No existing GameState found, creating a new one')
            new_game_id = str(uuid.uuid4())
            db.session.execute(text(f"INSERT INTO game_state (game_id) VALUES ('{new_game_id}')"))
            db.session.commit()
            
            # Get the newly created GameState
            result = db.session.execute(text("SELECT id, game_id FROM game_state LIMIT 1")).fetchone()
            game_state_id, game_state_game_id = result
            
            # Create a GameState instance from the database row
            game_state = GameState()
            game_state.id = game_state_id
            game_state.game_id = game_state_game_id
            
        logging.info(f'Using GameState with ID: {game_state.id} and game_id: {game_state.game_id}')
    except Exception as e:
        logging.error(f'Error checking for existing GameState: {str(e)}', exc_info=True)
        # Fallback to ORM method
        game_state = GameState.query.first()
        if not game_state:
            game_state = GameState(game_id=str(uuid.uuid4()))
            db.session.add(game_state)
            db.session.commit()
        elif not game_state.game_id:
            game_state.game_id = str(uuid.uuid4())
            db.session.add(game_state)
            db.session.commit()
        
    # Add economic_state to GameState if it's missing
    try:
        logging.info('Checking for economic_state column in game_state table')
        from sqlalchemy import text
        
        # Check if economic_state column exists
        result = db.session.execute(text("SELECT 1 FROM pragma_table_info('game_state') WHERE name='economic_state'")).fetchone()
        if not result:
            # Add the column if it doesn't exist
            db.session.execute(text("ALTER TABLE game_state ADD COLUMN economic_state VARCHAR(20) DEFAULT 'stable'"))
            db.session.commit()
            logging.info('Successfully added economic_state column to game_state table')
        else:
            logging.info('economic_state column already exists in game_state table')
            
        # Update the game_state instance if it exists
        if 'game_state' in locals():
            # Get the current economic_state value
            result = db.session.execute(text("SELECT economic_state FROM game_state WHERE id = :id"), 
                                       {"id": game_state.id}).fetchone()
            if result and hasattr(result, '_mapping'):
                economic_state_value = result._mapping.get('economic_state', 'stable')
            else:
                economic_state_value = 'stable'
                
            # Set the value on the instance for use in this session
            setattr(game_state, 'economic_state', economic_state_value)
            logging.info(f'Set economic_state={economic_state_value} on GameState instance')
    except Exception as e:
        logging.error(f'Error checking or adding economic_state column: {str(e)}', exc_info=True)
        
    # Run economic cycle columns migration
    try:
        economic_cycle_columns_result = run_add_economic_cycle_columns_migration()
        if economic_cycle_columns_result:
            logging.info('Successfully ran economic cycle columns migration.')
        else:
            logging.warning('Failed to run economic cycle columns migration.')
    except Exception as e:
        logging.error(f'Error running economic cycle columns migration: {str(e)}', exc_info=True)
        
    # ---- Stage 1: Initialize basic services and controllers ----
    banker = Banker(socketio)
    community_fund = CommunityFund(socketio, game_state)
    event_system = EventSystem(socketio, banker, community_fund)
    auction_system = AuctionSystem(socketio, banker)
    economic_controller = EconomicCycleController(socketio=socketio, app=app)
    special_space_controller = SpecialSpaceController(socketio=socketio, game_controller=None, economic_controller=economic_controller, app_config=app.config)
    social_controller = SocialController(socketio, app.config) 
    remote_controller = RemoteController(app) # Needs app instance
    player_controller = PlayerController(db) # Pass the db instance
    auth_controller = AuthController() # Initialize AuthController
    game_logic = GameLogic(app) # Initialize GameLogic
    property_controller = PropertyController(db, banker, event_system, socketio) # Assuming these dependencies
    auction_controller = AuctionController(db, banker, event_system, socketio) # Assuming these dependencies
    
    # Initialize finance controller
    from src.controllers.finance_controller import FinanceController
    finance_controller = FinanceController(socketio=socketio, banker=banker, game_state=game_state)
    
    # Store all dependencies in app.config before initializing other controllers
    app.config['banker'] = banker
    app.config['community_fund'] = community_fund
    app.config['event_system'] = event_system
    app.config['auction_system'] = auction_system  
    app.config['special_space_controller'] = special_space_controller
    app.config['social_controller'] = social_controller
    app.config['remote_controller'] = remote_controller
    app.config['player_controller'] = player_controller
    app.config['auth_controller'] = auth_controller
    app.config['game_state_instance'] = game_state
    app.config['game_logic'] = game_logic 
    app.config['property_controller'] = property_controller
    app.config['auction_controller'] = auction_controller
    app.config['socketio'] = socketio
    app.config['economic_manager'] = None  # Will be set to economic_manager later
    app.config['economic_controller'] = economic_controller
    app.config['finance_controller'] = finance_controller
    app.config['app'] = app

    # Initialize game controller and store it before socket controller
    game_controller = GameController(app.config)
    app.config['game_controller'] = game_controller
    
    # Initialize bot controller
    bot_controller = BotController(app.config)
    app.config['bot_controller'] = bot_controller
    
    # NOTE: Socket controller initialization is now handled by register_socket_events()
    # This prevents duplication/conflicts with controllers initialized there

    # Initialize social controllers
    chat_controller = ChatController(socketio, app.config)
    alliance_controller = AllianceController(socketio, app.config)
    reputation_controller = ReputationController(socketio, app.config)
    app.config['chat_controller'] = chat_controller
    app.config['alliance_controller'] = alliance_controller
    app.config['reputation_controller'] = reputation_controller

    # Initialize trade controller with app config
    trade_controller = TradeController(app.config)
    app.config['trade_controller'] = trade_controller

    # Register the trade routes
    app.register_blueprint(trade_routes, url_prefix='/api/trade')
    # Set the trade controller in the trade routes
    trade_routes_controller = trade_controller
    
    # Initialize economic cycle manager
    from src.models.economic_cycle_manager import EconomicCycleManager
    economic_manager = EconomicCycleManager(socketio, banker)
    
    # ---- Stage 2: Store ALL initial instances in app config ----
    app.config['banker'] = banker
    app.config['community_fund'] = community_fund
    app.config['event_system'] = event_system
    app.config['auction_system'] = auction_system
    app.config['special_space_controller'] = special_space_controller
    app.config['social_controller'] = social_controller
    app.config['remote_controller'] = remote_controller
    app.config['player_controller'] = player_controller
    app.config['auth_controller'] = auth_controller
    app.config['game_state_instance'] = game_state
    app.config['game_logic'] = game_logic # Store GameLogic instance
    app.config['property_controller'] = property_controller # Store property controller
    app.config['auction_controller'] = auction_controller # Store auction controller
    app.config['socketio'] = socketio # Store socketio instance
    # socket_controller is now initialized by register_socket_events() function
    app.config['economic_manager'] = economic_manager # Store economic cycle manager
    app.config['economic_controller'] = economic_controller # Store economic cycle controller
    app.config['finance_controller'] = finance_controller # Store finance controller
    # Add economic system configuration
    app.config['property_values_follow_economy'] = True  # Properties values fluctuate with the economy
    # Add app instance itself to the app_config for bot controller
    app.config['app'] = app

    # ---- Stage 3: Initialize controllers dependent on stored config ----
    game_controller = GameController(app.config) # Needs game_logic etc. in app_config
    app.config['game_controller'] = game_controller # Store game controller

    bot_controller = BotController(app.config) # Needs game_logic, game_controller etc. in app_config
    app.config['bot_controller'] = bot_controller # Store bot controller

    logging.info('Core services and controllers initialized and stored in app config')

# Security headers
@app.after_request
def add_security_headers(response):
    # Enforce HTTPS with Cloudflare
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content security policy - updated to allow SVG images and data URIs
    response.headers['Content-Security-Policy'] = "default-src 'self' https: wss:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:;"
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# ---- Static file route FIRST ----
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ---- Default route for SPA client AFTER specific routes ----
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # This check might not even be necessary now if serve_static handles it
    # But we leave it for now in case other files are expected here
    if path != "" and os.path.exists('static' + '/' + path):
        # Check if it's trying to access static files directly - should be handled by serve_static
        # This part might need refinement depending on what 'serve' is truly meant for
        # For a typical SPA, we usually only serve index.html here.
        # Let's simplify to just serve index.html for non-API/non-static routes
        return send_from_directory('static', 'index.html') 
    else:
        return send_from_directory('static', 'index.html')

# Basic health check endpoint
@app.route('/api/health')
def health_check():
    # Check if running via Cloudflare Tunnel
    tunnel_status = remote_controller.get_tunnel_status() if app.config['REMOTE_PLAY_ENABLED'] else None
    tunnel_running = tunnel_status and tunnel_status.get('running', False) if tunnel_status else False
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "remote_play": {
            "enabled": app.config['REMOTE_PLAY_ENABLED'],
            "active": tunnel_running,
            "url": tunnel_status.get('url') if tunnel_running else None
        }
    })

# Register socket events
register_socket_events(socketio, app.config)
register_economic_events(socketio, app.config)  # Register economic events
# Register trade socket events
from src.controllers.trade_controller import register_trade_socket_events
register_trade_socket_events(socketio, app.config)  # Register trade events

# Register API routes
# Pass the controller instances directly
register_player_routes(app, player_controller)
register_game_routes(app, game_controller)
register_property_routes(app)
# register_auction_routes(app)   # Auction routes - not found, commented out
# Use centralized admin routes registration instead of individual blueprints
register_admin_routes(app)
# register_bot_event_routes(app) # File not found
register_special_space_routes(app)
register_finance_routes(app)
app.register_blueprint(init_finance_player_routes(app), url_prefix='/api/finance')  # Initialize and register the blueprint
register_community_fund_routes(app)
register_crime_routes(app, socketio)
# Register remote routes only if available
if register_remote_routes:
    try:
        register_remote_routes(app)
        logging.info("Remote routes registered successfully")
    except Exception as e:
        logging.error(f"Failed to register remote routes: {str(e)}", exc_info=True)
else:
    logging.warning("Remote routes not available. Remote play is disabled.")

register_game_mode_routes(app)
try:
    register_social_routes(
        app, 
        socketio, 
        app.config.get('chat_controller'),
        app.config.get('alliance_controller'),
        app.config.get('reputation_controller')
    )
except Exception as e:
    logging.error(f"Error registering social routes: {str(e)}", exc_info=True)

# Register auth routes - Import just before use
from src.routes.auth_routes import register_auth_routes
register_auth_routes(app, auth_controller)

# --- PERMANENT PROPERTY ADMIN ROUTE --- 
@app.route('/api/admin/properties', methods=['GET'], strict_slashes=False)
@admin_required
def admin_get_properties():
    """Get a list of all properties with details for the admin panel."""
    try:
        # Eager load the owner relationship to avoid N+1 queries
        properties = Property.query.options(joinedload(Property.owner)).order_by(Property.id).all()
        
        properties_data = []
        for prop in properties:
            owner_name = prop.owner.username if prop.owner else "Bank"
            
            # --- Debugging Log --- 
            # Use app.logger since we are in app.py context
            app.logger.debug(f"Inspecting property ID {prop.id} ({prop.name}) before calculate_rent. Attributes: {vars(prop)}")
            # --- End Debugging Log ---
            
            current_rent = prop.calculate_rent() # Assuming calculate_rent exists on Property model
            
            # Simplified the returned data to match frontend expectations
            properties_data.append({
                'id': prop.id,
                'name': prop.name,
                'owner_name': owner_name,
                'houses': prop.houses,
                'hotel': prop.hotel,
                'is_mortgaged': prop.is_mortgaged,
                'price': prop.price,
                'current_rent': current_rent
            })
            
        return jsonify({"success": True, "properties": properties_data})
        
    except Exception as e:
        app.logger.error(f"Error fetching all properties for admin: {str(e)}", exc_info=True) # Use app.logger
        return jsonify({"success": False, "error": "Failed to retrieve property list."}), 500
# --- END PROPERTY ADMIN ROUTE ---

# --- TEMPORARY TEST ROUTE ---
@app.route('/api/admin/bots/test')
def bots_test_route():
    return jsonify({"message": "Bots test route working!"})
# --- END TEST ROUTE ---

# Add the following test route after this one:

@app.route('/api/admin/bots/types/test', methods=['GET'])
def bot_types_test():
    """Test route for bot types that doesn't require admin auth."""
    return jsonify({
        "success": True,
        "bot_types": [
            {
                "id": "conservative", "name": "Conservative Bot",
                "description": "Focuses on safe investments and steady growth. Maintains high cash reserves."
            },
            {
                "id": "aggressive", "name": "Aggressive Bot",
                "description": "Rapid expansion and high-risk investments. Willing to spend nearly all cash on properties."
            },
            {
                "id": "strategic", "name": "Strategic Bot",
                "description": "Balanced approach focusing on completing property monopolies and strategic development."
            }
        ],
        "difficulty_levels": [
            {
                "id": "easy", "name": "Easy",
                "description": "70% optimal decisions, 20% property valuation error, shorter planning horizon."
            },
            {
                "id": "medium", "name": "Medium",
                "description": "85% optimal decisions, 10% property valuation error, moderate planning horizon."
            },
            {
                "id": "hard", "name": "Hard",
                "description": "95% optimal decisions, 5% property valuation error, extended planning horizon."
            }
        ]
    })

# Add a direct bot types API with no authentication required
@app.route('/api/bot-types', methods=['GET'])
def direct_bot_types():
    """Direct API for bot types that works independently of authentication."""
    return jsonify({
        "success": True,
        "bot_types": [
            {
                "id": "conservative", "name": "Conservative Bot",
                "description": "Focuses on safe investments and steady growth. Maintains high cash reserves."
            },
            {
                "id": "aggressive", "name": "Aggressive Bot",
                "description": "Rapid expansion and high-risk investments. Willing to spend nearly all cash on properties."
            },
            {
                "id": "strategic", "name": "Strategic Bot",
                "description": "Balanced approach focusing on completing property monopolies and strategic development."
            },
            {
                "id": "opportunistic", "name": "Opportunistic Bot",
                "description": "Uses market timing strategy to buy during recession and sell during boom cycles."
            }
        ],
        "difficulty_levels": [
            {
                "id": "easy", "name": "Easy",
                "description": "70% optimal decisions, 20% property valuation error, shorter planning horizon."
            },
            {
                "id": "medium", "name": "Medium",
                "description": "85% optimal decisions, 10% property valuation error, moderate planning horizon."
            },
            {
                "id": "hard", "name": "Hard",
                "description": "95% optimal decisions, 5% property valuation error, extended planning horizon."
            }
        ]
    })

# Add direct API endpoint for bot creation:
@app.route('/api/create-bot', methods=['POST'])
def direct_create_bot():
    """Direct API for creating a bot without requiring the blueprint."""
    try:
        data = request.json
        admin_pin = data.get('admin_pin')
        
        # Validate admin PIN
        if admin_pin != app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Invalid admin PIN"
            }), 401
        
        # Extract bot data
        bot_name = data.get('name')
        bot_type = data.get('type', 'conservative')
        difficulty = data.get('difficulty', 'medium')
        
        # Get bot controller
        bot_controller = app.config.get('bot_controller')
        if not bot_controller:
            return jsonify({
                "success": False,
                "error": "Bot controller not initialized"
            }), 500
        
        # Create the bot using the controller's create_bot method
        new_bot = bot_controller.create_bot(bot_name, bot_type, difficulty)
        
        if new_bot:
            return jsonify({
                "success": True,
                "bot_id": new_bot.id,
                "name": new_bot.username,
                "type": bot_type,
                "difficulty": difficulty
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create bot"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error creating bot via direct API: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Static file routes
@app.route('/admin')
def admin():
    return render_template('admin.html', admin_key=app.config.get('ADMIN_KEY', ''))

@app.route('/board')
def board():
    return render_template('board.html')

@app.route('/connect')
def connect():
    """Display connection information for remote play"""
    # Check if remote play is enabled and tunnel is running
    tunnel_status = remote_controller.get_tunnel_status() if app.config['REMOTE_PLAY_ENABLED'] else None
    tunnel_running = tunnel_status and tunnel_status.get('running', False) if tunnel_status else False
    
    return render_template(
        'connect.html', 
        remote_enabled=app.config['REMOTE_PLAY_ENABLED'],
        tunnel_running=tunnel_running,
        tunnel_url=tunnel_status.get('url') if tunnel_running else None
    )

@app.route('/admin_crime')
def admin_crime():
    return render_template('admin_crime.html')

@app.route('/admin_player')
def admin_player():
    return render_template('admin_player.html')

@app.route('/admin_bot')
def admin_bot():
    return render_template('admin_bot.html')

@app.route('/admin_game_modes')
def admin_game_modes():
    # Implementation of this route is not provided in the original file or the code block
    # This route should be implemented based on the requirements of the application
    return jsonify({"error": "This route is not implemented"}), 501

def run_delayed_task(task_func, delay_seconds):
    """Run a task after the specified delay and repeat it if the task schedules itself."""
    # Sleep for the initial delay
    eventlet.sleep(delay_seconds)
    
    # Execute the task
    task_func()

# Scheduled tasks
def setup_scheduled_tasks():
    """Set up background tasks to run on a schedule."""
    if app.config['ADAPTIVE_DIFFICULTY_ENABLED']:
        # Start adaptive difficulty assessment
        difficulty_controller = AdaptiveDifficultyController(socketio)
        
        def run_difficulty_assessment():
            while True:
                # Sleep first to avoid immediate assessment on startup
                eventlet.sleep(app.config['ADAPTIVE_DIFFICULTY_INTERVAL'] * 60)
                
                try:
                    # Create an application context
                    with app.app_context():
                        # Assess game balance
                        assessment = difficulty_controller.assess_game_balance()
                        
                        # If adjustment needed, apply it
                        if assessment.get('needs_adjustment'):
                            adjustment_direction = assessment.get('adjustment_direction')
                            difficulty_controller.adjust_difficulty(adjustment_direction)
                            
                            # Log the auto-adjustment
                            logging.info(f"Auto-adjusted bot difficulty: {adjustment_direction}")
                except Exception as e:
                    logging.error(f"Error in scheduled difficulty assessment: {str(e)}")
        
        # Start the assessment thread
        eventlet.spawn(run_difficulty_assessment)
        logging.info(f"Adaptive difficulty scheduler started with interval of {app.config['ADAPTIVE_DIFFICULTY_INTERVAL']} minutes")
    
    if app.config['POLICE_PATROL_ENABLED']:
        # Start police patrol
        crime_controller = CrimeController(socketio)
        # Register in app config so it's available to other components
        app.config['crime_controller'] = crime_controller
        
        def run_police_patrol():
            while True:
                # Sleep first to avoid immediate patrol on startup
                eventlet.sleep(app.config['POLICE_PATROL_INTERVAL'] * 60)
                
                try:
                    # Create an application context
                    with app.app_context():
                        # Run police patrol
                        patrol_result = crime_controller.check_for_police_patrol()
                        
                        # Log the patrol results
                        if patrol_result.get('success'):
                            logging.info(f"Police patrol completed: {patrol_result.get('message')}")
                except Exception as e:
                    logging.error(f"Error in scheduled police patrol: {str(e)}")
        
        # Start the patrol thread
        eventlet.spawn(run_police_patrol)
        logging.info(f"Police patrol scheduler started with interval of {app.config['POLICE_PATROL_INTERVAL']} minutes")
    
    # Setup auto-start of Cloudflare Tunnel if enabled
    if app.config['REMOTE_PLAY_ENABLED']:
        def setup_remote_tunnel():
            # Wait a bit for app to start
            eventlet.sleep(5)
            
            try:
                # Check if tunnel is configured
                if remote_controller.check_tunnel_config():
                    # Try to start tunnel
                    result = remote_controller.start_tunnel()
                    if result.get('success'):
                        app.config['TUNNEL_URL'] = result.get('tunnel_url')
                        logging.info(f"Remote play tunnel started: {result.get('tunnel_url')}")
                    else:
                        logging.warning(f"Failed to start remote play tunnel: {result.get('message')}")
                else:
                    logging.info("Remote play is enabled but no tunnel is configured. Use admin interface to create one.")
            except Exception as e:
                logging.error(f"Error setting up remote tunnel: {str(e)}")
        
        # Start the setup thread
        eventlet.spawn(setup_remote_tunnel)
        logging.info("Remote play auto-start scheduler initiated")
    
    # Setup economic cycle updates
    # Get the economic cycle manager from app config
    economic_controller = app.config.get('economic_controller')
    if economic_controller and app.config['ECONOMIC_CYCLE_ENABLED']:
        def run_economic_cycle():
            """Update economic state, interest rates, and property values."""
            if app.config['ECONOMIC_CYCLE_ENABLED']:
                logging.info("Running scheduled economic cycle update")
                try:
                    # Create an application context
                    with app.app_context():
                        # Find active games instead of using the one from app.config
                        active_games = GameState.query.filter_by(status='active').all()
                        
                        if not active_games:
                            logging.info("No active games found for economic cycle update")
                            return
                        
                        # Update each active game's economic cycle
                        for game in active_games:
                            try:
                                # Make sure the game has a valid game_id
                                if not game.game_id:
                                    logging.warning(f"Game with ID {game.id} has no game_id, skipping economic cycle update")
                                    continue
                                    
                                logging.info(f"Processing economic cycle for game {game.game_id} (ID: {game.id})")
                                result = economic_controller.process_economic_cycle(game.game_id)
                                if result.get('success'):
                                    logging.info(f"Economic cycle updated for game {game.game_id}: {result.get('previous_state')} -> {result.get('new_state')}")
                                else:
                                    logging.warning(f"Economic cycle update failed for game {game.game_id}: {result.get('error')}")
                                    
                                    # If the game state wasn't found, try updating using the numeric ID instead
                                    if result.get('error') == 'Game state not found':
                                        logging.info(f"Trying to update economic cycle using numeric ID {game.id} instead of UUID")
                                        result = economic_controller.process_economic_cycle(str(game.id))
                                        if result.get('success'):
                                            logging.info(f"Economic cycle updated for game ID {game.id}: {result.get('previous_state')} -> {result.get('new_state')}")
                                        else:
                                            logging.warning(f"Economic cycle update still failed for game ID {game.id}: {result.get('error')}")
                                            
                            except Exception as game_error:
                                logging.error(f"Error updating economic cycle for game {game.game_id}: {str(game_error)}", exc_info=True)
                
                except Exception as e:
                    logging.error(f"Error in economic cycle update: {str(e)}", exc_info=True)
                    
                # Schedule the next run
                if not app.testing:  # Don't reschedule in testing mode
                    interval = app.config.get('ECONOMIC_CYCLE_INTERVAL', 5) * 60  # Convert minutes to seconds
                    socketio.start_background_task(
                        run_delayed_task, 
                        run_economic_cycle, 
                        interval
                    )
            else:
                logging.info("Economic cycle updates are disabled")
        
        # Setup random economic events
        if app.config.get('RANDOM_ECONOMIC_EVENTS_ENABLED', True):
            def trigger_random_economic_event():
                """Trigger random economic events in active games."""
                logging.info("Running scheduled random economic event")
                try:
                    # Create an application context
                    with app.app_context():
                        # Get all active games
                        active_games = GameState.query.filter_by(status='active').all()
                        
                        if not active_games:
                            logging.info("No active games found for random economic event")
                            return
                        
                        # Select a random game to affect
                        game = random.choice(active_games)
                        
                        # Trigger a random economic event for this game
                        admin_key = app.config.get('ADMIN_KEY')
                        result = economic_controller.trigger_economic_event(game.game_id, admin_key)
                        
                        if result.get('success'):
                            logging.info(f"Random economic event triggered for game {game.game_id}: {result.get('event_type')}")
                        else:
                            logging.warning(f"Failed to trigger random economic event: {result.get('error')}")
                except Exception as e:
                    logging.error(f"Error triggering random economic event: {str(e)}", exc_info=True)
                
                # Schedule the next event
                if not app.testing:  # Don't reschedule in testing mode
                    # Use a different interval for random events (30-60 minutes)
                    min_interval = app.config.get('MIN_ECONOMIC_EVENT_INTERVAL', 30) * 60  # Convert minutes to seconds
                    max_interval = app.config.get('MAX_ECONOMIC_EVENT_INTERVAL', 60) * 60  # Convert minutes to seconds
                    random_interval = random.randint(min_interval, max_interval)
                    
                    socketio.start_background_task(
                        run_delayed_task, 
                        trigger_random_economic_event, 
                        random_interval
                    )
                
        # Initial scheduling of tasks
        if app.config['ADAPTIVE_DIFFICULTY_ENABLED']:
            socketio.start_background_task(
                run_delayed_task, 
                run_difficulty_assessment, 
                app.config.get('ADAPTIVE_DIFFICULTY_INTERVAL', 15) * 60  # Convert minutes to seconds
            )
            
        if app.config['POLICE_PATROL_ENABLED']:
            socketio.start_background_task(
                run_delayed_task, 
                run_police_patrol, 
                app.config.get('POLICE_PATROL_INTERVAL', 45) * 60  # Convert minutes to seconds
            )
            
        if app.config['REMOTE_PLAY_ENABLED']:
            socketio.start_background_task(setup_remote_tunnel)
            
        if app.config['ECONOMIC_CYCLE_ENABLED']:
            socketio.start_background_task(
                run_delayed_task, 
                run_economic_cycle, 
                app.config.get('ECONOMIC_CYCLE_INTERVAL', 5) * 60  # Convert minutes to seconds
            )
            
        # Schedule random economic events if enabled
        if app.config.get('RANDOM_ECONOMIC_EVENTS_ENABLED', True):
            socketio.start_background_task(
                run_delayed_task, 
                trigger_random_economic_event, 
                app.config.get('INITIAL_ECONOMIC_EVENT_DELAY', 15) * 60  # Convert minutes to seconds
            )
    else:
        if not economic_controller:
            logging.warning("Economic cycle controller not found in app config. Economic updates will not run automatically.")
        else:
            logging.info("Economic cycle updates are disabled by configuration.")

# --- SocketIO Event Handlers ---

@socketio.on('get_all_players')
def handle_get_all_players(data):
    """Handles request from admin panel to get all players."""
    sid = request.sid
    admin_pin = data.get('admin_pin') # Get pin from data
    
    # Create a local reference to the app logger
    logger = app.logger
    
    # Primary authorization check for socket events
    if not admin_pin or admin_pin != app.config.get('ADMIN_KEY'):
        logger.warning(f"Unauthorized attempt to get_all_players from SID {sid}")
        emit('auth_error', {'error': 'Invalid admin credentials for player list'}, room=sid)
        return
        
    logger.info(f"Admin request for all players from SID {sid}")
    try:
        players = Player.query.order_by(Player.id).all()
        logger.info(f"Found {len(players)} players in total for admin list")
        
        players_data = []
        for p in players:
            # Get property count for this player
            property_count = Property.query.filter_by(owner_id=p.id).count()
            
            logger.info(f"Adding player to list: ID {p.id}, Name: {p.username}, Is Bot: {p.is_bot}, In Game: {p.in_game}")
            
            players_data.append({
                'id': p.id,
                'name': p.username,
                'money': p.money,
                'is_bot': p.is_bot,
                'in_game': p.in_game,
                'position': p.position,
                'in_jail': p.in_jail,
                'properties': property_count
                # Add other relevant fields as needed
            })
        
        logger.info(f"Emitting all_players_list with {len(players_data)} players to client {sid}")
        # Emit to the specific client that requested it
        emit('all_players_list', {'success': True, 'players': players_data}, room=sid)
        logger.info(f"Successfully emitted all_players_list to {sid}")
        
    except Exception as e:
        logger.error(f"Error fetching all players for admin: {str(e)}", exc_info=True)
        emit('event_error', {'error': 'Failed to retrieve player list.'}, room=sid)

@socketio.on('remove_bot')
def handle_remove_bot(data):
    """Handle bot removal request"""
    sid = request.sid
    admin_pin = data.get('admin_pin')
    logger = app.logger
    
    # Validate admin access
    if not admin_pin or admin_pin != app.config.get('ADMIN_KEY'):
        logger.warning(f"Unauthorized attempt to remove bot from SID {sid}")
        emit('auth_error', {'error': 'Invalid admin credentials'}, room=sid)
        return
    
    bot_id = data.get('bot_id')
    if not bot_id:
        logger.warning(f"Missing bot_id in remove_bot request from SID {sid}")
        emit('event_error', {'error': 'Missing bot_id parameter'}, room=sid)
        return
    
    # Verify bot exists
    bot_player = Player.query.get(bot_id)
    if not bot_player:
        logger.warning(f"Bot not found with ID {bot_id} in remove_bot request from SID {sid}")
        emit('event_error', {'error': 'Bot not found'}, room=sid)
        return
        
    if not bot_player.is_bot:
        logger.warning(f"Player with ID {bot_id} is not a bot in remove_bot request from SID {sid}")
        emit('event_error', {'error': 'Player is not a bot'}, room=sid)
        return
    
    try:
        # Update database to mark bot as not in game
        bot_player.in_game = False
        db.session.commit()
        
        # Broadcast bot removed event
        socketio.emit('bot_removed', {
            'bot_id': bot_id,
            'name': bot_player.username
        })
        
        logger.info(f"Bot {bot_player.username} (ID: {bot_id}) removed successfully by admin")
        
        # Confirm success to the admin who requested it
        emit('bot_removal_result', {
            'success': True,
            'message': f"Bot {bot_player.username} removed from the game"
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error removing bot with ID {bot_id}: {str(e)}", exc_info=True)
        emit('event_error', {'error': f'Failed to remove bot: {str(e)}'}, room=sid)

@socketio.on('reset_all_players')
def handle_reset_all_players(data):
    """Reset all players by marking them as not in game"""
    sid = request.sid
    admin_pin = data.get('admin_pin')
    
    # Create a local reference to the app logger
    logger = app.logger
    
    # Primary authorization check for socket events
    if not admin_pin or admin_pin != app.config.get('ADMIN_KEY'):
        logger.warning(f"Unauthorized attempt to reset all players from SID {sid}")
        emit('auth_error', {'error': 'Invalid admin credentials'}, room=sid)
        return
    
    logger.info(f"Admin request to reset all players from SID {sid}")
    try:
        # Get all players and mark them as not in game
        players = Player.query.all()
        count = 0
        
        for player in players:
            if player.in_game:
                player.in_game = False
                count += 1
        
        db.session.commit()
        
        # Broadcast an event to notify all clients
        socketio.emit('all_players_reset', {
            'count': count,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"All players reset successfully. {count} players marked as not in game.")
        
        # Send success response to the admin
        emit('reset_players_result', {
            'success': True,
            'count': count,
            'message': f"All players ({count}) marked as not in game"
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error resetting all players: {str(e)}", exc_info=True)
        emit('event_error', {'error': f'Failed to reset players: {str(e)}'}, room=sid)

@socketio.on('finance_update')
def handle_finance_update(data):
    """Handle financial updates and broadcast to relevant players"""
    sid = request.sid
    logger = app.logger
    
    try:
        update_type = data.get('type')
        player_id = data.get('player_id')
        
        if not update_type or not player_id:
            logger.warning(f"Missing required data in finance_update from SID {sid}")
            emit('event_error', {'error': 'Missing required parameters'}, room=sid)
            return
        
        # Create appropriate notification based on update type
        message = "Your financial status has been updated."
        
        if update_type == 'loan_created':
            message = "A new loan has been created for your account."
        elif update_type == 'loan_payment':
            message = "Your loan payment has been processed."
        elif update_type == 'cd_created':
            message = "A new Certificate of Deposit has been created."
        elif update_type == 'cd_matured':
            message = "Your Certificate of Deposit has matured."
        elif update_type == 'heloc_created':
            message = "A new Home Equity Line of Credit has been established."
        elif update_type == 'bankruptcy':
            message = "Your bankruptcy status has been updated."
        
        # Broadcast to the specific player's room
        socketio.emit('financial_update', {
            'type': update_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': data.get('details', {})
        }, room=f"player_{player_id}")
        
        logger.info(f"Financial update '{update_type}' sent to player {player_id}")
        
    except Exception as e:
        logger.error(f"Error handling finance update: {str(e)}", exc_info=True)
        emit('event_error', {'error': f'Failed to process finance update: {str(e)}'}, room=sid)

@socketio.on('create_bot')
def handle_create_bot(data):
    """Handle creating a new bot player"""
    admin_pin = data.get('admin_pin')
    if admin_pin != app.config['ADMIN_KEY']:
        socketio.emit('bot_event', {'error': 'Invalid admin PIN'}, room=request.sid)
        return
    
    try:
        # Get the bot controller from app config
        bot_controller = app.config.get('bot_controller')
        if not bot_controller:
            raise ValueError("Bot controller not initialized")
        
        # Extract bot data from request
        bot_name = data.get('name')
        bot_type = data.get('type', 'conservative')
        difficulty = data.get('difficulty', 'medium')
        
        # Check if username already exists
        existing_player = Player.query.filter_by(username=bot_name).first()
        if existing_player:
            # Generate a unique username by appending a random suffix
            import random
            random_suffix = str(random.randint(1000, 9999))
            unique_bot_name = f"{bot_name}_{random_suffix}"
            app.logger.info(f"Bot name '{bot_name}' already exists, using '{unique_bot_name}' instead")
            bot_name = unique_bot_name
        
        # Create the bot
        new_bot = bot_controller.create_bot(bot_name, bot_type, difficulty)
        
        if new_bot:
            # Return success with bot details
            socketio.emit('bot_event', {
                'success': True,
                'bot': {
                    'id': new_bot.id,
                    'name': new_bot.username,
                    'type': bot_type,
                    'difficulty': difficulty
                }
            }, room=request.sid)
        else:
            # Return failure
            socketio.emit('bot_event', {'error': 'Failed to create bot player'}, room=request.sid)
    except Exception as e:
        app.logger.error(f"Error creating bot: {str(e)}", exc_info=True)
        socketio.emit('bot_event', {'error': f'Failed to save new bot player: {str(e)}'}, room=request.sid)

# Catch-all route for handling 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

# Run the app
if __name__ == '__main__':
    setup_scheduled_tasks()
    port = get_port()
    debug_mode = is_debug_mode()
    logging.info(f"Starting server on port {port} with debug mode {'enabled' if debug_mode else 'disabled'}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, allow_unsafe_werkzeug=True) 