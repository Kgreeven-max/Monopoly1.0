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

logger = logging.getLogger(__name__)
finance_admin_bp = Blueprint('finance_admin', __name__, url_prefix='/finance')

# Initialize the finance controller - this will be replaced with a function
# that gets dependencies from app context
finance_controller = None

# Initialize the admin controller
admin_controller = AdminController()

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
        data = request.json or {}
        fix_issues = data.get('fix_issues', False)
        
        # Call the controller method
        result = admin_controller.audit_economic_system(fix_issues)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error auditing economic system: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@finance_admin_bp.route('/loans', methods=['GET'])
@admin_required
def get_all_loans():
    """
    Get a list of all active loans in the game.
    
    Query parameters:
    - player_id: Filter by player ID
    - status: Filter by loan status
    """
    try:
        # Get filter parameters
        filters = {}
        
        if 'player_id' in request.args:
            filters['player_id'] = int(request.args.get('player_id'))
        
        if 'status' in request.args:
            filters['status'] = request.args.get('status')
        
        # Call the controller method
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
    """
    Get a comprehensive overview of the financial system.
    
    Returns summary statistics on loans, transactions, player finances, and economic indicators.
    """
    try:
        # Create a basic default response structure
        default_response = {
            "success": True,
            "game_state": {
                "current_lap": 0,
                "game_id": None,
                "free_parking_fund": 0
            },
            "players": {
                "count": 0,
                "total_cash": 0,
                "average_cash": 0,
                "richest_player": None
            },
            "loans": {
                "total_count": 0,
                "active_count": 0,
                "total_active_value": 0,
                "avg_loan_value": 0
            },
            "transactions": {
                "total_count": 0,
                "recent_volume": 0,
                "recent_count": 0
            },
            "properties": {
                "total_count": 0,
                "bank_owned": 0,
                "player_owned": 0,
                "mortgaged": 0,
                "mortgage_rate": 0
            },
            "economic_indicators": {
                "debt_ratio": 0,
                "liquidity_index": 0,
                "market_activity": 0
            }
        }
        
        # Get game state
        game_state = GameState.get_instance()
        if not game_state:
            logger.warning("No game state instance found")
            return jsonify(default_response), 200
            
        current_lap = game_state.current_lap if game_state else 0
        
        # Ensure current_lap is not None before comparison
        if current_lap is None:
            current_lap = 0
        
        # Update game state in response
        default_response["game_state"]["current_lap"] = current_lap
        default_response["game_state"]["game_id"] = game_state.game_id if game_state else None
        
        # Check if game_state has free_parking_fund attribute
        if game_state and hasattr(game_state, 'free_parking_fund'):
            default_response["game_state"]["free_parking_fund"] = game_state.free_parking_fund
        
        try:
            # Get all players - handle empty case
            players = Player.query.filter_by(in_game=True).all() or []
            player_count = len(players)
            
            # Update players in response
            default_response["players"]["count"] = player_count
            
            if player_count > 0:
                # Get cash statistics
                total_player_cash = sum(player.cash for player in players)
                avg_player_cash = total_player_cash / player_count
                richest_player = max(players, key=lambda p: p.cash)
                
                default_response["players"]["total_cash"] = total_player_cash
                default_response["players"]["average_cash"] = avg_player_cash
                default_response["players"]["richest_player"] = {
                    "id": richest_player.id,
                    "username": richest_player.username,
                    "cash": richest_player.cash
                }
        except Exception as player_error:
            logger.error(f"Error processing player data: {player_error}")
            
        try:
            # Get loan statistics - handle empty case
            loans = Loan.query.all() or []
            active_loans = sum(1 for loan in loans if loan.is_active)
            total_loan_value = sum(loan.outstanding_balance for loan in loans if loan.is_active)
            
            default_response["loans"]["total_count"] = len(loans)
            default_response["loans"]["active_count"] = active_loans
            default_response["loans"]["total_active_value"] = total_loan_value
            default_response["loans"]["avg_loan_value"] = total_loan_value / active_loans if active_loans > 0 else 0
        except Exception as loan_error:
            logger.error(f"Error processing loan data: {loan_error}")
            
        try:
            # Get transaction statistics - handle empty case
            transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(100).all() or []
            transaction_count = Transaction.query.count() or 0
            recent_transaction_volume = sum(abs(t.amount) for t in transactions)
            
            default_response["transactions"]["total_count"] = transaction_count
            default_response["transactions"]["recent_volume"] = recent_transaction_volume
            default_response["transactions"]["recent_count"] = len(transactions)
        except Exception as transaction_error:
            logger.error(f"Error processing transaction data: {transaction_error}")
            
        try:
            # Get property statistics - handle empty case
            from src.models.property import Property
            properties = Property.query.all() or []
            bank_owned = sum(1 for p in properties if not p.owner_id)
            player_owned = sum(1 for p in properties if p.owner_id)
            mortgaged = sum(1 for p in properties if p.is_mortgaged)
            
            default_response["properties"]["total_count"] = len(properties)
            default_response["properties"]["bank_owned"] = bank_owned
            default_response["properties"]["player_owned"] = player_owned
            default_response["properties"]["mortgaged"] = mortgaged
            default_response["properties"]["mortgage_rate"] = mortgaged / len(properties) if properties else 0
        except Exception as property_error:
            logger.error(f"Error processing property data: {property_error}")
            
        # Calculate economic health indicators
        try:
            if default_response["players"]["total_cash"] > 0:
                debt_ratio = default_response["loans"]["total_active_value"] / default_response["players"]["total_cash"]
                default_response["economic_indicators"]["debt_ratio"] = debt_ratio
                
            liquidity_index = default_response["players"]["total_cash"] / (default_response["loans"]["total_active_value"] + 1)  # Add 1 to avoid division by zero
            default_response["economic_indicators"]["liquidity_index"] = liquidity_index
            
            market_activity = default_response["transactions"]["total_count"] / (current_lap + 1) if current_lap > 0 else default_response["transactions"]["total_count"]
            default_response["economic_indicators"]["market_activity"] = market_activity
        except Exception as indicator_error:
            logger.error(f"Error calculating economic indicators: {indicator_error}")
        
        return jsonify(default_response), 200
    
    except Exception as e:
        logger.error(f"Error fetching finance overview: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500 