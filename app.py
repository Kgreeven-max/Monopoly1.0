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
# from src.routes.property_routes import register_property_routes # File not found
# from src.routes.auction_routes import register_auction_routes # File not found
from src.routes.admin.game_admin_routes import game_admin_bp
from src.routes.admin.player_admin_routes import player_admin_bp
from src.routes.admin.bot_admin_routes import bot_admin_bp
from src.routes.admin.event_admin_routes import event_admin_bp
from src.routes.admin.crime_admin_routes import crime_admin_bp
from src.routes.admin.finance_admin_routes import finance_admin_bp
# Import the blueprint variable directly
from src.routes.admin.property_admin_routes import property_admin_bp
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
# Import database migration
from src.migrations.add_free_parking_fund import run_migration

# Initialize Flask app
app = Flask(__name__)

# Database configuration first, as it may be needed by other configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///pinopoly.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Other configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'pinopoly-development-key'),
    ADMIN_KEY=os.environ.get('ADMIN_KEY', 'pinopoly-admin'),
    DISPLAY_KEY=os.environ.get('DISPLAY_KEY', 'pinopoly-display'),
    DEBUG=os.environ.get('DEBUG', 'False').lower() == 'true',
    REMOTE_PLAY_ENABLED=os.environ.get('REMOTE_PLAY_ENABLED', 'False').lower() == 'true',
    REMOTE_PLAY_TIMEOUT=int(os.environ.get('REMOTE_PLAY_TIMEOUT', 60))
)

# Game configuration
app.config['ADAPTIVE_DIFFICULTY_ENABLED'] = os.environ.get('ADAPTIVE_DIFFICULTY_ENABLED', 'true').lower() == 'true'
app.config['ADAPTIVE_DIFFICULTY_INTERVAL'] = int(os.environ.get('ADAPTIVE_DIFFICULTY_INTERVAL', '15'))  # minutes
app.config['POLICE_PATROL_ENABLED'] = os.environ.get('POLICE_PATROL_ENABLED', 'true').lower() == 'true'
app.config['POLICE_PATROL_INTERVAL'] = int(os.environ.get('POLICE_PATROL_INTERVAL', '45'))  # minutes
app.config['PORT'] = int(os.environ.get('PORT', 5000))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
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
        
    # ---- Stage 1: Initialize basic services and controllers ----
    banker = Banker(socketio)
    community_fund = CommunityFund(socketio, game_state)
    event_system = EventSystem(socketio, banker, community_fund)
    auction_system = AuctionSystem(socketio, banker)
    special_space_controller = SpecialSpaceController(socketio, banker, community_fund)
    social_controller = SocialController(socketio, app.config) 
    remote_controller = RemoteController(app) # Needs app instance
    player_controller = PlayerController(db) # Pass the db instance
    auth_controller = AuthController() # Initialize AuthController
    game_logic = GameLogic(app) # Initialize GameLogic
    property_controller = PropertyController(db, banker, event_system, socketio) # Assuming these dependencies
    auction_controller = AuctionController(db, banker, event_system, socketio) # Assuming these dependencies
    
    # Initialize socket controller
    from src.controllers.socket_controller import SocketController
    socket_controller = SocketController(socketio, app.config)

    # Initialize social controllers
    chat_controller = ChatController(socketio, app.config)
    alliance_controller = AllianceController(socketio, app.config)
    reputation_controller = ReputationController(socketio, app.config)
    app.config['chat_controller'] = chat_controller
    app.config['alliance_controller'] = alliance_controller
    app.config['reputation_controller'] = reputation_controller

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
    app.config['socket_controller'] = socket_controller # Store socket controller

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

# Register API routes
# Pass the controller instances directly
register_player_routes(app, player_controller)
register_game_routes(app, game_controller)
# register_property_routes(app)  # Property routes - not found, commented out
# register_auction_routes(app)   # Auction routes - not found, commented out
app.register_blueprint(game_admin_bp, url_prefix='/api/admin')
app.register_blueprint(player_admin_bp, url_prefix='/api/admin')
app.register_blueprint(bot_admin_bp, url_prefix='/api/admin')
app.register_blueprint(event_admin_bp, url_prefix='/api/admin')
app.register_blueprint(crime_admin_bp, url_prefix='/api/admin')
app.register_blueprint(finance_admin_bp, url_prefix='/api/admin')
app.register_blueprint(property_admin_bp, url_prefix='/api/admin')
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

# Scheduled tasks
def setup_scheduled_tasks():
    """Set up scheduled background tasks"""
    if app.config['ADAPTIVE_DIFFICULTY_ENABLED']:
        # Start adaptive difficulty assessment
        difficulty_controller = AdaptiveDifficultyController(socketio)
        
        def run_difficulty_assessment():
            while True:
                # Sleep first to avoid immediate assessment on startup
                eventlet.sleep(app.config['ADAPTIVE_DIFFICULTY_INTERVAL'] * 60)
                
                try:
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
        
        def run_police_patrol():
            while True:
                # Sleep first to avoid immediate patrol on startup
                eventlet.sleep(app.config['POLICE_PATROL_INTERVAL'] * 60)
                
                try:
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

# Run the app
if __name__ == '__main__':
    setup_scheduled_tasks()
    socketio.run(app, host='0.0.0.0', port=app.config['PORT'], debug=True, allow_unsafe_werkzeug=True) 