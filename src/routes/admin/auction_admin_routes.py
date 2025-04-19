from flask import Blueprint, request, jsonify, current_app, Response
from src.utils.auth import admin_required
import logging
import json
from flask.views import MethodView
from ...controllers.auction_controller import AuctionController

# Create blueprint for auction admin routes
auction_admin_bp = Blueprint('auction_admin', __name__)
logger = logging.getLogger(__name__)

class AuctionAnalyticsView(MethodView):
    decorators = [admin_required]
    
    def get(self):
        """
        Get comprehensive analytics data about auctions.
        ---
        tags:
            - Admin Auction
        parameters:
            - name: game_id
              in: query
              type: string
              required: false
              description: ID of the game to filter auctions by
            - name: start_date
              in: query
              type: string
              required: false
              description: Start date for filtering auctions (YYYY-MM-DD)
            - name: end_date
              in: query
              type: string
              required: false
              description: End date for filtering auctions (YYYY-MM-DD)
        responses:
            200:
                description: Analytics data retrieved successfully
        """
        game_id = request.args.get('game_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        auction_controller = AuctionController()
        result = auction_controller.get_auction_analytics(game_id, start_date, end_date)
        
        return jsonify(result)

class PropertyAuctionHistoryView(MethodView):
    decorators = [admin_required]
    
    def get(self, property_id):
        """
        Get the complete auction history for a specific property.
        ---
        tags:
            - Admin Auction
        parameters:
            - name: property_id
              in: path
              type: integer
              required: true
              description: ID of the property to get auction history for
        responses:
            200:
                description: Property auction history retrieved successfully
        """
        auction_controller = AuctionController()
        result = auction_controller.get_property_auction_history(property_id)
        
        return jsonify(result)

class ExportAuctionDataView(MethodView):
    decorators = [admin_required]
    
    def get(self):
        """
        Export auction data to CSV format with optional filtering.
        ---
        tags:
            - Admin Auction
        parameters:
            - name: game_id
              in: query
              type: string
              required: false
              description: ID of the game to filter auctions by
            - name: start_date
              in: query
              type: string
              required: false
              description: Start date for filtering auctions (YYYY-MM-DD)
            - name: end_date
              in: query
              type: string
              required: false
              description: End date for filtering auctions (YYYY-MM-DD)
            - name: download
              in: query
              type: boolean
              required: false
              description: Set to true to download as a file instead of viewing as JSON
        responses:
            200:
                description: Auction data exported successfully
        """
        game_id = request.args.get('game_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        download = request.args.get('download', 'false').lower() == 'true'
        
        auction_controller = AuctionController()
        result = auction_controller.export_auction_data(game_id, start_date, end_date)
        
        if not result["success"]:
            return jsonify(result), 400
            
        if download:
            # Generate filename with game_id if available
            filename = f"auction_data"
            if game_id:
                filename += f"_game_{game_id}"
            filename += ".csv"
            
            # Return as downloadable file
            return Response(
                result["data"],
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
        else:
            # Return as JSON response
            return jsonify(result)

@auction_admin_bp.route('/active-auctions/<string:game_id>', methods=['GET'])
@admin_required
def get_active_auctions(game_id):
    """
    Get all active auctions for a specific game.
    
    Path Parameters:
        game_id: The ID of the game to get active auctions for
        
    Returns:
        JSON with list of active auctions
    """
    try:
        # Validate game_id
        if not game_id:
            return jsonify({
                "success": False,
                "message": "Invalid game_id"
            }), 400
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.get_active_auctions(game_id=game_id)
        
        # Return the result with appropriate status code
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in active auctions endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve active auctions: {str(e)}"
        }), 500


@auction_admin_bp.route('/auction/<string:auction_id>', methods=['GET'])
@admin_required
def get_auction_details(auction_id):
    """
    Get detailed information about a specific auction.
    
    Path Parameters:
        auction_id: The ID of the auction to get details for
        
    Returns:
        JSON with auction details
    """
    try:
        # Validate auction_id
        if not auction_id:
            return jsonify({
                "success": False,
                "message": "Invalid auction_id"
            }), 400
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.get_auction(auction_id=auction_id)
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 404
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in auction details endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve auction details: {str(e)}"
        }), 500


@auction_admin_bp.route('/auction-status/<string:auction_id>', methods=['GET'])
@admin_required
def get_auction_status(auction_id):
    """
    Get detailed status information for an auction, including participants and bids.
    
    Path Parameters:
        auction_id: The ID of the auction to get status for
        
    Returns:
        JSON with detailed auction status
    """
    try:
        # Validate auction_id
        if not auction_id:
            return jsonify({
                "success": False,
                "message": "Invalid auction_id"
            }), 400
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.get_auction_status(auction_id=auction_id)
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 404
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in auction status endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve auction status: {str(e)}"
        }), 500


@auction_admin_bp.route('/cancel-auction/<string:auction_id>', methods=['POST'])
@admin_required
def cancel_auction(auction_id):
    """
    Cancel an active auction (admin function).
    
    Path Parameters:
        auction_id: The ID of the auction to cancel
        
    Query Parameters:
        reason (optional): The reason for cancelling the auction
        
    Returns:
        JSON with result of the cancellation operation
    """
    try:
        # Validate auction_id
        if not auction_id:
            return jsonify({
                "success": False,
                "message": "Invalid auction_id"
            }), 400
            
        # Get the reason for cancellation
        reason = request.args.get('reason', 'Admin cancelled auction')
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.cancel_auction(
            auction_id=auction_id,
            reason=reason
        )
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 404
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in cancel auction endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to cancel auction: {str(e)}"
        }), 500


@auction_admin_bp.route('/cleanup-stale-auctions', methods=['POST'])
@admin_required
def cleanup_stale_auctions():
    """
    Cleanup stale auctions that have been inactive for a specific period.
    
    Query Parameters:
        hours_old (optional): Minimum age in hours for an auction to be considered stale (default: 24)
        
    Returns:
        JSON with result of the cleanup operation
    """
    try:
        # Get the hours parameter
        hours_old = request.args.get('hours_old', 24, type=int)
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.cleanup_stale_auctions(hours_old=hours_old)
        
        # Return the result with appropriate status code
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in cleanup stale auctions endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to cleanup stale auctions: {str(e)}"
        }), 500


@auction_admin_bp.route('/start-sequential-auctions', methods=['POST'])
@admin_required
def start_sequential_auctions():
    """
    Start sequential auctions for multiple properties.
    
    Request Body (JSON):
        game_id: The game ID where the auctions should be started
        property_ids: Array of property IDs to auction
        starting_bids: (optional) Array of starting bids for each property (in same order as property_ids)
        duration: (optional) Duration in seconds for each auction (default: 120)
        reason: (optional) Reason for starting the sequential auctions
        
    Returns:
        JSON with result of the operation
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        # Validate required parameters
        game_id = data.get('game_id')
        property_ids = data.get('property_ids')
        
        if not game_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: game_id"
            }), 400
            
        if not property_ids or not isinstance(property_ids, list) or len(property_ids) == 0:
            return jsonify({
                "success": False,
                "message": "Missing or invalid required parameter: property_ids"
            }), 400
            
        # Get optional parameters
        starting_bids = data.get('starting_bids')
        duration = data.get('duration', 120)
        reason = data.get('reason', 'Admin initiated sequential auctions')
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.start_sequential_auctions(
            game_id=game_id,
            property_ids=property_ids,
            starting_bids=starting_bids,
            duration=duration,
            reason=reason
        )
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 400
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in start sequential auctions endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to start sequential auctions: {str(e)}"
        }), 500


@auction_admin_bp.route('/auction-schedule/<string:game_id>', methods=['GET'])
@admin_required
def get_auction_schedule(game_id):
    """
    Get information about the current auction schedule for a game,
    including sequential auctions in progress.
    
    Path Parameters:
        game_id: The ID of the game to check auction schedule for
        
    Returns:
        JSON with auction schedule details
    """
    try:
        # Validate game_id
        if not game_id:
            return jsonify({
                "success": False,
                "message": "Invalid game_id"
            }), 400
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.get_auction_schedule(game_id=game_id)
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 404
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in auction schedule endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve auction schedule: {str(e)}"
        }), 500


@auction_admin_bp.route('/process-bot-bid', methods=['POST'])
@admin_required
def process_bot_bid():
    """
    Process a bot bid for testing purposes.
    
    Request Body (JSON):
        auction_id: The ID of the auction
        bot_id: The ID of the bot player
        strategy: (optional) The bidding strategy to use (default, aggressive, conservative, opportunistic)
        
    Returns:
        JSON with result of the bid processing
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        # Validate required parameters
        auction_id = data.get('auction_id')
        bot_id = data.get('bot_id')
        
        if not auction_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: auction_id"
            }), 400
            
        if not bot_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: bot_id"
            }), 400
            
        # Get optional parameters
        strategy = data.get('strategy', 'default')
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.process_bot_bid(
            auction_id=auction_id,
            bot_id=bot_id,
            bot_strategy=strategy
        )
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 400
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in process bot bid endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to process bot bid: {str(e)}"
        }), 500


@auction_admin_bp.route('/batch-end-auctions', methods=['POST'])
@admin_required
def batch_end_auctions():
    """
    End multiple auctions at once.
    
    Request Body (JSON):
        auction_ids: Array of auction IDs to end
        reason: (optional) Reason for ending the auctions
        
    Returns:
        JSON with result of the batch operation
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        # Validate required parameters
        auction_ids = data.get('auction_ids')
        
        if not auction_ids or not isinstance(auction_ids, list) or len(auction_ids) == 0:
            return jsonify({
                "success": False,
                "message": "Missing or invalid required parameter: auction_ids"
            }), 400
            
        # Get optional parameters
        reason = data.get('reason', 'Admin batch ended auctions')
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.batch_end_auctions(
            auction_ids=auction_ids,
            reason=reason
        )
        
        # Return the result with appropriate status code
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in batch end auctions endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to batch end auctions: {str(e)}"
        }), 500


@auction_admin_bp.route('/process-multiple-bot-bids', methods=['POST'])
@admin_required
def process_multiple_bot_bids():
    """
    Process bids from multiple bots for testing purposes.
    
    Request Body (JSON):
        auction_id: The ID of the auction
        bot_ids: Array of bot player IDs to process bids for
        strategies: (optional) Dictionary mapping bot_id to strategy name 
                   (default, aggressive, conservative, opportunistic)
        
    Returns:
        JSON with result of the bid processing for each bot
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        # Validate required parameters
        auction_id = data.get('auction_id')
        bot_ids = data.get('bot_ids')
        
        if not auction_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: auction_id"
            }), 400
            
        if not bot_ids or not isinstance(bot_ids, list) or len(bot_ids) == 0:
            return jsonify({
                "success": False,
                "message": "Missing or invalid required parameter: bot_ids"
            }), 400
            
        # Get optional parameters
        strategies = data.get('strategies')
            
        # Get auction controller from app context
        auction_controller = current_app.auction_controller
        if not auction_controller:
            logger.error("Auction controller not available")
            return jsonify({
                "success": False,
                "message": "Internal server error: Auction service unavailable"
            }), 500
            
        # Call the controller method
        result = auction_controller.process_multiple_bot_bids(
            auction_id=auction_id,
            bot_ids=bot_ids,
            strategies=strategies
        )
        
        # Return the result with appropriate status code
        if result.get('success') is False:
            return jsonify(result), 400
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in process multiple bot bids endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Failed to process multiple bot bids: {str(e)}"
        }), 500


# Register routes
auction_admin_bp.add_url_rule('/auction/analytics', view_func=AuctionAnalyticsView.as_view('auction_analytics'))
auction_admin_bp.add_url_rule('/auction/property-history/<int:property_id>', view_func=PropertyAuctionHistoryView.as_view('property_auction_history'))
auction_admin_bp.add_url_rule('/export-auction-data', view_func=ExportAuctionDataView.as_view('export_auction_data'))

# Function to register blueprint with Flask app
def register_auction_admin_routes(app):
    app.register_blueprint(auction_admin_bp, url_prefix='/api/admin/auctions') 