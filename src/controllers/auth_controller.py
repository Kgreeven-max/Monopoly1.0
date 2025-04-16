import logging
from src.models import db
from src.models.player import Player
from src.models.game import Game # Import Game model
# TODO: Import password hashing library (e.g., werkzeug.security or passlib)
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AuthController:
    """Handles player authentication (registration, login)."""

    def __init__(self):
        # Doesn't strictly need dependencies for basic registration yet
        pass

    def register_player(self, username, pin):
        """Registers a new player."""
        logger.info(f"Attempting registration for username: {username}")
        try:
            # Basic validation
            if not username or len(username) < 3:
                logger.warning("Registration failed: Invalid username.")
                return {'success': False, 'error': 'Username must be at least 3 characters'}
            if not pin or len(pin) < 4:
                logger.warning("Registration failed: Invalid PIN.")
                return {'success': False, 'error': 'PIN must be at least 4 characters'}

            # Check if username already exists
            existing_player = Player.query.filter_by(username=username).first()
            if existing_player:
                logger.warning(f"Registration failed: Username '{username}' already exists.")
                return {'success': False, 'error': 'Username already taken'}

            # --- Find or Create Default Game --- 
            # For now, assume we use game ID 1. Create if it doesn't exist.
            game_id_to_use = 1
            default_game = Game.query.get(game_id_to_use)
            if not default_game:
                logger.info(f"Default game (ID: {game_id_to_use}) not found. Creating it.")
                default_game = Game(id=game_id_to_use, status='Waiting')
                db.session.add(default_game)
                # Commit the game creation separately or rely on the later commit?
                # Committing separately is safer if game creation could fail.
                try:
                    db.session.commit()
                    logger.info(f"Created default game with ID: {game_id_to_use}")
                except Exception as game_err:
                    db.session.rollback()
                    logger.error(f"Failed to create default game: {game_err}", exc_info=True)
                    return {'success': False, 'error': 'Failed to initialize game.'}
            # --- End Find or Create Default Game ---

            # TODO: Hash the PIN before storing
            # hashed_pin = generate_password_hash(pin)
            hashed_pin = pin # Placeholder - Store plain text for now

            # Create new player and assign game_id
            new_player = Player(username=username, pin=hashed_pin, game_id=default_game.id)
            
            # Add player to database
            db.session.add(new_player)
            # Commit player and potentially the game if not committed above
            db.session.commit()

            logger.info(f"Successfully registered player '{username}' with ID {new_player.id} in Game {default_game.id}")
            return {
                'success': True,
                'message': 'Registration successful',
                'player_id': new_player.id
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration for {username}: {e}", exc_info=True)
            return {'success': False, 'error': 'An internal error occurred during registration.'}

    def login_player(self, identifier: str, pin: str) -> Dict[str, Any]:
        """Authenticates a player based on username/ID and PIN (plain text)."""
        logger.info(f"Attempting login for identifier: {identifier}")
        
        # Determine if identifier is numeric (likely ID) or string (username)
        is_id = identifier.isdigit()
        
        try:
            if is_id:
                player = Player.query.get(int(identifier))
            else:
                player = Player.query.filter_by(username=identifier).first()

            if player is None:
                logger.warning(f"Login failed: Player not found for identifier {identifier}.")
                return {'success': False, 'error': 'Player not found'}
            
            # --- WARNING: Plain text PIN comparison (skipped hashing) --- 
            if player.pin == pin: 
                # Login successful
                # TODO: Implement session management (e.g., JWT, Flask-Login)
                return {'success': True, 'player_id': player.id, 'username': player.username}
            else:
                logger.warning(f"Login failed: Invalid PIN for identifier {identifier} (Player ID: {player.id})")
                return {'success': False, 'error': 'Invalid PIN'}
                
        except Exception as e:
            logger.error(f"Database error during login attempt for {identifier}: {e}")
            return {'success': False, 'error': 'Database error during login.'}

    # TODO: Add login_player method 