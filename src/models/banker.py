from . import db
from datetime import datetime
import logging
# Import Player model directly for type hinting and fetching
from .player import Player

class Banker:
    """
    Manages the core financial transfers between players and the bank.
    Responsibilities are limited to validating funds and updating cash balances.
    Transaction logging and notifications are handled by the calling controllers.
    """
    
    def __init__(self, socketio):
        self.socketio = socketio # Store socketio instance
        self.logger = logging.getLogger("banker")
        self._balance = 15000  # Initial bank balance
        self.logger.info("Banker initialized.")
        
    @property
    def balance(self):
        """Get the current bank balance"""
        return self._balance
        
    def set_balance(self, amount):
        """Set the bank balance"""
        self._balance = amount
        self.logger.info(f"Bank balance set to ${amount}")
        return self._balance
        
    def player_pays_bank(self, player_id: int, amount: int, description: str) -> dict:
        """Process a payment from a player to the bank."""
        if amount <= 0:
            self.logger.warning(f"Attempted payment of non-positive amount ({amount}) from player {player_id}.")
            return {"success": False, "error": "Payment amount must be positive."}
            
        player = Player.query.get(player_id)
        if not player:
            self.logger.error(f"Payment failed: Player {player_id} not found.")
            return {"success": False, "error": "Player not found."}
            
        if player.money < amount:
            self.logger.info(f"Payment failed: Player {player.username} (ID: {player_id}) has insufficient funds. Required: {amount}, Available: {player.money}.")
            return {"success": False, "error": "Insufficient funds.", "required": amount, "available": player.money}
            
        try:
            player.money -= amount
            self._balance += amount  # Update bank balance
            db.session.add(player)
            db.session.commit()
            self.logger.info(f"Player {player_id} paid ${amount} to the bank for '{description}'. New balance: ${player.money}")
            return {"success": True, "player_id": player_id, "new_balance": player.money}
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error during player_pays_bank for player {player_id}, amount {amount}: {e}", exc_info=True)
            return {"success": False, "error": "Database error during payment processing."}

    def bank_pays_player(self, player_id: int, amount: int, description: str) -> dict:
        """Process a payment from the bank to a player."""
        if amount <= 0:
            self.logger.warning(f"Attempted bank payment of non-positive amount ({amount}) to player {player_id}.")
            return {"success": False, "error": "Payment amount must be positive."}
            
        player = Player.query.get(player_id)
        if not player:
            self.logger.error(f"Bank payment failed: Player {player_id} not found.")
            return {"success": False, "error": "Player not found."}
            
        try:
            player.money += amount
            self._balance -= amount  # Update bank balance
            db.session.add(player)
            db.session.commit()
            self.logger.info(f"Bank paid ${amount} to player {player_id} for '{description}'. New balance: ${player.money}")
            return {"success": True, "player_id": player_id, "new_balance": player.money}
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error during bank_pays_player for player {player_id}, amount {amount}: {e}", exc_info=True)
            return {"success": False, "error": "Database error during payment processing."}

    def player_pays_player(self, from_player_id: int, to_player_id: int, amount: int, description: str) -> dict:
        """Process a payment from one player to another."""
        if from_player_id == to_player_id:
             self.logger.warning(f"Attempted payment from player {from_player_id} to themselves.")
             return {"success": False, "error": "Cannot pay yourself."}
             
        if amount <= 0:
            self.logger.warning(f"Attempted player-to-player payment of non-positive amount ({amount}) from {from_player_id} to {to_player_id}.")
            return {"success": False, "error": "Payment amount must be positive."}
            
        from_player = Player.query.get(from_player_id)
        to_player = Player.query.get(to_player_id)
        
        if not from_player:
            self.logger.error(f"Player payment failed: Payer {from_player_id} not found.")
            return {"success": False, "error": "Paying player not found."}
        if not to_player:
            self.logger.error(f"Player payment failed: Payee {to_player_id} not found.")
            return {"success": False, "error": "Receiving player not found."}
            
        if from_player.money < amount:
            self.logger.info(f"Payment failed: Player {from_player.username} (ID: {from_player_id}) has insufficient funds to pay player {to_player.username} (ID: {to_player_id}). Required: {amount}, Available: {from_player.money}.")
            return {"success": False, "error": "Insufficient funds.", "required": amount, "available": from_player.money}
            
        try:
            from_player.money -= amount
            to_player.money += amount
            
            # Bank reserves don't change on direct player-to-player transfers
            # But we still want to track the transaction for accounting purposes
            # The line below is optional; it enables the banker to track the volume of money flowing between players
            # self._transaction_volume += amount
            
            db.session.add(from_player)
            db.session.add(to_player)
            db.session.commit()
            self.logger.info(f"Player {from_player_id} paid ${amount} to player {to_player_id} for '{description}'. Balances: Payer=${from_player.money}, Payee=${to_player.money}")
            return {
                "success": True, 
                "from_player_id": from_player_id,
                "from_player_new_balance": from_player.money,
                "to_player_id": to_player_id,
                "to_player_new_balance": to_player.money
            }
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database error during player_pays_player from {from_player_id} to {to_player_id}, amount {amount}: {e}", exc_info=True)
            return {"success": False, "error": "Database error during payment processing."}

    def update_loan_rates(self, base_interest_rate):
        """Update loan rates based on the current base interest rate
        
        Args:
            base_interest_rate: The new base interest rate
            
        Returns:
            Dict with result of operation
        """
        try:
            from src.models.finance.loan import Loan
            
            # Get all active loans
            active_loans = Loan.query.filter_by(is_active=True).all()
            
            updated_count = 0
            for loan in active_loans:
                # Update the loan interest rate based on its type and the base rate
                if not loan.fixed_rate:
                    # For variable rate loans, update the rate
                    # The formula can be adjusted based on loan risk, player credit score, etc.
                    loan.interest_rate = base_interest_rate + loan.rate_premium
                    db.session.add(loan)
                    updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                self.logger.info(f"Updated interest rates for {updated_count} loans based on new base rate: {base_interest_rate}")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "base_rate": base_interest_rate
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating loan rates: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error updating loan rates: {str(e)}"
            }

    # --- Deprecated Methods --- 
    # These methods were overly specific and included logic (like property updates, 
    # transaction creation, notifications) that belongs in the calling controllers.
    # Use the generic player_pays_bank, bank_pays_player, player_pays_player instead.

    # def process_property_purchase(self, player, property, game_state):
    #     """Process a property purchase from the bank"""
    #     ...
        
    # def process_property_sale_to_bank(self, player, property, game_state):
    #     """Process a property sale back to the bank"""
    #     ...
        
    # def provide_loan(self, player, amount, interest_rate, term_laps, game_state):
    #     """Provide a loan to a player from the bank"""
    #     ...
        
    # def accept_deposit(self, player, amount, interest_rate, term_laps, game_state):
    #     """Accept a CD (Certificate of Deposit) from a player"""
    #     ...
        
    # def pay_salary(self, player, base_amount, game_state):
    #     """Pay salary to player when passing GO"""
    #     ...

    # def transfer(self, from_entity_id, to_entity_id, amount, description):
    #     """Generic transfer method (can be complex to implement correctly)"""
    #     # This could potentially consolidate the logic of the above methods,
    #     # but requires careful handling of entity types (player, bank, community_fund)
    #     # For now, sticking to the more explicit methods.
    #     pass

# Example usage (from a controller):
# banker = Banker()
# result = banker.player_pays_bank(player_id=1, amount=100, description="Paying luxury tax")
# if result["success"]:
#     # Controller would now create the Transaction record and emit socket events
#     pass
# else:
#     # Handle error
#     pass 