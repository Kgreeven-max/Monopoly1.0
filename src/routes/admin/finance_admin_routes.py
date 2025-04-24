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
from src.controllers.admin_controller import AdminController
from sqlalchemy import func

logger = logging.getLogger(__name__)
finance_admin_bp = Blueprint('finance_admin', __name__, url_prefix='/finance')

# Initialize the finance controller - this will be replaced with a function
# that gets dependencies from app context
finance_controller = None

# Initialize the admin controller
admin_controller = None

def get_admin_controller():
    """Get admin controller with dependencies from app context"""
    global admin_controller
    if admin_controller is None:
        from src.controllers.admin_controller import AdminController
        admin_controller = AdminController()
    return admin_controller

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

@finance_admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_finance_settings():
    """
    Get current financial system settings.
    
    Returns settings for interest rates, loans, taxes, and other economic parameters.
    """
    try:
        result = admin_controller.get_finance_settings()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting finance settings: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_finance_settings():
    """
    Update financial system settings.
    
    Request body may include:
    - interest_rate: Bank interest rate
    - loan_interest_rate: Loan interest rate
    - income_tax_rate: Income tax rate
    - property_tax_rate: Property tax rate
    - loan_term_limits: Limits for loan terms
    - bankruptcy_threshold: Threshold for declaring bankruptcy
    - starting_cash: Starting cash for new players
    - inflation_rate: Game inflation rate
    """
    try:
        # Get update data from request
        update_data = request.json
        
        if not update_data:
            return jsonify({"success": False, "error": "Update data is required"}), 400
        
        # Call the controller method
        result = admin_controller.update_finance_settings(update_data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error updating finance settings: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/modify-cash/<int:player_id>', methods=['POST'])
@admin_required
def modify_player_cash(player_id):
    """
    Modify a player's cash balance.
    
    Request body:
    - amount: Amount to add or subtract (positive to add, negative to subtract)
    - reason: Reason for the modification
    - record_transaction: Whether to record this as a transaction (default: true)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Cash modification data is required"}), 400
        
        amount = data.get('amount')
        reason = data.get('reason', 'Admin adjustment')
        record_transaction = data.get('record_transaction', True)
        
        if amount is None:
            return jsonify({"success": False, "error": "Amount is required"}), 400
        
        # Call the controller method
        result = admin_controller.modify_player_cash(player_id, amount, reason, record_transaction)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error modifying cash for player {player_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/transactions', methods=['GET'])
@admin_required
def get_transactions():
    """
    Get transaction history with filtering options.
    
    Query parameters:
    - player_id: Filter by player ID
    - type: Filter by transaction type
    - min_amount: Minimum transaction amount
    - max_amount: Maximum transaction amount
    - start_date: Transactions after this date
    - end_date: Transactions before this date
    - limit: Maximum number of transactions to return (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    try:
        # Get filter parameters
        filters = {}
        
        if 'player_id' in request.args:
            filters['player_id'] = int(request.args.get('player_id'))
        
        if 'type' in request.args:
            filters['type'] = request.args.get('type')
        
        if 'min_amount' in request.args:
            filters['min_amount'] = float(request.args.get('min_amount'))
        
        if 'max_amount' in request.args:
            filters['max_amount'] = float(request.args.get('max_amount'))
        
        if 'start_date' in request.args:
            filters['start_date'] = request.args.get('start_date')
        
        if 'end_date' in request.args:
            filters['end_date'] = request.args.get('end_date')
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Call the controller method
        admin_controller = get_admin_controller()
        result = admin_controller.get_transactions(filters, limit, offset)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting transactions: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/create-transaction', methods=['POST'])
@admin_required
def create_transaction():
    """
    Create a new transaction between players or between player and bank.
    
    Request body:
    - from_player_id: Source player ID (null for bank)
    - to_player_id: Destination player ID (null for bank)
    - amount: Transaction amount
    - transaction_type: Type of transaction
    - description: Description of the transaction
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Transaction data is required"}), 400
        
        from_player_id = data.get('from_player_id')
        to_player_id = data.get('to_player_id')
        amount = data.get('amount')
        transaction_type = data.get('transaction_type', 'admin_transfer')
        description = data.get('description', 'Admin created transaction')
        
        if amount is None:
            return jsonify({"success": False, "error": "Amount is required"}), 400
        
        if from_player_id is None and to_player_id is None:
            return jsonify({"success": False, "error": "At least one player ID is required"}), 400
        
        # Call the controller method
        result = admin_controller.create_transaction(
            from_player_id,
            to_player_id,
            amount,
            transaction_type,
            description
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/reset-economy', methods=['POST'])
@admin_required
def reset_economy():
    """
    Reset the economy to a baseline state.
    
    Request body:
    - reset_player_balances: Whether to reset player cash balances to starting amount (default: false)
    - reset_bank_balance: Whether to reset bank balance (default: false)
    - reset_property_values: Whether to reset property values (default: false)
    - confirmation: Must be set to "CONFIRM_RESET" for safety
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Reset data is required"}), 400
        
        confirmation = data.get('confirmation')
        
        if confirmation != "CONFIRM_RESET":
            return jsonify({"success": False, "error": "Confirmation string 'CONFIRM_RESET' is required"}), 400
        
        reset_player_balances = data.get('reset_player_balances', False)
        reset_bank_balance = data.get('reset_bank_balance', False)
        reset_property_values = data.get('reset_property_values', False)
        
        # Call the controller method
        result = admin_controller.reset_economy(
            reset_player_balances,
            reset_bank_balance,
            reset_property_values
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error resetting economy: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/audit', methods=['POST'])
@admin_required
def audit_economic_system():
    """
    Perform a full audit of the economic system.
    
    Checks for inconsistencies in player balances, transactions, and property values.
    
    Request body (optional):
    - fix_issues: Whether to attempt to fix discovered issues (default: false)
    """
    try:
        # Handle empty request body gracefully
        fix_issues = False
        
        try:
            # Try to get JSON data, but don't fail if there is none
            data = request.get_json(silent=True) or {}
            fix_issues = data.get('fix_issues', False)
            logger.info(f"Audit requested with fix_issues={fix_issues}")
        except Exception as e:
            logger.warning(f"No JSON data provided or invalid JSON: {str(e)}")
            data = {}
        
        # Call the controller method
        logger.info("Calling admin_controller.audit_economic_system")
        result = admin_controller.audit_economic_system(fix_issues)
        logger.info(f"Audit completed with success={result.get('success')}")
        
        if result.get('success'):
            logger.info(f"Audit successful: {result.get('message', 'No message')}")
            logger.info(f"Issues found: {result.get('issues_found', 0)}, Issues fixed: {result.get('issues_fixed', 0)}")
            return jsonify(result), 200
        else:
            logger.error(f"Audit failed: {result.get('error', 'No error message provided')}")
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error auditing economic system: {e}", exc_info=True)
        error_response = {
            "success": False, 
            "error": str(e),
            "traceback": str(e.__traceback__)
        }
        return jsonify(error_response), 500

@finance_admin_bp.route('/loans', methods=['GET'])
@admin_required
def get_all_loans():
    """
    Get all loans in the system with filtering options.
    
    Query parameters:
    - player_id: Filter by player ID
    - status: Filter by loan status ('active' or 'paid')
    - loan_type: Filter by loan type ('loan', 'heloc', etc.)
    - limit: Maximum number of loans to return (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    try:
        # Get filters from query parameters
        filters = {}
        
        if 'player_id' in request.args:
            filters['player_id'] = int(request.args.get('player_id'))
        
        if 'status' in request.args:
            filters['status'] = request.args.get('status')
        
        if 'loan_type' in request.args:
            filters['loan_type'] = request.args.get('loan_type')
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Call the controller method
        admin_controller = get_admin_controller()
        result = admin_controller.get_all_loans(filters)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting all loans: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans/<int:loan_id>', methods=['PUT'])
@admin_required
def modify_loan(loan_id):
    """
    Modify an existing loan's terms.
    
    Request body may include:
    - interest_rate: New interest rate
    - remaining_amount: New remaining amount
    - term_remaining: New remaining term (in turns)
    - status: New loan status
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Loan modification data is required"}), 400
        
        # Call the controller method
        result = admin_controller.modify_loan(loan_id, data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error modifying loan {loan_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans', methods=['POST'])
@admin_required
def create_loan():
    """
    Create a new loan for a player.
    
    Request body:
    - player_id: ID of the player receiving the loan
    - amount: Loan amount
    - interest_rate: Interest rate
    - term: Loan term in turns
    - reason: Reason for the loan
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "error": "Loan data is required"}), 400
        
        player_id = data.get('player_id')
        amount = data.get('amount')
        interest_rate = data.get('interest_rate')
        term = data.get('term')
        reason = data.get('reason', 'Admin created loan')
        
        if player_id is None:
            return jsonify({"success": False, "error": "Player ID is required"}), 400
        
        if amount is None:
            return jsonify({"success": False, "error": "Amount is required"}), 400
        
        if interest_rate is None:
            return jsonify({"success": False, "error": "Interest rate is required"}), 400
        
        if term is None:
            return jsonify({"success": False, "error": "Term is required"}), 400
        
        # Call the controller method
        result = admin_controller.create_loan(
            player_id,
            amount,
            interest_rate,
            term,
            reason
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error creating loan: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/audit-player/<int:player_id>', methods=['POST'])
@admin_required
def audit_player(player_id):
    """
    Perform a financial audit on a specific player.
    
    Checks for inconsistencies in the player's balance, properties, and transaction history.
    
    Request body (optional):
    - fix_issues: Whether to attempt to fix discovered issues (default: false)
    """
    try:
        data = request.json or {}
        fix_issues = data.get('fix_issues', False)
        
        # Call the controller method
        result = admin_controller.audit_player_finances(player_id, fix_issues)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error auditing player {player_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/debt-collection', methods=['POST'])
@admin_required
def trigger_debt_collection():
    """
    Trigger a debt collection cycle.
    
    Forces all outstanding debts to be processed, including loan payments, property taxes, etc.
    
    Request body (optional):
    - force_action: Whether to force collection even if players can't pay (default: false)
    """
    try:
        data = request.json or {}
        force_action = data.get('force_action', False)
        
        # Call the controller method
        result = admin_controller.trigger_debt_collection(force_action)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error triggering debt collection: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/economy-stats', methods=['GET'])
@admin_required
def get_economy_stats():
    """
    Get statistics about the game's economy.
    
    Returns information about cash distribution, property values, bank reserves, etc.
    
    Query parameters:
    - time_period: Period for trend data (day, week, month, all)
    """
    try:
        # Check if the AdminController has the required method
        if not hasattr(admin_controller, 'get_economy_stats'):
            logger.warning("get_economy_stats method not implemented in AdminController")
            return jsonify({
                "success": False,
                "error": "This endpoint is not yet implemented"
            }), 501  # 501 Not Implemented is more appropriate here
        
        time_period = request.args.get('time_period', 'all')
        
        # Call the controller method
        result = admin_controller.get_economy_stats(time_period)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error getting economy stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/overview', methods=['GET'])
@admin_required
def get_financial_overview():
    """Get financial system overview for the admin dashboard."""
    try:
        # Get player financial data from AdminController
        admin_controller = get_admin_controller()
        financial_data = admin_controller.get_player_financial_data()
        if not financial_data.get('success'):
            return jsonify({
                "success": False, 
                "error": financial_data.get('error', 'Failed to retrieve player financial data')
            }), 500

        # Get game state for economic data
        game_state = GameState.query.first()
        if not game_state:
            return jsonify({
                "success": False, 
                "error": "Game state not found"
            }), 500

        # Get community fund balance - use balance property instead of get_balance method
        community_fund = current_app.config.get('community_fund')
        community_fund_balance = 0
        
        # Try different ways to get the community fund balance
        if community_fund:
            if hasattr(community_fund, 'balance'):
                community_fund_balance = community_fund.balance
            elif hasattr(community_fund, 'funds'):
                community_fund_balance = community_fund.funds
            elif hasattr(community_fund, 'get_balance'):
                community_fund_balance = community_fund.get_balance()
            elif hasattr(community_fund, '_funds'): # Direct access to internal attribute
                community_fund_balance = community_fund._funds
            elif hasattr(community_fund, 'fund_balance'):
                community_fund_balance = community_fund.fund_balance
            elif hasattr(community_fund, 'amount'):
                community_fund_balance = community_fund.amount
            # Add fallback for free_parking_fund in game_state
            elif game_state and hasattr(game_state, 'free_parking_fund'):
                community_fund_balance = game_state.free_parking_fund
        
        # Fallback to game state settings
        if community_fund_balance == 0 and game_state and hasattr(game_state, 'settings'):
            community_fund_balance = game_state.settings.get("community_fund", 0)

        # Count active loans
        active_loans = Loan.query.filter_by(is_active=True).count()
        loan_total = db.session.query(func.sum(Loan.amount)).filter_by(is_active=True).scalar() or 0

        # Calculate bank reserves (if banker has balance property)
        banker = current_app.config.get('banker')
        bank_reserves = 0
        if banker:
            if hasattr(banker, 'balance'):
                bank_reserves = banker.balance
            elif hasattr(banker, 'get_balance'):
                bank_reserves = banker.get_balance()
            elif hasattr(banker, 'money'):
                bank_reserves = banker.money
            elif hasattr(banker, 'cash'):
                bank_reserves = banker.cash
            else:
                # Fallback estimate
                bank_reserves = 1500 * 10

        # Build stats object
        stats = {
            "total_money": financial_data.get('total_money', 0),
            "bank_reserves": bank_reserves,
            "player_holdings": financial_data.get('total_money', 0),
            "community_fund": community_fund_balance,
            "loans_count": active_loans,
            "loans_total": loan_total,
            "player_count": financial_data.get('total_players', 0)
        }

        # Get interest rates based on economic state
        base_rate = game_state.base_interest_rate if hasattr(game_state, 'base_interest_rate') else 0.05
        economic_state = game_state.economic_cycle_state if hasattr(game_state, 'economic_cycle_state') else "normal"
        
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
                    "poor_credit": base_rate + modifier + 0.05
                },
                "cd": {
                    "short_term": base_rate - 0.01,
                    "medium_term": base_rate,
                    "long_term": base_rate + 0.01
                },
                "heloc": base_rate + 0.03
            }
        }
        
        # Format rates for display
        formatted_rates = {
            "base_interest_rate": f"{(base_rate * 100):.2f}%",
            "loan_rate": f"{((base_rate + modifier + 0.02) * 100):.2f}%",
            "savings_rate": f"{(base_rate * 100):.2f}%",
            "mortgage_rate": f"{((base_rate + 0.03) * 100):.2f}%"
        }
        
        # Try to get formatted rates from finance controller
        finance_controller = get_finance_controller()
        if finance_controller and hasattr(finance_controller, 'format_interest_rates_for_display'):
            try:
                formatted_rates = finance_controller.format_interest_rates_for_display()
            except Exception as e:
                logger.warning(f"Could not get formatted rates from finance controller: {e}")
        
        return jsonify({
            "success": True,
            "stats": stats,
            "rates": rates,
            "formatted_rates": formatted_rates
        })
        
    except Exception as e:
        logger.error(f"Error getting financial overview: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 