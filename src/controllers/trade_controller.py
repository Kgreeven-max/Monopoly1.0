import logging
from datetime import datetime
from flask import current_app # For accessing app context dependencies like db, banker, socketio
import json

from src.models import db
from src.models.trade import Trade, TradeItem
from src.models.player import Player
from src.models.property import Property
from src.models.banker import Banker
from src.models.game_state import GameState # For getting game_id for socket rooms

logger = logging.getLogger(__name__)

class TradeController:
    """Controller for managing player-to-player trades."""

    def __init__(self):
        # Dependencies will be accessed via current_app.config within methods
        self.logger = logging.getLogger("trade_controller")
        self.logger.info("TradeController initialized.")

    def _get_dependencies(self):
        """Helper to retrieve dependencies from app context."""
        banker = current_app.config.get('banker')
        socketio = current_app.config.get('socketio')
        if not banker or not socketio:
            self.logger.error("Missing dependencies (Banker or SocketIO) in app config.")
            raise ValueError("Banker or SocketIO not configured in the application.")
        return banker, socketio

    def propose_trade(self, proposer_id: int, pin: str, receiver_id: int, trade_data: dict) -> dict:
        """Propose a new trade between two players."""
        banker, socketio = self._get_dependencies()
        
        # --- Validation ---
        if proposer_id == receiver_id:
            return {"success": False, "error": "Cannot trade with yourself."}

        proposer = Player.query.get(proposer_id)
        receiver = Player.query.get(receiver_id)

        if not proposer or proposer.pin != pin:
            return {"success": False, "error": "Invalid proposer credentials."}
        if not receiver or not receiver.in_game:
            return {"success": False, "error": "Receiving player not found or not in game."}
            
        # Basic structure validation of trade_data
        proposer_items = trade_data.get('proposer_items', {})
        receiver_items = trade_data.get('receiver_items', {})
        proposer_cash = proposer_items.get('cash', 0)
        receiver_cash = receiver_items.get('cash', 0)
        proposer_prop_ids = proposer_items.get('properties', [])
        receiver_prop_ids = receiver_items.get('properties', [])
        # TODO: Add jail card validation later if implemented

        if not isinstance(proposer_cash, int) or proposer_cash < 0 or \
           not isinstance(receiver_cash, int) or receiver_cash < 0:
            return {"success": False, "error": "Invalid cash amount in trade."}
            
        if not all(isinstance(pid, int) for pid in proposer_prop_ids) or \
           not all(isinstance(pid, int) for pid in receiver_prop_ids):
             return {"success": False, "error": "Invalid property ID format in trade."}

        # Validate proposer can fulfill their side NOW
        validation = self._validate_trade_fulfillment(proposer, proposer_cash, proposer_prop_ids)
        if not validation["success"]:
             return {"success": False, "error": f"You cannot fulfill this trade: {validation['error']}"}
             
        # Validate receiver owns the properties they are offering
        receiver_validation = self._validate_trade_fulfillment(receiver, 0, receiver_prop_ids, check_cash=False)
        if not receiver_validation["success"]:
              return {"success": False, "error": f"Receiver does not own offered properties: {receiver_validation['error']}"}

        # --- Create Trade Record ---
        try:
            new_trade = Trade(
                proposer_id=proposer_id,
                receiver_id=receiver_id,
                proposer_cash=proposer_cash,
                receiver_cash=receiver_cash,
                status='pending'
                # Add details like jail cards later if needed
            )
            db.session.add(new_trade)
            
            # Add property items
            for prop_id in proposer_prop_ids:
                item = TradeItem(trade=new_trade, property_id=prop_id, is_from_proposer=True)
                db.session.add(item)
            for prop_id in receiver_prop_ids:
                item = TradeItem(trade=new_trade, property_id=prop_id, is_from_proposer=False)
                db.session.add(item)
                
            db.session.commit()
            self.logger.info(f"Trade {new_trade.id} proposed by player {proposer_id} to player {receiver_id}.")

            # --- Notify Receiver ---
            game_state = GameState.get_instance()
            if game_state:
                 # Find receiver's socket room/ID if necessary (might need SocketController integration)
                 # For now, emitting generally to the game room, client needs to filter
                 socketio.emit('trade_proposed', {
                     'trade': new_trade.to_dict(),
                     'proposer_name': proposer.username,
                     'receiver_id': receiver_id # Target specific client if possible
                 }, room=game_state.game_id) # Use game room
                 self.logger.info(f"Emitted trade_proposed for trade {new_trade.id} to room {game_state.game_id}")

            return {"success": True, "trade": new_trade.to_dict()}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error proposing trade from {proposer_id} to {receiver_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error creating trade proposal."}

    def respond_to_trade(self, player_id: int, pin: str, trade_id: int, accept: bool) -> dict:
        """Respond to a pending trade proposal."""
        banker, socketio = self._get_dependencies()

        # --- Validation ---
        trade = Trade.query.get(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found."}
        if trade.status != 'pending':
            return {"success": False, "error": f"Trade is not pending (status: {trade.status})."}
        if trade.receiver_id != player_id:
            return {"success": False, "error": "You are not the recipient of this trade proposal."}

        receiver = Player.query.get(player_id)
        if not receiver or receiver.pin != pin:
            return {"success": False, "error": "Invalid receiver credentials."}
            
        proposer = Player.query.get(trade.proposer_id)
        if not proposer: # Should not happen if trade exists, but check
            return {"success": False, "error": "Proposing player not found."}


        # --- Process Response ---
        try:
            if not accept:
                trade.status = 'rejected'
                db.session.commit()
                self.logger.info(f"Trade {trade_id} rejected by player {player_id}.")
                # Notify proposer
                game_state = GameState.get_instance()
                if game_state:
                    socketio.emit('trade_rejected', {
                        'trade_id': trade_id,
                        'receiver_name': receiver.username,
                        'proposer_id': proposer.id # Target specific client if possible
                    }, room=game_state.game_id)
                return {"success": True, "message": "Trade rejected."}

            # --- Execute Accepted Trade ---
            # Re-validate fulfillment for BOTH players at the time of acceptance
            proposer_items = trade.items.filter_by(is_from_proposer=True).all()
            receiver_items = trade.items.filter_by(is_from_proposer=False).all()
            proposer_prop_ids = [item.property_id for item in proposer_items]
            receiver_prop_ids = [item.property_id for item in receiver_items]

            proposer_validation = self._validate_trade_fulfillment(proposer, trade.proposer_cash, proposer_prop_ids)
            if not proposer_validation["success"]:
                 trade.status = 'failed_validation' # Mark trade as failed
                 db.session.commit()
                 self.logger.warning(f"Trade {trade_id} acceptance failed: Proposer cannot fulfill. Reason: {proposer_validation['error']}")
                 # Notify both?
                 return {"success": False, "error": f"Trade failed: Proposer cannot fulfill trade. {proposer_validation['error']}"}
                 
            receiver_validation = self._validate_trade_fulfillment(receiver, trade.receiver_cash, receiver_prop_ids)
            if not receiver_validation["success"]:
                 trade.status = 'failed_validation'
                 db.session.commit()
                 self.logger.warning(f"Trade {trade_id} acceptance failed: Receiver cannot fulfill. Reason: {receiver_validation['error']}")
                 # Notify both?
                 return {"success": False, "error": f"Trade failed: You cannot fulfill trade. {receiver_validation['error']}"}

            # Perform the exchange
            description = f"Trade {trade_id} between {proposer.username} and {receiver.username}"

            # 1. Cash Exchange (using Banker)
            if trade.proposer_cash > 0:
                result = banker.player_pays_player(proposer.id, receiver.id, trade.proposer_cash, description + " (proposer cash)")
                if not result["success"]: raise ValueError(f"Banker error: {result['error']}") # Raise to trigger rollback
            if trade.receiver_cash > 0:
                result = banker.player_pays_player(receiver.id, proposer.id, trade.receiver_cash, description + " (receiver cash)")
                if not result["success"]: raise ValueError(f"Banker error: {result['error']}")

            # 2. Property Exchange
            for item in proposer_items:
                prop = Property.query.get(item.property_id)
                if not prop or prop.owner_id != proposer.id: raise ValueError(f"Property {item.property_id} inconsistency.")
                prop.owner_id = receiver.id
                # Reset mortgage status? Or trade mortgaged properties? Let's assume clear for now.
                prop.is_mortgaged = False 
                db.session.add(prop)
            for item in receiver_items:
                prop = Property.query.get(item.property_id)
                if not prop or prop.owner_id != receiver.id: raise ValueError(f"Property {item.property_id} inconsistency.")
                prop.owner_id = proposer.id
                prop.is_mortgaged = False
                db.session.add(prop)
                
            # TODO: Jail Card Exchange (if implemented)

            # Update Trade Status
            trade.status = 'completed'
            db.session.commit()
            self.logger.info(f"Trade {trade_id} completed between player {proposer.id} and {receiver.id}.")

            # Notify Both Players
            game_state = GameState.get_instance()
            if game_state:
                 socketio.emit('trade_completed', {
                     'trade': trade.to_dict(),
                     'proposer_name': proposer.username,
                     'receiver_name': receiver.username
                 }, room=game_state.game_id)

            return {"success": True, "message": "Trade completed successfully.", "trade": trade.to_dict()}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error responding to trade {trade_id} by player {player_id}: {e}", exc_info=True)
            # Attempt to mark trade as failed if exception occurred during execution
            try:
                trade.status = 'failed_execution'
                db.session.commit()
            except Exception as e2:
                 self.logger.error(f"Failed to mark trade {trade_id} as failed after error: {e2}")
            return {"success": False, "error": "Internal server error processing trade response."}


    def cancel_trade(self, player_id: int, pin: str, trade_id: int) -> dict:
        """Cancel a pending trade proposal made by the player."""
        _, socketio = self._get_dependencies()
        
        # --- Validation ---
        trade = Trade.query.get(trade_id)
        if not trade:
            return {"success": False, "error": "Trade not found."}
        if trade.status != 'pending':
            return {"success": False, "error": f"Cannot cancel trade with status '{trade.status}'."}
        if trade.proposer_id != player_id:
            return {"success": False, "error": "Only the proposer can cancel this trade."}

        proposer = Player.query.get(player_id)
        if not proposer or proposer.pin != pin:
            return {"success": False, "error": "Invalid proposer credentials."}

        # --- Update Status ---
        try:
            trade.status = 'cancelled'
            db.session.commit()
            self.logger.info(f"Trade {trade_id} cancelled by proposer {player_id}.")

            # Notify Receiver
            receiver = Player.query.get(trade.receiver_id)
            game_state = GameState.get_instance()
            if receiver and game_state:
                 socketio.emit('trade_cancelled', {
                     'trade_id': trade_id,
                     'proposer_name': proposer.username,
                     'receiver_id': receiver.id # Target specific client if possible
                 }, room=game_state.game_id)

            return {"success": True, "message": "Trade cancelled."}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error cancelling trade {trade_id} by player {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error cancelling trade."}

    def list_player_trades(self, player_id: int, pin: str) -> dict:
         """List pending trades involving the player (proposed or received)."""
         # --- Validation ---
         player = Player.query.get(player_id)
         if not player or player.pin != pin:
            return {"success": False, "error": "Invalid player credentials."}
            
         try:
            proposed_trades = Trade.query.filter_by(proposer_id=player_id, status='pending').all()
            received_trades = Trade.query.filter_by(receiver_id=player_id, status='pending').all()
            
            return {
                "success": True,
                "proposed": [t.to_dict() for t in proposed_trades],
                "received": [t.to_dict() for t in received_trades]
            }
         except Exception as e:
            self.logger.error(f"Database error listing trades for player {player_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error listing trades."}
            
    def get_trade_details(self, trade_id: int, player_id: int, pin: str) -> dict:
         """Get details for a specific trade if the player is involved."""
         # --- Validation ---
         player = Player.query.get(player_id)
         if not player or player.pin != pin:
            return {"success": False, "error": "Invalid player credentials."}

         trade = Trade.query.get(trade_id)
         if not trade:
            return {"success": False, "error": "Trade not found."}
            
         if trade.proposer_id != player_id and trade.receiver_id != player_id:
             return {"success": False, "error": "You are not involved in this trade."}
             
         return {"success": True, "trade": trade.to_dict()}
         
    def _validate_trade_fulfillment(self, player: Player, cash_offered: int, property_ids_offered: list, check_cash=True) -> dict:
        """Helper to check if a player can fulfill their side of a trade."""
        if check_cash and player.cash < cash_offered:
            return {"success": False, "error": f"Insufficient cash (needs ${cash_offered}, has ${player.cash})"}

        owned_props = {prop.id for prop in player.properties}
        for prop_id in property_ids_offered:
            if prop_id not in owned_props:
                 prop_name = Property.query.get(prop_id).name if Property.query.get(prop_id) else f"ID {prop_id}"
                 return {"success": False, "error": f"Does not own property '{prop_name}'"}
            # Check if property is mortgaged - trades usually involve clear properties
            prop = Property.query.get(prop_id)
            if prop.is_mortgaged:
                 return {"success": False, "error": f"Property '{prop.name}' is mortgaged"}
                 
        # TODO: Add check for jail cards if implemented
        
        return {"success": True}

    # Placeholder for admin approval logic if needed later
    def admin_approve_trade(self, trade_id):
         logger.warning("admin_approve_trade not implemented.")
         return {"success": False, "error": "Admin approval feature not implemented."} 