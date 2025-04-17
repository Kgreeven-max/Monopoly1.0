from flask import Blueprint, jsonify, request
import logging
from src.controllers.finance_controller import FinanceController

logger = logging.getLogger(__name__)

def register_finance_routes(app):
    """Register finance-related routes with the Flask app"""
    finance_controller = FinanceController(
        socketio=app.config.get('socketio'),
        banker=app.config.get('banker'),
        game_state=app.config.get('game_state_instance')
    )
    
    logger.info(f"Finance controller initialized with: socketio={finance_controller.socketio is not None}, "
               f"banker={finance_controller.banker is not None}, "
               f"game_state={finance_controller.game_state is not None}")
    
    @app.route('/api/finance/loan/new', methods=['POST'])
    def new_loan():
        """Take out a new loan"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        amount = data.get('amount')
        
        if not player_id or not pin or not amount:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and amount are required'}), 400
        
        result = finance_controller.create_loan(player_id, pin, amount)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/loan/repay', methods=['POST'])
    def repay_loan():
        """Repay a loan fully or partially"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        loan_id = data.get('loan_id')
        amount = data.get('amount')  # Optional, full amount if not provided
        
        if not player_id or not pin or not loan_id:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and loan ID are required'}), 400
        
        result = finance_controller.repay_loan(player_id, pin, loan_id, amount)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/cd/new', methods=['POST'])
    def new_cd():
        """Create a new Certificate of Deposit"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        amount = data.get('amount')
        length_laps = data.get('length_laps')  # 3, 5, or 7
        
        if not player_id or not pin or not amount or not length_laps:
            return jsonify({'success': False, 'error': 'Player ID, PIN, amount, and length are required'}), 400
        
        result = finance_controller.create_cd(player_id, pin, amount, length_laps)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/cd/withdraw', methods=['POST'])
    def withdraw_cd():
        """Withdraw from a Certificate of Deposit"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        cd_id = data.get('cd_id')
        
        if not player_id or not pin or not cd_id:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and CD ID are required'}), 400
        
        result = finance_controller.withdraw_cd(player_id, pin, cd_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/heloc/new', methods=['POST'])
    def new_heloc():
        """Take out a Home Equity Line of Credit on a property"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        property_id = data.get('property_id')
        amount = data.get('amount')
        
        if not player_id or not pin or not property_id or not amount:
            return jsonify({'success': False, 'error': 'Player ID, PIN, property ID, and amount are required'}), 400
        
        result = finance_controller.create_heloc(player_id, pin, property_id, amount)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/interest-rates', methods=['GET'])
    def get_interest_rates():
        """Get current interest rates for loans and CDs"""
        result = finance_controller.get_interest_rates()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/loans', methods=['GET'])
    def get_player_loans():
        """Get a list of a player's loans and CDs"""
        player_id = request.args.get('player_id')
        pin = request.args.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = finance_controller.get_player_loans(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/finance/bankruptcy', methods=['POST'])
    def declare_bankruptcy():
        """Declare bankruptcy when unable to pay debts"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = finance_controller.declare_bankruptcy(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    return app 