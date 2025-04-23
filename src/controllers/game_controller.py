import logging
from datetime import datetime
from flask import request, current_app # Added current_app for easier access
import json
import random
import uuid

from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property, PropertyType
from src.models.transaction import Transaction
from src.models.game_history import GameHistory
from src.models.game_mode import GameMode
from src.controllers.team_controller import TeamController
from src.controllers.game_mode_controller import GameModeController
from src.models.special_space import SpecialSpace
# Assuming GameLogic is imported where needed, or add:
# from src.game_logic.game_logic import GameLogic 

logger = logging.getLogger(__name__)

class GameController:
    """Controller for game-related operations"""
    
    def __init__(self, app_config):
        self.logger = logging.getLogger("game_controller")
        self.app_config = app_config
        self.socketio = app_config.get('socketio')
        self.game_logic = app_config.get('game_logic') # Retrieve GameLogic instance
        if not self.game_logic:
             self.logger.error("GameLogic dependency not found in app_config!")
             # Handle error appropriately, maybe raise an exception
        
        self.game_mode_controller = GameModeController(self.socketio)
        self.team_controller = TeamController(self.socketio)
    
    def _initialize_properties(self, game_id):
        """Deletes existing properties and creates the standard set for the game."""
        # Delete existing properties that would conflict with new ones
        try:
            # Get all property positions we're going to create
            positions = [data[2] for data in self.get_standard_property_data()]
            
            # Delete any properties with these positions (regardless of game_id)
            num_deleted = Property.query.filter(Property.position.in_(positions)).delete(synchronize_session=False)
            db.session.commit() # Commit the deletion
            if num_deleted > 0:
                self.logger.info(f"Deleted {num_deleted} existing properties for new game {game_id}.")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting existing properties for game {game_id}: {e}", exc_info=True)
            raise # Re-raise the exception to prevent potentially inconsistent state

        self.logger.info(f"Initializing standard properties for game_id {game_id}...")
        
        # Insert the standard property data
        properties_data = self.get_standard_property_data()

        for data in properties_data:
            if data[1] is None: # Skip non-property spaces
                continue
            
            # Create Property object using only arguments accepted by __init__
            prop = Property(
                name=data[0],
                position=data[2],
                group_name=data[4], # Use group_name as per __init__
                price=data[3],
                rent=data[5],
                # improvement_cost can default or be set if needed
                mortgage_value=data[3] // 2,
                # rent_levels can default or be set if needed
            )
            
            # Set other attributes directly on the object
            prop.type = data[1]
            prop.color_group = data[4] # Set the database column attribute
            prop.house_cost = data[6]
            prop.hotel_cost = data[7]
            prop.rent_house_1 = data[8][0] if len(data[8]) > 0 else None
            prop.rent_house_2 = data[8][1] if len(data[8]) > 1 else None
            prop.rent_house_3 = data[8][2] if len(data[8]) > 2 else None
            prop.rent_house_4 = data[8][3] if len(data[8]) > 3 else None
            prop.rent_hotel = data[8][4] if len(data[8]) > 4 else None
            prop.game_id = game_id
            
            db.session.add(prop)
        
        try:
            db.session.commit()
            self.logger.info(f"Successfully initialized {len(properties_data) - 10} properties for game {game_id}.") # Adjusted count
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to commit properties for game {game_id}: {e}", exc_info=True)
            raise # Re-raise exception to indicate failure
            
    def get_standard_property_data(self):
        """Return standard property data for initialization"""
        return [
            # Name, Type, Position, Price, Group, Rent, Houses Cost, Hotel Cost, Rents[1-4+Hotel]
            ("Go", None, 0, 0, "Corner", 0, 0, 0, []), # Placeholder for non-properties
            ("Mediterranean Avenue", PropertyType.STREET, 1, 60, "Brown", 2, 50, 50, [10, 30, 90, 160, 250]),
            ("Community Chest", None, 2, 0, "Chest", 0, 0, 0, []),
            ("Baltic Avenue", PropertyType.STREET, 3, 60, "Brown", 4, 50, 50, [20, 60, 180, 320, 450]),
            ("Income Tax", None, 4, 0, "Tax", 0, 0, 0, []),
            ("Reading Railroad", PropertyType.RAILROAD, 5, 200, "Railroad", 25, 0, 0, []), # Rent handled differently
            ("Oriental Avenue", PropertyType.STREET, 6, 100, "LightBlue", 6, 50, 50, [30, 90, 270, 400, 550]),
            ("Chance", None, 7, 0, "Chance", 0, 0, 0, []),
            ("Vermont Avenue", PropertyType.STREET, 8, 100, "LightBlue", 6, 50, 50, [30, 90, 270, 400, 550]),
            ("Connecticut Avenue", PropertyType.STREET, 9, 120, "LightBlue", 8, 50, 50, [40, 100, 300, 450, 600]),
            ("Jail / Just Visiting", None, 10, 0, "Corner", 0, 0, 0, []),
            ("St. Charles Place", PropertyType.STREET, 11, 140, "Pink", 10, 100, 100, [50, 150, 450, 625, 750]),
            ("Electric Company", PropertyType.UTILITY, 12, 150, "Utility", 0, 0, 0, []), # Rent handled differently
            ("States Avenue", PropertyType.STREET, 13, 140, "Pink", 10, 100, 100, [50, 150, 450, 625, 750]),
            ("Virginia Avenue", PropertyType.STREET, 14, 160, "Pink", 12, 100, 100, [60, 180, 500, 700, 900]),
            ("Pennsylvania Railroad", PropertyType.RAILROAD, 15, 200, "Railroad", 25, 0, 0, []),
            ("St. James Place", PropertyType.STREET, 16, 180, "Orange", 14, 100, 100, [70, 200, 550, 750, 950]),
            ("Community Chest", None, 17, 0, "Chest", 0, 0, 0, []),
            ("Tennessee Avenue", PropertyType.STREET, 18, 180, "Orange", 14, 100, 100, [70, 200, 550, 750, 950]),
            ("New York Avenue", PropertyType.STREET, 19, 200, "Orange", 16, 100, 100, [80, 220, 600, 800, 1000]),
            ("Free Parking", None, 20, 0, "Corner", 0, 0, 0, []),
            ("Kentucky Avenue", PropertyType.STREET, 21, 220, "Red", 18, 150, 150, [90, 250, 700, 875, 1050]),
            ("Chance", None, 22, 0, "Chance", 0, 0, 0, []),
            ("Indiana Avenue", PropertyType.STREET, 23, 220, "Red", 18, 150, 150, [90, 250, 700, 875, 1050]),
            ("Illinois Avenue", PropertyType.STREET, 24, 240, "Red", 20, 150, 150, [100, 300, 750, 925, 1100]),
            ("B. & O. Railroad", PropertyType.RAILROAD, 25, 200, "Railroad", 25, 0, 0, []),
            ("Atlantic Avenue", PropertyType.STREET, 26, 260, "Yellow", 22, 150, 150, [110, 330, 800, 975, 1150]),
            ("Ventnor Avenue", PropertyType.STREET, 27, 260, "Yellow", 22, 150, 150, [110, 330, 800, 975, 1150]),
            ("Water Works", PropertyType.UTILITY, 28, 150, "Utility", 0, 0, 0, []),
            ("Marvin Gardens", PropertyType.STREET, 29, 280, "Yellow", 24, 150, 150, [120, 360, 850, 1025, 1200]),
            ("Go To Jail", None, 30, 0, "Action", 0, 0, 0, []),
            ("Pacific Avenue", PropertyType.STREET, 31, 300, "Green", 26, 200, 200, [130, 390, 900, 1100, 1275]),
            ("North Carolina Avenue", PropertyType.STREET, 32, 300, "Green", 26, 200, 200, [130, 390, 900, 1100, 1275]),
            ("Community Chest", None, 33, 0, "Chest", 0, 0, 0, []),
            ("Pennsylvania Avenue", PropertyType.STREET, 34, 320, "Green", 28, 200, 200, [150, 450, 1000, 1200, 1400]),
            ("Short Line", PropertyType.RAILROAD, 35, 200, "Railroad", 25, 0, 0, []),
            ("Chance", None, 36, 0, "Chance", 0, 0, 0, []),
            ("Park Place", PropertyType.STREET, 37, 350, "Blue", 35, 200, 200, [175, 500, 1100, 1300, 1500]),
            ("Luxury Tax", None, 38, 0, "Tax", 0, 0, 0, []),
            ("Boardwalk", PropertyType.STREET, 39, 400, "Blue", 50, 200, 200, [200, 600, 1400, 1700, 2000])
        ]

    def create_new_game(self, difficulty='normal', lap_limit=0, free_parking_fund=True, 
                         auction_required=True, turn_timeout=60):
        """Create a new game with specified settings"""
        try:
            self.logger.info(f"Creating new game with settings: difficulty={difficulty}, lap_limit={lap_limit}")
            
            # Get the existing game state
            game_state = GameState.query.first()
            if not game_state:
                # If no game state exists, create a new one
                import uuid
                game_state = GameState(game_id=str(uuid.uuid4()))
                self.logger.info(f"Created new GameState instance with game_id: {game_state.game_id}")
                db.session.add(game_state)
                db.session.commit()
            else:
                # If game state exists, reset it to get a new game_id
                self.logger.info(f"Resetting existing GameState with ID: {game_state.id}")
                game_state.reset()
                
            # Store the new game_id for reference
            new_game_id = game_state.game_id
            
            # Set the game properties
            game_state.difficulty = difficulty
            game_state.total_laps = lap_limit  # Update field name if different
            game_state.free_parking_fund = free_parking_fund
            game_state.auction_required = auction_required
            game_state.turn_timer = turn_timeout
            game_state.status = 'setup'  # Set to setup state
            
            self.logger.info(f"Game state transitioned to 'setup' mode. Ready for player addition.")
            
            # Reset all bots by setting them to not in game
            bots = Player.query.filter_by(is_bot=True).all()
            for bot in bots:
                bot.in_game = False
                
            # Clear the active_bots dictionary from bot_controller if it exists
            from src.controllers.bot_controller import active_bots
            active_bots.clear()
            
            # Clear all existing players from the game
            players = Player.query.filter_by(in_game=True).all()
            for player in players:
                player.in_game = False
                self.logger.info(f"Removed player {player.username} from game")
            
            # Validate and update property multipliers
            try:
                from src.models.property import Property
                # Check if certain property price multipliers need to be applied
                props = Property.query.all()
                if not props:
                    self.logger.warning(f"No properties found in database for verification")
                # If properties exist but are from a different game, delete them
                else:
                    for prop in props:
                        db.session.delete(prop)
                    db.session.commit()
                    self.logger.info(f"Cleared properties from previous game")
            except Exception as ve:
                self.logger.error(f"Error during verification: {str(ve)}")
                # Continue anyway - don't fail the game creation just because verification had issues
                self.logger.info(f"Continuing with game creation despite verification error")
            
            # Now initialize properties for this new game
            self._initialize_properties(new_game_id)
            
            # Save all changes
            db.session.commit()
            
            self.logger.info(f"New game created with difficulty {difficulty} and game_id {new_game_id}")
            
            return {
                'success': True,
                'game_id': new_game_id,
                'message': 'New game created'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating new game: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_player(self, username, pin):
        """Add a new player to the game"""
        try:
            game_state = GameState.get_instance()
            if game_state.status != 'setup':
                return {
                    'success': False,
                    'error': 'Cannot add players after game has started'
                }
            
            existing_player = Player.query.filter_by(username=username).first()
            if existing_player and existing_player.in_game:
                return {
                    'success': False,
                    'error': 'Username already exists'
                }
            
            if existing_player:
                player = existing_player
                player.in_game = True
                player.pin = pin
            else:
                player = Player(username=username, pin=pin)
            
            player.cash = self._get_starting_cash(game_state.difficulty)
            player.position = 0
            player.is_bankrupt = False
            player.turns_in_jail = 0
            player.is_in_jail = False
            
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {username} added to game")
            
            return {
                'success': True,
                'player_id': player.id,
                'message': 'Player added to game'
            }
            
        except Exception as e:
            self.logger.error(f"Error adding player: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_starting_cash(self, difficulty):
        """Get starting cash amount based on difficulty"""
        if difficulty == 'easy':
            return 2000
        elif difficulty == 'normal':
            return 1500
        elif difficulty == 'hard':
            return 1200
        else:
            return 1500
    
    def start_game(self, data):
        """Start a new game or resume an existing one."""
        self.logger.info(f"Game start requested: {data}")
        
        try:
            admin_pin = data.get('admin_pin')
            
            # Verify admin pin
            if not admin_pin or admin_pin != self.app_config.get('ADMIN_KEY'):
                self.logger.warning(f"Invalid admin pin provided for game start")
                return {'success': False, 'error': 'Invalid admin credentials'}
            
            # Get game_id if specified, otherwise use the default game
            game_id = data.get('game_id')
            
            # Get current game state
            if game_id:
                game_state = GameState.query.filter_by(game_id=game_id).first()
                if not game_state:
                    self.logger.error(f"No game state found with game_id: {game_id}")
                    return {'success': False, 'error': f'Game state not found with ID: {game_id}'}
            else:
                game_state = GameState.query.first()
                if not game_state:
                    self.logger.error(f"No game state found")
                    return {'success': False, 'error': 'Game state not found'}
            
            # Register all bot players in the active_bots dictionary
            # Import required modules here to avoid circular imports
            from src.controllers.bot_controller import active_bots, ConservativeBot, AggressiveBot, StrategicBot, OpportunisticBot
            from src.models.player import Player
            
            bot_players = Player.query.filter_by(is_bot=True, in_game=True).all()
            self.logger.info(f"Found {len(bot_players)} bot players to register for game start")
            
            for bot_player in bot_players:
                # If bot already in active_bots, skip
                if bot_player.id in active_bots:
                    continue
                    
                # Infer bot type from name as a fallback
                bot_type = 'conservative'  # Default
                if 'aggressive' in bot_player.username.lower():
                    bot_type = 'aggressive'
                elif 'strategic' in bot_player.username.lower():
                    bot_type = 'strategic'
                elif 'opportunistic' in bot_player.username.lower():
                    bot_type = 'opportunistic'
                
                # Create appropriate bot instance
                if bot_type == 'aggressive':
                    active_bots[bot_player.id] = AggressiveBot(bot_player.id, 'medium')
                elif bot_type == 'strategic':
                    active_bots[bot_player.id] = StrategicBot(bot_player.id, 'medium')
                elif bot_type == 'opportunistic':
                    active_bots[bot_player.id] = OpportunisticBot(bot_player.id, 'medium')
                else:
                    active_bots[bot_player.id] = ConservativeBot(bot_player.id, 'medium')
                
                self.logger.info(f"Registered bot {bot_player.username} (ID: {bot_player.id}) with type {bot_type}")
            
            self.logger.info(f"Active bots after registration: {list(active_bots.keys())}")
            
            # Initialize player order if not set
            if not game_state.player_order:
                # Query active players from the database
                active_players = Player.query.filter_by(in_game=True).all()
                
                if not active_players:
                    self.logger.error("No active players found to start the game")
                    return {'success': False, 'error': 'Cannot start game with no players'}
                
                # Randomize player order
                player_ids = [str(player.id) for player in active_players]
                import random
                random.shuffle(player_ids)
                game_state.player_order = ','.join(player_ids)
                self.logger.info(f"Initialized player order: {game_state.player_order}")
            
            # Initialize special spaces and cards
            self._initialize_board_elements()
            
            # Set game as active
            game_state.status = 'active'
            game_state.start_time = datetime.now()
            game_state.started_at = datetime.now()  # Set the started_at timestamp
            game_state.current_lap = 1
            
            # Select first player based on player order
            first_player_id = int(game_state.player_order.split(',')[0])
            first_player = Player.query.get(first_player_id)
            game_state.current_player_id = first_player.id
            
            # Initialize expected action to roll dice for first player
            game_state.expected_action_type = 'roll_dice'
            game_state.expected_action_details = None
            
            # Mark the game_running flag
            game_state.game_running = True
            
            db.session.add(game_state)
            db.session.commit()
            self.logger.info(f"Game state set to active, current player: {first_player.username}")
            
            # Ensure bot thread is started after committing the database changes
            if hasattr(self.app_config.get('bot_controller', {}), 'socketio') and self.app_config.get('app'):
                from src.controllers.bot_controller import start_bot_action_thread
                self.logger.info("Starting bot action thread from game controller")
                start_bot_action_thread(self.app_config.get('bot_controller').socketio, self.app_config)
            
            # Emit game started event
            if self.socketio:
                self.socketio.emit('game_started', {
                    'game_id': game_state.game_id,
                    'first_player': {
                        'id': first_player.id,
                        'name': first_player.username
                    },
                    'player_count': len(active_players),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Emit turn started for first player
                self.socketio.emit('turn_started', {
                    'player_id': first_player.id,
                    'player_name': first_player.username,
                    'turn_number': 1,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Return game state
            if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                return {
                    'success': True, 
                    'message': 'Game started successfully', 
                    'game_state': self.game_logic.get_game_state(game_state.id),
                    'game_id': game_state.game_id
                }
            else:
                return {'success': True, 'message': 'Game started successfully', 'game_id': game_state.game_id}
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error starting game: {e}", exc_info=True)
            return {'success': False, 'error': f'Failed to start game: {str(e)}'}

    def _initialize_board_elements(self):
        """Initialize board elements like special spaces and cards"""
        self.logger.info("Initializing board elements")
        
        try:
            # Get special space controller
            special_space_controller = self.app_config.get('special_space_controller')
            if not special_space_controller:
                self.logger.error("Special space controller not available")
                return False
            
            # Initialize special spaces
            spaces_result = special_space_controller.initialize_special_spaces()
            if not spaces_result.get('success', False):
                self.logger.error(f"Failed to initialize special spaces: {spaces_result.get('error', 'Unknown error')}")
                return False
            
            # Initialize cards
            cards_result = special_space_controller.initialize_cards()
            if not cards_result.get('success', False):
                self.logger.error(f"Failed to initialize cards: {cards_result.get('error', 'Unknown error')}")
                return False
            
            self.logger.info(f"Successfully initialized board elements: {spaces_result.get('spaces_created', 0)} spaces, {cards_result.get('community_chest_cards', 0)} Community Chest cards, {cards_result.get('chance_cards', 0)} Chance cards")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing board elements: {e}", exc_info=True)
            return False
    
    def end_game(self, reason='normal'):
        """End the current game"""
        try:
            game_state = self.app_config.get('game_state_instance')
            if not game_state:
                 return {"success": False, "error": "Game state not found"}
            
            if game_state.status != 'active':
                return {
                    'success': False,
                    'error': 'Game is not active'
                }
            
            game_state.status = 'ended'
            game_state.ended_at = datetime.now()
            
            winner_id = self._determine_winner() 
            
            history = GameHistory(
                started_at=game_state.started_at,
                ended_at=game_state.ended_at,
                player_count=Player.query.filter_by(in_game=True).count(),
                winner_id=winner_id,
                end_reason=reason
            )
            
            db.session.add(history)
            db.session.add(game_state)
            db.session.commit()
            
            self.logger.info(f"Game ended with reason: {reason}")
            
            if self.socketio:
                self.socketio.emit('game_over', {
                    'reason': reason,
                    'winner_id': winner_id,
                    'timestamp': game_state.ended_at.isoformat()
                }, room=game_state.game_id) 
            
            return {
                'success': True,
                'message': 'Game ended',
                'history_id': history.id
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error ending game: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _determine_winner(self):
        """Determine the winner of the game based on net worth"""
        players = Player.query.filter_by(in_game=True).all()
        if not players:
            return None
            
        player_worths = []
        for player in players:
            if player.is_bankrupt:
                continue
                
            net_worth = player.cash
            
            for prop in player.properties:
                net_worth += prop.current_value
            
            player_worths.append((player.id, net_worth))
        
        player_worths.sort(key=lambda x: x[1], reverse=True)
        
        return player_worths[0][0] if player_worths else None
    
    def get_game_state(self):
        """Get the current state of the game"""
        try:
            game_state = GameState.get_instance()
            
            # Add safeguard for started_at attribute
            try:
                started_at_value = game_state.started_at.isoformat() if game_state.started_at else None
            except AttributeError:
                self.logger.warning("GameState missing 'started_at' attribute - initializing to None")
                game_state.started_at = None
                db.session.add(game_state)
                db.session.commit()
                started_at_value = None
                
            # Add safeguard for ended_at attribute
            try:
                ended_at_value = game_state.ended_at.isoformat() if game_state.ended_at else None
            except AttributeError:
                self.logger.warning("GameState missing 'ended_at' attribute - initializing to None")
                game_state.ended_at = None
                db.session.add(game_state)
                db.session.commit()
                ended_at_value = None
            
            result = {
                'success': True,
                'game_id': game_state.game_id,
                'status': game_state.status,
                'difficulty': game_state.difficulty,
                'current_lap': game_state.current_lap,
                'started_at': started_at_value,
                'ended_at': ended_at_value
            }
            
            if game_state.status == 'active' and game_state.current_player_id:
                current_player = Player.query.get(game_state.current_player_id)
                result['current_player'] = {
                    'id': current_player.id,
                    'username': current_player.username,
                    'position': current_player.position
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting game state: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_players(self):
        """Get a list of all players in the game"""
        try:
            players = Player.query.filter_by(in_game=True).all()
            
            player_list = [{
                'id': player.id,
                'username': player.username,
                'cash': player.cash,
                'position': player.position,
                'is_bankrupt': player.is_bankrupt,
                'is_in_jail': player.is_in_jail,
                'property_count': len(player.properties)
            } for player in players]
            
            return {
                'success': True,
                'players': player_list
            }
            
        except Exception as e:
            self.logger.error(f"Error getting players: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_game_config(self, config_data):
        """Update game configuration"""
        try:
            game_state = GameState.get_instance()
            
            if game_state.status != 'setup':
                return {
                    'success': False,
                    'error': 'Cannot update config after game has started'
                }
            
            if 'difficulty' in config_data:
                game_state.difficulty = config_data['difficulty']
                
            if 'lap_limit' in config_data:
                game_state.lap_limit = config_data['lap_limit']
                
            if 'free_parking_fund' in config_data:
                game_state.free_parking_fund = config_data['free_parking_fund']
                
            if 'auction_required' in config_data:
                game_state.auction_required = config_data['auction_required']
                
            if 'turn_timeout' in config_data:
                game_state.turn_timeout = config_data['turn_timeout']
            
            db.session.add(game_state)
            db.session.commit()
            
            self.logger.info("Game configuration updated")
            
            return {
                'success': True,
                'message': 'Game configuration updated'
            }
            
        except Exception as e:
            self.logger.error(f"Error updating game config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_game_history_by_id(self, history_id):
        """Get game history by ID"""
        try:
            history = GameHistory.query.get(history_id)
            
            if not history:
                return {
                    'success': False,
                    'error': 'Game history not found'
                }
            
            winner = Player.query.get(history.winner_id) if history.winner_id else None
            
            return {
                'success': True,
                'history': {
                    'id': history.id,
                    'started_at': history.started_at.isoformat(),
                    'ended_at': history.ended_at.isoformat(),
                    'player_count': history.player_count,
                    'winner': winner.username if winner else None,
                    'end_reason': history.end_reason
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting game history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_game_history(self, limit=10):
        """Get history of all completed games"""
        try:
            histories = GameHistory.query.order_by(GameHistory.ended_at.desc()).limit(limit).all()
            
            history_list = []
            for history in histories:
                winner = Player.query.get(history.winner_id) if history.winner_id else None
                
                history_list.append({
                    'id': history.id,
                    'started_at': history.started_at.isoformat(),
                    'ended_at': history.ended_at.isoformat(),
                    'player_count': history.player_count,
                    'winner': winner.username if winner else None,
                    'end_reason': history.end_reason
                })
            
            return {
                'success': True,
                'histories': history_list
            }
            
        except Exception as e:
            self.logger.error(f"Error getting game histories: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_roll_dice(self, data):
        """Handles the 'roll_dice' socket event from a client."""
        player_id = data.get('playerId') 
        game_id = data.get('gameId', 1) 
        player_sid = request.sid # Get SID for targeted responses

        if not player_id:
             self.logger.warning(f"Received roll_dice event without playerId (SID: {player_sid})")
             self.socketio.emit('game_error', {'error': 'Player ID missing'}, room=player_sid)
             return 

        self.logger.info(f"Received roll_dice request from Player {player_id} (SID: {player_sid}) for Game {game_id}")

        if not self.game_logic:
             self.logger.error("GameLogic not initialized in GameController.")
             self.socketio.emit('game_error', {'error': 'Server configuration error'}, room=player_sid)
             return

        with current_app.app_context():
            try:
                 game_state = GameState.query.get(game_id)
                 if not game_state:
                     self.logger.error(f"Game state {game_id} not found for roll_dice.")
                     self.socketio.emit('game_error', {'error': 'Game not found'}, room=player_sid)
                     return

                 # --- Action Validation --- 
                 # Can only roll if it's your turn AND no other action is pending 
                 # (unless the pending action is specifically 'roll_again' or 'jail_action_prompt')
                 if game_state.current_player_id != player_id:
                     self.socketio.emit('game_error', {'error': 'Not your turn'}, room=player_sid)
                     return
                 
                 player = Player.query.get(player_id) # Fetch player for jail check
                 if not player:
                      self.socketio.emit('game_error', {'error': 'Player not found'}, room=player_sid)
                      return
                 
                 # Allow roll only if no action pending OR if the action is to roll (jail or doubles)
                 is_jail_roll_prompt = game_state.expected_action_type == 'jail_action_prompt'
                 is_doubles_roll_prompt = game_state.expected_action_type == 'roll_again' # Assuming we might set this explicitly
                 
                 if game_state.expected_action_type and not (is_jail_roll_prompt or is_doubles_roll_prompt):
                     self.logger.warning(f"Player {player_id} tried to roll dice, but expected action is '{game_state.expected_action_type}'")
                     self.socketio.emit('game_error', {'error': f'Cannot roll now, must first {game_state.expected_action_type}'}, room=player_sid)
                     return
                 # Allow rolling if in jail, GameLogic handles the specific jail roll logic
                 if not player.in_jail and game_state.expected_action_type == 'jail_action_prompt':
                      self.logger.warning(f"Player {player_id} tried to roll for jail action but is not in jail.")
                      self.socketio.emit('game_error', {'error': 'Cannot perform jail roll, not in jail.'}, room=player_sid)
                      return
                 # --- End Action Validation --- 

                 # Call the core game logic function
                 result = self.game_logic.roll_dice_and_move(player_id, game_id)

                 if not result.get('success'):
                     self.logger.warning(f"roll_dice_and_move failed for Player {player_id}: {result.get('error')}")
                     self.socketio.emit('game_error', {'error': result.get('error', 'Roll failed')}, room=player_sid) 
                     return

                 # --- Process successful roll result --- 
                 # ... (Emit events: dice_rolled, go_salary_collected, player_moved, player_jailed, rent_paid) ...
                 game_state_data = result.get('game_state')
                 landing_action = result.get('landing_action', {})
                 next_action = result.get('next_action', 'end_turn') 

                 # Emit general events
                 self.socketio.emit('dice_rolled', { 'playerId': player_id, 'roll': result.get('dice_roll'), 'doubles': result.get('doubles'), 'inJailAttempt': player.in_jail }, room=game_id)
                 if result.get('passed_go'): self.socketio.emit('go_salary_collected', { 'playerId': player_id, 'amount': self.game_logic.GO_SALARY }, room=game_id)
                 self.socketio.emit('player_moved', { 'playerId': player_id, 'newPosition': result.get('new_position'), 'diceTotal': sum(result.get('dice_roll', [0,0])) }, room=game_id)
                 if result.get('sent_to_jail'): self.socketio.emit('player_jailed', { 'playerId': player_id, 'reason': result.get('message', 'Sent to jail') }, room=game_id)
                 if landing_action.get('action') == 'paid_rent': self.socketio.emit('rent_paid', { 'payerId': player_id, 'ownerId': landing_action.get('owner_id'), 'amount': landing_action.get('rent_amount'), 'propertyId': landing_action.get('property_id') }, room=game_id)
                 
                 # Emit targeted prompts/errors
                 action_type = landing_action.get('action')
                 if action_type == 'insufficient_funds_for_rent':
                      self.socketio.emit('prompt_manage_assets', {'reason': 'rent', 'required': landing_action.get('required'), 'details': landing_action }, room=player_sid)
                 elif action_type == 'buy_or_auction_prompt':
                      self.socketio.emit('prompt_buy_property', landing_action, room=player_sid)
                 elif action_type == 'draw_chance_card' or action_type == 'draw_community_chest_card':
                      self.socketio.emit('action_required', {'action': action_type}, room=player_sid)
                 elif action_type == 'pay_tax':
                       self.socketio.emit('action_required', {'action': 'pay_tax', 'details': landing_action.get('tax_details') }, room=player_sid)
                 # Add prompt for manage_assets_for_jail_fine if needed (though GameLogic returns error currently)
                 elif action_type == 'manage_assets_or_bankrupt': # Generic prompt
                     self.socketio.emit('prompt_manage_assets', {'reason': landing_action.get('reason', 'unknown'), 'required': landing_action.get('required'), 'details': landing_action }, room=player_sid)

                 # Broadcast the overall game state update
                 if game_state_data: # GameLogic now returns state in result
                     self.socketio.emit('game_state_update', game_state_data, room=game_id)
                 else:
                      self.logger.error(f"Game state missing from roll_dice_and_move result for game {game_id}")
                      # Fetch manually as fallback?
                      fallback_state = self.get_game_state(game_id)
                      if fallback_state.get('success'):
                           self.socketio.emit('game_state_update', fallback_state, room=game_id)

                 # Determine next step (end turn, roll again, wait for action)
                 if next_action == 'end_turn':
                      self._internal_end_turn(player_id, game_id) 
                 elif next_action == 'roll_again':
                      # Player needs to send 'roll_dice' again. Update expected state.
                      game_state.expected_action_type = 'roll_again'
                      game_state.expected_action_details = None # No specific details needed
                      db.session.add(game_state)
                      db.session.commit() # Commit the expected state change
                      self.logger.info(f"Player {player_id} rolled doubles, gets another turn.")
                      self.socketio.emit('action_required', {'action': 'roll_again'}, room=player_sid)
                      # Broadcast updated state with the new expected action
                      self.socketio.emit('game_state_update', game_state.to_dict(), room=game_id)
                 else:
                      # Waiting for player action specified by expected_action_type set by GameLogic
                      self.logger.info(f"Waiting for player {player_id} action: {game_state.expected_action_type}")

            except Exception as e:
                 db.session.rollback() 
                 self.logger.error(f"Error during handle_roll_dice for Player {player_id}: {e}", exc_info=True)
                 self.socketio.emit('game_error', {'error': 'An internal server error occurred.'}, room=player_sid)


    def _internal_end_turn(self, player_id, game_id):
        """Internal helper to end turn, find next player, and update state."""
        self.logger.info(f"Attempting to end turn internally for Player {player_id} in Game {game_id}")
        
        try:
            game_state = GameState.query.get(game_id)
            if not game_state:
                self.logger.error(f"Game state {game_id} not found during end turn.")
                return False
            
            if game_state.status != 'active':
                self.logger.warning(f"Cannot end turn for inactive game {game_id}.")
                return False

            current_player_id = game_state.current_player_id
            if current_player_id != player_id:
                self.logger.warning(f"Ending turn for actual current player {current_player_id} instead of requested {player_id}.")
                player_id = current_player_id 

            # --- Reset State for Player Ending Turn --- 
            player_ending_turn = Player.query.get(player_id)
            if player_ending_turn:
                player_ending_turn.consecutive_doubles_count = 0 
                db.session.add(player_ending_turn)

            # --- Clear Expected Action --- 
            self.logger.debug(f"Clearing expected action state for game {game_id} at end of turn.")
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            db.session.add(game_state)

            # --- Find Next Player --- 
            players = Player.query.filter_by(game_id=game_id, in_game=True, is_bankrupt=False).order_by(Player.turn_order).all()
            if not players:
                self.logger.error(f"No active players found in game {game_id}")
                return False
            
            # Find current player's index
            current_index = -1
            for i, player in enumerate(players):
                if player.id == player_id:
                    current_index = i
                    break
                
            if current_index == -1:
                self.logger.warning(f"Current player {player_id} not found in active players list.")
                # Default to the first player
                next_player = players[0] if players else None
            else:
                # Get next player (wrap around to beginning if needed)
                next_index = (current_index + 1) % len(players)
                next_player = players[next_index]
                
                # Check if we've completed a lap (everyone has had a turn)
                if next_index <= current_index:
                    game_state.current_lap += 1
                    self.logger.info(f"Game {game_id}: Advanced to lap {game_state.current_lap}")
                    
                    # Process lap-based effects
                    # Economic phase changes
                    if hasattr(game_state, 'process_economic_cycle'):
                        game_state.process_economic_cycle()
                    
                    # Game mode specific lap effects
                    if hasattr(game_state, 'process_game_mode_lap_effects'):
                        game_state.process_game_mode_lap_effects()

            if not next_player:
                self.logger.warning(f"No valid next player found in game {game_id}. Ending game.")
                self.end_game(reason="no_active_players")
                return True

            # --- Win Condition Checks --- 
            # Check if only one player remains
            active_players_count = Player.query.filter_by(game_id=game_id, in_game=True, is_bankrupt=False).count()
            if active_players_count <= 1:
                self.logger.info(f"Only {active_players_count} player(s) remaining. Ending game.")
                self.end_game(reason="last_player_standing")
                return True
            
            # Check if we've reached the lap limit
            if game_state.lap_limit > 0 and game_state.current_lap > game_state.lap_limit:
                self.logger.info(f"Lap limit {game_state.lap_limit} reached. Ending game.")
                self.end_game(reason="lap_limit_reached")
                return True
            
            # Check if custom game mode has a win condition
            game_mode_controller = self.app_config.get('game_mode_controller')
            if game_mode_controller:
                win_check = game_mode_controller.check_win_condition(game_id)
                if win_check.get('game_over', False):
                    self.logger.info(f"Game mode win condition met: {win_check.get('reason')}. Ending game.")
                    self.end_game(reason=win_check.get('reason', 'game_mode_win_condition'))
                    return True

            # --- Update Game State for Next Turn --- 
            game_state.current_player_id = next_player.id
            game_state.turn_number += 1
            
            # Set expected action for the START of the next player's turn if they are in jail
            if next_player.in_jail:
                game_state.expected_action_type = 'jail_action_prompt'
                game_state.expected_action_details = {'turns_remaining': 3 - next_player.jail_turns}
                self.logger.info(f"Next player {next_player.id} starting turn in jail. Setting expected action.")
            
            # Process team-based turn effects if applicable
            team_controller = self.app_config.get('team_controller')
            if team_controller and hasattr(game_state, 'team_based') and game_state.team_based:
                team_controller.process_team_turn(game_id)
            
            db.session.commit() # Commit all changes
            
            self.logger.info(f"Turn ended for player {player_id}. New turn for player {next_player.id} (Turn: {game_state.turn_number}, Lap: {game_state.current_lap}) Game ID: {game_id}")

            # --- Emit Events --- 
            if self.socketio:
                # Emit turn changed event
                self.socketio.emit('turn_changed', {
                    'previous_player_id': player_id,
                    'next_player_id': next_player.id,
                    'next_player_name': next_player.username,
                    'current_lap': game_state.current_lap,
                    'turn_number': game_state.turn_number,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Emit updated game state
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_state.id)
                
                if not updated_state:
                    updated_state = self.get_game_state()
                    
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)

                # Trigger bot turn if next player is a bot
                if next_player.is_bot:
                    bot_controller = self.app_config.get('bot_controller')
                    if bot_controller:
                        self.logger.info(f"Next player {next_player.id} is a bot. Triggering bot turn.")
                        # Run bot logic in background to avoid blocking
                        self.socketio.start_background_task(bot_controller.take_turn, next_player.id, game_id)
                    else:
                        self.logger.error(f"BotController not found in app_config. Cannot trigger bot turn for {next_player.id}.")
            else:
                self.logger.warning("SocketIO not available in GameController, cannot emit turn events or trigger bot.")
            
            return True

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during _internal_end_turn for Player {player_id}: {e}", exc_info=True)
            return False

    def end_turn(self, data):
        """Handles the 'end_turn' socket event from a client."""
        player_id = data.get('playerId')
        game_id = data.get('gameId', 1)
        player_sid = request.sid 

        self.logger.info(f"Received end_turn request from Player {player_id} (SID: {player_sid}) for Game {game_id}")

        with current_app.app_context(): 
            game_state = GameState.query.get(game_id)
            if not game_state: self.logger.error(f"Game state {game_id} not found."); self.socketio.emit('game_error', {'error': 'Game not found'}, room=player_sid); return
            if game_state.status != 'active': self.logger.warning(f"End turn requested for inactive game {game_id}"); self.socketio.emit('game_error', {'error': 'Game not active'}, room=player_sid); return
                
            if game_state.current_player_id != player_id:
                 self.logger.warning(f"Player {player_id} tried to end turn, but current player is {game_state.current_player_id}")
                 self.socketio.emit('game_error', {'error': 'Not your turn'}, room=player_sid)
                 return
                 
            # Player can only end turn if no action is pending OR if the only pending action is to roll again (doubles)
            if game_state.expected_action_type and game_state.expected_action_type != 'roll_again':
                 self.logger.warning(f"Player {player_id} tried to end turn, but action '{game_state.expected_action_type}' is pending.")
                 self.socketio.emit('game_error', {'error': f'Cannot end turn, must first {game_state.expected_action_type}'}, room=player_sid)
                 return
            # --- End Action Validation --- 

            # Call the internal logic
            self._internal_end_turn(player_id, game_id)

    def _get_player_sid(self, player_id):
         """Helper function to get the SID for a given player ID (Requires tracking SIDs)."""
         # This is a placeholder. You need a mechanism to map player IDs to SIDs.
         # Common approaches:
         # 1. Store SID in Player model (requires update on connect/disconnect)
         # 2. Maintain a dictionary in memory mapping player_id -> sid (managed on connect/disconnect)
         # Example using a simple in-memory dictionary (assumed to be managed elsewhere):
         # player_sids = current_app.config.get('player_sids', {})
         # return player_sids.get(player_id)
         self.logger.warning(f"_get_player_sid not implemented. Cannot send direct prompts to player {player_id}.")
         return None # Placeholder

    def handle_property_purchase(self, data):
        """Handle a player's request to purchase a property they've landed on."""
        self.logger.info(f"Property purchase requested: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property purchase: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot purchase property in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Verify player is the current player
            if game_state.current_player_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to buy property but not current player {game_state.current_player_id}")
                return {'success': False, 'error': 'Not your turn'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify player has landed on this property
            if player.position != property_obj.position:
                self.logger.warning(f"Player {player_id} attempting to buy property at position {property_obj.position} but is at position {player.position}")
                return {'success': False, 'error': 'Not on this property'}
            
            # Verify property is available for purchase
            if property_obj.owner_id is not None:
                self.logger.warning(f"Property {property_id} already owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'Property already owned'}
            
            # Verify property is purchasable (not a special square)
            if property_obj.type not in ['property', 'railroad', 'utility']:
                self.logger.warning(f"Property {property_id} of type {property_obj.type} is not purchasable")
                return {'success': False, 'error': 'Property not purchasable'}
            
            # Verify player has enough money
            if player.money < property_obj.price:
                self.logger.warning(f"Player {player_id} has insufficient funds ({player.money}) to buy property {property_id} ({property_obj.price})")
                return {'success': False, 'error': 'Insufficient funds'}
            
            # Process the purchase
            player.money -= property_obj.price
            property_obj.owner_id = player_id
            
            # Update property group ownership stats for monopoly calculations
            self._update_property_group_stats(player_id, property_obj)
            
            # Save changes
            db.session.add(player)
            db.session.add(property_obj)
            db.session.commit()
            
            self.logger.info(f"Player {player_id} successfully purchased property {property_id} for ${property_obj.price}")
            
            # Emit events
            if self.socketio:
                # Notify about property purchase
                self.socketio.emit('property_purchased', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'price': property_obj.price,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Notify about player money update
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money + property_obj.price,
                    'new_balance': player.money,
                    'change': -property_obj.price,
                    'reason': 'property_purchase'
                }, room=game_id)
                
                # Update game state for all players
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_id)
                
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            # Clear expected action if this was expected
            if game_state.expected_action_type == 'property_decision':
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.add(game_state)
                db.session.commit()
            
            return {'success': True, 'message': 'Property purchased successfully'}
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during property purchase: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during purchase'}

    def _update_property_group_stats(self, player_id, purchased_property):
        """Update property group ownership stats for monopoly calculations."""
        if not purchased_property.group:
            return
        
        # Find all properties in this group
        group_properties = Property.query.filter_by(
            game_id=purchased_property.game_id,
            group=purchased_property.group
        ).all()
        
        # Count how many the player now owns in this group
        player_owned_count = 0
        total_in_group = 0
        
        for prop in group_properties:
            total_in_group += 1
            if prop.owner_id == player_id:
                player_owned_count += 1
        
        # Check if player now has a monopoly on this group
        has_monopoly = (player_owned_count == total_in_group)
        
        if has_monopoly:
            self.logger.info(f"Player {player_id} now has a monopoly on group {purchased_property.group}")
            
            # Update all properties in the group to enable improvements
            for prop in group_properties:
                if prop.owner_id == player_id and prop.type == 'property':
                    prop.can_improve = True
                    db.session.add(prop)
            
            # Emit monopoly event
            if self.socketio:
                player = Player.query.get(player_id)
                self.socketio.emit('monopoly_acquired', {
                    'player_id': player_id,
                    'player_name': player.username if player else 'Unknown',
                    'property_group': purchased_property.group,
                    'group_properties': [p.name for p in group_properties],
                    'timestamp': datetime.now().isoformat()
                }, room=purchased_property.game_id)

    def handle_property_decline(self, data):
        """Handle a player's decision to decline purchasing a property they've landed on."""
        self.logger.info(f"Property purchase declined: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property decline: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot decline property in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Verify player is the current player
            if game_state.current_player_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to decline property but not current player {game_state.current_player_id}")
                return {'success': False, 'error': 'Not your turn'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify property is available for purchase
            if property_obj.owner_id is not None:
                self.logger.warning(f"Property {property_id} already owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'Property already owned'}
            
            # Clear expected action if this was expected
            if game_state.expected_action_type == 'property_decision':
                game_state.expected_action_type = None
                game_state.expected_action_details = None
                db.session.add(game_state)
                db.session.commit()
            
            # Log the property decline
            self.logger.info(f"Player {player_id} declined to purchase property {property_id}")
            
            # Get the auction controller directly from app_config
            auction_controller = current_app.config.get('auction_controller')
            
            # Start the auction through the auction controller
            if auction_controller:
                self.logger.info(f"Starting auction for property {property_id} through auction controller")
                auction_result = auction_controller.start_auction(game_id, property_id)
                
                if auction_result.get('success'):
                    self.logger.info(f"Successfully started auction {auction_result.get('auction_id')} for property {property_id}")
                    return {'success': True, 'message': 'Property declined, auction started', 'auction_id': auction_result.get('auction_id')}
                else:
                    error_msg = auction_result.get('error', 'Unknown error starting auction')
                    self.logger.error(f"Failed to start auction for property {property_id}: {error_msg}")
                    
                    # Even if auction fails, we emit a notification and allow the game to continue
                    if self.socketio:
                        self.socketio.emit('property_declined', {
                            'player_id': player_id,
                            'player_name': player.username,
                            'property_id': property_id,
                            'property_name': property_obj.name,
                            'auction_status': 'failed',
                            'error': error_msg,
                            'timestamp': datetime.now().isoformat()
                        }, room=game_id)
                    
                    return {'success': True, 'message': 'Property declined, but auction failed to start', 'error': error_msg}
            else:
                # If no auction controller is available, simply emit an event and continue the game
                self.logger.warning("No auction controller available to start auction")
                if self.socketio:
                    self.socketio.emit('property_declined', {
                        'player_id': player_id,
                        'player_name': player.username,
                        'property_id': property_id,
                        'property_name': property_obj.name,
                        'auction_status': 'disabled',
                        'timestamp': datetime.now().isoformat()
                    }, room=game_id)
                    
                    self.socketio.emit('notification', {
                        'message': f"{player.username} declined to purchase {property_obj.name}. Auction feature is not available.",
                        'type': 'info'
                    }, room=game_id)
                
                return {'success': True, 'message': 'Property declined, no auction system available'}
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during property decline: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during property decline'}

    def handle_improve_property(self, data):
        """Handle a player's request to improve a property by adding a house or hotel."""
        self.logger.info(f"Property improvement requested: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        improvement_type = data.get('improvement_type', 'house')  # 'house' or 'hotel'
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property improvement: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot improve property in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Verify it's the player's turn (can only improve properties on your turn)
            if game_state.current_player_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to improve property but not current player {game_state.current_player_id}")
                return {'success': False, 'error': 'Not your turn'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify property is owned by the player
            if property_obj.owner_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to improve property owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'You do not own this property'}
            
            # Verify property type allows improvement (only regular properties, not railroads or utilities)
            if property_obj.type != PropertyType.STREET:
                self.logger.warning(f"Property {property_id} of type {property_obj.type} cannot be improved")
                return {'success': False, 'error': 'This property type cannot be improved'}
            
            # Verify player has a monopoly on the property group (can_improve flag should be set)
            if not property_obj.can_improve:
                self.logger.warning(f"Property {property_id} cannot be improved without a monopoly")
                return {'success': False, 'error': 'You need a monopoly to improve this property'}
            
            # Verify property is not mortgaged
            if property_obj.is_mortgaged:
                self.logger.warning(f"Property {property_id} is mortgaged and cannot be improved")
                return {'success': False, 'error': 'Cannot improve a mortgaged property'}
            
            # Check if trying to build a hotel
            cost = 0
            if improvement_type == 'hotel':
                # Verify property already has 4 houses before building a hotel
                if property_obj.houses != 4:
                    self.logger.warning(f"Property {property_id} needs 4 houses before building a hotel")
                    return {'success': False, 'error': 'Need 4 houses before building a hotel'}
                
                cost = property_obj.hotel_cost
                
                # Verify player has enough money
                if player.money < cost:
                    self.logger.warning(f"Player {player_id} has insufficient funds ({player.money}) to build a hotel ({cost})")
                    return {'success': False, 'error': 'Insufficient funds'}
                
                # Process the hotel build
                property_obj.houses = 0
                property_obj.hotels = 1
                
            # Otherwise building a house
            else:
                # Verify property doesn't already have a hotel
                if property_obj.hotels > 0:
                    self.logger.warning(f"Property {property_id} already has a hotel")
                    return {'success': False, 'error': 'Property already has a hotel'}
                
                # Verify property doesn't already have 4 houses
                if property_obj.houses >= 4:
                    self.logger.warning(f"Property {property_id} already has maximum houses (4)")
                    return {'success': False, 'error': 'Property already has maximum houses'}
                
                cost = property_obj.house_cost
                
                # Verify player has enough money
                if player.money < cost:
                    self.logger.warning(f"Player {player_id} has insufficient funds ({player.money}) to build a house ({cost})")
                    return {'success': False, 'error': 'Insufficient funds'}
                
                # Process the house build
                property_obj.houses += 1
            
            # Update player's money
            player.money -= cost
            
            # Update the property's rent based on the new improvement level
            self._update_property_rent(property_obj)
            
            # Save changes
            db.session.add(player)
            db.session.add(property_obj)
            db.session.commit()
            
            self.logger.info(f"Player {player_id} successfully built a {improvement_type} on property {property_id} for ${cost}")
            
            # Emit events
            if self.socketio:
                # Notify about property improvement
                self.socketio.emit('property_improved', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'improvement_type': improvement_type,
                    'houses': property_obj.houses,
                    'hotels': property_obj.hotels,
                    'cost': cost,
                    'new_rent': property_obj.rent,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Notify about player money update
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money + cost,
                    'new_balance': player.money,
                    'change': -cost,
                    'reason': 'property_improvement'
                }, room=game_id)
                
                # Update game state for all players
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_id)
                
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            return {'success': True, 'message': f'{improvement_type.capitalize()} built successfully'}
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during property improvement: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during property improvement'}

    def _update_property_rent(self, property_obj):
        """Update a property's rent based on its improvement level."""
        # For regular properties with houses/hotels
        if property_obj.type == PropertyType.STREET:
            if property_obj.hotels > 0:
                # Set rent to hotel rent
                property_obj.rent = property_obj.rent_hotel
            elif property_obj.houses > 0:
                # Set rent based on number of houses
                if property_obj.houses == 1:
                    property_obj.rent = property_obj.rent_house_1
                elif property_obj.houses == 2:
                    property_obj.rent = property_obj.rent_house_2
                elif property_obj.houses == 3:
                    property_obj.rent = property_obj.rent_house_3
                elif property_obj.houses == 4:
                    property_obj.rent = property_obj.rent_house_4
            else:
                # No improvements, but check if there's a monopoly (double rent)
                group_properties = Property.query.filter_by(
                    game_id=property_obj.game_id,
                    group=property_obj.group
                ).all()
                
                all_owned_by_same_player = True
                for prop in group_properties:
                    if prop.owner_id != property_obj.owner_id:
                        all_owned_by_same_player = False
                        break
                
                if all_owned_by_same_player:
                    # Double the base rent when player has a monopoly
                    property_obj.rent = property_obj.base_rent * 2
                else:
                    # Reset to base rent
                    property_obj.rent = property_obj.base_rent
        
        # For railroads, rent depends on how many railroads the player owns
        elif property_obj.type == PropertyType.RAILROAD:
            railroad_count = Property.query.filter_by(
                game_id=property_obj.game_id,
                type=PropertyType.RAILROAD,
                owner_id=property_obj.owner_id
            ).count()
            
            # Set railroad rent based on ownership count
            if railroad_count == 1:
                property_obj.rent = 25
            elif railroad_count == 2:
                property_obj.rent = 50
            elif railroad_count == 3:
                property_obj.rent = 100
            elif railroad_count == 4:
                property_obj.rent = 200
        
        # For utilities, rent depends on dice roll and utility count
        # This is handled dynamically when rent is collected, not stored on the property

    def handle_special_space(self, data):
        """Handle player landing on or interacting with special spaces like Jail, Free Parking, etc."""
        self.logger.info(f"Special space action requested: {data}")
        
        player_id = data.get('player_id')
        space_position = data.get('position')
        pin = data.get('pin')
        action_type = data.get('action_type')  # e.g., 'pay_jail_fine', 'use_jail_card', etc.
        
        if not all([player_id, space_position is not None]):
            self.logger.error(f"Missing required data for special space action: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Get game state
            game_state = GameState.query.first()
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot process special space in inactive game")
                return {'success': False, 'error': 'Game not active'}
            
            # Verify player is the current player
            if game_state.current_player_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to interact with special space but not current player {game_state.current_player_id}")
                return {'success': False, 'error': 'Not your turn'}
            
            # Verify player PIN
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                self.logger.error(f"Invalid player or PIN for player {player_id}")
                return {'success': False, 'error': 'Invalid player credentials'}
            
            # Get the special space controller from app_config
            special_space_controller = self.app_config.get('special_space_controller')
            if not special_space_controller:
                self.logger.error("Special space controller not available")
                return {'success': False, 'error': 'Special space handling is not available'}
            
            # Handle specific space types
            special_space = SpecialSpace.query.filter_by(position=space_position).first()
            if not special_space:
                self.logger.error(f"No special space found at position {space_position}")
                return {'success': False, 'error': 'Space not found'}
                
            self.logger.info(f"Handling special space: {special_space.name} (Type: {special_space.space_type})")
            
            result = None
            
            # Jail handling (position 10)
            if special_space.space_type == "jail":
                if player.in_jail:
                    # Player is in jail and trying to get out
                    if action_type == 'pay_jail_fine':
                        result = self._handle_pay_jail_fine(player, game_state)
                    elif action_type == 'use_jail_card':
                        result = self._handle_use_jail_card(player, game_state)
                    elif action_type == 'roll_for_doubles':
                        # This is handled separately in the dice roll logic
                        result = {'success': True, 'message': 'Roll attempt processed'}
                    else:
                        result = {'success': False, 'error': 'Invalid jail action'}
                else:
                    # Player is just visiting
                    result = {'success': True, 'message': 'Just visiting jail'}
            
            # Go to jail handling (position 30)
            elif special_space.space_type == "go_to_jail":
                result = special_space_controller.send_to_jail(player_id)
                # Turn should end after going to jail
                if result.get('success'):
                    self.end_turn({'player_id': player_id, 'pin': pin})
            
            # Free parking handling (position 20)
            elif special_space.space_type == "free_parking":
                result = special_space_controller.handle_free_parking(player_id)
            
            # Tax space handling (position 4 and 38)
            elif special_space.space_type == "tax":
                # Check if player has enough money for the tax
                tax_data = json.loads(special_space.action_data) if special_space.action_data else {}
                tax_amount = special_space_controller.tax_handler._calculate_tax_amount(player, tax_data, game_state)
                
                if player.cash < tax_amount:
                    # Player must manage assets or go bankrupt
                    game_state.expected_action_type = 'manage_assets_for_tax'
                    game_state.expected_action_details = json.dumps({
                        'amount': tax_amount,
                        'reason': f'{special_space.name.lower()}_tax',
                        'space_id': special_space.id
                    })
                    
                    db.session.add(game_state)
                    db.session.commit()
                    
                    result = {
                        'success': False,
                        'error': 'Insufficient funds for tax',
                        'required': tax_amount,
                        'current_cash': player.cash
                    }
                else:
                    # Process tax payment through the special space controller
                    result = special_space_controller.tax_handler.process_tax(player_id, special_space.id)
            
            # Chance and Community Chest handling
            elif special_space.space_type in ["chance", "community_chest"]:
                if special_space.space_type == "chance":
                    result = special_space_controller.process_chance_card(player_id)
                else:
                    result = special_space_controller.process_community_chest_card(player_id)
            
            # GO space handling (no special action needed)
            elif special_space.space_type == "go":
                result = {'success': True, 'message': 'Landed on GO'}
            
            else:
                # This shouldn't happen with proper board setup
                result = {'success': False, 'error': f'Unhandled special space type: {special_space.space_type}'}
            
            # Update game state if action was successful
            if result and result.get('success'):
                # Clear expected action if this action resolves it
                if game_state.expected_action_type in ['jail_action_prompt', 'manage_assets_for_tax', 'draw_card']:
                    game_state.expected_action_type = None
                    game_state.expected_action_details = None
                    db.session.add(game_state)
                    db.session.commit()
                    
                # Update game state for all players
                if self.socketio:
                    updated_state = None
                    if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                        updated_state = self.game_logic.get_game_state(game_state.id)
                    
                    if updated_state:
                        self.socketio.emit('game_state_update', updated_state)
            
            return result or {'success': False, 'error': 'Failed to process special space action'}
        
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling special space: {e}", exc_info=True)
            return {'success': False, 'error': f'Internal error handling special space: {str(e)}'}

    def _handle_pay_jail_fine(self, player, game_state):
        """Handle player paying fine to get out of jail."""
        self.logger.info(f"Player {player.id} wants to pay fine to get out of jail")
        
        # Get special space controller
        special_space_controller = self.app_config.get('special_space_controller')
        if not special_space_controller:
            self.logger.error("Special space controller not available")
            return {'success': False, 'error': 'Special space handling is not available'}
        
        # Use the special space controller to handle the payment
        result = special_space_controller.pay_jail_fine(player.id)
        
        # Log the result
        if result.get('success'):
            self.logger.info(f"Player {player.id} successfully paid jail fine")
        else:
            self.logger.warning(f"Player {player.id} failed to pay jail fine: {result.get('error')}")
        
        return result

    def _handle_use_jail_card(self, player, game_state):
        """Handle player using a Get Out of Jail Free card."""
        self.logger.info(f"Player {player.id} wants to use a jail card")
        
        # Get special space controller
        special_space_controller = self.app_config.get('special_space_controller')
        if not special_space_controller:
            self.logger.error("Special space controller not available")
            return {'success': False, 'error': 'Special space handling is not available'}
        
        # Use the special space controller to handle the jail card
        result = special_space_controller.use_jail_card(player.id)
        
        # Log the result
        if result.get('success'):
            self.logger.info(f"Player {player.id} successfully used jail card")
        else:
            self.logger.warning(f"Player {player.id} failed to use jail card: {result.get('error')}")
        
        return result

    def handle_mortgage_property(self, data):
        """Handle a player's request to mortgage a property."""
        self.logger.info(f"Property mortgage requested: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property mortgage: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot mortgage property in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify property is owned by the player
            if property_obj.owner_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to mortgage property owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'You do not own this property'}
            
            # Verify property is not already mortgaged
            if property_obj.is_mortgaged:
                self.logger.warning(f"Property {property_id} is already mortgaged")
                return {'success': False, 'error': 'Property is already mortgaged'}
            
            # Verify property has no buildings (houses or hotels)
            if property_obj.houses > 0 or property_obj.hotels > 0:
                self.logger.warning(f"Cannot mortgage property {property_id} with buildings")
                return {'success': False, 'error': 'Cannot mortgage property with buildings. Sell buildings first.'}
            
            # Process the mortgage
            mortgage_value = property_obj.mortgage_value or property_obj.price // 2
            
            property_obj.is_mortgaged = True
            player.money += mortgage_value
            
            # Save changes
            db.session.add(property_obj)
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {player_id} successfully mortgaged property {property_id} for ${mortgage_value}")
            
            # Emit events
            if self.socketio:
                # Notify about property mortgage
                self.socketio.emit('property_mortgaged', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'mortgage_value': mortgage_value,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Notify about player money update
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money - mortgage_value,
                    'new_balance': player.money,
                    'change': mortgage_value,
                    'reason': 'property_mortgage'
                }, room=game_id)
                
                # Update game state for all players
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_id)
                
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            return {'success': True, 'message': 'Property mortgaged successfully', 'mortgage_value': mortgage_value}
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during property mortgage: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during mortgage'}

    def handle_unmortgage_property(self, data):
        """Handle a player's request to unmortgage a property."""
        self.logger.info(f"Property unmortgage requested: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property unmortgage: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot unmortgage property in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify property is owned by the player
            if property_obj.owner_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to unmortgage property owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'You do not own this property'}
            
            # Verify property is mortgaged
            if not property_obj.is_mortgaged:
                self.logger.warning(f"Property {property_id} is not mortgaged")
                return {'success': False, 'error': 'Property is not mortgaged'}
            
            # Calculate unmortgage cost (mortgage value + 10% interest)
            mortgage_value = property_obj.mortgage_value or property_obj.price // 2
            unmortgage_cost = int(mortgage_value * 1.1)  # 10% interest
            
            # Verify player has enough money
            if player.money < unmortgage_cost:
                self.logger.warning(f"Player {player_id} has insufficient funds ({player.money}) to unmortgage property {property_id} (${unmortgage_cost})")
                return {'success': False, 'error': 'Insufficient funds', 'required': unmortgage_cost, 'current_money': player.money}
            
            # Process the unmortgage
            property_obj.is_mortgaged = False
            player.money -= unmortgage_cost
            
            # Save changes
            db.session.add(property_obj)
            db.session.add(player)
            db.session.commit()
            
            self.logger.info(f"Player {player_id} successfully unmortgaged property {property_id} for ${unmortgage_cost}")
            
            # Emit events
            if self.socketio:
                # Notify about property unmortgage
                self.socketio.emit('property_unmortgaged', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'unmortgage_cost': unmortgage_cost,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Notify about player money update
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money + unmortgage_cost,
                    'new_balance': player.money,
                    'change': -unmortgage_cost,
                    'reason': 'property_unmortgage'
                }, room=game_id)
                
                # Update game state for all players
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_id)
                
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            return {'success': True, 'message': 'Property unmortgaged successfully', 'unmortgage_cost': unmortgage_cost}
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during property unmortgage: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during unmortgage'}

    def handle_sell_improvement(self, data):
        """Handle a player's request to sell an improvement (house or hotel) from a property."""
        self.logger.info(f"Property improvement sale requested: {data}")
        
        player_id = data.get('player_id')
        property_id = data.get('property_id')
        game_id = data.get('game_id')
        improvement_type = data.get('improvement_type', 'house')  # 'house' or 'hotel'
        
        if not all([player_id, property_id, game_id]):
            self.logger.error(f"Missing required data for property improvement sale: {data}")
            return {'success': False, 'error': 'Missing required data'}
        
        try:
            # Verify game is active
            game_state = GameState.query.get(game_id)
            if not game_state or game_state.status != 'active':
                self.logger.warning(f"Cannot sell improvement in inactive game {game_id}")
                return {'success': False, 'error': 'Game not active'}
            
            # Get player and property
            player = Player.query.get(player_id)
            property_obj = Property.query.get(property_id)
            
            if not player or not property_obj:
                self.logger.error(f"Player {player_id} or Property {property_id} not found")
                return {'success': False, 'error': 'Player or property not found'}
            
            # Verify property is owned by the player
            if property_obj.owner_id != player_id:
                self.logger.warning(f"Player {player_id} attempting to sell improvement on property owned by Player {property_obj.owner_id}")
                return {'success': False, 'error': 'You do not own this property'}
            
            # Verify property has improvements that can be sold
            refund_amount = 0
            
            if improvement_type == 'hotel' and property_obj.hotels > 0:
                # Sell a hotel
                property_obj.hotels = 0
                property_obj.houses = 0  # No houses remain after selling a hotel
                refund_amount = int(property_obj.hotel_cost * 0.5)  # Get half value back
                
                # Update improvement level
                property_obj.improvement_level = 0  # Reset to base level
                self.logger.info(f"Player {player_id} sold a hotel on property {property_id} for ${refund_amount}")
                
            elif improvement_type == 'house' and property_obj.houses > 0:
                # Sell a house
                property_obj.houses -= 1
                refund_amount = int(property_obj.house_cost * 0.5)  # Get half value back
                
                # Update improvement level
                if property_obj.improvement_level > 0:
                    property_obj.improvement_level -= 1
                
                self.logger.info(f"Player {player_id} sold a house on property {property_id} for ${refund_amount}")
                
            else:
                self.logger.warning(f"Property {property_id} has no {improvement_type}s to sell")
                return {'success': False, 'error': f'No {improvement_type}s to sell on this property'}
            
            # Update property value after removing improvement
            if property_obj.improvement_level >= 0:
                # Calculate new property value based on improvement level
                result = property_obj.remove_improvement()
                if not result.get('success', False):
                    self.logger.warning(f"Failed to remove improvement: {result.get('reason', 'Unknown error')}")
                    return {'success': False, 'error': result.get('reason', 'Failed to remove improvement')}
            
            # Add refund to player's money
            player.money += refund_amount
            
            # Save changes to database
            db.session.add(property_obj)
            db.session.add(player)
            db.session.commit()
            
            # Update player's credit score (minor positive effect for financial management)
            player.update_credit_score('sell_property', refund_amount, True)
            
            # Emit events
            if self.socketio:
                # Notify about property improvement sale
                self.socketio.emit('property_improvement_sold', {
                    'player_id': player_id,
                    'player_name': player.username,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'improvement_type': improvement_type,
                    'houses': property_obj.houses,
                    'hotels': property_obj.hotels,
                    'refund_amount': refund_amount,
                    'new_rent': property_obj.rent,
                    'timestamp': datetime.now().isoformat()
                }, room=game_id)
                
                # Notify about player money update
                self.socketio.emit('player_money_updated', {
                    'player_id': player_id,
                    'old_balance': player.money - sale_value,
                    'new_balance': player.money,
                    'change': sale_value,
                    'reason': 'improvement_sale'
                }, room=game_id)
                
                # Update game state for all players
                updated_state = None
                if self.game_logic and hasattr(self.game_logic, 'get_game_state'):
                    updated_state = self.game_logic.get_game_state(game_id)
                
                if updated_state:
                    self.socketio.emit('game_state_update', updated_state, room=game_id)
            
            return {
                'success': True, 
                'message': f'{improvement_type.capitalize()} sold successfully',
                'sale_value': sale_value,
                'houses': property_obj.houses,
                'hotels': property_obj.hotels
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during improvement sale: {e}", exc_info=True)
            return {'success': False, 'error': 'Internal error during improvement sale'}

    def reset_game(self, data):
        """Reset the game state."""
        self.logger.info(f"Game reset requested: {data}")
        
        try:
            admin_pin = data.get('admin_pin')
            
            # Verify admin pin
            if not admin_pin or admin_pin != self.app_config.get('ADMIN_KEY'):
                self.logger.warning(f"Invalid admin pin provided for game reset")
                return {'success': False, 'error': 'Invalid admin credentials'}
            
            # Get game state
            game_state = GameState.query.first()
            if not game_state:
                self.logger.error(f"No game state found")
                return {'success': False, 'error': 'Game state not found'}
            
            # Reset game state
            game_state.status = 'setup'
            game_state.current_player_id = None
            game_state.start_time = None
            game_state.started_at = None  # Explicitly reset started_at timestamp
            game_state.ended_at = None    # Explicitly reset ended_at timestamp
            game_state.current_lap = 0
            game_state.expected_action_type = None
            game_state.expected_action_details = None
            
            # Reset free parking fund
            game_state.free_parking_amount = 0
            
            db.session.add(game_state)
            
            # Reset all players still in game
            players = Player.query.filter_by(in_game=True).all()
            for player in players:
                player.position = 0
                player.cash = self._get_starting_cash()
                player.in_jail = False
                player.jail_turns = 0
                
                # Reset player's properties
                properties = Property.query.filter_by(owner_id=player.id).all()
                for prop in properties:
                    prop.owner_id = None
                    prop.is_mortgaged = False
                    prop.houses = 0
                    prop.hotel = False
                    db.session.add(prop)
                
                db.session.add(player)
            
            # Reinitialize board elements (special spaces and cards)
            self._initialize_board_elements()
            
            db.session.commit()
            
            # Emit game reset event
            if self.socketio:
                self.socketio.emit('game_reset', {
                    'admin_id': data.get('admin_id'),
                    'timestamp': datetime.now().isoformat()
                })
            
            return {'success': True, 'message': 'Game reset successfully'}
        
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error resetting game: {e}", exc_info=True)
            return {'success': False, 'error': f'Failed to reset game: {str(e)}'}

    # Make sure to register the handlers in app.py or wherever socketio events are defined:
    # socketio.on_event('roll_dice', game_controller.handle_roll_dice)
    # socketio.on_event('end_turn', game_controller.end_turn)
    # socketio.on_event('property_purchase', game_controller.handle_property_purchase)
    # socketio.on_event('property_decline', game_controller.handle_property_decline)
    # socketio.on_event('improve_property', game_controller.handle_improve_property)
    # socketio.on_event('sell_improvement', game_controller.handle_sell_improvement)
    # socketio.on_event('mortgage_property', game_controller.handle_mortgage_property)
    # socketio.on_event('unmortgage_property', game_controller.handle_unmortgage_property)
    # socketio.on_event('special_space_action', game_controller.handle_special_space)