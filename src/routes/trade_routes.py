from flask import Blueprint, request, jsonify
import logging

trade_routes = Blueprint('trade_routes', __name__)
logger = logging.getLogger(__name__)

# This will be set during app initialization
trade_controller = None

@trade_routes.route('/propose', methods=['POST'])
def propose_trade():
    """Propose a new trade"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    data = request.json
    result = trade_controller.create_trade_proposal(data)
    
    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@trade_routes.route('/accept', methods=['POST'])
def accept_trade():
    """Accept a trade proposal"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    data = request.json
    result = trade_controller.accept_trade(data)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@trade_routes.route('/reject', methods=['POST'])
def reject_trade():
    """Reject a trade proposal"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    data = request.json
    result = trade_controller.reject_trade(data)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@trade_routes.route('/cancel', methods=['POST'])
def cancel_trade():
    """Cancel a trade proposal"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    data = request.json
    result = trade_controller.cancel_trade(data)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@trade_routes.route('/pending/<int:player_id>', methods=['GET'])
def get_pending_trades(player_id):
    """Get pending trades for a player"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    result = trade_controller.get_pending_trades(player_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@trade_routes.route('/history/<int:player_id>', methods=['GET'])
def get_trade_history(player_id):
    """Get trade history for a player"""
    if not trade_controller:
        return jsonify({'success': False, 'error': 'Trade controller not initialized'}), 500
    
    limit = request.args.get('limit', 10, type=int)
    result = trade_controller.get_trade_history(player_id, limit)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@trade_routes.route('/details/<int:trade_id>', methods=['GET'])
def get_trade_details(trade_id):
    """Get details of a specific trade"""
    from src.models.trade import Trade
    
    trade = Trade.query.get(trade_id)
    if not trade:
        return jsonify({'success': False, 'error': 'Trade not found'}), 404
    
    # Format trade for API response
    if hasattr(trade_controller, '_format_trade_for_api'):
        trade_data = trade_controller._format_trade_for_api(trade)
    else:
        # Fallback if not available
        trade_data = trade.to_dict()
    
    return jsonify({
        'success': True,
        'trade': trade_data
    }), 200 