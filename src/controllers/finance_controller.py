from datetime import datetime
import logging
from typing import Dict, List, Optional, Union, Any

from src.models import db
from src.models.finance.loan import Loan
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.transaction import Transaction

# Set up logger
logger = logging.getLogger(__name__)

class FinanceController:
    """Controller for managing financial instruments (loans, CDs, HELOCs)"""
    
    def __init__(self, socketio=None, banker=None):
        """Initialize finance controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time communication
            banker: Banker instance for financial transactions
        """
        self.socketio = socketio
        self.banker = banker
    
    def create_loan(self, player_id: int, pin: str, amount: int) -> Dict:
        """Create a new loan for a player
        
        Args:
            player_id: ID of the player taking the loan
            pin: Player's PIN for authentication
            amount: Loan amount
            
        Returns:
            Dictionary with loan creation results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Verify player is eligible for loan
        if not self._is_eligible_for_loan(player, amount):
            return {
                "success": False,
                "error": "Player is not eligible for this loan amount"
            }
            
        # Get current game state
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # Calculate interest rate based on economic conditions
        interest_rate = self._calculate_loan_interest_rate(player, amount)
        
        # Standard loan length is 5 laps
        length_laps = 5
        
        # Create the loan
        loan = Loan.create_loan(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            length_laps=length_laps,
            current_lap=current_lap,
            loan_type="loan"
        )
        
        # Give cash to player
        player.cash += amount
        db.session.add(player)
        db.session.commit()
        
        # Create transaction record
        transaction = Transaction(
            from_player_id=None,  # From bank
            to_player_id=player_id,
            amount=amount,
            transaction_type="loan",
            description=f"Loan of ${amount} at {interest_rate*100:.1f}%",
            lap_number=current_lap
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('loan_created', {
                "player_id": player_id,
                "player_name": player.username,
                "loan_id": loan.id,
                "amount": amount,
                "interest_rate": interest_rate,
                "length_laps": length_laps
            })
            
        return {
            "success": True,
            "loan": loan.to_dict(),
            "transaction_id": transaction.id
        }
    
    def repay_loan(self, player_id: int, pin: str, loan_id: int, amount: Optional[int] = None) -> Dict:
        """Repay a loan partially or in full
        
        Args:
            player_id: ID of the player repaying the loan
            pin: Player's PIN for authentication
            loan_id: ID of the loan to repay
            amount: Amount to repay (None for full repayment)
            
        Returns:
            Dictionary with loan repayment results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Get the loan
        loan = Loan.query.get(loan_id)
        if not loan:
            return {
                "success": False,
                "error": "Loan not found"
            }
            
        # Verify loan belongs to player
        if loan.player_id != player_id:
            return {
                "success": False,
                "error": "This loan does not belong to this player"
            }
            
        # Get current value of loan
        current_value = loan.calculate_current_value()
        
        # Determine repayment amount
        if amount is None:
            amount = current_value
            
        # Check if player has enough cash
        if player.cash < amount:
            return {
                "success": False,
                "error": "Not enough cash to make this payment",
                "required": amount,
                "available": player.cash
            }
            
        # Process repayment
        repayment_result = loan.repay(amount)
        
        if repayment_result["success"]:
            # Deduct from player's cash
            player.cash -= amount
            db.session.add(player)
            
            # Get current game state
            game_state = GameState.query.first()
            current_lap = game_state.current_lap if game_state else 0
            
            # Create transaction record
            transaction = Transaction(
                from_player_id=player_id,
                to_player_id=None,  # To bank
                amount=amount,
                transaction_type="loan_repayment",
                loan_id=loan_id,
                description=f"Loan repayment of ${amount}",
                lap_number=current_lap
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Return change to player if applicable
            if repayment_result["overpayment"] > 0:
                player.cash += repayment_result["overpayment"]
                db.session.add(player)
                db.session.commit()
            
            # Emit event if socketio is available
            if self.socketio:
                self.socketio.emit('loan_repaid', {
                    "player_id": player_id,
                    "player_name": player.username,
                    "loan_id": loan_id,
                    "amount_paid": repayment_result["amount_paid"],
                    "loan_status": repayment_result["loan_status"]
                })
                
            repayment_result["transaction_id"] = transaction.id
            
        return repayment_result
    
    def create_cd(self, player_id: int, pin: str, amount: int, length_laps: int) -> Dict:
        """Create a Certificate of Deposit
        
        Args:
            player_id: ID of the player creating the CD
            pin: Player's PIN for authentication
            amount: CD amount
            length_laps: CD term in game laps
            
        Returns:
            Dictionary with CD creation results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Check if player has enough cash
        if player.cash < amount:
            return {
                "success": False,
                "error": "Not enough cash to create this CD",
                "required": amount,
                "available": player.cash
            }
            
        # Validate term length
        valid_terms = [3, 5, 7]
        if length_laps not in valid_terms:
            return {
                "success": False,
                "error": f"Invalid CD term. Must be one of: {valid_terms}"
            }
            
        # Get current game state
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # Calculate interest rate based on term length and economic conditions
        interest_rate = self._calculate_cd_interest_rate(length_laps)
        
        # Create the CD
        cd = Loan.create_loan(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            length_laps=length_laps,
            current_lap=current_lap,
            loan_type="cd"
        )
        
        # Deduct cash from player
        player.cash -= amount
        db.session.add(player)
        db.session.commit()
        
        # Create transaction record
        transaction = Transaction(
            from_player_id=player_id,
            to_player_id=None,  # To bank
            amount=amount,
            transaction_type="cd_deposit",
            loan_id=cd.id,
            description=f"CD deposit of ${amount} at {interest_rate*100:.1f}% for {length_laps} laps",
            lap_number=current_lap
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('cd_created', {
                "player_id": player_id,
                "player_name": player.username,
                "cd_id": cd.id,
                "amount": amount,
                "interest_rate": interest_rate,
                "length_laps": length_laps
            })
            
        return {
            "success": True,
            "cd": cd.to_dict(),
            "transaction_id": transaction.id
        }
    
    def withdraw_cd(self, player_id: int, pin: str, cd_id: int) -> Dict:
        """Withdraw a Certificate of Deposit
        
        Args:
            player_id: ID of the player withdrawing the CD
            pin: Player's PIN for authentication
            cd_id: ID of the CD to withdraw
            
        Returns:
            Dictionary with CD withdrawal results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Get the CD
        cd = Loan.query.get(cd_id)
        if not cd:
            return {
                "success": False,
                "error": "CD not found"
            }
            
        # Verify CD belongs to player
        if cd.player_id != player_id:
            return {
                "success": False,
                "error": "This CD does not belong to this player"
            }
            
        # Verify it's actually a CD
        if cd.loan_type != "cd":
            return {
                "success": False,
                "error": "This is not a Certificate of Deposit"
            }
            
        # Get current game state
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # Check if CD is mature
        is_mature = cd.calculate_remaining_laps(current_lap) <= 0
        
        # Process withdrawal
        withdrawal_result = cd.withdraw_cd(is_mature)
        
        if withdrawal_result["success"]:
            # Add funds to player's cash
            player.cash += withdrawal_result["withdrawal_amount"]
            db.session.add(player)
            
            # Create transaction record
            transaction = Transaction(
                from_player_id=None,  # From bank
                to_player_id=player_id,
                amount=withdrawal_result["withdrawal_amount"],
                transaction_type="cd_withdrawal",
                loan_id=cd_id,
                description=f"CD withdrawal of ${withdrawal_result['withdrawal_amount']}",
                lap_number=current_lap
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Emit event if socketio is available
            if self.socketio:
                self.socketio.emit('cd_withdrawn', {
                    "player_id": player_id,
                    "player_name": player.username,
                    "cd_id": cd_id,
                    "amount": withdrawal_result["withdrawal_amount"],
                    "penalty": withdrawal_result["penalty_amount"],
                    "was_mature": withdrawal_result["was_mature"]
                })
                
            withdrawal_result["transaction_id"] = transaction.id
            
        return withdrawal_result
    
    def create_heloc(self, player_id: int, pin: str, property_id: int, amount: int) -> Dict:
        """Create a Home Equity Line of Credit
        
        Args:
            player_id: ID of the player creating the HELOC
            pin: Player's PIN for authentication
            property_id: ID of the property to take the HELOC on
            amount: HELOC amount
            
        Returns:
            Dictionary with HELOC creation results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Get the property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
            
        # Verify property belongs to player
        if property_obj.owner_id != player_id:
            return {
                "success": False,
                "error": "You do not own this property"
            }
            
        # Check property eligibility
        if property_obj.is_mortgaged:
            return {
                "success": False,
                "error": "Cannot take a HELOC on a mortgaged property"
            }
            
        # Calculate maximum HELOC amount
        max_heloc = self._calculate_max_heloc_amount(property_obj)
        
        if amount > max_heloc:
            return {
                "success": False,
                "error": f"Maximum HELOC amount for this property is ${max_heloc}",
                "max_amount": max_heloc
            }
            
        # Check existing HELOCs on this property
        existing_helocs = Loan.get_active_loans_for_property(property_id)
        existing_total = sum(loan.calculate_current_value() for loan in existing_helocs)
        
        if existing_total + amount > max_heloc:
            remaining = max_heloc - existing_total
            return {
                "success": False,
                "error": f"You can only borrow ${remaining} more against this property",
                "available_equity": remaining
            }
            
        # Get current game state
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # Calculate interest rate (lower than regular loans due to collateral)
        interest_rate = self._calculate_heloc_interest_rate(property_obj)
        
        # Standard HELOC length is 8 laps
        length_laps = 8
        
        # Create the HELOC
        heloc = Loan.create_loan(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            length_laps=length_laps,
            current_lap=current_lap,
            loan_type="heloc",
            property_id=property_id
        )
        
        # Give cash to player
        player.cash += amount
        db.session.add(player)
        db.session.commit()
        
        # Create transaction record
        transaction = Transaction(
            from_player_id=None,  # From bank
            to_player_id=player_id,
            amount=amount,
            transaction_type="heloc",
            property_id=property_id,
            loan_id=heloc.id,
            description=f"HELOC of ${amount} at {interest_rate*100:.1f}% on {property_obj.name}",
            lap_number=current_lap
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('heloc_created', {
                "player_id": player_id,
                "player_name": player.username,
                "heloc_id": heloc.id,
                "property_id": property_id,
                "property_name": property_obj.name,
                "amount": amount,
                "interest_rate": interest_rate,
                "length_laps": length_laps
            })
            
        return {
            "success": True,
            "heloc": heloc.to_dict(),
            "transaction_id": transaction.id
        }
    
    def get_interest_rates(self) -> Dict:
        """Get current interest rates for loans and CDs
        
        Returns:
            Dictionary with current interest rates
        """
        game_state = GameState.query.first()
        economic_state = game_state.inflation_state if game_state else "normal"
        
        # Base rates by economic state
        base_rates = {
            "recession": 0.03,    # 3% during recession
            "normal": 0.05,       # 5% during normal conditions
            "growth": 0.07,       # 7% during growth
            "boom": 0.10          # 10% during boom
        }
        
        base_rate = base_rates.get(economic_state, 0.05)
        
        # Calculate specific rates
        return {
            "success": True,
            "economic_state": economic_state,
            "base_rate": base_rate,
            "rates": {
                "loan": {
                    "standard": round(base_rate + 0.02, 3),         # Standard loan
                    "poor_credit": round(base_rate + 0.05, 3),      # Poor credit premium
                    "good_credit": round(base_rate, 3)              # Good credit discount
                },
                "cd": {
                    "short_term": round(base_rate - 0.01, 3),       # 3-lap CD
                    "medium_term": round(base_rate, 3),             # 5-lap CD
                    "long_term": round(base_rate + 0.01, 3)         # 7-lap CD
                },
                "heloc": {
                    "standard": round(base_rate - 0.01, 3),         # Standard HELOC
                    "undeveloped": round(base_rate, 3),             # Undeveloped property
                    "developed": round(base_rate - 0.02, 3)         # Developed property
                }
            }
        }
    
    def get_player_loans(self, player_id: int, pin: str) -> Dict:
        """Get all financial instruments for a player
        
        Args:
            player_id: ID of the player
            pin: Player's PIN for authentication
            
        Returns:
            Dictionary with player's loans, CDs, and HELOCs
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Get all financial instruments
        loans = Loan.get_active_loans_for_player(player_id)
        cds = Loan.get_active_cds_for_player(player_id)
        helocs = Loan.get_active_helocs_for_player(player_id)
        
        # Calculate totals
        loan_total = sum(loan.calculate_current_value() for loan in loans)
        cd_total = sum(cd.calculate_current_value() for cd in cds)
        heloc_total = sum(heloc.calculate_current_value() for heloc in helocs)
        
        return {
            "success": True,
            "player_id": player_id,
            "loans": [loan.to_dict() for loan in loans],
            "cds": [cd.to_dict() for cd in cds],
            "helocs": [heloc.to_dict() for heloc in helocs],
            "totals": {
                "loans": loan_total,
                "cds": cd_total,
                "helocs": heloc_total,
                "net_debt": loan_total + heloc_total - cd_total
            }
        }
    
    def declare_bankruptcy(self, player_id: int, pin: str) -> Dict:
        """Declare bankruptcy when unable to pay debts
        
        Args:
            player_id: ID of the player declaring bankruptcy
            pin: Player's PIN for authentication
            
        Returns:
            Dictionary with bankruptcy results
        """
        # Validate player
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            return {
                "success": False,
                "error": "Invalid player credentials"
            }
            
        # Get all active loans
        loans = Loan.get_active_loans_for_player(player_id)
        helocs = Loan.get_active_helocs_for_player(player_id)
        cds = Loan.get_active_cds_for_player(player_id)
        
        # Calculate total debt
        loan_total = sum(loan.calculate_current_value() for loan in loans)
        heloc_total = sum(heloc.calculate_current_value() for heloc in helocs)
        cd_total = sum(cd.calculate_current_value() for cd in cds)
        
        total_debt = loan_total + heloc_total
        
        # Make sure player is eligible for bankruptcy
        # (can't pay even if all properties were liquidated)
        properties = Property.query.filter_by(owner_id=player_id).all()
        property_value = sum(prop.current_price for prop in properties)
        
        if player.cash + property_value >= total_debt:
            return {
                "success": False,
                "error": "You have sufficient assets to pay your debts. Liquidate properties to avoid bankruptcy."
            }
            
        # Process bankruptcy
        # 1. Withdraw all CDs
        for cd in cds:
            cd.is_active = False
            db.session.add(cd)
            
        # 2. Mark all loans as inactive
        for loan in loans + helocs:
            loan.is_active = False
            db.session.add(loan)
            
        # 3. Forfeit all properties
        for prop in properties:
            prop.owner_id = None
            prop.is_mortgaged = False
            db.session.add(prop)
            
        # 4. Reset player cash
        starting_cash = game_state.settings.get("starting_cash", 1500)
        player.cash = starting_cash
        player.bankruptcy_count += 1
        db.session.add(player)
        
        # 5. Get current game state for transaction
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # 6. Create transaction record
        transaction = Transaction(
            from_player_id=player_id,
            to_player_id=None,  # To bank
            amount=total_debt,
            transaction_type="bankruptcy",
            description=f"Declared bankruptcy, debt of ${total_debt} forgiven",
            lap_number=current_lap
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('player_bankruptcy', {
                "player_id": player_id,
                "player_name": player.username,
                "total_debt": total_debt,
                "properties_lost": len(properties),
                "new_cash_balance": starting_cash
            })
            
        return {
            "success": True,
            "total_debt_forgiven": total_debt,
            "properties_lost": len(properties),
            "properties": [prop.name for prop in properties],
            "cds_lost": len(cds),
            "cd_value": cd_total,
            "new_cash_balance": starting_cash,
            "transaction_id": transaction.id
        }
    
    def _is_eligible_for_loan(self, player: Player, amount: int) -> bool:
        """Check if player is eligible for a loan
        
        Args:
            player: Player object
            amount: Requested loan amount
            
        Returns:
            True if eligible, False otherwise
        """
        # Calculate player's net worth
        properties = Property.query.filter_by(owner_id=player.id).all()
        property_value = sum(prop.current_price for prop in properties)
        
        net_worth = player.cash + property_value
        
        # Maximum loan is 80% of net worth
        max_loan = int(net_worth * 0.8)
        
        # Get current outstanding loans
        loans = Loan.get_active_loans_for_player(player.id)
        helocs = Loan.get_active_helocs_for_player(player.id)
        
        current_debt = sum(loan.calculate_current_value() for loan in loans + helocs)
        
        # Check if new loan would exceed maximum
        return current_debt + amount <= max_loan
    
    def _calculate_loan_interest_rate(self, player: Player, amount: int) -> float:
        """Calculate interest rate for a loan based on player's credit and economic conditions
        
        Args:
            player: Player object
            amount: Loan amount
            
        Returns:
            Interest rate as decimal (e.g., 0.05 for 5%)
        """
        # Get current interest rates
        rates = self.get_interest_rates()["rates"]["loan"]
        
        # Start with standard rate
        rate = rates["standard"]
        
        # Adjust based on bankruptcy history
        if player.bankruptcy_count > 0:
            rate = rates["poor_credit"]
        elif player.cash > 2000:  # Good cash reserves
            rate = rates["good_credit"]
            
        # Small adjustment based on loan amount
        # (larger loans have slightly higher rates)
        if amount > 1000:
            rate += 0.005
            
        return rate
    
    def _calculate_cd_interest_rate(self, term_length: int) -> float:
        """Calculate interest rate for a CD based on term length and economic conditions
        
        Args:
            term_length: CD term in game laps
            
        Returns:
            Interest rate as decimal (e.g., 0.04 for 4%)
        """
        # Get current interest rates
        rates = self.get_interest_rates()["rates"]["cd"]
        
        if term_length == 3:
            return rates["short_term"]
        elif term_length == 7:
            return rates["long_term"]
        else:
            return rates["medium_term"]
    
    def _calculate_heloc_interest_rate(self, property_obj: Property) -> float:
        """Calculate interest rate for a HELOC based on property and economic conditions
        
        Args:
            property_obj: Property object
            
        Returns:
            Interest rate as decimal (e.g., 0.045 for 4.5%)
        """
        # Get current interest rates
        rates = self.get_interest_rates()["rates"]["heloc"]
        
        # Default to standard rate
        rate = rates["standard"]
        
        # Adjust based on property development
        development_level = property_obj.get_development_level()
        
        if development_level == 0:
            rate = rates["undeveloped"]
        elif development_level >= 2:
            rate = rates["developed"]
            
        return rate
    
    def _calculate_max_heloc_amount(self, property_obj: Property) -> int:
        """Calculate maximum HELOC amount for a property
        
        Args:
            property_obj: Property object
            
        Returns:
            Maximum HELOC amount
        """
        # HELOC is based on property value
        property_value = property_obj.current_price
        
        # Maximum HELOC is 60% of property value
        max_heloc = int(property_value * 0.6)
        
        # Add bonus for developed properties
        development_level = property_obj.get_development_level()
        development_bonus = development_level * 0.05  # +5% per level
        
        max_heloc = int(max_heloc * (1 + development_bonus))
        
        return max_heloc 