from flask_socketio import emit
import logging
from flask import request, jsonify, current_app
from src.models import db
from src.models.property import Property
from src.models.player import Player
from src.models.banker import Banker
from src.models.auction import Auction
from src.models.transaction import Transaction
from src.models.game_state import GameState
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Constants
AUCTION_TIMER_DEFAULT = 30 # seconds
AUCTION_TIMER_EXTENSION = 10 # seconds
AUCTION_TIMER_CHECK_INTERVAL = 1.0 # seconds

class AuctionController:
    """Controller for managing property auctions using DB persistence."""
    
    def __init__(self, db_session, banker, event_system, socketio):
        self.db = db_session
        self.banker = banker
        self.event_system = event_system
        self.socketio = socketio
        self.active_timers = {} # auction_id -> threading.Timer object
        logger.info("AuctionController initialized (DB Persistence Mode).")

    def _start_auction_logic(self, property_id, is_foreclosure=False, owner_id=None, minimum_bid=None):
        """Internal logic to start a standard or foreclosure auction."""
        # --- Validation ---
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"success": False, "error": "Property not found"}

        if not is_foreclosure and property_obj.owner_id is not None:
            return {"success": False, "error": "Property already has an owner"}
            
        if is_foreclosure and property_obj.owner_id != owner_id:
             return {"success": False, "error": "Property owner mismatch for foreclosure"}

        # Check if an auction is already active for this property
        existing_auction = Auction.query.filter_by(property_id=property_id, status='active').first()
        if existing_auction:
            logger.warning(f"Attempted to start auction for property {property_id} which already has active auction {existing_auction.id}")
            return {"success": False, "error": "Auction already active for this property", "auction_id": existing_auction.id}

        # --- Setup Auction --- 
        players = Player.query.filter_by(in_game=True, is_bankrupt=False).all()
        if is_foreclosure:
            eligible_player_ids = [p.id for p in players if p.id != owner_id]
        else:
            eligible_player_ids = [p.id for p in players]

        if not eligible_player_ids:
             return {"success": False, "error": "No eligible players to participate in the auction"}

        if minimum_bid is None:
             if is_foreclosure:
                 minimum_bid = int(property_obj.current_price * 0.6)
             else:
                 minimum_bid = int(property_obj.current_price * 0.7)
        else:
             minimum_bid = int(minimum_bid) # Ensure integer

        # --- Create Auction Record --- 
        try:
            auction = Auction(
                property_id=property_id,
                status='active',
                minimum_bid=minimum_bid,
                current_bid=None, # Start with no bid
                current_bidder_id=None,
                start_time=datetime.utcnow(),
                is_foreclosure=is_foreclosure,
                original_owner_id=owner_id if is_foreclosure else None
            )
            auction.set_eligible_players(eligible_player_ids)
            
            db.session.add(auction)
            db.session.commit()
            logger.info(f"Created auction record {auction.id} for property {property_id}.")

            # --- Start Timer & Notify --- 
            self._start_auction_timer(auction.id)

            game_state = GameState.get_instance() # For room ID
            if game_state:
                event_name = 'foreclosure_auction_started' if is_foreclosure else 'auction_started'
                emit_data = {
                    'auction_id': auction.id,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                    'minimum_bid': minimum_bid,
                    'start_price': property_obj.current_price, # Informational
                    'timer': AUCTION_TIMER_DEFAULT, # Initial timer duration
                    'eligible_players': eligible_player_ids,
                    'is_foreclosure': is_foreclosure,
                    'owner_id': owner_id # For foreclosure context
                }
                self.socketio.emit(event_name, emit_data, room=game_state.game_id)
                logger.info(f"Emitted {event_name} for auction {auction.id} to room {game_state.game_id}")
            else:
                 logger.error(f"Could not emit auction start: GameState not found.")
            
            return {"success": True, "auction": auction.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating auction record for property {property_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error starting auction"}

    def _place_bid_logic(self, auction_id, player_id, bid_amount):
        """Internal logic to place a bid."""
        # --- Validation ---
        auction = Auction.query.get(auction_id)
        if not auction or auction.status != 'active':
            return {"success": False, "error": "Auction not found or not active"}

        eligible_players = auction.get_eligible_players()
        players_passed = auction.get_passed_players()
        if player_id not in eligible_players or player_id in players_passed:
            return {"success": False, "error": "Player not eligible to bid"}

        # Check bid amount
        if auction.current_bid is not None and bid_amount <= auction.current_bid:
            return {"success": False, "error": f"Bid must be higher than current bid (${auction.current_bid})"}
        if bid_amount < auction.minimum_bid:
            return {"success": False, "error": f"Bid must be at least the minimum bid (${auction.minimum_bid})"}

        player = Player.query.get(player_id)
        if not player or player.cash < bid_amount:
            return {"success": False, "error": "Insufficient funds", "required": bid_amount, "available": player.cash if player else 0}

        # --- Update Auction Record --- 
        try:
            auction.current_bid = bid_amount
            auction.current_bidder_id = player_id
            auction.last_bid_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"Bid placed in auction {auction_id} by player {player_id} for ${bid_amount}")

            # --- Reset Timer & Notify --- 
            self._reset_auction_timer(auction_id)

            game_state = GameState.get_instance()
            if game_state:
                bid_data = {
                    'auction_id': auction_id,
                    'player_id': player_id,
                    'player_name': player.username,
                    'bid_amount': bid_amount,
                    'timestamp': auction.last_bid_time.isoformat()
                }
                self.socketio.emit('auction_bid_update', bid_data, room=game_state.game_id)
                logger.info(f"Emitted auction_bid_update for auction {auction_id} to room {game_state.game_id}")
            
            return {"success": True, "auction_id": auction_id, "bid_amount": bid_amount}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error placing bid for auction {auction_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error placing bid"}

    def _pass_auction_logic(self, auction_id, player_id):
        """Internal logic for a player passing."""
        auction = Auction.query.get(auction_id)
        if not auction or auction.status != 'active':
            return {"success": False, "error": "Auction not found or not active"}

        eligible_players = auction.get_eligible_players()
        players_passed = auction.get_passed_players()
        if player_id not in eligible_players or player_id in players_passed:
            # Allow passing even if already passed, just confirm
            logger.info(f"Player {player_id} passed auction {auction_id} (already passed or ineligible)")
            return {"success": True, "message": "Pass confirmed", "already_passed": True}

        try:
            auction.add_passed_player(player_id)
            db.session.commit()
            logger.info(f"Player {player_id} passed auction {auction_id}")
            
            # Check if passing ends the auction
            remaining_eligible = [p for p in eligible_players if p not in auction.get_passed_players()]
            
            game_state = GameState.get_instance()
            if game_state:
                 pass_data = {
                    'auction_id': auction_id,
                    'player_id': player_id,
                    'player_name': Player.query.get(player_id).username # Fetch name
                 }
                 self.socketio.emit('auction_player_passed', pass_data, room=game_state.game_id)
                 logger.info(f"Emitted auction_player_passed for auction {auction_id} to room {game_state.game_id}")

            if len(remaining_eligible) <= 1:
                logger.info(f"Only {len(remaining_eligible)} players left in auction {auction_id} after pass. Ending auction.")
                self._end_auction_logic(auction_id)
                # _end_auction_logic will handle notifications
                return {"success": True, "message": "Pass recorded, auction ended", "auction_ended": True}
            else:
                 return {"success": True, "message": "Pass recorded", "auction_ended": False}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error processing pass for auction {auction_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error processing pass"}

    def _end_auction_logic(self, auction_id):
        """Internal logic to end an auction, determine winner, and process payment."""
        with db.session.no_autoflush: # Avoid premature flushes if related objects are modified
            auction = Auction.query.get(auction_id)
            if not auction or auction.status != 'active':
                # Could be ended by another process/timer already
                logger.warning(f"Attempted to end auction {auction_id} which is not active or found. Status: {auction.status if auction else 'Not Found'}")
                return {"success": False, "error": "Auction not active or not found"}

            # Cancel any existing timer
            self._cancel_timer(auction_id)

            winner_id = auction.current_bidder_id
            winning_bid = auction.current_bid
            property_obj = auction.property # Use relationship
            
            if not property_obj:
                logger.error(f"Cannot end auction {auction_id}: Associated property {auction.property_id} not found.")
                auction.status = 'cancelled' # Mark as cancelled due to error
                db.session.commit()
                return {"success": False, "error": "Property associated with auction not found"}

            try:
                if winner_id and winning_bid is not None:
                    # Process payment using Banker
                    payment_result = self.banker.player_pays_bank(winner_id, winning_bid, f"Winning bid for {property_obj.name}")

                    if payment_result["success"]:
                        auction.status = 'completed'
                        property_obj.owner_id = winner_id
                        property_obj.is_mortgaged = False # Acquired free and clear
                        db.session.add(property_obj)
                        logger.info(f"Auction {auction_id} completed. Winner: Player {winner_id}, Property: {property_obj.id}, Bid: ${winning_bid}")
                        
                        # Create Transaction record
                        trans = Transaction(
                            player_id=winner_id,
                            amount=-winning_bid,
                            transaction_type='auction_win',
                            property_id=property_obj.id,
                            description=f"Won auction for {property_obj.name} with bid ${winning_bid}"
                        )
                        db.session.add(trans)
                    else:
                        # Payment failed - Should ideally not happen if bid validation worked, but handle defensively
                        logger.error(f"Payment failed for auction {auction_id} winner {winner_id}. Error: {payment_result.get('error')}. Cancelling auction.")
                        auction.status = 'cancelled' 
                        # Property remains unowned or returns to original owner if foreclosure? Needs clarification.
                        winner_id = None # No winner if payment fails
                        winning_bid = None
                else:
                    # No bids placed or no bidder
                    logger.info(f"Auction {auction_id} ended with no valid bids.")
                    auction.status = 'completed' # Completed without sale
                    # Property remains unowned / returns to original owner if foreclosure?
                    winner_id = None
                    winning_bid = None

                auction.end_time = datetime.utcnow()
                db.session.add(auction) # Add auction changes
                db.session.commit()

                # --- Notify --- 
                game_state = GameState.get_instance()
                if game_state:
                    end_data = {
                        'auction_id': auction_id,
                        'status': auction.status,
                        'property_id': property_obj.id,
                        'property_name': property_obj.name,
                        'winner_id': winner_id,
                        'winner_name': Player.query.get(winner_id).username if winner_id else None,
                        'winning_bid': winning_bid,
                        'end_time': auction.end_time.isoformat()
                    }
                    self.socketio.emit('auction_ended', end_data, room=game_state.game_id)
                    logger.info(f"Emitted auction_ended for auction {auction_id} to room {game_state.game_id}")
                
                return {"success": True, "status": auction.status, "winner_id": winner_id, "winning_bid": winning_bid}

            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error ending auction {auction_id}: {e}", exc_info=True)
                # Attempt to cancel auction in DB on error
                try: 
                    auction.status = 'cancelled'
                    auction.end_time = datetime.utcnow()
                    db.session.commit()
                except Exception as e2:
                     logger.error(f"Failed to mark auction {auction_id} as cancelled after error: {e2}")
                return {"success": False, "error": "Database error ending auction"}

    # --- Timer Management --- 

    def _start_auction_timer(self, auction_id):
        """Starts the countdown timer for an auction."""
        if auction_id in self.active_timers:
            logger.warning(f"Timer already active for auction {auction_id}. Cancelling old timer.")
            self._cancel_timer(auction_id)
        
        def timer_callback():
            logger.info(f"Timer expired for auction {auction_id}. Checking status.")
            # Need app context for DB access within the timer thread
            with current_app.app_context():
                self._end_auction_logic(auction_id)
            # Remove timer entry after execution
            if auction_id in self.active_timers:
                 del self.active_timers[auction_id]

        logger.info(f"Starting timer ({AUCTION_TIMER_DEFAULT}s) for auction {auction_id}")
        timer = threading.Timer(AUCTION_TIMER_DEFAULT, timer_callback)
        self.active_timers[auction_id] = timer
        timer.start()

    def _reset_auction_timer(self, auction_id):
        """Resets the auction timer after a valid bid."""
        if auction_id not in self.active_timers:
            logger.warning(f"Attempted to reset timer for non-existent or inactive auction {auction_id}")
            # Potentially start a new timer if the auction is somehow active without one?
            # self._start_auction_timer(auction_id) # Careful about race conditions
            return
        
        self._cancel_timer(auction_id) # Cancel the existing timer

        # Start a new shorter timer
        def timer_callback():
             logger.info(f"Extended timer expired for auction {auction_id}. Checking status.")
             with current_app.app_context():
                 self._end_auction_logic(auction_id)
             if auction_id in self.active_timers:
                 del self.active_timers[auction_id]

        logger.info(f"Resetting timer ({AUCTION_TIMER_EXTENSION}s) for auction {auction_id} after bid.")
        timer = threading.Timer(AUCTION_TIMER_EXTENSION, timer_callback)
        self.active_timers[auction_id] = timer
        timer.start()

    def _cancel_timer(self, auction_id):
        """Cancels the active timer for an auction."""
        if auction_id in self.active_timers:
            timer = self.active_timers.pop(auction_id)
            if timer:
                timer.cancel()
                logger.info(f"Cancelled timer for auction {auction_id}")
        # else: logger.debug(f"No active timer found to cancel for auction {auction_id}")

    # --- Placeholder/Passthrough Methods (Controller logic moved here) ---
    
    def start_auction(self, property_id):
         """Public method to initiate starting an auction."""
         logger.info(f"Request received to start auction for property {property_id}")
         return self._start_auction_logic(property_id)

    def start_foreclosure_auction(self, property_id, owner_id, minimum_bid=None):
         """Public method to initiate starting a foreclosure auction."""
         logger.info(f"Request received to start foreclosure auction for property {property_id}, owner {owner_id}")
         return self._start_auction_logic(property_id, is_foreclosure=True, owner_id=owner_id, minimum_bid=minimum_bid)

    def place_bid(self, auction_id, player_id, bid_amount):
         """Public method to place a bid."""
         logger.info(f"Request received for player {player_id} to bid ${bid_amount} on auction {auction_id}")
         return self._place_bid_logic(auction_id, player_id, bid_amount)

    def pass_auction(self, auction_id, player_id):
         """Public method for a player to pass."""
         logger.info(f"Request received for player {player_id} to pass on auction {auction_id}")
         return self._pass_auction_logic(auction_id, player_id)

    def end_auction(self, auction_id): # Typically called by timer or pass logic
         """Public method to explicitly end an auction (use with caution)."""
         logger.warning(f"Explicit request received to end auction {auction_id}. Normally handled by timer/pass.")
         return self._end_auction_logic(auction_id)
         
    def cancel_auction(self, auction_id, admin_id): # Keep admin cancel separate
        """Cancels an active auction (Admin action)."""
        logger.info(f"Admin {admin_id} requested cancellation of auction {auction_id}")
        auction = Auction.query.get(auction_id)
        if not auction:
             return {"success": False, "error": "Auction not found"}
        if auction.status != 'active':
            return {"success": False, "error": "Auction is not active"}
            
        self._cancel_timer(auction_id)
        
        try:
            auction.status = 'cancelled'
            auction.end_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"Auction {auction_id} cancelled by admin {admin_id}.")
            
            # Notify
            game_state = GameState.get_instance()
            if game_state:
                cancel_data = auction.to_dict() # Send full final state
                self.socketio.emit('auction_cancelled', cancel_data, room=game_state.game_id)
                logger.info(f"Emitted auction_cancelled for auction {auction_id} to room {game_state.game_id}")
                
            return {"success": True, "message": "Auction cancelled"}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error cancelling auction {auction_id}: {e}", exc_info=True)
            return {"success": False, "error": "Database error cancelling auction"}
            
    def get_active_auctions(self):
         """Retrieves all currently active auctions from the database."""
         try:
             active_auctions = Auction.query.filter_by(status='active').all()
             return {"success": True, "auctions": [a.to_dict() for a in active_auctions]}
         except Exception as e:
             logger.error(f"Error retrieving active auctions: {e}", exc_info=True)
             return {"success": False, "error": "Database error retrieving auctions"}
             
    def get_auction(self, auction_id):
         """Retrieves details for a specific auction by ID from the database."""
         try:
             auction = Auction.query.get(auction_id)
             if not auction:
                 return {"success": False, "error": "Auction not found"}
             return {"success": True, "auction": auction.to_dict()}
         except Exception as e:
             logger.error(f"Error retrieving auction {auction_id}: {e}", exc_info=True)
             return {"success": False, "error": "Database error retrieving auction"}

# --- Registration Function --- 

def register_auction_events(socketio, app_config):
    """Register auction-related socket event handlers"""
    # Get the AuctionController instance from app_config
    auction_controller = app_config.get('auction_controller') 
    if not auction_controller:
        logger.error("Auction controller not found in app config during auction event registration.")
        return
    
    @socketio.on('start_auction')
    def handle_start_auction(data):
        """Start a new auction for a property (likely triggered by game logic/admin)"""
        property_id = data.get('property_id')
        # Add admin auth check if needed for manual start
        # admin_key = data.get('admin_key') ...
        
        logger.debug(f"handle_start_auction received for property {property_id}")
        # Call the controller's internal logic method
        result = auction_controller._start_auction_logic(property_id)
        
        # Confirmation/Error emission is handled within _start_auction_logic via self.socketio
        # Only emit specific confirmation back to caller if needed?
        if result.get('success'):
             emit('auction_started_confirmation', {'auction_id': result['auction']['id'], 'success': True}, room=request.sid)
        else:
             emit('auction_error', {'error': result.get('error', 'Failed to start auction')}, room=request.sid)
    
    @socketio.on('start_foreclosure') # Admin/System Triggered
    def handle_start_foreclosure(data):
        """Start a foreclosure auction for a property"""
        property_id = data.get('property_id')
        owner_id = data.get('owner_id')
        minimum_bid = data.get('minimum_bid')
        admin_key = data.get('admin_key') # Require admin key for this
        
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            emit('auction_error', {'error': 'Unauthorized admin action'}, room=request.sid)
            return
        
        logger.debug(f"handle_start_foreclosure received for property {property_id}, owner {owner_id}")
        result = auction_controller._start_auction_logic(property_id, is_foreclosure=True, owner_id=owner_id, minimum_bid=minimum_bid)
        
        if result.get('success'):
             emit('foreclosure_started_confirmation', {'auction_id': result['auction']['id'], 'success': True}, room=request.sid)
        else:
             emit('auction_error', {'error': result.get('error', 'Failed to start foreclosure auction')}, room=request.sid)
    
    @socketio.on('place_bid')
    def handle_place_bid(data):
        """Handle a bid from a player"""
        auction_id = data.get('auction_id')
        player_id = data.get('player_id')
        pin = data.get('pin')
        bid_amount = data.get('bid_amount')
        sid = request.sid
        
        # Validate player PIN
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('auction_error', {'error': 'Invalid player credentials'}, room=sid)
            return
        
        # Validate bid amount format
        try:
            bid_amount = int(bid_amount)
            if bid_amount <= 0:
                raise ValueError("Bid must be positive")
        except (ValueError, TypeError):
            emit('auction_error', {'error': 'Invalid bid amount format'}, room=sid)
            return
        
        logger.debug(f"handle_place_bid received for auction {auction_id} from player {player_id}")
        result = auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Confirmation/Error emission is handled within _place_bid_logic via self.socketio
        # Emit specific confirmation back to the bidder
        if result.get('success'):
             emit('bid_confirmation', {'auction_id': auction_id, 'amount': bid_amount, 'success': True}, room=sid)
        else:
             emit('auction_error', {'error': result.get('error', 'Failed to place bid')}, room=sid)
    
    @socketio.on('pass_auction')
    def handle_pass_auction(data):
        """Handle a player passing on an auction"""
        auction_id = data.get('auction_id')
        player_id = data.get('player_id')
        pin = data.get('pin')
        sid = request.sid
        
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('auction_error', {'error': 'Invalid player credentials'}, room=sid)
            return
        
        logger.debug(f"handle_pass_auction received for auction {auction_id} from player {player_id}")
        result = auction_controller._pass_auction_logic(auction_id, player_id)
        
        # Emit specific confirmation back to the player
        if result.get('success'):
             emit('pass_confirmation', {'auction_id': auction_id, 'success': True, 'auction_ended': result.get('auction_ended', False)}, room=sid)
        else:
             emit('auction_error', {'error': result.get('error', 'Failed to process pass')}, room=sid)
    
    @socketio.on('get_auctions')
    def handle_get_auctions():
        """Get all active auctions"""
        logger.debug(f"handle_get_auctions request received")
        result = auction_controller.get_active_auctions() # Call the controller method
        emit('auction_list', result, room=request.sid)
    
    @socketio.on('get_auction')
    def handle_get_auction(data):
        """Get details of a specific auction"""
        auction_id = data.get('auction_id')
        logger.debug(f"handle_get_auction request received for auction {auction_id}")
        result = auction_controller.get_auction(auction_id) # Call the controller method
        
        if result.get('success'):
            emit('auction_details', result, room=request.sid)
        else:
            emit('auction_error', {'error': result.get('error', 'Failed to retrieve auction')}, room=request.sid)
    
    @socketio.on('cancel_auction') # Admin only
    def handle_cancel_auction(data):
        """Admin function to cancel an auction"""
        auction_id = data.get('auction_id')
        admin_key = data.get('admin_key')
        sid = request.sid
        
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            emit('auction_error', {'error': 'Unauthorized admin action'}, room=sid)
            return
        
        admin_id = data.get('admin_id', 'UNKNOWN_ADMIN') # Optional admin ID for logging
        logger.debug(f"handle_cancel_auction received for auction {auction_id} from admin")
        result = auction_controller.cancel_auction(auction_id, admin_id) # Call controller method
        
        if result.get('success'):
             emit('auction_cancelled_confirmation', {'auction_id': auction_id, 'success': True}, room=sid)
        else:
             emit('auction_error', {'error': result.get('error', 'Failed to cancel auction')}, room=sid)

    logger.info("AuctionController event handlers registered.")

# No HTTP routes defined here anymore, they belong in a routes file if needed. 