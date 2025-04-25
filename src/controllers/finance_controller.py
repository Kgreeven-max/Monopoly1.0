from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

from src.models import db
from src.models.finance.loan import Loan
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.transaction import Transaction
from src.utils.errors import GameError

# Set up logger
logger = logging.getLogger(__name__)

class FinanceController:
    """Controller for managing financial instruments (loans, CDs, HELOCs)"""
    
    def __init__(self, socketio=None, banker=None, game_state: GameState = None):
        """Initialize finance controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time communication
            banker: Banker instance for financial transactions
            game_state: GameState instance for managing game state
        """
        self.socketio = socketio
        self.banker = banker
        self.game_state = game_state
    
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
        
        # Update player's credit score
        player.update_credit_score('loan_creation', amount, True)
        
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
                "length_laps": length_laps,
                "credit_score": player.credit_score
            })
            
        return {
            "success": True,
            "loan": loan.to_dict(),
            "transaction_id": transaction.id,
            "credit_score": player.credit_score
        }
    
    def repay_loan(self, player_id: int, pin: str, loan_id: int, amount: Optional[int] = None) -> Dict:
        """Repay a loan partially or in full
        
        Args:
            player_id: ID of the player repaying the loan
            pin: Player's PIN for authentication
            loan_id: ID of the loan to repay
            amount: Optional amount to repay, if None, repay full loan
            
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
            
        # Determine repayment amount
        if amount is None:
            amount = loan.calculate_current_value(loan.current_lap)
            
        # Check if player has enough cash
        if player.money < amount:
            return {
                "success": False,
                "error": "Not enough cash to repay this loan",
                "required": amount,
                "available": player.money
            }
            
        # Process the repayment
        repayment_result = loan.repay(amount)
        
        if repayment_result["success"]:
            # Deduct cash from player
            player.money -= repayment_result["amount_paid"]
            
            # Get current game state
            game_state = GameState.query.first()
            current_lap = game_state.current_lap if game_state else 0
            
            # Create transaction record
            transaction = Transaction(
                from_player_id=player_id,
                to_player_id=None,  # To bank
                amount=repayment_result["amount_paid"],
                transaction_type="loan_repayment",
                loan_id=loan_id,
                description=f"Loan repayment of ${repayment_result['amount_paid']}",
                lap_number=current_lap
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Update credit score for timely repayment
            if not repayment_result["is_late"]:
                player.update_credit_score("loan_repayment", repayment_result["amount_paid"], True)
            else:
                player.update_credit_score("late_repayment", repayment_result["amount_paid"], False)
                
            db.session.add(player)
            db.session.commit()
            
            # Return change to player if applicable
            if repayment_result["overpayment"] > 0:
                player.money += repayment_result["overpayment"]
                db.session.add(player)
                db.session.commit()
            
            # Emit event if socketio is available
            if self.socketio:
                self.socketio.emit('loan_repaid', {
                    "player_id": player_id,
                    "player_name": player.username,
                    "loan_id": loan_id,
                    "amount_paid": repayment_result["amount_paid"],
                    "loan_status": repayment_result["loan_status"],
                    "credit_score": player.credit_score
                })
                
            repayment_result["transaction_id"] = transaction.id
            repayment_result["credit_score"] = player.credit_score
            
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
        if player.money < amount:
            return {
                "success": False,
                "error": "Not enough cash to create this CD",
                "required": amount,
                "available": player.money
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
        player.money -= amount
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
            player.money += withdrawal_result["withdrawal_amount"]
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
            property_id: ID of the property to use as collateral
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
        existing_total = sum(loan.calculate_current_value(loan.current_lap) for loan in existing_helocs)
        
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
        
        # Add funds to player
        player.money += amount
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
        """Get current interest rates for loans, CDs, and HELOCs
        
        Returns:
            Dictionary with rates
        """
        # Get base economic state
        game_state = GameState.query.first()
        
        if not game_state:
            # Default values if game state is unavailable
            return {
                "base_rate": 0.05,  # 5% base rate
                "economic_state": "normal",
                "rates": {
                    "loan": {
                        "standard": 0.06,  # 6%
                        "good_credit": 0.05,  # 5%
                        "excellent_credit": 0.045,  # 4.5%
                        "poor_credit": 0.08  # 8%
                    },
                    "cd": {
                        "short_term": 0.04,  # 4%
                        "medium_term": 0.05,  # 5%
                        "long_term": 0.06  # 6%
                    },
                    "heloc": {
                        "standard": 0.045,  # 4.5%
                        "undeveloped": 0.05,  # 5%
                        "developed": 0.04  # 4%
                    }
                }
            }
        
        # Get base rate from game state
        base_rate = getattr(game_state, 'base_interest_rate', 0.05)
        economic_state = getattr(game_state, 'inflation_state', "normal")
        
        # Apply economic state modifier to rates
        state_modifiers = {
            "recession": 0.02,  # Higher rates during recession
            "normal": 0.0,      # Base rate during normal times
            "growth": -0.01,    # Lower rates during growth
            "boom": -0.02       # Lowest rates during boom
        }
        
        modifier = state_modifiers.get(economic_state, 0.0)
        
        # Define rate structure
        rates = {
            "base_rate": base_rate,
            "economic_state": economic_state,
            "rates": {
                "loan": {
                    "standard": base_rate + modifier + 0.02,
                    "good_credit": base_rate + modifier,
                    "excellent_credit": base_rate + modifier - 0.005,
                    "poor_credit": base_rate + modifier + 0.05
                },
                "cd": {
                    "short_term": base_rate - 0.01,
                    "medium_term": base_rate,
                    "long_term": base_rate + 0.01
                },
                "heloc": {
                    "standard": base_rate + 0.01,
                    "undeveloped": base_rate + 0.015,
                    "developed": base_rate + 0.005
                }
            }
        }
        
        return rates
    
    def get_player_loans(self, player_id: int, pin: str = None) -> Dict:
        """Get all loans for a player
        
        Args:
            player_id: ID of the player
            pin: Player's PIN for authentication (optional if using player_required decorator)
            
        Returns:
            Dictionary with player's loans
        """
        # Validate player if PIN is provided
        if pin:
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                return {
                    "success": False,
                    "error": "Invalid player credentials"
                }
        
        # Get all loans for this player
        loans = Loan.query.filter_by(player_id=player_id, loan_type="loan").all()
        
        return {
            "success": True,
            "loans": [loan.to_dict() for loan in loans]
        }
    
    def get_player_cds(self, player_id: int, pin: str = None) -> Dict:
        """Get all certificates of deposit for a player
        
        Args:
            player_id: ID of the player
            pin: Player's PIN for authentication (optional if using player_required decorator)
            
        Returns:
            Dictionary with player's CDs
        """
        # Validate player if PIN is provided
        if pin:
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                return {
                    "success": False,
                    "error": "Invalid player credentials"
                }
        
        # Get all CDs for this player
        cds = Loan.query.filter_by(player_id=player_id, loan_type="cd").all()
        
        return {
            "success": True,
            "cds": [cd.to_dict() for cd in cds]
        }
    
    def get_player_helocs(self, player_id: int, pin: str = None) -> Dict:
        """Get all home equity lines of credit for a player
        
        Args:
            player_id: ID of the player
            pin: Player's PIN for authentication (optional if using player_required decorator)
            
        Returns:
            Dictionary with player's HELOCs
        """
        # Validate player if PIN is provided
        if pin:
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                return {
                    "success": False,
                    "error": "Invalid player credentials"
                }
        
        # Get all HELOCs for this player
        helocs = Loan.query.filter_by(player_id=player_id, loan_type="heloc").all()
        
        return {
            "success": True,
            "helocs": [heloc.to_dict() for heloc in helocs]
        }
    
    def get_player_financial_summary(self, player_id: int, pin: str = None) -> Dict:
        """Get a comprehensive financial summary for a player
        
        Args:
            player_id: Player ID
            pin: Optional PIN for verification
            
        Returns:
            Dictionary with player's financial summary
        """
        # Validate player if PIN provided
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
            
        if pin and player.pin != pin:
            return {
                "success": False,
                "error": "Invalid PIN"
            }
            
        # Get player properties
        properties = Property.query.filter_by(owner_id=player_id).all()
        property_value = sum(prop.current_price for prop in properties)
        
        # Get player loans
        loans = Loan.query.filter_by(player_id=player_id, loan_type="loan").all()
        
        # Get current game state for current lap
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        loan_debt = sum(loan.calculate_current_value(current_lap) for loan in loans)
        
        # Get player CDs
        cds = Loan.query.filter_by(player_id=player_id, loan_type="cd").all()
        cd_value = sum(cd.calculate_current_value(current_lap) for cd in cds)
        
        # Get player HELOCs
        helocs = Loan.query.filter_by(player_id=player_id, loan_type="heloc").all()
        heloc_debt = sum(heloc.calculate_current_value(current_lap) for heloc in helocs)
        
        # Calculate net worth
        net_worth = player.money + property_value + cd_value - loan_debt - heloc_debt
        
        return {
            "success": True,
            "summary": {
                "player_id": player_id,
                "player_name": player.username,
                "cash": player.money,
                "property_value": property_value,
                "property_count": len(properties),
                "loan_debt": loan_debt,
                "loan_count": len(loans),
                "cd_value": cd_value,
                "cd_count": len(cds),
                "heloc_debt": heloc_debt,
                "heloc_count": len(helocs),
                "net_worth": net_worth
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
        loan_total = sum(loan.calculate_current_value(loan.current_lap) for loan in loans)
        heloc_total = sum(heloc.calculate_current_value(heloc.current_lap) for heloc in helocs)
        cd_total = sum(cd.calculate_current_value(cd.current_lap) for cd in cds)
        
        total_debt = loan_total + heloc_total
        
        # Make sure player is eligible for bankruptcy
        # (can't pay even if all properties were liquidated)
        properties = Property.query.filter_by(owner_id=player_id).all()
        property_value = sum(prop.current_price for prop in properties)
        
        if player.money + property_value >= total_debt:
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
        starting_cash = getattr(GameState.query.first(), 'settings', {}).get("starting_cash", 1500)
        player.money = starting_cash
        player.bankruptcy_count += 1
        
        # 5. Severely damage credit score
        player.update_credit_score('bankruptcy', total_debt, True)
        
        db.session.add(player)
        
        # 6. Get current game state for transaction
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        # 7. Create transaction record
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
                "new_cash_balance": starting_cash,
                "bankruptcy_count": player.bankruptcy_count,
                "credit_score": player.credit_score
            })
            
        return {
            "success": True,
            "total_debt_forgiven": total_debt,
            "properties_lost": len(properties),
            "properties": [prop.name for prop in properties],
            "cds_lost": len(cds),
            "cd_value": cd_total,
            "new_cash_balance": starting_cash,
            "transaction_id": transaction.id,
            "bankruptcy_count": player.bankruptcy_count,
            "credit_score": player.credit_score
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
        
        net_worth = player.money + property_value
        
        # Maximum loan is 80% of net worth
        max_loan = int(net_worth * 0.8)
        
        # Get current outstanding loans
        loans = Loan.get_active_loans_for_player(player.id)
        helocs = Loan.get_active_helocs_for_player(player.id)
        
        # Get current game state for current lap
        game_state = GameState.query.first()
        current_lap = game_state.current_lap if game_state else 0
        
        current_debt = sum(loan.calculate_current_value(current_lap) for loan in loans + helocs)
        
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
        
        # Determine base rate based on credit score
        credit_rating = player.get_credit_rating()
        
        if credit_rating == "excellent":
            rate = rates.get("excellent_credit", rates["good_credit"] - 0.005)
        elif credit_rating == "good":
            rate = rates["good_credit"]
        elif credit_rating == "fair":
            rate = rates["standard"]
        else:  # poor credit
            rate = rates["poor_credit"]
            
        # Add penalty for bankruptcy history
        if player.bankruptcy_count > 0:
            rate += 0.01 * min(player.bankruptcy_count, 3)  # Maximum +3% for 3+ bankruptcies
            
        # Small adjustment based on loan amount
        # (larger loans have slightly higher rates)
        if amount > 1000:
            rate += 0.005
        if amount > 2000:
            rate += 0.005  # Additional 0.5% for very large loans
            
        # Get economic factors
        game_state = GameState.query.first()
        if game_state and hasattr(game_state, 'inflation_state'):
            # Economic state affects rates
            economic_adjustments = {
                "recession": -0.005,  # Lower rates during recession
                "normal": 0,
                "growth": 0.005,  # Higher rates during growth
                "boom": 0.01  # Higher rates during boom
            }
            
            rate += economic_adjustments.get(game_state.inflation_state, 0)
        
        # Ensure minimum rate
        return max(0.01, rate)  # Minimum 1% interest
    
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

    def get_financial_stats(self) -> Dict[str, Any]:
        """
        Get overall financial statistics for the game.
        """
        # Calculate total money in the game
        bank_reserves = self.game_state.bank.money
        
        # Calculate total player holdings
        player_holdings = sum(player.money for player in self.game_state.players.values())
        
        # Calculate total community fund
        community_fund = self.game_state.community_chest_fund
        
        # Calculate total active loans
        loans_total = sum(loan.amount for loan in self.game_state.loans.values())
        
        # Calculate total money in the game system
        total_money = bank_reserves + player_holdings + community_fund
        
        return {
            "total_money": total_money,
            "bank_reserves": bank_reserves,
            "player_holdings": player_holdings,
            "community_fund": community_fund,
            "loans_total": loans_total
        }
    
    def update_bank_settings(self, interest_rate: float, max_loan_amount: int, 
                            enable_automatic_fees: bool) -> Dict[str, Any]:
        """
        Update bank settings in the game.
        """
        # Update bank settings in game state
        self.game_state.bank.interest_rate = interest_rate
        self.game_state.bank.max_loan_amount = max_loan_amount
        self.game_state.bank.automatic_fees_enabled = enable_automatic_fees
        
        # Save game state
        self.game_state.save_game()
        
        logger.info(f"Bank settings updated: interest_rate={interest_rate}, "
                   f"max_loan_amount={max_loan_amount}, "
                   f"enable_automatic_fees={enable_automatic_fees}")
        
        return {
            "success": True,
            "message": "Bank settings updated successfully",
            "settings": {
                "interest_rate": interest_rate,
                "max_loan_amount": max_loan_amount,
                "enable_automatic_fees": enable_automatic_fees
            }
        }
    
    def perform_bank_audit(self) -> Dict[str, Any]:
        """
        Perform a bank audit to verify game finances are correct.
        """
        # Initial money in game (from game settings)
        initial_money = self.game_state.initial_bank_money
        
        # Current money calculations
        bank_money = self.game_state.bank.money
        player_money = sum(player.money for player in self.game_state.players.values())
        community_fund = self.game_state.community_chest_fund
        
        # Total current money in the system
        current_total = bank_money + player_money + community_fund
        
        # Check if money has been created or destroyed
        discrepancy = current_total - initial_money
        
        # Get transaction history for the audit report
        transactions = self.get_transaction_history(limit=10)
        
        audit_result = {
            "initial_money": initial_money,
            "current_total": current_total,
            "discrepancy": discrepancy,
            "is_balanced": discrepancy == 0,
            "bank_money": bank_money,
            "player_money": player_money,
            "community_fund": community_fund,
            "recent_transactions": transactions
        }
        
        logger.info(f"Bank audit performed: balanced={audit_result['is_balanced']}, "
                   f"discrepancy=${discrepancy}")
        
        return {
            "success": True,
            "message": f"Audit completed. {'Money is balanced.' if discrepancy == 0 else f'Discrepancy found: ${discrepancy}'}",
            "audit": audit_result
        }
    
    def get_active_loans(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active loans in the game.
        """
        active_loans = []
        
        for loan_id, loan in self.game_state.loans.items():
            if loan.active:
                player = self.game_state.get_player(loan.player_id)
                if player:
                    active_loans.append({
                        "id": loan_id,
                        "player_id": loan.player_id,
                        "player_name": player.display_name,
                        "amount": loan.amount,
                        "interest": f"{loan.interest_rate}%",
                        "due_date": f"Round {loan.due_round}" if loan.due_round else "Not specified",
                        "created_at": loan.created_at.strftime("%m/%d/%Y %H:%M")
                    })
        
        return active_loans
    
    def mark_loan_paid(self, loan_id: str) -> Dict[str, Any]:
        """
        Mark a loan as paid.
        """
        if loan_id not in self.game_state.loans:
            raise GameError(f"Loan with ID {loan_id} not found")
        
        loan = self.game_state.loans[loan_id]
        loan.active = False
        loan.paid_at = datetime.now()
        
        # Save game state
        self.game_state.save_game()
        
        logger.info(f"Loan {loan_id} marked as paid")
        
        return {
            "success": True,
            "message": f"Loan {loan_id} marked as paid"
        }
    
    def extend_loan(self, loan_id: str, additional_rounds: int = 3) -> Dict[str, Any]:
        """
        Extend a loan's due date.
        """
        if loan_id not in self.game_state.loans:
            raise GameError(f"Loan with ID {loan_id} not found")
        
        loan = self.game_state.loans[loan_id]
        
        if loan.due_round:
            loan.due_round += additional_rounds
        else:
            loan.due_round = self.game_state.current_round + additional_rounds
        
        # Save game state
        self.game_state.save_game()
        
        logger.info(f"Loan {loan_id} extended by {additional_rounds} rounds")
        
        return {
            "success": True,
            "message": f"Loan extended to round {loan.due_round}"
        }
    
    def adjust_player_cash(self, player_id: int, amount: int, reason: str) -> Dict[str, Any]:
        """
        Adjust a player's cash balance. Positive amount adds cash, negative removes it.
        """
        player = self.game_state.get_player(player_id)
        if not player:
            raise GameError(f"Player with ID {player_id} not found")
        
        # Record transaction in history
        transaction_type = "Credit" if amount >= 0 else "Debit"
        transaction = Transaction(
            from_entity="Admin",
            to_entity=player.display_name,
            amount=abs(amount),
            reason=reason,
            transaction_type=transaction_type
        )
        self.game_state.add_transaction(transaction)
        
        # Update player balance
        player.money += amount
        
        # Save game state
        self.game_state.save_game()
        
        logger.info(f"Player {player.display_name} cash adjusted by ${amount} for reason: {reason}")
        
        return {
            "success": True,
            "message": f"Player balance adjusted by ${amount}",
            "new_balance": player.money
        }
    
    def adjust_community_fund(self, amount: int, reason: str) -> Dict[str, Any]:
        """
        Adjust the community fund balance. Positive amount adds money, negative removes it.
        """
        # Record transaction in history
        transaction_type = "Credit" if amount >= 0 else "Debit"
        transaction = Transaction(
            from_entity="Admin" if amount >= 0 else "Community Fund",
            to_entity="Community Fund" if amount >= 0 else "Admin",
            amount=abs(amount),
            reason=reason,
            transaction_type=transaction_type
        )
        self.game_state.add_transaction(transaction)
        
        # Update community fund balance
        self.game_state.community_chest_fund += amount
        
        # Save game state
        self.game_state.save_game()
        
        logger.info(f"Community fund adjusted by ${amount} for reason: {reason}")
        
        return {
            "success": True,
            "message": f"Community fund adjusted by ${amount}",
            "new_balance": self.game_state.community_chest_fund
        }
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the transaction history for the game.
        """
        transactions = []
        
        # Get the most recent transactions first (limited by parameter)
        recent_transactions = list(self.game_state.transactions)[-limit:] if limit else self.game_state.transactions
        
        for tx in recent_transactions:
            transactions.append({
                "time": tx.timestamp.strftime("%H:%M:%S"),
                "type": tx.transaction_type,
                "from": tx.from_entity,
                "to": tx.to_entity,
                "amount": tx.amount,
                "reason": tx.reason
            })
        
        return transactions
    
    def format_interest_rates_for_display(self):
        """Format interest rates for display in the admin panel
        
        Returns:
            Dictionary with formatted interest rates
        """
        # Get the current rates
        rates = self.get_interest_rates()
        
        # Format rates for display
        formatted_rates = {
            "base_interest_rate": f"{rates['base_rate'] * 100:.2f}%",
            "loan_rate": f"{rates['rates']['loan']['standard'] * 100:.2f}%",
            "savings_rate": f"{rates['rates']['cd']['medium_term'] * 100:.2f}%",
            "mortgage_rate": f"{rates['rates']['heloc']['standard'] * 100:.2f}%"
        }
        
        return formatted_rates 