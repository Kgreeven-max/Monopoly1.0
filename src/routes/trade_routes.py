from flask import jsonify, request, current_app
from src.controllers.trade_controller import TradeController
from functools import wraps
import logging
# Import shared decorator
from src.routes.decorators import admin_required

logger = logging.getLogger(__name__)

def register_trade_routes(app):
    """Register trade-related routes with the Flask app"""
    trade_controller = TradeController()
    
    @app.route('/api/trade/propose', methods=['POST'])
    def propose_trade():
        """Propose a trade to another player"""
        data = request.json
        proposer_id = data.get('proposer_id')
        proposer_pin = data.get('proposer_pin')
        receiver_id = data.get('receiver_id')
        trade_data = data.get('trade_data')
        
        if not proposer_id or not proposer_pin or not receiver_id or not trade_data:
            return jsonify({'success': False, 'error': 'Proposer ID, PIN, receiver ID, and trade data are required'}), 400
        
        result = trade_controller.propose_trade(proposer_id, proposer_pin, receiver_id, trade_data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    @app.route('/api/trade/respond', methods=['POST'])
    def respond_to_trade():
        """Accept or reject a proposed trade"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        trade_id = data.get('trade_id')
        accept = data.get('accept')
        
        if not player_id or not pin or not trade_id or accept is None:
            return jsonify({'success': False, 'error': 'Player ID, PIN, trade ID, and accept value are required'}), 400
        
        result = trade_controller.respond_to_trade(player_id, pin, trade_id, accept)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/trade/list', methods=['GET'])
    def list_trades():
        """List active trades for a player"""
        player_id = request.args.get('player_id')
        pin = request.args.get('pin')
        
        if not player_id or not pin:
            return jsonify({'success': False, 'error': 'Player ID and PIN are required'}), 400
        
        result = trade_controller.list_player_trades(player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/trade/cancel', methods=['DELETE'])
    def cancel_trade():
        """Cancel a proposed trade"""
        data = request.json
        player_id = data.get('player_id')
        pin = data.get('pin')
        trade_id = data.get('trade_id')
        
        if not player_id or not pin or not trade_id:
            return jsonify({'success': False, 'error': 'Player ID, PIN, and trade ID are required'}), 400
        
        result = trade_controller.cancel_trade(player_id, pin, trade_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/trade/details', methods=['GET'])
    def trade_details():
        """Get details of a specific trade"""
        trade_id = request.args.get('trade_id')
        player_id = request.args.get('player_id')
        pin = request.args.get('pin')
        
        if not trade_id or not player_id or not pin:
            return jsonify({'success': False, 'error': 'Trade ID, player ID, and PIN are required'}), 400
        
        result = trade_controller.get_trade_details(trade_id, player_id, pin)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/trade/admin-approve', methods=['POST'])
    @admin_required
    def admin_approve_trade():
        """Admin approval for flagged trades"""
        data = request.json
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return jsonify({'success': False, 'error': 'Trade ID is required'}), 400
        
        result = trade_controller.admin_approve_trade(trade_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400 