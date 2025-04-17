from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime
from src.models import db
from src.models.finance.loan import Loan
from src.models.player import Player
from src.models.transaction import Transaction
from src.models.game_state import GameState
from src.controllers.finance_controller import FinanceController
from src.routes.decorators import admin_required
from src.utils.errors import GameError

logger = logging.getLogger(__name__)
finance_admin_bp = Blueprint('finance_admin', __name__, url_prefix='/finance')

# Initialize the finance controller - this will be replaced with a function
# that gets dependencies from app context
finance_controller = None

def get_finance_controller():
    """Get finance controller with dependencies from app context"""
    global finance_controller
    if finance_controller is None:
        finance_controller = FinanceController(
            socketio=current_app.config.get('socketio'),
            banker=current_app.config.get('banker'),
            game_state=current_app.config.get('game_state_instance')
        )
    return finance_controller

@finance_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_financial_stats():
    """Get overall financial statistics for the admin dashboard"""
    try:
        stats = get_finance_controller().get_financial_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"Error getting financial stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def manage_bank_settings():
    """Get or update bank settings"""
    try:
        if request.method == 'GET':
            # Return current settings
            return jsonify({
                "success": True,
                "interest_rate": get_finance_controller().game_state.loan_interest_rate,
                "max_loan_amount": get_finance_controller().game_state.max_loan_amount,
                "enable_automatic_fees": get_finance_controller().game_state.automatic_fees_enabled
            })
        else:
            # Update settings
            data = request.json
            
            # Update interest rate if provided
            if 'interest_rate' in data:
                get_finance_controller().game_state.loan_interest_rate = float(data['interest_rate'])
            
            # Update max loan amount if provided
            if 'max_loan_amount' in data:
                get_finance_controller().game_state.max_loan_amount = int(data['max_loan_amount'])
            
            # Update automatic fees setting if provided
            if 'enable_automatic_fees' in data:
                get_finance_controller().game_state.automatic_fees_enabled = bool(data['enable_automatic_fees'])
            
            # Save changes
            db.session.commit()
            
            logger.info(f"Bank settings updated: interest_rate={get_finance_controller().game_state.loan_interest_rate}, "
                       f"max_loan_amount={get_finance_controller().game_state.max_loan_amount}, "
                       f"automatic_fees={get_finance_controller().game_state.automatic_fees_enabled}")
            
            return jsonify({
                "success": True,
                "message": "Bank settings updated successfully"
            })
    except Exception as e:
        logger.error(f"Error managing bank settings: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/modify-player-cash', methods=['POST'])
@admin_required
def adjust_player_money():
    """Adjust a player's cash balance"""
    try:
        data = request.json
        player_id = data.get('player_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Admin adjustment')
        
        if not player_id or amount is None:
            return jsonify({
                "success": False,
                "error": "Player ID and amount are required"
            }), 400
        
        # Convert amount to int
        try:
            amount = int(amount)
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Amount must be a valid number"
            }), 400
        
        # Get the player
        player = Player.query.get(player_id)
        if not player:
            return jsonify({
                "success": False,
                "error": "Player not found"
            }), 404
        
        # Adjust player's cash
        player.money += amount
        
        # Create transaction record
        transaction = Transaction(
            from_player_id=None if amount > 0 else player_id,  # From bank if adding, from player if subtracting
            to_player_id=player_id if amount > 0 else None,  # To player if adding, to bank if subtracting
            amount=abs(amount),
            transaction_type="admin_adjustment",
            description=reason,
            timestamp=datetime.now()
        )
        
        # Save changes
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Player {player.username} (ID: {player_id}) money adjusted by ${amount}. Reason: {reason}")
        
        return jsonify({
            "success": True,
            "player_id": player_id,
            "player_name": player.username,
            "adjustment": amount,
            "new_balance": player.money,
            "reason": reason,
            "transaction_id": transaction.id
        })
    except Exception as e:
        logger.error(f"Error adjusting player money: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/community-fund', methods=['GET', 'POST'])
@admin_required
def manage_community_fund():
    """Get or update community fund balance"""
    try:
        if request.method == 'GET':
            # Return current balance
            return jsonify({
                "success": True,
                "balance": get_finance_controller().game_state.community_fund
            })
        else:
            # Update community fund
            data = request.json
            action = data.get('action')
            amount = data.get('amount')
            reason = data.get('reason', 'Admin action')
            
            if not action:
                return jsonify({
                    "success": False,
                    "error": "Action is required (add, withdraw, or reset)"
                }), 400
                
            if action not in ['add', 'withdraw', 'reset']:
                return jsonify({
                    "success": False,
                    "error": "Invalid action. Must be add, withdraw, or reset"
                }), 400
                
            # For add or withdraw, amount is required
            if action in ['add', 'withdraw'] and not amount:
                return jsonify({
                    "success": False,
                    "error": "Amount is required for add or withdraw actions"
                }), 400
                
            # Convert amount to int if provided
            if amount:
                try:
                    amount = int(amount)
                except ValueError:
                    return jsonify({
                        "success": False,
                        "error": "Amount must be a valid number"
                    }), 400
            
            # Update community fund based on action
            old_balance = get_finance_controller().game_state.community_fund
            if action == 'add':
                get_finance_controller().game_state.community_fund += amount
                db.session.commit()
                logger.info(f"Added ${amount} to community fund. Reason: {reason}")
            elif action == 'withdraw':
                if get_finance_controller().game_state.community_fund < amount:
                    return jsonify({
                        "success": False,
                        "error": "Not enough funds in community fund",
                        "requested": amount,
                        "available": get_finance_controller().game_state.community_fund
                    }), 400
                get_finance_controller().game_state.community_fund -= amount
                db.session.commit()
                logger.info(f"Withdrew ${amount} from community fund. Reason: {reason}")
            elif action == 'reset':
                get_finance_controller().game_state.community_fund = 0
                db.session.commit()
                logger.info(f"Reset community fund to zero. Reason: {reason}")
            
            return jsonify({
                "success": True,
                "action": action,
                "old_balance": old_balance,
                "new_balance": get_finance_controller().game_state.community_fund,
                "amount": amount if action != 'reset' else old_balance
            })
    except Exception as e:
        logger.error(f"Error managing community fund: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans', methods=['GET'])
@admin_required
def get_active_loans():
    """Get all active loans"""
    try:
        loans = get_finance_controller().get_active_loans()
        return jsonify({"success": True, "loans": loans})
    except Exception as e:
        logger.error(f"Error getting active loans: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans/create', methods=['POST'])
@admin_required
def create_loan():
    """Create a new loan for a player"""
    try:
        data = request.json
        player_id = data.get('player_id')
        amount = data.get('amount')
        interest_rate = data.get('interest_rate')
        term = data.get('term')
        reason = data.get('reason', 'Admin issued loan')
        
        if not player_id or not amount or interest_rate is None or not term:
            return jsonify({
                "success": False,
                "error": "Player ID, amount, interest rate, and term are required"
            }), 400
        
        # Convert to proper types
        try:
            amount = int(amount)
            interest_rate = float(interest_rate) / 100  # Convert from percentage to decimal
            term = int(term)
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Invalid number format"
            }), 400
        
        # Get the player
        player = Player.query.get(player_id)
        if not player:
            return jsonify({
                "success": False,
                "error": "Player not found"
            }), 404
        
        # Get current game state
        game_state = GameState.get_instance()
        current_lap = game_state.current_lap if game_state else 0
        
        # Create the loan
        loan = Loan(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            length_laps=term,
            issued_lap=current_lap,
            status='active',
            loan_type='loan',
            description=reason
        )
        
        # Give money to player
        player.money += amount
        
        # Create transaction record
        transaction = Transaction(
            from_player_id=None,  # From bank
            to_player_id=player_id,
            amount=amount,
            transaction_type="loan_issued",
            description=reason,
            timestamp=datetime.now()
        )
        
        # Save changes
        db.session.add(loan)
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Loan created for player {player.username} (ID: {player_id}): "
                   f"${amount} at {interest_rate*100:.1f}% for {term} rounds")
        
        return jsonify({
            "success": True,
            "loan_id": loan.id,
            "player_id": player_id,
            "player_name": player.username,
            "amount": amount,
            "interest_rate": interest_rate,
            "term": term,
            "reason": reason
        })
    except Exception as e:
        logger.error(f"Error creating loan: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans/<int:loan_id>/pay', methods=['POST'])
@admin_required
def mark_loan_paid(loan_id):
    """Mark a loan as paid"""
    try:
        result = get_finance_controller().mark_loan_paid(loan_id)
        return jsonify(result)
    except GameError as e:
        logger.error(f"Game error marking loan {loan_id} as paid: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error marking loan {loan_id} as paid: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans/<int:loan_id>/extend', methods=['POST'])
@admin_required
def extend_loan(loan_id):
    """Extend a loan by additional rounds"""
    try:
        data = request.json
        additional_rounds = data.get('additional_rounds')
        
        if not additional_rounds:
            return jsonify({
                "success": False,
                "error": "Additional rounds are required"
            }), 400
        
        try:
            additional_rounds = int(additional_rounds)
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Additional rounds must be a valid number"
            }), 400
        
        # Get the loan
        loan = Loan.query.get(loan_id)
        if not loan:
            return jsonify({
                "success": False,
                "error": "Loan not found"
            }), 404
        
        # Get the player
        player = Player.query.get(loan.player_id)
        if not player:
            return jsonify({
                "success": False,
                "error": "Player not found"
            }), 404
        
        # Extend the loan
        old_length = loan.length_laps
        loan.length_laps += additional_rounds
        db.session.commit()
        
        logger.info(f"Loan {loan_id} for player {player.username} (ID: {loan.player_id}) "
                   f"extended from {old_length} to {loan.length_laps} rounds")
        
        # Get updated due date
        game_state = GameState.get_instance()
        current_lap = game_state.current_lap if game_state else 0
        due_lap = loan.issued_lap + loan.length_laps
        
        return jsonify({
            "success": True,
            "loan_id": loan_id,
            "player_id": loan.player_id,
            "player_name": player.username,
            "old_length": old_length,
            "new_length": loan.length_laps,
            "additional_rounds": additional_rounds,
            "new_due_date": f"Round {due_lap}",
            "rounds_left": max(0, due_lap - current_lap)
        })
    except Exception as e:
        logger.error(f"Error extending loan: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/transactions', methods=['GET'])
@admin_required
def get_transactions():
    """Get recent transactions"""
    try:
        # Get limit parameter (default 20)
        limit = request.args.get('limit', 20, type=int)
        
        # Get recent transactions
        transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        transaction_data = []
        for t in transactions:
            # Get player names
            from_player = Player.query.get(t.from_player_id) if t.from_player_id else None
            to_player = Player.query.get(t.to_player_id) if t.to_player_id else None
            
            from_name = from_player.username if from_player else "Bank"
            to_name = to_player.username if to_player else "Bank"
            
            # Format time
            time_str = t.timestamp.strftime("%I:%M %p") if t.timestamp else "Unknown"
            
            transaction_data.append({
                "id": t.id,
                "time": time_str,
                "type": t.transaction_type,
                "from": from_name,
                "to": to_name,
                "amount": t.amount,
                "reason": t.description
            })
        
        return jsonify({
            "success": True,
            "transactions": transaction_data
        })
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/audit', methods=['POST'])
@admin_required
def trigger_bank_audit():
    """Trigger a bank audit to verify all accounts and transactions"""
    try:
        audit_result = get_finance_controller().perform_bank_audit()
        return jsonify(audit_result)
    except Exception as e:
        logger.error(f"Error during bank audit: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/overview', methods=['GET'])
@admin_required
def get_finance_overview():
    """Get basic financial overview for the admin dashboard"""
    try:
        # Get financial stats from controller
        stats = get_finance_controller().get_financial_stats()
        
        # Get current interest rates
        rates = get_finance_controller().get_interest_rates()
        
        # Combine data for overview
        overview = {
            "success": True,
            "stats": stats,
            "rates": rates
        }
        
        return jsonify(overview)
    except Exception as e:
        logger.error(f"Error getting finance overview: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 