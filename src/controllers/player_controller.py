import logging
from flask import jsonify
from src.models.player import Player
from src.models import db
from flask import current_app

logger = logging.getLogger(__name__)

class PlayerController:
    """Handles player actions and state management."""

    def __init__(self, db_session):
        self.db = db_session # Pass the db session or SQLAlchemy instance

    def _authenticate_player(self, player_id, pin) -> Player | None:
        """Helper method to authenticate player by ID and PIN."""
        player = Player.query.get(player_id)
        if not player:
            logger.warning(f"Authentication failed: Player ID {player_id} not found.")
            return None
        if not player.verify_pin(pin):
            logger.warning(f"Authentication failed: Invalid PIN for Player ID {player_id}.")
            return None
        return player

    def roll_dice(self, player_id, pin):
        """Placeholder for rolling dice."""
        player = self._authenticate_player(player_id, pin)
        if not player:
            return {'success': False, 'error': 'Authentication failed'}

        # TODO: Implement dice rolling logic (interact with Dice model/service?)
        logger.info(f"Player {player_id} requested dice roll.")
        # Placeholder response
        return {'success': True, 'message': 'Dice rolled (logic pending).', 'dice1': 0, 'dice2': 0, 'total': 0}

    def end_turn(self, player_id, pin):
        """Placeholder for ending a player's turn."""
        player = self._authenticate_player(player_id, pin)
        if not player:
            return {'success': False, 'error': 'Authentication failed'}

        # TODO: Implement turn ending logic (update GameState, notify next player?)
        logger.info(f"Player {player_id} requested end turn.")
        # Placeholder response
        return {'success': True, 'message': 'Turn ended (logic pending).'}

    def report_income(self, player_id, pin, income):
        """Placeholder for reporting income (e.g., passing GO)."""
        player = self._authenticate_player(player_id, pin)
        if not player:
            return {'success': False, 'error': 'Authentication failed'}

        # TODO: Implement income reporting logic (update player cash, create transaction)
        logger.info(f"Player {player_id} reported income: {income}. Logic pending.")
        # Placeholder response
        return {'success': True, 'message': f'Income {income} reported (logic pending).'}

    def handle_jail_action(self, player_id, pin, action):
        """Placeholder for handling actions while in jail."""
        player = self._authenticate_player(player_id, pin)
        if not player:
            return {'success': False, 'error': 'Authentication failed'}

        # TODO: Implement jail action logic based on 'action' ('pay', 'card', 'roll')
        logger.info(f"Player {player_id} requested jail action: {action}. Logic pending.")
        # Placeholder response
        return {'success': True, 'message': f'Jail action {action} requested (logic pending).'}

    def get_player_status(self, player_id: int):
        """Fetches basic status information for a given player ID."""
        logger.info(f"Fetching status for player ID: {player_id}")
        try:
            player = self.db.session.get(Player, player_id)
            
            if player is None:
                logger.warning(f"Player status request failed: Player ID {player_id} not found.")
                return {'success': False, 'error': 'Player not found'}, 404

            # Return relevant player data (customize as needed)
            player_data = {
                'id': player.id,
                'username': player.username,
                'money': player.money,
                'position': player.position,
                'in_jail': player.in_jail,
                # Add other relevant fields: properties, get_out_of_jail_cards, etc.
            }
            logger.debug(f"Player status found for {player_id}: {player_data}")
            return {'success': True, 'player_status': player_data}, 200

        except Exception as e:
            logger.error(f"Error fetching status for player {player_id}: {e}")
            return {'success': False, 'error': 'Internal server error fetching player status.'}, 500

    def get_player_properties(self, player_id, pin):
        """Placeholder for getting player properties."""
        player = self._authenticate_player(player_id, pin)
        if not player:
            return {'success': False, 'error': 'Authentication failed'}

        # TODO: Fetch and return player's properties
        properties = player.get_properties() # Assuming Player model has this method
        logger.info(f"Player {player_id} requested properties.")
        # Placeholder response
        return {'success': True, 'properties': [prop.to_dict() for prop in properties]}
        
    def handle_bankruptcy(self, player_id, pin):
        """
        Handle player bankruptcy by calling the FinanceController's declare_bankruptcy method
        and updating game state.
        
        Args:
            player_id (int): The ID of the player declaring bankruptcy
            pin (str): The player's PIN for authentication
            
        Returns:
            dict: A dictionary with the results of the bankruptcy process
        """
        logger.info(f"Player {player_id} requesting bankruptcy declaration")
        
        # Validate player credentials
        player = self._authenticate_player(player_id, pin)
        if not player:
            logger.warning(f"Bankruptcy authentication failed for player {player_id}")
            return {'success': False, 'error': 'Authentication failed'}
        
        # Get finance controller from app config
        finance_controller = current_app.config.get('finance_controller')
        if not finance_controller:
            logger.error("Finance controller not found in app config")
            return {'success': False, 'error': 'Server configuration error'}
        
        # Call finance controller to declare bankruptcy
        result = finance_controller.declare_bankruptcy(player_id, pin)
        
        if result.get('success'):
            logger.info(f"Player {player_id} successfully declared bankruptcy. Properties lost: {result.get('properties_lost', 0)}")
            
            # Get game controller to update game state
            game_controller = current_app.config.get('game_controller')
            if game_controller:
                # Check if the player can continue playing
                game_state = GameState.query.filter_by(current_player_id=player_id).first()
                if game_state:
                    # Set expected action to end turn
                    game_state.expected_actions = [{
                        "player_id": player_id,
                        "action": "end_turn"
                    }]
                    self.db.session.commit()
                    logger.info(f"Updated expected actions to end_turn for bankrupt player {player_id}")
            
            # Update player state to reflect bankruptcy in the UI
            player_data = {
                'id': player.id,
                'username': player.username,
                'bankrupt': True,
                'bankruptcy_count': player.bankruptcy_count,
                'credit_score': player.credit_score
            }
            
            # Emit bankruptcy event for real-time UI updates if SocketIO available
            socketio = current_app.config.get('socketio')
            if socketio:
                socketio.emit('player_updated', {
                    'player': player_data
                })
            
            return {
                'success': True,
                'player': player_data,
                'message': 'Bankruptcy processed successfully',
                'debt_forgiven': result.get('total_debt_forgiven', 0),
                'properties_lost': result.get('properties_lost', 0),
                'new_balance': result.get('new_cash_balance', 0)
            }
        else:
            logger.warning(f"Bankruptcy declaration failed for player {player_id}: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'error': result.get('error', 'Failed to process bankruptcy')
            } 