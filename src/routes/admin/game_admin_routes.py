from flask import Blueprint, jsonify, request
import logging
import datetime
from src.controllers.admin_controller import AdminController
from src.routes.decorators import admin_required
from src.models.player import Player
from src.models.game_state import GameState

logger = logging.getLogger(__name__)
game_admin_bp = Blueprint('game_admin', __name__, url_prefix='')

# Assumes AdminController instance is accessible
admin_controller = AdminController()

@game_admin_bp.route('/games/create', methods=['POST'])
@admin_required
def create_game():
    """
    Create a new game with specified settings.
    
    This API creates a new game with the provided name, mode, and player settings.
    """
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
            
        # Get the game controller from app config
        from flask import current_app
        game_controller = current_app.config.get('game_controller')
        if not game_controller:
            logger.error("Game controller not found in app config")
            return jsonify({
                "success": False,
                "error": "Game controller not initialized"
            }), 500
            
        # Create a new game with settings from the request
        game_mode = data.get('mode', 'classic')
        difficulty = 'normal'  # Default
        lap_limit = 0  # No limit by default
        free_parking_fund = True  # Enabled by default
        auction_required = True  # Enabled by default
        turn_timeout = 60  # Default 60 seconds
        
        # Override defaults with values from request if provided
        if 'difficulty' in data:
            difficulty = data.get('difficulty')
        if 'lap_limit' in data:
            lap_limit = data.get('lap_limit')
        if 'free_parking_fund' in data:
            free_parking_fund = data.get('free_parking_fund')
        if 'auction_required' in data:
            auction_required = data.get('auction_required')
        if 'turn_timeout' in data:
            turn_timeout = data.get('turn_timeout')
            
        logger.info(f"Creating new game with mode: {game_mode}, difficulty: {difficulty}")
        
        result = game_controller.create_new_game(
            difficulty=difficulty,
            lap_limit=lap_limit,
            free_parking_fund=free_parking_fund,
            auction_required=auction_required,
            turn_timeout=turn_timeout
        )
        
        if not result.get('success'):
            logger.error(f"Game creation failed: {result.get('error')}")
            return jsonify(result), 500
            
        # Get the created game ID
        game_id = result.get('game_id')
        logger.info(f"Game created successfully with ID: {game_id}")
        
        # Add bots if requested
        bot_count = data.get('bot_count', 0)
        if bot_count > 0:
            bot_controller = current_app.config.get('bot_controller')
            if bot_controller:
                # Use different bot types for variety
                bot_types = ['conservative', 'aggressive', 'strategic', 'opportunistic']
                
                for i in range(bot_count):
                    bot_name = f"Bot_{i+1}"
                    # Select a bot type from the list with wraparound
                    bot_type = bot_types[i % len(bot_types)]
                    bot_controller.create_bot(bot_name, bot_type=bot_type)
                    logger.info(f"Created bot {bot_name} with type {bot_type}")
                    
        # Initialize the game mode if one was specified
        if game_mode != 'classic':
            game_mode_controller = current_app.config.get('game_mode_controller')
            if game_mode_controller:
                mode_result = game_mode_controller.initialize_game_mode(game_id, game_mode)
                logger.info(f"Initialized game mode {game_mode} for game {game_id}")
                if not mode_result.get('success'):
                    logger.warning(f"Failed to initialize game mode: {mode_result.get('error')}")
                
        # Get current game state to ensure data is correct
        # CRITICAL: Need to update game mode in the database
        from src.models.game_state import GameState
        from src.models import db
        
        # First update the database record - verify it exists
        game_state = GameState.query.filter_by(game_id=game_id).first()
        if game_state:
            # Make sure the mode is set
            game_state.mode = game_mode
            # Add the game state to the session
            db.session.add(game_state)
            db.session.commit()
            logger.info(f"Successfully updated game mode to {game_mode} for game {game_id}")
        else:
            logger.error(f"Could not find game with ID {game_id} after creation")
                
        # Now update the singleton instance to match the database
        singleton_instance = GameState.get_instance()
        if singleton_instance.game_id != game_id:
            # Get the current game state directly from the database
            logger.info(f"Refreshing singleton instance to new game ID: {game_id}")
            db_game_state = GameState.query.filter_by(game_id=game_id).first()
            
            if db_game_state:
                # Copy all attributes from the database instance to the singleton
                for column in singleton_instance.__table__.columns:
                    column_name = column.name
                    if hasattr(db_game_state, column_name):
                        setattr(singleton_instance, column_name, getattr(db_game_state, column_name))
                logger.info(f"Successfully refreshed singleton instance to game {game_id}")
            else:
                logger.error(f"Could not refresh singleton - game {game_id} not found in database")
                
        # Return success with game details
        return jsonify({
            "success": True,
            "game_id": game_id,
            "message": "Game created successfully",
            "name": data.get('name', 'New Game'),
            "mode": game_mode,
            "max_players": data.get('max_players', 8),
            "bot_count": bot_count,
            "public": data.get('public', False)
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating game: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to create game: {str(e)}"
        }), 500

@game_admin_bp.route('/games/active', methods=['GET'])
@admin_required
def get_active_games():
    """
    Get a list of all active games in the system.
    
    This API returns basic information about active games including players, game mode, and status.
    """
    try:
        # Query all game states directly from database to avoid singleton issues
        # For now, we'll just return the most recent one, but this could be expanded in the future
        game_states = GameState.query.order_by(GameState.id.desc()).limit(10).all()
        
        if not game_states:
            logger.warning("No active game states found in get_active_games")
            return jsonify({
                "success": False,
                "error": "No active game states found"
            }), 404
        
        # Get the singleton instance and refresh it with the most recent game if needed
        singleton_instance = GameState.get_instance()
        most_recent_game = game_states[0]
        
        # If the singleton doesn't match the most recent game, refresh it
        if singleton_instance.game_id != most_recent_game.game_id:
            logger.warning(f"Singleton game_id ({singleton_instance.game_id}) doesn't match most recent game_id ({most_recent_game.game_id})")
            singleton_instance.refresh_from_db(most_recent_game.game_id)
            logger.info(f"Refreshed singleton to match most recent game: {most_recent_game.game_id}")
        
        game_data_list = []
        
        # Generate response data for each game
        for game_state in game_states:
            # Only include active or recently active games
            if game_state.status not in ['active', 'setup', 'paused']:
                continue
                
            # Get active players for this game
            # In a multi-game system, you would filter by game_id as well
            active_players = Player.query.filter_by(in_game=True).all()
            player_count = len(active_players)
            
            logger.debug(f"Found {player_count} active players for game {game_state.game_id}")
            
            game_data = {
                "id": game_state.game_id,
                "mode": game_state.mode or "standard",
                "player_count": player_count,
                "max_players": 8,  # Placeholder - would be from game settings
                "current_lap": game_state.current_lap,
                "current_turn_player": None,  # Would need to find the current player
                "status": game_state.status,
                "duration_minutes": 0,  # Placeholder - would calculate from start time
                "created_at": datetime.datetime.now().isoformat(),  # Placeholder
                "settings": {
                    "starting_cash": 1500,  # Standard values
                    "go_salary": 200,
                    "free_parking_collects_fees": hasattr(game_state, 'free_parking_fund') and game_state.free_parking_fund,
                    "auction_enabled": hasattr(game_state, 'auction_required') and game_state.auction_required,
                    "max_turns": None,
                    "max_time_minutes": None
                }
            }
            
            # Find the current player if possible
            if game_state.current_player_id:
                try:
                    current_player = Player.query.get(game_state.current_player_id)
                    if current_player:
                        game_data["current_turn_player"] = current_player.username
                except Exception as player_error:
                    logger.warning(f"Error getting current player: {player_error}")
                    # Continue without current player info
            
            # Calculate game duration if start_time is available
            if hasattr(game_state, 'start_time') and game_state.start_time:
                start_time = game_state.start_time
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.datetime.fromisoformat(start_time)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing start_time: {e}")
                        start_time = None
                
                if start_time:
                    duration = datetime.datetime.now() - start_time
                    game_data["duration_minutes"] = int(duration.total_seconds() / 60)
            
            game_data_list.append(game_data)
        
        response_data = {
            "success": True,
            "games": game_data_list
        }
        
        # Try to create the response once to catch any serialization errors
        try:
            response = jsonify(response_data)
            return response, 200
        except Exception as json_error:
            logger.error(f"JSON serialization error: {json_error}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"JSON serialization error: {str(json_error)}"
            }), 500
    
    except Exception as e:
        logger.error(f"Error getting active games: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to get active games: {str(e)}"
        }), 500

@game_admin_bp.route('/games/<string:game_id>', methods=['GET'])
@admin_required
def get_game_details(game_id):
    """
    Get detailed information about a specific game.
    
    This API returns detailed information including players, properties, and game settings.
    """
    try:
        # Get game state using direct database query first to avoid singleton issues
        game_state_db = GameState.query.filter_by(game_id=game_id).first()
        
        if not game_state_db:
            logger.warning(f"Game with ID {game_id} not found in database")
            return jsonify({
                "success": False,
                "error": "Game not found in database"
            }), 404
            
        # Get the singleton instance and refresh it if needed
        game_state = GameState.get_instance()
        
        # If the singleton's game_id doesn't match, refresh it from the database
        if game_state.game_id != game_id:
            logger.warning(f"Singleton game_id ({game_state.game_id}) doesn't match requested game_id ({game_id})")
            game_state.refresh_from_db(game_id)
            logger.info(f"Refreshed singleton to match game_id: {game_id}")
        
        # Get players in this game
        players = Player.query.filter_by(in_game=True).all()
        
        # Format player data
        player_data = []
        for player in players:
            player_data.append({
                "id": player.id,
                "name": player.username,
                "type": "bot" if player.is_bot else "human",
                "cash": player.money,
                "position": player.position,
                "is_in_jail": player.in_jail,
                "jail_turns": player.jail_turns,
                "property_count": len(player.properties) if player.properties is not None else 0,
                "in_game": player.in_game
            })
        
        # Build detailed game response
        game_details = {
            "id": game_state.game_id,
            "name": "Pi-nopoly Game",  # Placeholder
            "mode": game_state.mode or "classic",
            "status": "active" if game_state.status == 'active' else "inactive",
            "created_at": datetime.datetime.now().isoformat(),  # Placeholder
            "current_lap": game_state.current_lap,
            "current_turn_player": None,  # Will be set below if available
            "duration_minutes": 0,  # Placeholder - would calculate from start time
            "players": player_data,
            "settings": {
                "starting_cash": 1500,  # Standard values
                "go_salary": 200,
                "free_parking_collects_fees": True,
                "auction_enabled": True,
                "max_turns": None,
                "max_time_minutes": None
            }
        }
        
        # Find the current player if possible
        if game_state.current_player_id:
            current_player = Player.query.get(game_state.current_player_id)
            if current_player:
                game_details["current_turn_player"] = current_player.username
        
        # Calculate game duration if start_time is available
        if hasattr(game_state, 'start_time') and game_state.start_time:
            start_time = game_state.start_time
            if isinstance(start_time, str):
                try:
                    start_time = datetime.datetime.fromisoformat(start_time)
                except (ValueError, TypeError):
                    start_time = None
            
            if start_time:
                duration = datetime.datetime.now() - start_time
                game_details["duration_minutes"] = int(duration.total_seconds() / 60)
        
        return jsonify({
            "success": True,
            "game": game_details
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting game details for game {game_id}: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to get game details: {str(e)}"
        }), 500

@game_admin_bp.route('/games/<string:game_id>/end', methods=['POST'])
@admin_required
def end_game(game_id):
    """
    End a specific game.
    
    This API forcefully ends a game, marking it as inactive and players as not in game.
    """
    try:
        # Query the specific game from database first
        game_state_db = GameState.query.filter_by(game_id=game_id).first()
        
        if not game_state_db:
            logger.warning(f"Game with ID {game_id} not found in database")
            return jsonify({
                "success": False,
                "error": "Game not found in database"
            }), 404
        
        # Get the singleton instance and refresh it if needed
        game_state = GameState.get_instance()
        
        # If the singleton's game_id doesn't match, refresh it from the database
        if game_state.game_id != game_id:
            logger.warning(f"Singleton game_id ({game_state.game_id}) doesn't match requested game_id ({game_id})")
            game_state.refresh_from_db(game_id)
            logger.info(f"Refreshed singleton to match game_id: {game_id}")
        
        # Mark game as inactive
        game_state.status = 'ended'
        
        # Mark all players as not in game
        players = Player.query.filter_by(in_game=True).all()
        for player in players:
            player.in_game = False
        
        # Save changes to database
        from src.models import db
        db.session.commit()
        
        # Emit game ended event if socketio is available
        from flask import current_app
        socketio = current_app.config.get('socketio')
        if socketio:
            socketio.emit('game_ended', {
                "game_id": game_id,
                "message": "Game has been ended by an administrator"
            })
        
        return jsonify({
            "success": True,
            "message": f"Game {game_id} has been ended",
            "players_removed": len(players)
        }), 200
    
    except Exception as e:
        logger.error(f"Error ending game {game_id}: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to end game: {str(e)}"
        }), 500

@game_admin_bp.route('/games/analytics', methods=['GET'])
@admin_required
def get_game_analytics():
    """
    Get analytics data for games over a period of time.
    
    Query parameters:
    - days: Number of days to analyze (default: 30)
    """
    try:
        # Get the number of days from query parameters
        days = int(request.args.get('days', 30))
        
        # Get game state
        game_state = GameState.get_instance()
        
        if not game_state:
            return jsonify({
                "success": False,
                "error": "No active game state found"
            }), 404
        
        # Get current date and time
        now = datetime.datetime.now()
        
        # Calculate start date
        start_date = now - datetime.timedelta(days=days)
        
        # Get all players
        players = Player.query.all()
        active_players = [p for p in players if p.in_game]
        
        # Placeholder analytics data
        analytics = {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat()
            },
            "players": {
                "total": len(players),
                "active": len(active_players),
                "bots": len([p for p in players if p.is_bot]),
                "humans": len([p for p in players if not p.is_bot])
            },
            "game_stats": {
                "current_lap": game_state.current_lap,
                "average_turns_per_game": game_state.current_lap,  # Placeholder - would average over multiple games
                "average_game_duration_minutes": 0,  # Placeholder
                "games_completed": 0,  # Placeholder
                "games_in_progress": 1 if game_state.status == 'active' else 0
            },
            "economic_stats": {
                "total_money_in_circulation": sum(p.money for p in players),
                "average_player_cash": sum(p.money for p in active_players) / len(active_players) if active_players else 0,
                "property_ownership_rate": 0  # Placeholder - would calculate based on properties
            },
            "charts": {
                "player_activity": generate_placeholder_chart_data(days),
                "cash_distribution": {
                    "labels": ["0-500", "501-1000", "1001-1500", "1501-2000", "2001+"],
                    "data": [
                        len([p for p in active_players if p.money <= 500]),
                        len([p for p in active_players if p.money > 500 and p.money <= 1000]),
                        len([p for p in active_players if p.money > 1000 and p.money <= 1500]),
                        len([p for p in active_players if p.money > 1500 and p.money <= 2000]),
                        len([p for p in active_players if p.money > 2000])
                    ]
                }
            }
        }
        
        return jsonify({
            "success": True,
            "analytics": analytics
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting game analytics: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to get game analytics: {str(e)}"
        }), 500

def generate_placeholder_chart_data(days):
    """
    Generate placeholder data for a time series chart.
    
    Args:
        days: Number of days to generate data for
    
    Returns:
        Dictionary with labels and data arrays
    """
    labels = []
    data = []
    
    # Generate a label and data point for each day
    for i in range(days):
        date = (datetime.datetime.now() - datetime.timedelta(days=days-i-1)).strftime('%m/%d')
        labels.append(date)
        # Random data between 0 and 10
        import random
        data.append(random.randint(0, 10))
    
    return {
        "labels": labels,
        "data": data
    }

@game_admin_bp.route('/modify-state', methods=['POST'])
@admin_required
def modify_game_state():
    """Override current game state values"""
    data = request.json
    state_changes = data.get('state_changes')
    reason = data.get('reason', 'Admin adjustment')
    
    if not state_changes:
        return jsonify({'success': False, 'error': 'State changes are required'}), 400
    
    # Call the implemented admin_controller method
    result = admin_controller.modify_game_state(state_changes, reason)
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_admin_bp.route('/status', methods=['GET'])
@admin_required
def admin_status():
    """Get current game status for admin dashboard"""
    # Delegate to controller (already refactored)
    result = admin_controller.get_admin_game_status()
    
    if result.get('success'):
        result.pop('success', None)
        return jsonify(result), 200
    else:
        return jsonify({"error": result.get('error', 'Failed to get admin status')}), 500

@game_admin_bp.route('/reset', methods=['POST'])
@admin_required
def admin_reset_game():
    """Reset the game to initial state"""
    try:
        # Call the implemented admin_controller method
        result = admin_controller.reset_game()
        
        logger.info(f"Game reset result: {result}")
        
        # Notify clients that bots have been reset
        if result.get('success'):
            # Get socketio from app config
            from flask import current_app
            socketio = current_app.config.get('socketio')
            if socketio:
                socketio.emit('bots_reset', {'message': 'All bots removed during game reset'})
                logger.info("Emitted bots_reset event to clients")
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error in admin_reset_game: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@game_admin_bp.route('/system-status', methods=['GET'])
@admin_required
def system_status():
    """Get server and game system status"""
    # Call the implemented admin_controller method
    result = admin_controller.get_system_status()
        
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@game_admin_bp.route('/system-health-trends', methods=['GET'])
@admin_required
def system_health_trends():
    """Get system health metrics and trends over time"""
    try:
        # Get the optional hours parameter
        hours = request.args.get('hours', default=24, type=int)
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # 1 hour to 7 days
            return jsonify({
                "success": False, 
                "error": "Hours parameter must be between 1 and 168"
            }), 400
        
        # Call the implemented admin_controller method
        result = admin_controller.get_system_health_trends(hours)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error in system_health_trends: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 