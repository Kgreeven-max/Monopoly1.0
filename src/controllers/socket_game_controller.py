"""
Clean WebSocket Game Controller
Single source of truth for all game state communication
"""

from flask_socketio import emit, join_room, leave_room
from flask import request, current_app
import logging
from datetime import datetime
from src.models import db
from src.models.player import Player
from src.models.game_state import GameState
from src.models.property import Property

logger = logging.getLogger(__name__)


class SocketGameController:
    """Clean socket controller with single state management"""
    
    def __init__(self, socketio_instance, app_config):
        self.socketio = socketio_instance
        self.app_config = app_config
        self.game_controller = app_config.get('game_controller')
        self.game_logic = app_config.get('game_logic')
        
    def build_complete_game_state(self, game_id=None):
        """
        Build complete game state - single source of truth
        This is THE function that defines our game state structure
        """
        try:
            # Get active game
            if game_id:
                game_state = GameState.query.filter_by(game_id=game_id).first()
            else:
                # Find most recent active game
                game_state = GameState.query.filter(
                    GameState.status.in_(['In Progress', 'setup', 'Setup', 'Waiting', 'active', 'running'])
                ).order_by(GameState.id.desc()).first()
                
            if not game_state:
                logger.warning("No active game found")
                return None
                
            # Get all players in the game with their properties eagerly loaded
            from sqlalchemy.orm import selectinload
            players = Player.query.filter_by(in_game=True).options(
                selectinload(Player.properties)
            ).all()
            
            # Get all properties
            properties = Property.query.all()
            
            # Build player data
            player_list = []
            for player in players:
                player_data = {
                    'id': str(player.id),
                    'name': player.username or f'Player {player.id}',
                    'money': player.money,
                    'position': player.position or 0,
                    'properties': [p.position for p in player.properties],
                    'token': getattr(player, 'token', None) or 'car',
                    'color': getattr(player, 'color', None) or '#999999',
                    'isBot': player.is_bot,
                    'isBankrupt': player.is_bankrupt,
                    'isInJail': player.in_jail,
                    'jailTurns': player.jail_turns,
                    'getOutOfJailCards': player.get_out_of_jail_cards,
                    'netWorth': player.calculate_net_worth(),
                    'isCurrentPlayer': str(player.id) == str(game_state.current_player_id) if game_state.current_player_id else False
                }
                player_list.append(player_data)
            
            # Build property data
            property_list = []
            for prop in properties:
                property_data = {
                    'id': prop.position,
                    'name': prop.name,
                    'type': 'property' if prop.price else 'special',
                    'price': prop.price,
                    'owner': str(prop.owner_id) if prop.owner_id else None,
                    'houses': prop.houses,
                    'hasHotel': prop.hotel,
                    'isMortgaged': prop.is_mortgaged,
                    'rent': prop.rent,
                    'group': prop.color_group
                }
                property_list.append(property_data)
            
            # Build complete state
            complete_state = {
                'gameId': game_state.game_id,
                'status': game_state.status,
                'round': game_state.turn_number,
                'currentPlayer': {
                    'id': str(game_state.current_player_id) if game_state.current_player_id else None,
                    'expectedAction': game_state.expected_action_type
                },
                'players': player_list,
                'properties': property_list,
                'communityFund': game_state.community_fund,
                'lastRoll': None,  # TODO: Add last_dice_roll field to GameState model if needed
                'timestamp': datetime.now().isoformat()
            }
            
            return complete_state
            
        except Exception as e:
            logger.error(f"Error building game state: {e}", exc_info=True)
            return None
    
    def emit_game_state(self, room=None):
        """Emit complete game state to room or all"""
        state = self.build_complete_game_state()
        if state:
            if room:
                self.socketio.emit('game_state', state, room=room)
            else:
                # Find game room and emit
                game_state = GameState.query.filter(
                    GameState.status.in_(['In Progress', 'setup', 'Setup', 'Waiting', 'active', 'running'])
                ).first()
                if game_state:
                    self.socketio.emit('game_state', state, room=game_state.game_id)
            logger.info(f"Emitted game state to room: {room or 'game room'}")
    
    def register_handlers(self):
        """Register clean socket event handlers"""
        
        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            """Clean authentication - immediately sends game state"""
            sid = request.sid
            mode = data.get('mode', 'player')
            
            logger.info(f"[Auth] {mode} authentication from {sid}")
            
            if mode == 'display':
                # Display/board authentication
                game_state = self.build_complete_game_state()
                if game_state:
                    # Join game room
                    game = GameState.query.filter(
                        GameState.status.in_(['In Progress', 'setup', 'Setup', 'Waiting', 'active', 'running'])
                    ).first()
                    if game:
                        join_room(game.game_id)
                        logger.info(f"[Auth] Display joined room {game.game_id}")
                    
                    # Send immediate game state
                    emit('game_state', game_state)
                    emit('auth_success', {'mode': 'display', 'gameState': game_state})
                else:
                    emit('auth_error', {'error': 'No active game'})
                    
            elif mode == 'player':
                # Player authentication
                player_id = data.get('playerId')
                pin = data.get('pin')
                
                player = Player.query.get(player_id) if player_id else None
                if player and player.pin == pin:
                    # Join player room and game room
                    join_room(f'player_{player_id}')
                    game = GameState.query.filter(
                        GameState.status.in_(['In Progress', 'setup', 'Setup', 'Waiting', 'active', 'running'])
                    ).first()
                    if game:
                        join_room(game.game_id)
                    
                    # Send game state
                    game_state = self.build_complete_game_state()
                    if game_state:
                        emit('game_state', game_state)
                    emit('auth_success', {'mode': 'player', 'playerId': player_id})
                else:
                    emit('auth_error', {'error': 'Invalid credentials'})
        
        @self.socketio.on('request_state')
        def handle_request_state(data=None):
            """Request current game state"""
            sid = request.sid
            logger.info(f"[State] State request from {sid}")
            
            game_state = self.build_complete_game_state()
            if game_state:
                emit('game_state', game_state)
            else:
                emit('state_error', {'error': 'No game state available'})
        
        @self.socketio.on('player_action')
        def handle_player_action(data):
            """Unified player action handler"""
            sid = request.sid
            action_type = data.get('type')
            player_id = data.get('playerId')
            action_data = data.get('data', {})
            
            logger.info(f"[Action] {action_type} from player {player_id}")
            
            # Route to appropriate handler
            if action_type == 'roll_dice':
                result = self.handle_roll_dice(player_id)
            elif action_type == 'end_turn':
                result = self.handle_end_turn(player_id)
            elif action_type == 'buy_property':
                result = self.handle_buy_property(player_id, action_data)
            # Add more action types as needed
            else:
                result = {'success': False, 'error': f'Unknown action: {action_type}'}
            
            # Always emit updated game state after any action
            if result.get('success'):
                self.emit_game_state()
                
                # Emit specific animation events if needed
                if action_type == 'roll_dice' and 'movement' in result:
                    self.socketio.emit('animate_movement', {
                        'playerId': player_id,
                        'from': result['movement']['from'],
                        'to': result['movement']['to'],
                        'path': result['movement']['path']
                    }, room=GameState.query.first().game_id)
            else:
                emit('action_error', result)
    
    def handle_roll_dice(self, player_id):
        """Handle dice roll action"""
        if self.game_logic:
            result = self.game_logic.roll_dice_and_move(player_id)
            return result
        return {'success': False, 'error': 'Game logic not available'}
    
    def handle_end_turn(self, player_id):
        """Handle end turn action"""
        if self.game_controller:
            result = self.game_controller.end_turn(player_id)
            return result
        return {'success': False, 'error': 'Game controller not available'}
    
    def handle_buy_property(self, player_id, data):
        """Handle buy property action"""
        property_id = data.get('propertyId')
        # Implementation depends on your property controller
        return {'success': True}  # Placeholder


def register_clean_socket_handlers(socketio, app_config):
    """Register the clean socket handlers"""
    controller = SocketGameController(socketio, app_config)
    app_config['socket_game_controller'] = controller
    controller.register_handlers()
    logger.info("Clean socket game handlers registered")
    return controller