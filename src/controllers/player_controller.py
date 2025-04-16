import logging
from flask import jsonify
from src.models.player import Player
from src.models import db

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