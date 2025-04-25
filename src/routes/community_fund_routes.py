from flask import Blueprint, jsonify, request, current_app
from datetime import datetime

def register_community_fund_routes(app):
    """Register community fund routes
    
    Args:
        app: Flask application
    """
    community_fund = app.config.get('community_fund')
    finance_controller = app.config.get('finance_controller')
    
    @app.route('/api/community-fund', methods=['GET'])
    def get_community_fund():
        """Get community fund information"""
        # Use finance controller first if available for more accurate information
        if finance_controller:
            result = finance_controller.get_community_fund_balance()
            if result.get("success", False):
                return jsonify({
                    "success": True,
                    "fund": {
                        "balance": result.get("balance", 0),
                        "updated_at": result.get("timestamp", "")
                    }
                })
        
        # Fall back to regular community fund if finance controller failed or is unavailable
        if not community_fund:
            return jsonify({
                "success": False,
                "error": "Community fund not initialized"
            }), 500
            
        info = community_fund.get_info()
        return jsonify({
            "success": True,
            "fund": info
        })
    
    @app.route('/api/community-fund/refresh', methods=['GET'])
    def refresh_community_fund():
        """Refresh and get the current community fund balance"""
        # Use finance controller if available
        if finance_controller:
            # Call the refresh method to sync all community fund data
            balance = finance_controller.refresh_community_fund_value()
            
            return jsonify({
                "success": True,
                "balance": balance,
                "timestamp": datetime.now().isoformat()
            })
        
        # Fall back to community fund if finance controller not available
        if community_fund:
            # Just return the current info without refreshing
            info = community_fund.get_info()
            return jsonify({
                "success": True,
                "balance": info.get("balance", 0),
                "timestamp": info.get("updated_at", "")
            })
            
        return jsonify({
            "success": False,
            "error": "Community fund not initialized"
        }), 500
    
    @app.route('/api/admin/community-fund/add', methods=['POST'])
    def admin_add_funds():
        """Admin route to add funds to the community fund"""
        data = request.json
        admin_key = data.get('admin_key')
        amount = data.get('amount')
        reason = data.get('reason', "Admin contribution")
        
        # Verify admin key
        if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403
            
        # Validate amount
        if not amount or not isinstance(amount, int) or amount <= 0:
            return jsonify({
                "success": False,
                "error": "Invalid amount"
            }), 400
            
        # Add funds
        if not community_fund:
            return jsonify({
                "success": False,
                "error": "Community fund not initialized"
            }), 500
            
        new_balance = community_fund.add_funds(amount, reason)
        
        # If finance controller exists, refresh the value to ensure all systems have the same value
        if finance_controller:
            finance_controller.refresh_community_fund_value()
        
        return jsonify({
            "success": True,
            "amount_added": amount,
            "reason": reason,
            "new_balance": new_balance
        })
    
    @app.route('/api/admin/community-fund/withdraw', methods=['POST'])
    def admin_withdraw_funds():
        """Admin route to withdraw funds from the community fund"""
        data = request.json
        admin_key = data.get('admin_key')
        amount = data.get('amount')
        reason = data.get('reason', "Admin withdrawal")
        
        # Verify admin key
        if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403
            
        # Validate amount
        if not amount or not isinstance(amount, int) or amount <= 0:
            return jsonify({
                "success": False,
                "error": "Invalid amount"
            }), 400
            
        # Withdraw funds
        if not community_fund:
            return jsonify({
                "success": False,
                "error": "Community fund not initialized"
            }), 500
            
        result = community_fund.withdraw_funds(amount, reason)
        
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    @app.route('/api/admin/community-fund/clear', methods=['POST'])
    def admin_clear_funds():
        """Admin route to clear all funds from the community fund"""
        data = request.json
        admin_key = data.get('admin_key')
        reason = data.get('reason', "Admin clear")
        
        # Verify admin key
        if not admin_key or admin_key != current_app.config.get('ADMIN_KEY'):
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403
            
        # Clear funds
        if not community_fund:
            return jsonify({
                "success": False,
                "error": "Community fund not initialized"
            }), 500
            
        cleared_amount = community_fund.clear_funds(reason)
        
        return jsonify({
            "success": True,
            "amount_cleared": cleared_amount,
            "reason": reason
        })
        
    return app 