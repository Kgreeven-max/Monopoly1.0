import logging
from flask import jsonify, current_app
from src.models import db
from src.models.game_state import GameState
from src.models.player import Player
from src.models.property import Property
from src.models.finance.loan import Loan # Needed for player details

logger = logging.getLogger(__name__)

class AdminController:
    """Controller for handling administrative actions"""

    def get_admin_game_status(self):
        """Retrieves the overall game status for the admin dashboard."""
        try:
            game_state = GameState.get_instance()
            if not game_state:
                return {"success": False, "error": "Game state not initialized"}

            players = Player.query.all()
            properties = Property.query.all()

            return {
                "success": True,
                "game_state": game_state.to_dict(),
                "player_count": len(players),
                "property_count": len(properties),
                "active_players": sum(1 for p in players if p.in_game),
                "bank_owned_properties": sum(1 for p in properties if not p.owner_id)
            }
        except Exception as e:
            logger.error(f"Error getting admin game status: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve admin game status"}

    def get_admin_player_details(self, player_id):
        """Retrieves detailed information about a specific player for admin view."""
        try:
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}

            # Assuming relationships are set up correctly (e.g., player.properties, player.loans)
            # Ensure Loan model is imported if needed for player.loans relationship
            return {
                "success": True,
                "player": player.to_dict(),
                "properties": [p.to_dict() for p in player.properties],
                "loans": [l.to_dict() for l in player.loans],
                "net_worth": player.calculate_net_worth()
            }
        except Exception as e:
            logger.error(f"Error getting admin player details for ID {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to retrieve player details"}

    def reset_game(self):
        """Resets the game by creating a new game through the GameController."""
        try:
            # Get GameController from app_config
            game_controller = current_app.config.get('game_controller')
            if not game_controller:
                logger.error("GameController not found in app config")
                return {"success": False, "error": "Game controller not initialized"}

            # Use GameController to create a new game with default settings
            result = game_controller.create_new_game()
            
            if result.get('success'):
                logger.info(f"Game reset successfully. New game ID: {result.get('game_id')}")
                return result
            else:
                logger.error(f"Failed to reset game: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error resetting game: {e}", exc_info=True)
            return {"success": False, "error": f"Failed to reset game: {str(e)}"}

    # --- Placeholder methods for actions previously defined in routes ---
    # These would need proper implementation if used
    
    def modify_player_cash(self, player_id, amount, reason):
        logger.warning("AdminController.modify_player_cash not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}

    def transfer_property(self, property_id, from_player_id, to_player_id, reason):
        logger.warning("AdminController.transfer_property not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}

    def trigger_player_audit(self, player_id):
        logger.warning("AdminController.trigger_player_audit not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}

    def add_bot_player(self, bot_name, bot_type):
        logger.warning("AdminController.add_bot_player not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}

    def modify_game_state(self, state_changes, reason):
        logger.warning("AdminController.modify_game_state not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}
        
    def get_system_status(self):
        logger.warning("AdminController.get_system_status not fully implemented.")
        # TODO: Implement logic from original route
        return {"success": False, "error": "Not Implemented"}

    def remove_player(self, player_id, handle_properties='bank', reason='Admin removal'):
        """
        Remove a player from the game.
        
        Args:
            player_id: ID of the player to remove
            handle_properties: How to handle player properties ('bank' or 'auction')
            reason: Reason for removal
            
        Returns:
            Dict with operation result
        """
        try:
            # 1. Verify player exists
            player = Player.query.get(player_id)
            if not player:
                return {"success": False, "error": "Player not found"}
            
            # 2. Handle player properties based on disposition preference
            if handle_properties == 'bank':
                # Transfer all properties to bank
                properties = Property.query.filter_by(owner_id=player_id).all()
                for prop in properties:
                    prop.owner_id = None  # Bank ownership
                    prop.is_mortgaged = False  # Reset mortgage status
                    prop.houses = 0  # Remove houses
                    prop.hotel = False  # Remove hotel
                db.session.commit()
                logger.info(f"Properties of player {player.username} transferred to bank")
                
            elif handle_properties == 'auction':
                # Queue properties for auction
                properties = Property.query.filter_by(owner_id=player_id).all()
                auction_controller = current_app.config.get('auction_controller')
                if auction_controller:
                    for prop in properties:
                        auction_controller.queue_property_for_auction(prop.id, f"Admin removal of player {player.username}")
                    logger.info(f"Properties of player {player.username} queued for auction")
                else:
                    logger.error("Auction controller not available for property auction")
                    return {"success": False, "error": "Auction controller not available"}
            
            # 3. Mark player as not in game
            player.in_game = False
            db.session.commit()
            
            # 4. Handle socket disconnection if player is connected
            socket_controller = current_app.config.get('socket_controller')
            if socket_controller:
                # Get connection status
                status = socket_controller.get_player_connection_status(player_id)
                if status.get('status') == 'connected':
                    # Disconnect socket
                    socketio = current_app.config.get('socketio')
                    if socketio and status.get('socket_id'):
                        try:
                            socketio.server.disconnect(status.get('socket_id'))
                            logger.info(f"Socket for player {player_id} disconnected")
                        except Exception as e:
                            logger.warning(f"Could not disconnect socket for player {player_id}: {str(e)}")
                    
                    # Cancel reconnect timer and remove from tracking
                    socket_controller.cancel_reconnect_timer(player_id)
                    socket_controller.remove_connected_player_entry(player_id)
                    
                    # Notify all clients
                    game_state = GameState.get_instance()
                    if game_state:
                        socket_controller.notify_all_player_removed(player_id, player.username, game_state.game_id)
            
            # 5. Log the action
            logger.info(f"Player {player.username} (ID: {player_id}) removed by admin. Reason: {reason}")
            
            return {
                "success": True,
                "message": f"Player {player.username} removed from game",
                "player_id": player_id,
                "username": player.username,
                "properties_handled": handle_properties
            }
            
        except Exception as e:
            logger.error(f"Error removing player {player_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Failed to remove player: {str(e)}"} 