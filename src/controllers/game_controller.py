import logging
from datetime import datetime
from flask import request, current_app # Added current_app for easier access

from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property, PropertyType
from src.models.transaction import Transaction
from src.models.game_history import GameHistory
from src.models.game_mode import GameMode
from src.controllers.team_controller import TeamController
from src.controllers.game_mode_controller import GameModeController
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
        # Delete existing properties for this game ID first
        try:
            num_deleted = Property.query.filter_by(game_id=game_id).delete()
            db.session.commit() # Commit the deletion
            if num_deleted > 0:
                self.logger.info(f"Deleted {num_deleted} existing properties for game_id {game_id}.")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting existing properties for game {game_id}: {e}", exc_info=True)
            raise # Re-raise the exception to prevent potentially inconsistent state

        self.logger.info(f"Initializing standard properties for game_id {game_id}...")
        
        # Standard Property Data (Simplified - rents need defining properly)
        # TODO: Move this data to a configuration file (e.g., JSON) for better management
        properties_data = [
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

    def create_new_game(self, difficulty='normal', lap_limit=0, free_parking_fund=True, 
                         auction_required=True, turn_timeout=60):
        """Create a new game with specified settings"""
        try:
            game_state = self.app_config.get('game_state_instance') or GameState.query.first()
            if not game_state:
                 self.logger.error("Failed to get or create GameState instance.")
                 return {'success': False, 'error': 'Game state initialization failed.'}
                 
            game_state.reset()
            
            game_state.difficulty = difficulty
            game_state.lap_limit = lap_limit
            game_state.free_parking_fund = free_parking_fund
            game_state.auction_required = auction_required
            game_state.turn_timeout = turn_timeout
            game_state.started_at = None
            game_state.ended_at = None
            game_state.status = 'setup'
            
            # Reset all bots by setting them to not in game
            bots = Player.query.filter_by(is_bot=True).all()
            for bot in bots:
                bot.in_game = False
                
            # Clear the active_bots dictionary from bot_controller if it exists
            from src.controllers.bot_controller import active_bots
            active_bots.clear()
            self.logger.info(f"Cleared {len(bots)} bots during game reset")
            
            db.session.add(game_state)
            db.session.commit()
            
            self.logger.info(f"New game created with difficulty {difficulty}")
            
            # Initialize properties for this new game
            self._initialize_properties(game_state.game_id)
            
            return {
                'success': True,
                'game_id': game_state.game_id,
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
    
    def start_game(self):
        """Start the game"""
        try:
            game_state = GameState.get_instance()
            
            if game_state.status != 'setup':
                return {
                    'success': False,
                    'error': 'Game is not in setup phase'
                }
            
            players = Player.query.filter_by(in_game=True).all()
            if len(players) < 2:
                return {
                    'success': False,
                    'error': 'At least 2 players required to start'
                }
            
            game_state.status = 'active'
            game_state.started_at = datetime.now()
            game_state.current_player_id = players[0].id
            game_state.current_lap = 1
            
            db.session.add(game_state)
            db.session.commit()
            
            self.logger.info("Game started")
            
            # Emit initial game state after starting
            if self.socketio:
                initial_state = self.get_game_state() # Get the full state
                if initial_state.get('success'):
                     self.socketio.emit('game_state_update', initial_state, room=game_state.game_id)
                     self.logger.info(f"Broadcasted initial game_state_update to room {game_state.game_id}")
                else:
                     self.logger.error(f"Failed to get initial game state after starting game {game_state.game_id}")
            
            return {
                'success': True,
                'message': 'Game started',
                'current_player': players[0].username
            }
            
        except Exception as e:
            self.logger.error(f"Error starting game: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
            
            result = {
                'success': True,
                'game_id': game_state.game_id,
                'status': game_state.status,
                'difficulty': game_state.difficulty,
                'current_lap': game_state.current_lap,
                'started_at': game_state.started_at.isoformat() if game_state.started_at else None,
                'ended_at': game_state.ended_at.isoformat() if game_state.ended_at else None
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
             if not game_state: return # Error logged before call
             if game_state.status != 'active': return # Error logged before call

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
             db.session.add(game_state) # Add game state changes to session

             # --- Find Next Player --- 
             player_order_ids = [int(pid) for pid in game_state.player_order.split(',') if pid]
             if not player_order_ids: self.logger.error(f"Player order is empty for game {game_id}. Cannot advance turn."); return
             try: current_index = player_order_ids.index(player_id) 
             except ValueError: self.logger.warning(f"Current player {player_id} not found in order {player_order_ids}. Resetting."); current_index = -1
             next_player_id = None; next_player_obj = None; attempts = 0; num_players = len(player_order_ids); start_index = current_index + 1
             while attempts < num_players:
                 check_index = (start_index + attempts) % num_players
                 potential_player_id = player_order_ids[check_index]
                 # Eager load properties for potential winner check later if needed
                 potential_player = Player.query.filter_by(id=potential_player_id, game_id=game_id, in_game=True, is_bankrupt=False).first()
                 if potential_player: 
                     next_player_id = potential_player_id; next_player_obj = potential_player
                     if check_index <= current_index and current_index != -1: 
                          game_state.current_lap += 1
                          self.logger.info(f"Game {game_id}: Advanced to lap {game_state.current_lap}")
                          # TODO: Process lap-based effects (economy, etc.)
                          # game_state.process_economic_cycle() # Maybe call here?
                     break
                 attempts += 1
             if next_player_id is None: 
                  self.logger.warning(f"Could not find any valid next player in game {game_id}. Ending game."); self.end_game(reason="no_active_players"); return

             # --- Win Condition Checks --- 
             active_players_count = Player.query.filter_by(game_id=game_id, in_game=True, is_bankrupt=False).count()
             if active_players_count <= 1: self.logger.info(f"Only {active_players_count} player(s) remaining. Ending game."); self.end_game(reason="last_player_standing"); return
             if game_state.lap_limit > 0 and game_state.current_lap > game_state.lap_limit: self.logger.info(f"Lap limit reached. Ending game."); self.end_game(reason="lap_limit_reached"); return

             # --- Update Game State for Next Turn --- 
             game_state.current_player_id = next_player_id
             game_state.turn_number += 1
             
             # Set expected action for the START of the next player's turn if they are in jail
             if next_player_obj and next_player_obj.in_jail:
                 game_state.expected_action_type = 'jail_action_prompt'
                 game_state.expected_action_details = {'turns_remaining': 3 - next_player_obj.jail_turns}
                 self.logger.info(f"Next player {next_player_id} starting turn in jail. Setting expected action.")
             # Else, expected action remains None (cleared earlier)
             
             db.session.commit() # Commit all changes (player doubles, expected action, game state)
             
             self.logger.info(f"Turn ended for player {player_id}. New turn for player {next_player_id} (Turn: {game_state.turn_number}, Lap: {game_state.current_lap}) Game ID: {game_id}")

             # --- Emit Events --- 
             if self.socketio:
                 self.socketio.emit('turn_changed', { 'next_player_id': next_player_id, 'next_player_name': next_player_obj.username if next_player_obj else 'Unknown', 'current_lap': game_state.current_lap, 'turn_number': game_state.turn_number, 'timestamp': datetime.now().isoformat() }, room=game_id)
                 updated_state_data = self.game_logic.get_game_state(game_id) # Get state *after* commit
                 if updated_state_data:
                      self.socketio.emit('game_state_update', updated_state_data, room=game_id)
                 else:
                      self.logger.error(f"GameLogic.get_game_state failed for {game_id} after turn end.")

                 # --- Trigger Bot Turn ---
                 if next_player_obj and next_player_obj.is_bot:
                      bot_controller = self.app_config.get('bot_controller')
                      if bot_controller:
                           self.logger.info(f"Next player {next_player_id} is a bot. Triggering bot turn.")
                           # Run bot logic in background to avoid blocking event handler
                           self.socketio.start_background_task(bot_controller.take_turn, next_player_id, game_id)
                      else:
                           self.logger.error(f"BotController not found in app_config. Cannot trigger bot turn for {next_player_id}.")
             else:
                 self.logger.warning("SocketIO not available in GameController, cannot emit turn events or trigger bot.")

         except Exception as e:
             db.session.rollback()
             self.logger.error(f"Error during _internal_end_turn for Player {player_id}: {e}", exc_info=True)
             # Maybe emit a general error to the game room? 
             # self.socketio.emit('game_error', {'error': 'Internal error during turn transition.'}, room=game_id)

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

    # Make sure to register the handlers in app.py or wherever socketio events are defined:
    # socketio.on_event('roll_dice', game_controller.handle_roll_dice)
    # socketio.on_event('end_turn', game_controller.end_turn)