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
import json
import random
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO
import uuid
import csv
import io
from sqlalchemy import func, desc, and_

logger = logging.getLogger(__name__)

# Constants
AUCTION_TIMER_DEFAULT = 30 # seconds
AUCTION_TIMER_EXTENSION = 10 # seconds
AUCTION_TIMER_CHECK_INTERVAL = 1.0 # seconds

class AuctionController:
    """Controller for managing property auctions using DB persistence."""
    
    def __init__(self, db_session, banker, event_system, socketio: SocketIO):
        self.db = db_session
        self.banker = banker
        self.event_system = event_system
        self.socketio = socketio
        self.active_timers = {} # auction_id -> timer info dictionary
        self.app = current_app._get_current_object()  # Store Flask app for context management
        logger.info("AuctionController initialized (DB Persistence Mode).")
        
        # Start the background auction monitoring task
        self.start_auction_monitoring_task()

    def _start_auction_logic(self, property_id, game_id):
        """
        Internal method to start an auction for a property.
        
        Args:
            property_id (str): The ID of the property to auction.
            game_id (str): The ID of the game.
            
        Returns:
            dict: A dictionary with the results of starting the auction.
        """
        logger.info(f"Starting auction for property {property_id} in game {game_id}")
        
        try:
            # Get the property
            property_obj = Property.query.filter_by(id=property_id, game_id=game_id).first()
            if not property_obj:
                logger.error(f"Property {property_id} not found in game {game_id}")
                return {"success": False, "error": "Property not found"}
            
            # Get the game state
            game_state = GameState.query.filter_by(game_id=game_id).first()
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get all active players in the game
            active_players = Player.query.filter_by(game_id=game_id, is_active=True).all()
            if not active_players:
                logger.error(f"No active players found in game {game_id}")
                return {"success": False, "error": "No active players found"}
            
            # Create a new auction
            auction = Auction(
                property_id=property_id,
                game_id=game_id,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(minutes=2),  # 2 minute auction by default
                status="active",
                starting_bid=int(property_obj.price * 0.5),  # Start at 50% of property price
                current_bid=0,
                current_winner_id=None
            )
            
            db.session.add(auction)
            db.session.commit()
            
            # Add to game log
            log_entry = {
                "type": "auction_started",
                "property_id": property_id,
                "property_name": property_obj.name,
                "auction_id": auction.id,
                "starting_bid": auction.starting_bid,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {game_id}, creating new log")
                    current_log = []
                
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            game_state.expected_action = {
                "type": "auction_bid",
                "auction_id": auction.id,
                "property_id": property_id,
                "minimum_bid": auction.starting_bid
            }
            
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('auction_started', {
                'game_id': game_id,
                    'auction_id': auction.id,
                    'property_id': property_id,
                    'property_name': property_obj.name,
                'starting_bid': auction.starting_bid,
                'auction_duration': 120  # 2 minutes in seconds
            }, room=game_id)
            
            # Schedule the auction to end after the duration
            # This would be handled by a background task or scheduler in a real implementation
            
            return {
                "success": True,
                "auction_id": auction.id,
                "property_id": property_id,
                "starting_bid": auction.starting_bid
            }

        except Exception as e:
            logger.error(f"Error starting auction: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _place_bid_logic(self, auction_id, player_id, bid_amount):
        """
        Internal method to handle the logic of placing a bid in an auction.
        
        Validates auction status, player eligibility, and bid requirements.
        Updates the auction state with the new bid and notifies clients.
        
        Args:
            auction_id (str): The ID of the auction
            player_id (str): The ID of the player placing the bid
            bid_amount (float): The amount of the bid
            
        Returns:
            dict: Result of the bid placement with success status and details
        """
        logger.info(f"Processing bid of {bid_amount} from player {player_id} for auction {auction_id}")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found")
                return {"success": False, "error": "Auction not found"}
            
            # Check if auction is active
            if auction.status != "active":
                logger.error(f"Cannot place bid: Auction {auction_id} is not active (status: {auction.status})")
                return {"success": False, "error": f"Auction is not active, current status: {auction.status}"}
            
            # Check if auction has already ended
            if auction.end_time and auction.end_time < datetime.utcnow():
                logger.error(f"Cannot place bid: Auction {auction_id} has already ended")
                return {"success": False, "error": "Auction has already ended"}
            
            # Get the player
            player = Player.query.get(player_id)
            if not player:
                logger.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Check if player is active in the game
            if player.status != "active":
                logger.error(f"Player {player_id} is not active (status: {player.status})")
                return {"success": False, "error": "Player is not active in the game"}
            
            # Check minimum bid requirement
            if bid_amount <= auction.current_bid:
                logger.error(f"Bid amount {bid_amount} is not higher than current bid {auction.current_bid}")
                return {"success": False, "error": f"Bid must be higher than current bid of {auction.current_bid}"}
            
            # Check if player has enough funds
            if player.balance < bid_amount:
                logger.error(f"Player {player_id} has insufficient funds: balance {player.balance}, bid {bid_amount}")
                return {"success": False, "error": "Insufficient funds for this bid"}
            
            # Store previous winner for notification
            previous_winner_id = auction.current_winner_id
            
            # Update the auction with new bid
            auction.current_bid = bid_amount
            auction.current_winner_id = player_id
            
            # Get the game state for logging
            game_state = GameState.query.filter_by(game_id=auction.game_id).first()
            if not game_state:
                logger.error(f"Game {auction.game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Update game log
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {auction.game_id}, creating new log")
                    current_log = []
            else:
                current_log = []
            
            log_entry = {
                "type": "auction_bid",
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "player_id": player_id,
                "player_name": player.name,
                "bid_amount": bid_amount,
                "timestamp": datetime.utcnow().isoformat()
            }
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # If there's less than 30 seconds left, extend the auction
            time_remaining = (auction.end_time - datetime.utcnow()).total_seconds()
            if time_remaining < 30:
                self._reset_auction_timer(auction_id)
                logger.info(f"Bid placed with less than 30 seconds remaining - auction timer reset for {auction_id}")
            
            db.session.commit()
            
            # Prepare response data
            bid_data = {
                "success": True,
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "player_id": player_id,
                "player_name": player.name,
                "bid_amount": bid_amount,
                "previous_winner_id": previous_winner_id,
                "ends_at": auction.end_time.isoformat()
            }
            
            # Emit event to notify all clients in the game room
            self.socketio.emit('auction_bid_placed', bid_data, room=auction.game_id)
            
            return bid_data
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error placing bid: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

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
        """Internal logic for ending an auction"""
        try:
            # Get the Flask app from the config
            app = self.app_config.get('app')
            if not app:
                self.logger.error("Flask app not found in app_config")
                return False
                
            # Use the app context for database operations
            with app.app_context():
                auction = Auction.query.get(auction_id)
                if not auction:
                    self.logger.error(f"Auction {auction_id} not found")
                    return False
                    
                if auction.status != 'active':
                    self.logger.info(f"Auction {auction_id} is already ended")
                    return True
                    
                # Get the highest bid
                highest_bid = auction.get_highest_bid()
                
                if highest_bid:
                    # Property was sold
                    property_id = auction.property_id
                    buyer_id = highest_bid.bidder_id
                    amount = highest_bid.amount
                    
                    # Update property ownership
                    property_obj = Property.query.get(property_id)
                    if property_obj:
                        property_obj.owner_id = buyer_id
                        property_obj.is_mortgaged = False
                        
                        # Update buyer's money
                        buyer = Player.query.get(buyer_id)
                        if buyer:
                            buyer.money -= amount
                            
                            # Add to game log
                            game_state = GameState.query.get(auction.game_id)
                            if game_state:
                                log_entry = {
                                    "type": "auction_ended",
                                    "property_id": property_id,
                                    "property_name": property_obj.name,
                                    "buyer_id": buyer_id,
                                    "buyer_name": buyer.username,
                                    "amount": amount,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                                current_log.append(log_entry)
                                game_state.game_log = json.dumps(current_log)
                    
                    # Update auction status
                    auction.status = 'completed'
                    auction.current_bidder_id = buyer_id  # Use current_bidder_id instead of winner_id
                    auction.final_price = amount
                    
                    # Emit auction ended event
                    if self.socketio:
                        self.socketio.emit('auction_ended', {
                            'auction_id': auction_id,
                            'property_id': property_id,
                            'property_name': property_obj.name if property_obj else "Unknown",
                            'winner_id': buyer_id,
                            'winner_name': buyer.username if buyer else "Unknown",
                            'amount': amount
                        }, room=auction.game_id)
                else:
                    # No bids - property remains unowned
                    auction.status = 'completed'
                    auction.current_bidder_id = None  # Use current_bidder_id instead of winner_id
                    auction.final_price = 0
                    
                    # Emit auction ended event
                    if self.socketio:
                        self.socketio.emit('auction_ended', {
                            'auction_id': auction_id,
                            'property_id': auction.property_id,
                            'property_name': "Unknown",
                            'winner_id': None,
                            'winner_name': None,
                            'amount': 0
                        }, room=auction.game_id)
                
                # Commit changes
                db.session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error ending auction: {str(e)}", exc_info=True)
            return False

    # --- Timer Management --- 

    def _start_auction_timer(self, auction_id):
        """Start a timer for an auction to auto-end after its duration."""
        try:
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Cannot start timer for non-existent auction {auction_id}")
                return False
                
            # Cancel any existing timer for this auction
            self._cancel_timer(auction_id)
            
            # Calculate duration from end_time or use default
            now = datetime.utcnow()
            if auction.end_time:
                remaining_seconds = max(0, (auction.end_time - now).total_seconds())
            else:
                remaining_seconds = AUCTION_TIMER_DEFAULT
                
            logger.info(f"Starting auction timer for {auction_id} with {remaining_seconds:.1f} seconds duration")
            
            def timer_callback():
                """Called when the timer expires to end the auction."""
                try:
                    # Directly call the end auction logic with this auction ID
                    logger.info(f"Auction timer expired for auction {auction_id}")
                    self._timer_auction_end_callback(auction_id)
                except Exception as e:
                    logger.error(f"Error in auction timer callback for auction {auction_id}: {str(e)}", exc_info=True)
            
            # Use socketio background task for timer which works with Flask's async mode
            timer = self.socketio.start_background_task(
                self._delayed_execution,
                timer_callback,
                remaining_seconds
            )
            
            # Store the timer in our active_timers dictionary
            self.active_timers[auction_id] = {
                'timer': timer,
                'expiry': now + timedelta(seconds=remaining_seconds)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting auction timer for {auction_id}: {str(e)}", exc_info=True)
            return False
            
    def _delayed_execution(self, callback_function, delay_seconds):
        """Helper method to execute a function after a delay using eventlet.sleep."""
        try:
            import eventlet
            eventlet.sleep(delay_seconds)
            callback_function()
        except Exception as e:
            logger.error(f"Error in delayed execution: {str(e)}", exc_info=True)
            
    def _reset_auction_timer(self, auction_id, extension_seconds=AUCTION_TIMER_EXTENSION):
        """Reset the auction timer when a new bid is placed, extending the duration."""
        try:
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Cannot reset timer for non-existent auction {auction_id}")
                return False
                
            logger.info(f"Extending auction timer for {auction_id} by {extension_seconds} seconds")
            
            # Cancel existing timer for this auction
            self._cancel_timer(auction_id)
            
            # Update the auction end time in the database
            now = datetime.utcnow()
            new_end_time = now + timedelta(seconds=extension_seconds)
            auction.end_time = new_end_time
            db.session.add(auction)
            db.session.commit()
            
            # Start a new timer
            def timer_callback():
                """Called when the timer expires to end the auction."""
                try:
                    logger.info(f"Extended auction timer expired for auction {auction_id}")
                    self._timer_auction_end_callback(auction_id)
                except Exception as e:
                    logger.error(f"Error in extended auction timer callback for auction {auction_id}: {str(e)}", exc_info=True)
            
            # Use socketio background task for timer which works with Flask's async mode
            timer = self.socketio.start_background_task(
                self._delayed_execution,
                timer_callback,
                extension_seconds
            )
            
            # Store the timer in our active_timers dictionary
            self.active_timers[auction_id] = {
                'timer': timer,
                'expiry': new_end_time
            }
            
            # Emit an event to notify clients of the timer extension
            self.socketio.emit('auction_timer_extended', {
                'auction_id': auction_id,
                'end_time': new_end_time.isoformat(),
                'seconds_remaining': extension_seconds
            }, room=auction.game_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting auction timer for {auction_id}: {str(e)}", exc_info=True)
            return False
            
    def _cancel_timer(self, auction_id):
        """Cancel an active timer for an auction."""
        try:
            if auction_id in self.active_timers:
                timer_info = self.active_timers[auction_id]
                # Note: For background tasks in Flask-SocketIO, we can't directly cancel
                # But we can mark it for cleanup and it won't execute its callback if we handle this properly
                logger.info(f"Cancelling auction timer for {auction_id}")
                self.active_timers.pop(auction_id, None)
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling timer for auction {auction_id}: {str(e)}", exc_info=True)
            return False
            
    def _timer_auction_end_callback(self, auction_id):
        """Callback executed when an auction timer expires."""
        try:
            with self.app.app_context():
                # Re-query the auction to get the latest state
                auction = Auction.query.get(auction_id)
                if not auction:
                    logger.error(f"Auction {auction_id} not found in timer callback")
                    return
                    
                # Check if the auction is still active (it might have been ended manually)
                if auction.status != 'active':
                    logger.info(f"Auction {auction_id} is no longer active (status: {auction.status}), ignoring timer callback")
                    return
                
                # Process auction end
                logger.info(f"Processing timeout-triggered end for auction {auction_id}")
                result = self._end_auction_logic(auction_id)
                
                # Check result and log appropriately
                if result.get('success'):
                    winner_id = result.get('winner_id')
                    if winner_id:
                        logger.info(f"Auction {auction_id} ended successfully due to timer expiry. Winner: Player {winner_id}")
                    else:
                        logger.info(f"Auction {auction_id} ended with no winner due to timer expiry")
                else:
                    logger.error(f"Failed to end auction {auction_id} in timer callback: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Error in auction timer callback for {auction_id}: {str(e)}", exc_info=True)

    def _check_active_auctions(self):
        """Periodically check all active auctions to ensure timers are working correctly."""
        logger.debug("Checking active auctions")
        
        try:
            with self.app.app_context():
                now = datetime.utcnow()
                # Find all active auctions
                active_auctions = Auction.query.filter_by(status='active').all()
                
                for auction in active_auctions:
                    # Check if this auction should have ended already
                    if auction.end_time and auction.end_time < now:
                        # If the auction should have ended but didn't, end it now
                        logger.warning(f"Auction {auction.id} should have ended at {auction.end_time} but is still active. Ending now.")
                        self._end_auction_logic(auction.id)
                    elif auction.id not in self.active_timers:
                        # If the auction is still running but doesn't have an active timer, start one
                        logger.warning(f"Active auction {auction.id} has no timer. Starting a new timer.")
                        self._start_auction_timer(auction.id)
        except Exception as e:
            logger.error(f"Error checking active auctions: {str(e)}", exc_info=True)
            
    def start_check_active_auctions_task(self):
        """Start a background task to periodically check active auctions."""
        try:
            def check_active_auctions_loop():
                """Loop that periodically checks active auctions."""
                while True:
                    try:
                        # Sleep for a while before checking again
                        import eventlet
                        eventlet.sleep(60)  # Check every minute
                        self._check_active_auctions()
                    except Exception as e:
                        logger.error(f"Error in check active auctions loop: {str(e)}", exc_info=True)
            
            # Start the background task
            self.socketio.start_background_task(check_active_auctions_loop)
            logger.info("Started background task to check active auctions")
            return True
        except Exception as e:
            logger.error(f"Failed to start check active auctions task: {str(e)}", exc_info=True)
            return False

    # --- Placeholder/Passthrough Methods (Controller logic moved here) ---
    
    def start_auction(self, game_id, property_id, starting_bid=None, duration=120):
        """
        Start a new auction for a property.
        
        Args:
            game_id (str): The ID of the game.
            property_id (str): The ID of the property to auction.
            starting_bid (float, optional): The starting bid amount. Defaults to property's base price * 0.5.
            duration (int, optional): The duration of the auction in seconds. Defaults to 120.
            
        Returns:
            dict: A dictionary with the auction details or error.
        """
        logger.info(f"Starting auction for property {property_id} in game {game_id}")
        
        try:
            # Get the game state
            game_state = GameState.query.filter_by(game_id=game_id).first()
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the property
            property_obj = Property.query.get(property_id)
            if not property_obj:
                logger.error(f"Property {property_id} not found")
                return {"success": False, "error": "Property not found"}
            
            # Check if property is already owned
            if property_obj.owner_id:
                logger.error(f"Property {property_id} already owned by player {property_obj.owner_id}")
                return {"success": False, "error": "Property already owned"}
            
            # Determine starting bid
            if starting_bid is None:
                starting_bid = property_obj.price * 0.5
            
            # Create a new auction
            auction = Auction(
                game_id=game_id,
                property_id=property_id,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(seconds=duration),
                starting_bid=starting_bid,
                current_bid=starting_bid,
                current_winner_id=None,
                status="active"
            )
            
            db.session.add(auction)
            db.session.flush()  # Get the ID without committing
            
            # Update game log
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {game_id}, creating new log")
                    current_log = []
            else:
                current_log = []
            
            log_entry = {
                "type": "auction_started",
                "auction_id": auction.id,
                "property_id": property_id,
                "property_name": property_obj.name,
                "starting_bid": starting_bid,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Set expected action for the game (all players can bid)
            expected_action = {
                "type": "auction_bid",
                "auction_id": auction.id,
                "property_id": property_id,
                "minimum_bid": starting_bid,
                "ends_at": auction.end_time.isoformat()
            }
            game_state.expected_action = json.dumps(expected_action)
            
            db.session.commit()
            
            # Schedule auction to end after the duration
            self._schedule_auction_end(auction.id, duration)
            
            # Emit event to notify clients
            auction_data = {
                "success": True,
                "auction_id": auction.id,
                "property_id": property_id,
                "property_name": property_obj.name,
                "starting_bid": starting_bid,
                "current_bid": starting_bid,
                "current_winner_id": None,
                "duration": duration,
                "ends_at": auction.end_time.isoformat()
            }
            self.socketio.emit('auction_started', auction_data, room=game_id)
            
            return auction_data
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting auction: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def start_foreclosure_auction(self, property_id, owner_id, minimum_bid=None):
         """Public method to initiate starting a foreclosure auction."""
         logger.info(f"Request received to start foreclosure auction for property {property_id}, owner {owner_id}")
         return self._start_auction_logic(property_id, is_foreclosure=True, owner_id=owner_id, minimum_bid=minimum_bid)

    def place_bid(self, auction_id, player_id, bid_amount):
        """
        Place a bid in an active auction.
        
        Args:
            auction_id (str): The ID of the auction.
            player_id (str): The ID of the player placing the bid.
            bid_amount (float): The amount of the bid.
            
        Returns:
            dict: A dictionary with the results of the bid placement.
        """
        logger.info(f"Player {player_id} placing bid of {bid_amount} in auction {auction_id}")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found")
                return {"success": False, "error": "Auction not found"}
            
            # Check if auction is still active
            if auction.status != "active":
                logger.error(f"Auction {auction_id} is not active (status: {auction.status})")
                return {"success": False, "error": f"Auction is not active, current status: {auction.status}"}
            
            # Check if auction has ended
            if auction.end_time < datetime.utcnow():
                logger.error(f"Auction {auction_id} has already ended")
                return {"success": False, "error": "Auction has already ended"}
            
            # Get the player
            player = Player.query.get(player_id)
            if not player:
                logger.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Check if player is active in the game
            if player.status != "active":
                logger.error(f"Player {player_id} is not active (status: {player.status})")
                return {"success": False, "error": "Player is not active in the game"}
            
            # Check if bid is higher than current bid
            if bid_amount <= auction.current_bid:
                logger.error(f"Bid amount {bid_amount} is not higher than current bid {auction.current_bid}")
                return {"success": False, "error": f"Bid must be higher than current bid of {auction.current_bid}"}
            
            # Check if player has enough money
            if player.balance < bid_amount:
                logger.error(f"Player {player_id} has insufficient funds for bid of {bid_amount}")
                return {"success": False, "error": "Insufficient funds for this bid"}
            
            # Record the previous winner (for notification)
            previous_winner_id = auction.current_winner_id
            
            # Update the auction
            auction.current_bid = bid_amount
            auction.current_winner_id = player_id
            
            # Get the game state
            game_state = GameState.query.filter_by(game_id=auction.game_id).first()
            if not game_state:
                logger.error(f"Game {auction.game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Update game log
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {auction.game_id}, creating new log")
                    current_log = []
            else:
                current_log = []
            
            log_entry = {
                "type": "auction_bid",
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "player_id": player_id,
                "player_name": player.name,
                "bid_amount": bid_amount,
                "timestamp": datetime.utcnow().isoformat()
            }
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # If there's less than 30 seconds left, extend the auction
            time_remaining = (auction.end_time - datetime.utcnow()).total_seconds()
            if time_remaining < 30:
                auction.end_time = datetime.utcnow() + timedelta(seconds=30)
                logger.info(f"Extended auction {auction_id} by 30 seconds due to last-minute bid")
                # Reschedule the end timer
                self._schedule_auction_end(auction_id, 30)
            
            db.session.commit()
            
            # Prepare the bid data
            bid_data = {
                "success": True,
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "player_id": player_id,
                "player_name": player.name,
                "bid_amount": bid_amount,
                "previous_winner_id": previous_winner_id,
                "ends_at": auction.end_time.isoformat()
            }
            
            # Emit event to notify clients
            self.socketio.emit('auction_bid_placed', bid_data, room=auction.game_id)
            
            return bid_data
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error placing bid: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def pass_auction(self, auction_id, player_id):
         """Public method for a player to pass."""
         logger.info(f"Request received for player {player_id} to pass on auction {auction_id}")
         return self._pass_auction_logic(auction_id, player_id)

    def end_auction(self, auction_id): # Typically called by timer or pass logic
         """Public method to explicitly end an auction (use with caution)."""
         logger.warning(f"Explicit request received to end auction {auction_id}. Normally handled by timer/pass.")
         return self._end_auction_logic(auction_id)
         
    def cancel_auction(self, auction_id, reason="Admin cancelled"):
        """
        Cancel an active auction.
        
        Args:
            auction_id (str): The ID of the auction to cancel.
            reason (str, optional): The reason for cancellation. Defaults to "Admin cancelled".
            
        Returns:
            dict: A dictionary with the results of the cancellation.
        """
        logger.info(f"Cancelling auction {auction_id}: {reason}")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found")
                return {"success": False, "error": "Auction not found"}
            
            # Check if auction is still active
            if auction.status != "active":
                logger.warning(f"Attempted to cancel auction {auction_id} with status {auction.status}")
                return {"success": False, "error": f"Auction is not active, current status: {auction.status}"}
            
            # Cancel the timer
            self._cancel_timer(auction_id)
        
            # Update the auction
            auction.status = "cancelled"
            auction.end_time = datetime.utcnow()
            
            # Get the game state
            game_state = GameState.query.filter_by(game_id=auction.game_id).first()
            if not game_state:
                logger.error(f"Game {auction.game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Update game log
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {auction.game_id}, creating new log")
                    current_log = []
            else:
                current_log = []
            
            log_entry = {
                "type": "auction_cancelled",
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Reset expected action if it pertains to this auction
            if game_state.expected_action:
                try:
                    expected_action = json.loads(game_state.expected_action)
                    if expected_action.get("auction_id") == auction_id:
                        game_state.expected_action = None
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse expected action for game {auction.game_id}")
            
            db.session.commit()
            
            # Emit event to notify clients
            cancel_data = {
                "success": True,
                "auction_id": auction_id,
                "property_id": auction.property_id,
                "status": "cancelled",
                "reason": reason
            }
            self.socketio.emit('auction_cancelled', cancel_data, room=auction.game_id)
            
            return cancel_data
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling auction: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def get_active_auctions(self, game_id):
        """
        Get all active auctions for a specific game.
        
        Args:
            game_id (str): The ID of the game.
            
        Returns:
            dict: A dictionary with a list of active auctions.
        """
        logger.info(f"Getting active auctions for game {game_id}")
        
        try:
            # Get all active auctions for the game
            auctions = Auction.query.filter_by(game_id=game_id, status="active").all()
            
            # Format the auction data
            auction_list = []
            for auction in auctions:
                # Get the property
                property_obj = Property.query.get(auction.property_id)
                if not property_obj:
                    logger.warning(f"Property {auction.property_id} for auction {auction.id} not found")
                    continue
                    
                # Get the current highest bidder
                current_winner = None
                if auction.current_winner_id:
                    player = Player.query.get(auction.current_winner_id)
                    if player:
                        current_winner = {
                            "id": player.id,
                            "name": player.name
                        }
                
                # Calculate time remaining
                time_remaining = 0
                if auction.end_time > datetime.utcnow():
                    time_remaining = (auction.end_time - datetime.utcnow()).total_seconds()
                
                # Add the auction data to the list
                auction_data = {
                    "auction_id": auction.id,
                    "property_id": auction.property_id,
                    "property_name": property_obj.name,
                    "starting_bid": auction.starting_bid,
                    "current_bid": auction.current_bid,
                    "current_winner": current_winner,
                    "time_remaining": time_remaining,
                    "start_time": auction.start_time.isoformat(),
                    "end_time": auction.end_time.isoformat()
                }
                auction_list.append(auction_data)
            
            return {
                "success": True,
                "game_id": game_id,
                "auctions": auction_list,
                "count": len(auction_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting active auctions: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
             
    def get_auction(self, auction_id):
        """
        Get detailed information about a specific auction.
        
        Args:
            auction_id (str): The ID of the auction.
            
        Returns:
            dict: A dictionary with detailed auction information.
        """
        logger.info(f"Getting auction details for {auction_id}")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found")
                return {"success": False, "error": "Auction not found"}
            
            # Get the property
            property_obj = Property.query.get(auction.property_id)
            if not property_obj:
                logger.error(f"Property {auction.property_id} not found")
                return {"success": False, "error": "Property not found"}
            
            # Get current winner details if available
            current_winner = None
            if auction.current_winner_id:
                player = Player.query.get(auction.current_winner_id)
                if player:
                    current_winner = {
                        "id": player.id,
                        "name": player.name
                    }
                
            # Get game details
            game = GameState.query.filter_by(game_id=auction.game_id).first()
            game_data = None
            if game:
                game_data = {
                    "id": game.id,
                    "name": game.name if hasattr(game, 'name') else f"Game {game.id}"
                }
            
            # Calculate time remaining for active auctions
            time_remaining = 0
            if auction.status == "active" and auction.end_time > datetime.utcnow():
                time_remaining = (auction.end_time - datetime.utcnow()).total_seconds()
            
            # Prepare the result data
            result = {
                "success": True,
                "auction_id": auction.id,
                "game": game_data,
                "property": {
                    "id": property_obj.id,
                    "name": property_obj.name,
                    "type": property_obj.property_type,
                    "price": property_obj.price
                },
                "starting_bid": auction.starting_bid,
                "current_bid": auction.current_bid,
                "current_winner": current_winner,
                "status": auction.status,
                "time_remaining": time_remaining,
                "start_time": auction.start_time.isoformat(),
                "end_time": auction.end_time.isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting auction details: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _schedule_auction_end(self, auction_id, seconds):
        """
        Schedule an auction to end after the specified number of seconds.
        
        Args:
            auction_id (str): The ID of the auction to end.
            seconds (int): The number of seconds before ending the auction.
        """
        logger.info(f"Scheduling auction {auction_id} to end in {seconds} seconds")
        
        # Cancel any existing timer for this auction
        self._cancel_timer(auction_id)
        
        # Create a new timer
        timer = threading.Timer(seconds, self._timer_auction_end_callback, args=[auction_id])
        timer.daemon = True  # Allow the timer to be terminated when the main program exits
        timer.start()
        
        # Store the timer reference
        self.active_timers[auction_id] = timer
        
    def _timer_auction_end_callback(self, auction_id):
        """
        Callback function for when an auction timer expires.
        
        Args:
            auction_id (str): The ID of the auction to end.
        """
        logger.info(f"Timer expired for auction {auction_id}")
        
        # Remove the timer from the dictionary
        if auction_id in self.active_timers:
            del self.active_timers[auction_id]
        
        # End the auction
        result = self._end_auction_logic(auction_id)
        
        if not result["success"]:
            logger.error(f"Failed to end auction {auction_id} after timer expiry: {result.get('error')}")
        else:
            logger.info(f"Successfully ended auction {auction_id} after timer expiry")

    def start_auction_monitoring_task(self):
        """Start a background task to periodically check active auctions."""
        logger.info("Starting background auction monitoring task")
        
        def check_active_auctions_loop():
            """Background loop that periodically checks active auctions."""
            import eventlet
            while True:
                try:
                    # Sleep first
                    eventlet.sleep(60)  # Check every minute
                    
                    # Then check auctions
                    self._check_active_auctions()
                except Exception as e:
                    logger.error(f"Error in auction monitoring loop: {str(e)}", exc_info=True)
        
        # Start the background task
        self.socketio.start_background_task(check_active_auctions_loop)
        logger.info("Auction monitoring task started successfully")

    def get_schedule_auction_check(self, interval_seconds=60):
        """
        Schedule a periodic check of all active auctions.
        
        This method sets up a recurring task that verifies all active auctions
        are properly tracked with timers and auctions that should have ended are processed.
        
        Args:
            interval_seconds (int): The interval between checks in seconds. Default is 60 seconds.
            
        Returns:
            bool: True if the task was scheduled successfully, False otherwise.
        """
        logger.info(f"Scheduling auction check task to run every {interval_seconds} seconds")
        
        try:
            def auction_check_task():
                """Periodic task to check all active auctions."""
                while True:
                    try:
                        # Use eventlet.sleep to avoid blocking the event loop
                        import eventlet
                        eventlet.sleep(interval_seconds)
                        
                        # Check all active auctions
                        with self.app.app_context():
                            logger.debug("Performing scheduled check of active auctions")
                            self._check_active_auctions()
                    except Exception as e:
                        logger.error(f"Error in scheduled auction check: {str(e)}", exc_info=True)
            
            # Start the background task
            self.socketio.start_background_task(auction_check_task)
            logger.info("Auction check task scheduled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule auction check task: {str(e)}", exc_info=True)
            return False

    def get_auction_status(self, auction_id):
        """
        Get detailed status information for an auction.
        
        This method fetches comprehensive information about an auction,
        including the property details, current bids, time remaining,
        and participant information.
        
        Args:
            auction_id (str): The ID of the auction to get status for.
            
        Returns:
            dict: A dictionary with auction status information or error.
        """
        logger.info(f"Getting detailed status for auction {auction_id}")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found")
                return {"success": False, "error": "Auction not found"}
                
            # Get the property
            property_obj = Property.query.get(auction.property_id)
            if not property_obj:
                logger.error(f"Property {auction.property_id} for auction {auction_id} not found")
                return {"success": False, "error": "Property not found"}
                
            # Get current winner details if there is one
            current_winner = None
            if auction.current_winner_id:
                winner = Player.query.get(auction.current_winner_id)
                if winner:
                    current_winner = {
                        "id": winner.id,
                        "name": winner.name,
                        "balance": winner.balance
                    }
            
            # Calculate time remaining
            time_remaining = 0
            if auction.status == "active" and auction.end_time > datetime.utcnow():
                now = datetime.utcnow()
                if auction.end_time > now:
                    time_remaining = (auction.end_time - now).total_seconds()
            
            # Get all eligible players
            eligible_players = []
            for player_id in auction.get_eligible_players():
                player = Player.query.get(player_id)
                if player:
                    eligible_players.append({
                        "id": player.id,
                        "name": player.name,
                        "status": "passed" if player_id in auction.get_passed_players() else "active"
                    })
            
            # Build the full auction status
            status_data = {
                "success": True,
                "auction_id": auction_id,
                "property": {
                    "id": property_obj.id,
                    "name": property_obj.name,
                    "color": property_obj.color if hasattr(property_obj, 'color') else None,
                    "price": property_obj.price,
                    "property_type": property_obj.property_type if hasattr(property_obj, 'property_type') else "property"
                },
                "status": auction.status,
                "starting_bid": auction.starting_bid,
                "current_bid": auction.current_bid,
                "current_winner": current_winner,
                "time_remaining": time_remaining,
                "start_time": auction.start_time.isoformat() if auction.start_time else None,
                "end_time": auction.end_time.isoformat() if auction.end_time else None,
                "eligible_players": eligible_players,
                "game_id": auction.game_id
            }
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error getting auction status: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error retrieving auction status: {str(e)}"}

    def batch_end_auctions(self, auction_ids, reason="Admin batch operation"):
        """
        End multiple auctions at once.
        
        This method ends multiple auctions in a single batch operation,
        which is primarily used for admin cleanup or maintenance.
        
        Args:
            auction_ids (list): List of auction IDs to end.
            reason (str): The reason for ending these auctions.
            
        Returns:
            dict: A dictionary with results of the batch operation.
        """
        logger.info(f"Processing batch end for {len(auction_ids)} auctions: {reason}")
        
        results = {
            "success": True,
            "total": len(auction_ids),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for auction_id in auction_ids:
            try:
                # Process each auction
                auction_result = self._end_auction_logic(auction_id)
                
                # Track the result
                result_entry = {
                    "auction_id": auction_id,
                    "success": auction_result.get("success", False)
                }
                
                results["processed"] += 1
                
                if auction_result.get("success", False):
                    results["successful"] += 1
                    result_entry["status"] = auction_result.get("status", "completed")
                    result_entry["winner_id"] = auction_result.get("winner_id")
                else:
                    results["failed"] += 1
                    result_entry["error"] = auction_result.get("error", "Unknown error")
                    
                results["details"].append(result_entry)
                
            except Exception as e:
                logger.error(f"Error processing auction {auction_id} in batch: {str(e)}", exc_info=True)
                results["processed"] += 1
                results["failed"] += 1
                results["details"].append({
                    "auction_id": auction_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Set overall success based on results
        if results["failed"] > 0:
            results["success"] = False
            
        logger.info(f"Batch auction end completed: {results['successful']} successful, {results['failed']} failed")
        return results

    def cleanup_stale_auctions(self, hours_old=24):
        """
        Find and clean up auctions that are stuck in an active state but should have ended.
        
        This method is primarily used for maintenance to ensure no auctions remain
        in an active state when they should have ended.
        
        Args:
            hours_old (int): Consider auctions older than this many hours as stale.
            
        Returns:
            dict: A dictionary with results of the cleanup operation.
        """
        logger.info(f"Cleaning up stale auctions older than {hours_old} hours")
        
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            # Find all stale auctions
            stale_auctions = Auction.query.filter(
                Auction.status == "active",
                Auction.end_time < cutoff_time
            ).all()
            
            if not stale_auctions:
                logger.info("No stale auctions found")
                return {
                    "success": True,
                    "message": "No stale auctions found",
                    "count": 0
                }
            
            # Get all auction IDs
            auction_ids = [auction.id for auction in stale_auctions]
            
            # Process the batch end
            result = self.batch_end_auctions(
                auction_ids, 
                reason=f"Automatic cleanup of stale auctions older than {hours_old} hours"
            )
            
            # Add additional context
            result["stale_auctions_found"] = len(auction_ids)
            result["cutoff_time"] = cutoff_time.isoformat()
            
            logger.info(f"Stale auction cleanup completed: {result['successful']} ended, {result['failed']} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error during stale auction cleanup: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error during stale auction cleanup: {str(e)}",
                "count": 0
            }

    def start_sequential_auctions(self, game_id, property_ids, starting_bids=None, duration=120, reason="Sequential auction"):
        """
        Start auctions for multiple properties sequentially.
        
        This method queues up multiple properties for auction and starts them one by one,
        with each subsequent auction starting when the previous one completes.
        
        Args:
            game_id (str): The ID of the game
            property_ids (list): List of property IDs to auction in sequence
            starting_bids (dict, optional): Dictionary mapping property IDs to starting bids
            duration (int, optional): Duration for each auction in seconds
            reason (str, optional): Reason for starting these auctions
            
        Returns:
            dict: Result of the sequential auction setup
        """
        logger.info(f"Starting sequential auctions for {len(property_ids)} properties in game {game_id}")
        
        if not property_ids:
            return {"success": False, "error": "No properties provided for auction"}
        
        # Validate game exists
        game_state = GameState.query.filter_by(game_id=game_id).first()
        if not game_state:
            logger.error(f"Game {game_id} not found for sequential auctions")
            return {"success": False, "error": "Game not found"}
        
        # Validate all properties exist and are available for auction
        valid_properties = []
        invalid_properties = []
        
        for prop_id in property_ids:
            property_obj = Property.query.get(prop_id)
            if not property_obj or property_obj.game_id != game_id:
                invalid_properties.append(prop_id)
                continue
                
            if property_obj.owner_id is not None:
                # Check if it's a foreclosure scenario
                if starting_bids and prop_id in starting_bids:
                    # Allow it if a starting bid is specified (foreclosure)
                    valid_properties.append(prop_id)
                else:
                    invalid_properties.append(prop_id)
            else:
                valid_properties.append(prop_id)
        
        if not valid_properties:
            return {
                "success": False, 
                "error": "No valid properties available for auction",
                "invalid_properties": invalid_properties
            }
        
        # Store the sequential auction queue in the game state
        sequential_auction_data = {
            "property_ids": valid_properties,
            "current_index": 0,
            "starting_bids": starting_bids or {},
            "duration": duration,
            "reason": reason,
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "completed": [],
            "pending": valid_properties.copy()
        }
        
        # Store this in game_state.auction_data
        try:
            if game_state.auction_data:
                current_auction_data = json.loads(game_state.auction_data)
                if current_auction_data.get("status") == "active":
                    logger.warning(f"Replacing active sequential auction in game {game_id}")
            
            game_state.auction_data = json.dumps(sequential_auction_data)
            db.session.commit()
            
            # Start the first auction
            first_property = valid_properties[0]
            first_starting_bid = None
            if starting_bids and first_property in starting_bids:
                first_starting_bid = starting_bids[first_property]
                
            result = self.start_auction(
                game_id=game_id,
                property_id=first_property,
                starting_bid=first_starting_bid,
                duration=duration
            )
            
            # Update the queue with the auction ID
            if result.get("success"):
                first_auction_id = result.get("auction", {}).get("id")
                if first_auction_id:
                    sequential_auction_data["current_auction_id"] = first_auction_id
                    game_state.auction_data = json.dumps(sequential_auction_data)
                    db.session.commit()
            
            return {
                "success": True,
                "message": f"Sequential auction started with {len(valid_properties)} properties",
                "first_auction": result,
                "total_properties": len(valid_properties),
                "invalid_properties": invalid_properties,
                "sequential_auction_id": str(uuid.uuid4())  # Generate a unique ID for this sequence
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting sequential auctions: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error starting sequential auctions: {str(e)}"}
    
    def _process_next_sequential_auction(self, game_id):
        """
        Process the next auction in a sequential auction queue.
        
        This method is called when an auction completes to start the next one in the sequence.
        
        Args:
            game_id (str): The ID of the game with sequential auctions
            
        Returns:
            dict: Result of starting the next auction or completing the sequence
        """
        logger.info(f"Processing next sequential auction for game {game_id}")
        
        try:
            # Get the game state
            game_state = GameState.query.filter_by(game_id=game_id).first()
            if not game_state or not game_state.auction_data:
                logger.error(f"Game {game_id} not found or has no auction data")
                return {"success": False, "error": "Game not found or no auction data"}
            
            # Parse the auction data
            auction_data = json.loads(game_state.auction_data)
            
            # Check if the sequential auction is still active
            if auction_data.get("status") != "active":
                logger.info(f"Sequential auction for game {game_id} is not active")
                return {"success": False, "error": "Sequential auction is not active"}
            
            # Get the current index and property IDs
            current_index = auction_data.get("current_index", 0)
            property_ids = auction_data.get("property_ids", [])
            
            # Move to the next property
            current_index += 1
            
            # Check if we've processed all properties
            if current_index >= len(property_ids):
                # All auctions complete
                auction_data["status"] = "completed"
                auction_data["completed_at"] = datetime.utcnow().isoformat()
                game_state.auction_data = json.dumps(auction_data)
                db.session.commit()
                
                logger.info(f"Sequential auction for game {game_id} completed. All properties processed.")
                
                # Emit an event to notify clients
                self.socketio.emit('sequential_auction_completed', {
                    "game_id": game_id,
                    "properties_auctioned": len(property_ids),
                    "completed_at": auction_data["completed_at"]
                }, room=game_id)
                
                return {
                    "success": True,
                    "message": "Sequential auction completed",
                    "properties_auctioned": len(property_ids)
                }
            
            # Get the next property
            next_property = property_ids[current_index]
            
            # Get the starting bid if specified
            starting_bids = auction_data.get("starting_bids", {})
            next_starting_bid = None
            if next_property in starting_bids:
                next_starting_bid = starting_bids[next_property]
            
            # Start the next auction
            result = self.start_auction(
                game_id=game_id,
                property_id=next_property,
                starting_bid=next_starting_bid,
                duration=auction_data.get("duration", 120)
            )
            
            # Update the auction data
            if result.get("success"):
                auction_data["current_index"] = current_index
                auction_data["current_auction_id"] = result.get("auction", {}).get("id")
                
                # Update completed and pending lists
                previous_property = property_ids[current_index - 1]
                if previous_property in auction_data["pending"]:
                    auction_data["pending"].remove(previous_property)
                    auction_data["completed"].append(previous_property)
                
                game_state.auction_data = json.dumps(auction_data)
                db.session.commit()
                
                # Emit an event to notify clients about the next auction
                self.socketio.emit('sequential_auction_next', {
                    "game_id": game_id,
                    "next_property": next_property,
                    "auction_id": auction_data["current_auction_id"],
                    "remaining": len(auction_data["pending"]),
                    "completed": len(auction_data["completed"])
                }, room=game_id)
                
                return {
                    "success": True,
                    "message": "Next sequential auction started",
                    "next_auction": result,
                    "property_index": current_index,
                    "remaining": len(property_ids) - current_index - 1
                }
            else:
                logger.error(f"Failed to start next auction in sequence: {result.get('error')}")
                return {"success": False, "error": f"Failed to start next auction: {result.get('error')}"}
            
        except Exception as e:
            logger.error(f"Error processing next sequential auction: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error processing next sequential auction: {str(e)}"}

    def process_bot_bid(self, auction_id, bot_id, bot_strategy="default"):
        """
        Process an automated bid from a bot player.
        
        This method calculates an appropriate bid amount based on the bot's strategy
        and the current auction state, then places the bid on behalf of the bot.
        
        Args:
            auction_id (str): The ID of the auction
            bot_id (str): The ID of the bot player
            bot_strategy (str, optional): Strategy identifier for the bot
                Options: "default", "aggressive", "conservative", "strategic"
                
        Returns:
            dict: Result of the bot's bid attempt
        """
        logger.info(f"Processing bot bid for auction {auction_id} from bot {bot_id} using strategy '{bot_strategy}'")
        
        try:
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                logger.error(f"Auction {auction_id} not found for bot bid")
                return {"success": False, "error": "Auction not found"}
                
            # Check if auction is active
            if auction.status != "active":
                logger.info(f"Bot {bot_id} cannot bid on inactive auction {auction_id}")
                return {"success": False, "error": "Auction is not active"}
                
            # Get the bot
            bot = Player.query.get(bot_id)
            if not bot:
                logger.error(f"Bot player {bot_id} not found")
                return {"success": False, "error": "Bot player not found"}
                
            # Check if the bot is active
            if bot.status != "active":
                logger.info(f"Bot {bot_id} is not active in the game")
                return {"success": False, "error": "Bot is not active"}
                
            # Get the property
            property_obj = Property.query.get(auction.property_id)
            if not property_obj:
                logger.error(f"Property {auction.property_id} not found")
                return {"success": False, "error": "Property not found"}
                
            # Calculate the next minimum bid
            minimum_bid = auction.current_bid + 1 if auction.current_bid > 0 else auction.starting_bid
            
            # Check if the bot can afford the minimum bid
            if bot.balance < minimum_bid:
                logger.info(f"Bot {bot_id} cannot afford minimum bid of {minimum_bid}")
                return {"success": False, "error": "Insufficient funds for minimum bid", "pass_auction": True}
                
            # Calculate bid amount based on strategy
            bid_amount = self._calculate_bot_bid(
                bot=bot,
                property_obj=property_obj,
                auction=auction,
                strategy=bot_strategy
            )
            
            # If the bid is 0 or less than minimum, the bot decides to pass
            if bid_amount <= 0 or bid_amount < minimum_bid:
                logger.info(f"Bot {bot_id} decided to pass on auction {auction_id}")
                return {"success": False, "error": "Bot decided to pass", "pass_auction": True}
                
            # Place the bid
            result = self._place_bid_logic(auction_id, bot_id, bid_amount)
            
            # Log the result
            if result.get("success"):
                logger.info(f"Bot {bot_id} successfully placed bid of {bid_amount} on auction {auction_id}")
            else:
                logger.warning(f"Bot {bot_id} failed to place bid: {result.get('error')}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing bot bid: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error processing bot bid: {str(e)}"}
            
    def _calculate_bot_bid(self, bot, property_obj, auction, strategy="default"):
        """
        Calculate an appropriate bid amount for a bot based on its strategy.
        
        Args:
            bot (Player): The bot player
            property_obj (Property): The property being auctioned
            auction (Auction): The auction object
            strategy (str): The bidding strategy to use
            
        Returns:
            float: The calculated bid amount (0 means pass)
        """
        # Base property value
        property_value = property_obj.price
        
        # Get the current highest bid
        current_bid = auction.current_bid if auction.current_bid > 0 else auction.starting_bid
        
        # Check if bot already has properties in this group
        bot_has_group_properties = False
        if hasattr(property_obj, 'group'):
            group_properties = Property.query.filter_by(group=property_obj.group, game_id=property_obj.game_id).all()
            bot_owned_in_group = sum(1 for p in group_properties if p.owner_id == bot.id)
            bot_has_group_properties = bot_owned_in_group > 0
        
        # Default percentages of property value the bot is willing to bid
        max_percentage = 1.0  # 100% of property value by default
        
        # Strategy-specific settings
        if strategy == "aggressive":
            # Aggressive bots bid higher
            max_percentage = 1.3  # 130% of property value
            if bot_has_group_properties:
                max_percentage = 1.5  # 150% if they have other properties in the group
                
        elif strategy == "conservative":
            # Conservative bots bid lower
            max_percentage = 0.8  # 80% of property value
            if not bot_has_group_properties:
                max_percentage = 0.6  # 60% if they don't have other properties in the group
                
        elif strategy == "strategic":
            # Strategic bots consider various factors
            max_percentage = 1.0  # Base 100%
            
            # Adjust based on property type
            if property_obj.property_type == "railroad":
                # Check how many railroads the bot already owns
                railroads_owned = Property.query.filter_by(
                    property_type="railroad", 
                    owner_id=bot.id, 
                    game_id=property_obj.game_id
                ).count()
                
                # More valuable if bot already has railroads
                if railroads_owned > 0:
                    max_percentage += 0.2 * railroads_owned  # +20% per railroad owned
                    
            elif property_obj.property_type == "utility":
                # Check if bot already owns a utility
                utilities_owned = Property.query.filter_by(
                    property_type="utility", 
                    owner_id=bot.id, 
                    game_id=property_obj.game_id
                ).count()
                
                # More valuable if bot already has a utility
                if utilities_owned > 0:
                    max_percentage += 0.5  # +50% if already has one utility
            
            # Adjust based on group completion potential
            if bot_has_group_properties:
                group_properties = Property.query.filter_by(
                    group=property_obj.group, 
                    game_id=property_obj.game_id
                ).all()
                
                # Calculate how close to completing the group
                total_in_group = len(group_properties)
                owned_in_group = sum(1 for p in group_properties if p.owner_id == bot.id)
                
                # If this would complete a monopoly, bid higher
                if owned_in_group + 1 >= total_in_group:
                    max_percentage += 0.5  # +50% for completing a monopoly
                else:
                    max_percentage += 0.2  # +20% for adding to an existing group
        
        # Calculate maximum bid based on property value and strategy
        max_bid = property_value * max_percentage
        
        # Ensure bot doesn't bid more than it can afford
        max_bid = min(max_bid, bot.balance)
        
        # If the current bid is already higher than what the bot is willing to pay, pass
        if current_bid >= max_bid:
            return 0  # Pass
            
        # Minimum increment to outbid
        increment = 10
        
        # Calculate bid amount (outbid by the increment)
        bid_amount = min(current_bid + increment, max_bid)
        
        # Round to nearest integer
        bid_amount = round(bid_amount)
        
        logger.debug(f"Bot {bot.id} with strategy '{strategy}' calculated bid of {bid_amount} for property {property_obj.id}")
        return bid_amount

    def start_emergency_auction(self, game_id, player_id, property_id, minimum_bid=None, duration=60):
        """
        Start an emergency auction for a player who needs funds quickly.
        
        This type of auction is used when a player needs immediate cash and chooses
        to auction one of their properties. It uses a shorter duration and
        potentially a higher minimum bid to ensure the player gets a fair value.
        
        Args:
            game_id (str): The ID of the game
            player_id (str): The ID of the player starting the emergency auction
            property_id (str): The ID of the property to auction
            minimum_bid (float, optional): Minimum acceptable bid (defaults to 75% of property value)
            duration (int, optional): Duration of the auction in seconds (defaults to 60)
            
        Returns:
            dict: Result of starting the emergency auction
        """
        logger.info(f"Starting emergency auction for property {property_id} by player {player_id} in game {game_id}")
        
        try:
            # Validate game
            game_state = GameState.query.filter_by(game_id=game_id).first()
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
                
            # Validate player
            player = Player.query.get(player_id)
            if not player:
                logger.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
                
            # Validate that player is active
            if player.status != "active":
                logger.error(f"Player {player_id} is not active")
                return {"success": False, "error": "Player is not active"}
                
            # Validate property exists and belongs to player
            property_obj = Property.query.get(property_id)
            if not property_obj:
                logger.error(f"Property {property_id} not found")
                return {"success": False, "error": "Property not found"}
                
            if property_obj.owner_id != player_id:
                logger.error(f"Property {property_id} does not belong to player {player_id}")
                return {"success": False, "error": "Player does not own this property"}
                
            # Check if property has houses/hotels that need to be sold first
            if hasattr(property_obj, 'houses') and property_obj.houses > 0:
                logger.error(f"Property {property_id} has improvements that must be sold first")
                return {
                    "success": False, 
                    "error": "Property has improvements (houses/hotels) that must be sold before auction",
                    "houses": property_obj.houses
                }
                
            # Check if property is mortgaged
            if hasattr(property_obj, 'is_mortgaged') and property_obj.is_mortgaged:
                logger.error(f"Property {property_id} is mortgaged and cannot be auctioned")
                return {"success": False, "error": "Property is mortgaged and cannot be auctioned"}
                
            # Set default minimum bid if not provided (75% of property value)
            if minimum_bid is None:
                minimum_bid = property_obj.price * 0.75
                
            # Create a new auction with EMERGENCY type
            auction = Auction(
                game_id=game_id,
                property_id=property_id,
                starting_bid=minimum_bid,
                current_bid=0,
                current_winner_id=None,
                status="active",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(seconds=duration),
                auction_type="EMERGENCY",
                original_owner_id=player_id
            )
            
            # Update the property status (mark as in auction)
            property_obj.status = "in_auction"
            
            # Save changes to database
            db.session.add(auction)
            db.session.commit()
            
            # Start the timer
            self._start_auction_timer(auction.id)
            
            # Emit an event to notify clients
            auction_data = {
                "auction_id": auction.id,
                "game_id": game_id,
                "property_id": property_id,
                "property_name": property_obj.name,
                "starting_bid": minimum_bid,
                "duration": duration,
                "end_time": auction.end_time.isoformat(),
                "player_id": player_id,
                "player_name": player.name,
                "auction_type": "EMERGENCY"
            }
            
            self.socketio.emit('emergency_auction_started', auction_data, room=game_id)
            
            # Log the auction in the game log
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse game log for game {game_id}, creating new log")
                    current_log = []
            else:
                current_log = []
                
            log_entry = {
                "type": "emergency_auction_started",
                "property_id": property_id,
                "property_name": property_obj.name,
                "player_id": player_id,
                "player_name": player.name,
                "starting_bid": minimum_bid,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Emergency auction started successfully",
                "auction": auction_data
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting emergency auction: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error starting emergency auction: {str(e)}"}

    def _handle_auction_exception(self, message):
        """Handle and log auction-related exceptions."""
        self.logger.error(f"Auction error: {message}")
        return {"success": False, "message": message}

    def get_auction_analytics(self, game_id, start_date=None, end_date=None):
        """
        Retrieve comprehensive analytics data for auctions based on game_id and optional date filters.
        
        Args:
            game_id (str): The ID of the game to analyze auctions for
            start_date (str, optional): Start date for filtering in format 'YYYY-MM-DD'
            end_date (str, optional): End date for filtering in format 'YYYY-MM-DD'
    
        Returns:
            dict: A dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Description of the result or error
                - data (dict): Analytics data containing:
                    - total_auctions (int): Total number of auctions 
                    - successful_auctions (int): Auctions that resulted in a sale
                    - failed_auctions (int): Auctions that ended without a sale
                    - success_rate (float): Percentage of successful auctions
                    - avg_price_increase (float): Average percentage increase from starting bid
                    - total_auction_value (float): Total money spent in successful auctions
                    - most_active_bidders (list): Top 5 players with most bids
                    - most_valuable_auctions (list): Top 5 highest value auctions
                    - property_type_distribution (dict): Distribution of auctions by property type
                    - avg_duration (float): Average duration of auctions in seconds
                    - bid_frequency (dict): Average bids per auction over time periods
        """
        try:
            from src.models.auction import Auction
            from src.models.property import Property
            from src.models.player import Player
            from src.models.game_state import GameState
            from sqlalchemy import func, and_, desc
            import json
            from datetime import datetime, timedelta
            
            # Validate date format if provided
            date_format = "%Y-%m-%d"
            start_datetime = None
            end_datetime = None
            
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, date_format)
                except ValueError:
                    self.logger.warning(f"Invalid start_date format: {start_date}")
                    return {
                        "success": False,
                        "message": "Invalid start_date format. Expected 'YYYY-MM-DD'."
                    }
            
            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, date_format)
                    # Set to end of day
                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                except ValueError:
                    self.logger.warning(f"Invalid end_date format: {end_date}")
                    return {
                        "success": False,
                        "message": "Invalid end_date format. Expected 'YYYY-MM-DD'."
                    }
            
            # Verify game exists
            game = self.db.session.query(GameState).filter_by(id=game_id).first()
            if not game:
                self.logger.warning(f"Game not found with ID: {game_id}")
                return {
                    "success": False,
                    "message": f"Game not found with ID: {game_id}"
                }
            
            # Build the base query
            query = self.db.session.query(Auction).filter(Auction.game_id == game_id)
            
            # Apply date filters if provided
            if start_datetime:
                query = query.filter(Auction.created_at >= start_datetime)
            
            if end_datetime:
                query = query.filter(Auction.created_at <= end_datetime)
            
            # Get all relevant auctions
            auctions = query.all()
            
            if not auctions:
                return {
                    "success": True,
                    "message": "No auction data found for the specified criteria",
                    "data": {
                        "total_auctions": 0,
                        "successful_auctions": 0,
                        "failed_auctions": 0,
                        "success_rate": 0,
                        "avg_price_increase": 0,
                        "total_auction_value": 0,
                        "most_active_bidders": [],
                        "most_valuable_auctions": [],
                        "property_type_distribution": {},
                        "avg_duration": 0,
                        "bid_frequency": {}
                    }
                }
            
            # Process analytics data
            total_auctions = len(auctions)
            successful_auctions = sum(1 for a in auctions if a.status == 'completed' and a.winner_id is not None)
            failed_auctions = sum(1 for a in auctions if a.status == 'completed' and a.winner_id is None)
            success_rate = (successful_auctions / total_auctions) * 100 if total_auctions > 0 else 0
            
            # Calculate average price increase
            price_increases = []
            total_value = 0
            
            for auction in auctions:
                if auction.status == 'completed' and auction.winner_id is not None and auction.starting_bid > 0 and auction.current_bid > 0:
                    increase = ((auction.current_bid - auction.starting_bid) / auction.starting_bid) * 100
                    price_increases.append(increase)
                    total_value += auction.current_bid
            
            avg_price_increase = sum(price_increases) / len(price_increases) if price_increases else 0
            
            # Most active bidders
            bidder_activity = {}
            for auction in auctions:
                if auction.bid_history:
                    try:
                        bid_history = json.loads(auction.bid_history) if isinstance(auction.bid_history, str) else auction.bid_history
                        for bid in bid_history:
                            bidder_id = bid.get('player_id')
                            if bidder_id:
                                bidder_activity[bidder_id] = bidder_activity.get(bidder_id, 0) + 1
                    except (json.JSONDecodeError, AttributeError):
                        self.logger.warning(f"Could not parse bid history for auction {auction.id}")
            
            most_active_bidders = []
            for bidder_id, bid_count in sorted(bidder_activity.items(), key=lambda x: x[1], reverse=True)[:5]:
                player = self.db.session.query(Player).filter_by(id=bidder_id).first()
                if player:
                    most_active_bidders.append({
                        "player_id": bidder_id,
                        "player_name": player.name,
                        "bid_count": bid_count
                    })
            
            # Most valuable auctions
            most_valuable_auctions = []
            for auction in sorted(auctions, key=lambda x: x.current_bid if x.status == 'completed' and x.winner_id is not None else 0, reverse=True)[:5]:
                if auction.status == 'completed' and auction.winner_id is not None:
                    property_obj = self.db.session.query(Property).filter_by(id=auction.property_id).first()
                    winner = self.db.session.query(Player).filter_by(id=auction.winner_id).first()
                    if property_obj and winner:
                        most_valuable_auctions.append({
                            "auction_id": auction.id,
                            "property_id": auction.property_id,
                            "property_name": property_obj.name,
                            "winner_id": auction.winner_id,
                            "winner_name": winner.name,
                            "final_bid": auction.current_bid,
                            "date": auction.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                        })
            
            # Property type distribution
            property_types = {}
            for auction in auctions:
                property_obj = self.db.session.query(Property).filter_by(id=auction.property_id).first()
                if property_obj:
                    prop_type = property_obj.property_type
                    property_types[prop_type] = property_types.get(prop_type, 0) + 1
            
            # Average auction duration
            durations = []
            for auction in auctions:
                if auction.status == 'completed' and auction.created_at and auction.updated_at:
                    duration = (auction.updated_at - auction.created_at).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Bid frequency
            bid_count_by_auction = {}
            for auction in auctions:
                if auction.bid_history:
                    try:
                        bid_history = json.loads(auction.bid_history) if isinstance(auction.bid_history, str) else auction.bid_history
                        bid_count_by_auction[auction.id] = len(bid_history)
                    except (json.JSONDecodeError, AttributeError):
                        bid_count_by_auction[auction.id] = 0
            
            avg_bids_per_auction = sum(bid_count_by_auction.values()) / len(bid_count_by_auction) if bid_count_by_auction else 0
            
            # Build result
            result = {
                "success": True,
                "message": "Auction analytics retrieved successfully",
                "data": {
                    "total_auctions": total_auctions,
                    "successful_auctions": successful_auctions,
                    "failed_auctions": failed_auctions,
                    "success_rate": round(success_rate, 2),
                    "avg_price_increase": round(avg_price_increase, 2),
                    "total_auction_value": round(total_value, 2),
                    "most_active_bidders": most_active_bidders,
                    "most_valuable_auctions": most_valuable_auctions,
                    "property_type_distribution": property_types,
                    "avg_duration": round(avg_duration, 2),
                    "bid_frequency": {
                        "avg_bids_per_auction": round(avg_bids_per_auction, 2)
                    }
                }
            }
            
            self.logger.info(f"Generated auction analytics for game {game_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating auction analytics: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to generate auction analytics: {str(e)}"
            }

    def get_property_auction_history(self, property_id):
        """
        Retrieve the complete auction history for a specific property.
        
        Args:
            property_id (int): The ID of the property to get auction history for
        
        Returns:
            dict: A dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Description of the result or error
                - property (dict): Basic property information
                - auction_count (int): Number of auctions for this property
                - auctions (list): List of auction data with detailed information
        """
        try:
            from src.models.auction import Auction
            from src.models.property import Property
            from src.models.player import Player
            import json
            
            # Verify property exists
            property_obj = self.db.session.query(Property).filter_by(id=property_id).first()
            if not property_obj:
                self.logger.warning(f"Property not found with ID: {property_id}")
                return {
                    "success": False,
                    "message": f"Property not found with ID: {property_id}"
                }
            
            # Get all auctions for this property
            auctions = self.db.session.query(Auction).filter_by(property_id=property_id).order_by(Auction.created_at.desc()).all()
            
            auction_data = []
            for auction in auctions:
                # Get winner info if available
                winner_name = None
                if auction.winner_id:
                    winner = self.db.session.query(Player).filter_by(id=auction.winner_id).first()
                    if winner:
                        winner_name = winner.name
                
                # Parse bid history
                bid_history = []
                if auction.bid_history:
                    try:
                        bid_data = json.loads(auction.bid_history) if isinstance(auction.bid_history, str) else auction.bid_history
                        for bid in bid_data:
                            bidder_id = bid.get('player_id')
                            bidder_name = None
                            if bidder_id:
                                bidder = self.db.session.query(Player).filter_by(id=bidder_id).first()
                                if bidder:
                                    bidder_name = bidder.name
                            
                            bid_entry = {
                                "player_id": bidder_id,
                                "player_name": bidder_name,
                                "amount": bid.get('amount'),
                                "timestamp": bid.get('timestamp')
                            }
                            bid_history.append(bid_entry)
                    except (json.JSONDecodeError, AttributeError):
                        self.logger.warning(f"Could not parse bid history for auction {auction.id}")
                
                # Build auction entry
                auction_entry = {
                    "auction_id": auction.id,
                    "game_id": auction.game_id,
                    "status": auction.status,
                    "starting_bid": auction.starting_bid,
                    "current_bid": auction.current_bid,
                    "winner_id": auction.winner_id,
                    "winner_name": winner_name,
                    "created_at": auction.created_at.strftime("%Y-%m-%d %H:%M:%S") if auction.created_at else None,
                    "updated_at": auction.updated_at.strftime("%Y-%m-%d %H:%M:%S") if auction.updated_at else None,
                    "bid_history": bid_history
                }
                
                auction_data.append(auction_entry)
            
            # Build result
            result = {
                "success": True,
                "message": "Property auction history retrieved successfully",
                "property": {
                    "id": property_obj.id,
                    "name": property_obj.name,
                    "property_type": property_obj.property_type,
                    "position": property_obj.position,
                    "base_price": property_obj.base_price
                },
                "auction_count": len(auction_data),
                "auctions": auction_data
            }
            
            self.logger.info(f"Retrieved auction history for property {property_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving property auction history: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to retrieve property auction history: {str(e)}"
            }

    def get_auction_schedule(self, game_id):
        """
        Get information about the current auction schedule for a game,
        including sequential auctions in progress.
        
        Args:
            game_id (str): The ID of the game
            
        Returns:
            dict: A dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Description of the result or error
                - schedule (dict): Information about the current auction schedule, including:
                    - sequential_auctions_active (bool): Whether sequential auctions are active
                    - current_auction (dict): Details of the current auction if sequential is active
                    - remaining_properties (list): Properties waiting to be auctioned
                    - completed_auctions (list): Details of completed auctions in this sequence
        """
        try:
            logger.info(f"Getting auction schedule for game {game_id}")
            
            # Get game from database
            game = GameState.query.filter_by(game_id=game_id).first()
            if not game:
                return {
                    "success": False,
                    "message": f"Game with ID {game_id} not found"
                }
            
            # Check if sequential auctions are active
            sequential_active = hasattr(game, 'auction_sequence') and game.auction_sequence is not None
            
            # Initialize response
            response = {
                "success": True,
                "message": "Auction schedule retrieved successfully",
                "schedule": {
                    "sequential_auctions_active": sequential_active,
                    "current_auction": None,
                    "remaining_properties": [],
                    "completed_auctions": []
                }
            }
            
            # If sequential auctions are not active, return early
            if not sequential_active:
                return response
                
            # Parse the auction sequence JSON
            try:
                auction_sequence = json.loads(game.auction_sequence) if isinstance(game.auction_sequence, str) else game.auction_sequence
                
                # Get current property ID
                current_property_id = auction_sequence.get('current_property_id')
                
                # Get remaining property IDs
                remaining_property_ids = auction_sequence.get('remaining_property_ids', [])
                
                # Get completed auction IDs
                completed_auction_ids = auction_sequence.get('completed_auction_ids', [])
                
                # Get current auction details if there is a current property
                if current_property_id:
                    current_auction = Auction.query.filter_by(
                        game_id=game_id,
                        property_id=current_property_id,
                        status='active'
                    ).first()
                    
                    if current_auction:
                        property_obj = Property.query.get(current_property_id)
                        property_name = property_obj.name if property_obj else f"Property {current_property_id}"
                        
                        response["schedule"]["current_auction"] = {
                            "id": current_auction.id,
                            "property_id": current_property_id,
                            "property_name": property_name,
                            "current_bid": current_auction.current_bid,
                            "starting_bid": current_auction.starting_bid,
                            "end_time": current_auction.end_time.isoformat() if current_auction.end_time else None
                        }
                
                # Get remaining property details
                for property_id in remaining_property_ids:
                    property_obj = Property.query.get(property_id)
                    if property_obj:
                        response["schedule"]["remaining_properties"].append({
                            "id": property_id,
                            "name": property_obj.name
                        })
                    else:
                        response["schedule"]["remaining_properties"].append({
                            "id": property_id,
                            "name": f"Property {property_id}"
                        })
                
                # Get completed auction details
                for auction_id in completed_auction_ids:
                    auction = Auction.query.get(auction_id)
                    if auction:
                        property_obj = Property.query.get(auction.property_id)
                        property_name = property_obj.name if property_obj else f"Property {auction.property_id}"
                        
                        winner = None
                        if auction.winner_id:
                            winner_obj = Player.query.get(auction.winner_id)
                            if winner_obj:
                                winner = {
                                    "id": winner_obj.id,
                                    "name": winner_obj.name
                                }
                        
                        response["schedule"]["completed_auctions"].append({
                            "id": auction.id,
                            "property_id": auction.property_id,
                            "property_name": property_name,
                            "final_bid": auction.current_bid,
                            "starting_bid": auction.starting_bid,
                            "winner": winner
                        })
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing auction sequence for game {game_id}: {str(e)}")
                response["schedule"]["sequential_auctions_active"] = False
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting auction schedule: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to retrieve auction schedule: {str(e)}"
            }

    def process_multiple_bot_bids(self, auction_id, bot_ids, strategies=None):
        """
        Process bids from multiple bots for the same auction.
        Useful for testing and simulating auction activity.
        
        Args:
            auction_id (str): The ID of the auction
            bot_ids (list): List of bot player IDs to process bids for
            strategies (dict, optional): Dictionary mapping bot_id to strategy name
                                        (default, aggressive, conservative, opportunistic)
        
        Returns:
            dict: A dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Description of the result or error
                - bids (list): List of bid results for each bot, including:
                    - bot_id (str): The ID of the bot
                    - bid_amount (float): The amount of the bid, or None if passed
                    - success (bool): Whether the bid was successful
                    - message (str): Description of the bid result
        """
        try:
            logger.info(f"Processing multiple bot bids for auction {auction_id}")
            
            if not bot_ids or not isinstance(bot_ids, list) or len(bot_ids) == 0:
                return {
                    "success": False,
                    "message": "No bot IDs provided"
                }
            
            # Initialize strategies if not provided
            if strategies is None:
                strategies = {}
                
            # Initialize results
            results = {
                "success": True,
                "message": "Multiple bot bids processed",
                "bids": []
            }
            
            # Get the auction
            auction = Auction.query.get(auction_id)
            if not auction:
                return {
                    "success": False,
                    "message": f"Auction {auction_id} not found"
                }
                
            # Check if auction is active
            if auction.status != "active":
                return {
                    "success": False,
                    "message": f"Auction {auction_id} is not active"
                }
            
            # Process each bot bid
            for bot_id in bot_ids:
                # Get strategy for this bot
                strategy = strategies.get(bot_id, "default")
                
                # Process the bid
                bid_result = self.process_bot_bid(
                    auction_id=auction_id,
                    bot_id=bot_id,
                    bot_strategy=strategy
                )
                
                # Format the result
                bot_result = {
                    "bot_id": bot_id,
                    "success": bid_result.get("success", False),
                    "message": bid_result.get("message", "Failed to process bot bid"),
                    "bid_amount": bid_result.get("bid_amount", None)
                }
                
                # Add to results
                results["bids"].append(bot_result)
            
            # Check if any bids were successful
            successful_bids = sum(1 for bid in results["bids"] if bid["success"])
            if successful_bids == 0:
                results["message"] = "No successful bids placed"
            else:
                results["message"] = f"{successful_bids} bot bids successfully processed"
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing multiple bot bids: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to process multiple bot bids: {str(e)}"
            }

    def export_auction_data(self, game_id=None, start_date=None, end_date=None, format="csv"):
        """
        Export auction data in CSV format for external analysis.
        
        Args:
            game_id (str, optional): Filter by game ID
            start_date (str, optional): Filter by start date (YYYY-MM-DD)
            end_date (str, optional): Filter by end date (YYYY-MM-DD)
            format (str, optional): Export format, currently only 'csv' is supported
            
        Returns:
            dict: A dictionary containing:
                - success (bool): Whether the operation was successful
                - message (str): Description of the result or error
                - data (str): The CSV data as a string (if format is 'csv')
                - columns (list): List of column names
                - count (int): Number of auctions in the export
        """
        try:
            logger.info(f"Exporting auction data. Game ID: {game_id}, Format: {format}")
            
            # Only CSV format is currently supported
            if format != "csv":
                return {
                    "success": False,
                    "message": f"Unsupported export format: {format}. Currently only 'csv' is supported."
                }
            
            # Build query
            query = Auction.query
            
            # Apply filters
            if game_id:
                query = query.filter_by(game_id=game_id)
                
            # Apply date filters
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                    query = query.filter(Auction.created_at >= start_datetime)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                    
            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                    # Add one day to include the entire end date
                    end_datetime = end_datetime + timedelta(days=1)
                    query = query.filter(Auction.created_at < end_datetime)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
            
            # Execute query
            auctions = query.all()
            
            # If no auctions found
            if not auctions:
                return {
                    "success": True,
                    "message": "No auction data found for the given filters",
                    "data": "",
                    "columns": [],
                    "count": 0
                }
            
            # Define CSV columns
            columns = [
                "auction_id", 
                "game_id", 
                "property_id", 
                "property_name",
                "status", 
                "starting_bid", 
                "current_bid", 
                "winner_id", 
                "current_winner_id",
                "created_at", 
                "updated_at", 
                "duration", 
                "bid_count", 
                "original_owner", 
                "emergency"
            ]
            
            # Generate CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(columns)
            
            # Write data rows
            for auction in auctions:
                # Get property name
                property_obj = Property.query.get(auction.property_id)
                property_name = property_obj.name if property_obj else f"Property {auction.property_id}"
                
                # Parse details JSON
                details = {}
                if auction.details:
                    try:
                        if isinstance(auction.details, str):
                            details = json.loads(auction.details)
                        else:
                            details = auction.details
                    except (json.JSONDecodeError, TypeError):
                        details = {}
                
                # Calculate bid count
                bid_count = 0
                if auction.bid_history:
                    try:
                        if isinstance(auction.bid_history, str):
                            bid_history = json.loads(auction.bid_history)
                        else:
                            bid_history = auction.bid_history
                        bid_count = len(bid_history)
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        bid_count = 0
                
                # Format dates
                created_at = auction.created_at.isoformat() if auction.created_at else ""
                updated_at = auction.updated_at.isoformat() if auction.updated_at else ""
                
                # Write row
                writer.writerow([
                    auction.id,
                    auction.game_id,
                    auction.property_id,
                    property_name,
                    auction.status,
                    auction.starting_bid,
                    auction.current_bid,
                    auction.winner_id,
                    auction.current_winner_id,
                    created_at,
                    updated_at,
                    auction.duration,
                    bid_count,
                    details.get("original_owner", ""),
                    "Yes" if details.get("emergency", False) else "No"
                ])
            
            # Get CSV data as string
            csv_data = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "message": f"Successfully exported {len(auctions)} auctions",
                "data": csv_data,
                "columns": columns,
                "count": len(auctions)
            }
            
        except Exception as e:
            logger.error(f"Error exporting auction data: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to export auction data: {str(e)}"
            }

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

    @socketio.on('get_auction_status')
    def handle_get_auction_status(data):
        """Get detailed status of a specific auction including participants"""
        auction_id = data.get('auction_id')
        logger.debug(f"handle_get_auction_status request received for auction {auction_id}")
        
        if not auction_id:
            emit('auction_error', {'error': 'Missing auction ID'}, room=request.sid)
            return
        
        result = auction_controller.get_auction_status(auction_id)
        
        if result.get('success'):
            emit('auction_status_update', result, room=request.sid)
        else:
            emit('auction_error', {'error': result.get('error', 'Failed to retrieve auction status')}, room=request.sid)

    @socketio.on('admin_cleanup_auctions')
    def handle_admin_cleanup_auctions(data):
        """Admin function to clean up stale auctions"""
        admin_key = data.get('admin_key')
        hours_old = data.get('hours_old', 24)
        sid = request.sid
        
        # Validate admin credentials
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            emit('auction_error', {'error': 'Unauthorized admin action'}, room=sid)
            return
        
        logger.info(f"Admin requested cleanup of auctions older than {hours_old} hours")
        result = auction_controller.cleanup_stale_auctions(hours_old)
        
        # Send the result back to the admin client
        if result.get('success'):
            emit('admin_cleanup_result', result, room=sid)
        else:
            emit('auction_error', {'error': result.get('error', 'Failed to cleanup auctions')}, room=sid)

    @socketio.on('start_sequential_auctions')
    def handle_start_sequential_auctions(data):
        """Admin function to start sequential auctions for multiple properties"""
        admin_key = data.get('admin_key')
        game_id = data.get('game_id')
        property_ids = data.get('property_ids', [])
        starting_bids = data.get('starting_bids', {})
        duration = data.get('duration', 120)
        reason = data.get('reason', 'Administrative sequential auction')
        sid = request.sid
        
        # Validate admin credentials
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            emit('auction_error', {'error': 'Unauthorized admin action'}, room=sid)
            return
            
        # Validate required parameters
        if not game_id:
            emit('auction_error', {'error': 'Missing game ID'}, room=sid)
            return
            
        if not property_ids or not isinstance(property_ids, list) or len(property_ids) == 0:
            emit('auction_error', {'error': 'No properties specified for auction'}, room=sid)
            return
            
        logger.info(f"Admin requested sequential auctions for {len(property_ids)} properties in game {game_id}")
        result = auction_controller.start_sequential_auctions(
            game_id=game_id,
            property_ids=property_ids,
            starting_bids=starting_bids,
            duration=duration,
            reason=reason
        )
        
        # Send the result back to the admin client
        if result.get('success'):
            emit('sequential_auctions_started', result, room=sid)
            
            # Also notify all clients in the game room about the sequential auction
            if game_id:
                auction_controller.socketio.emit('sequential_auctions_announcement', {
                    'game_id': game_id,
                    'property_count': len(property_ids),
                    'reason': reason,
                    'first_auction': result.get('first_auction')
                }, room=game_id)
        else:
            emit('auction_error', {'error': result.get('error', 'Failed to start sequential auctions')}, room=sid)

    @socketio.on('start_emergency_auction')
    def handle_start_emergency_auction(data):
        """Handle a request to start an emergency auction from a player"""
        player_id = data.get('player_id')
        pin = data.get('pin')
        property_id = data.get('property_id')
        minimum_bid = data.get('minimum_bid')
        sid = request.sid
        
        # Validate player credentials
        player = Player.query.get(player_id)
        if not player or player.pin != pin:
            emit('auction_error', {'error': 'Invalid player credentials'}, room=sid)
            return
            
        # Get the property to determine the game ID
        property_obj = Property.query.get(property_id)
        if not property_obj:
            emit('auction_error', {'error': 'Property not found'}, room=sid)
            return
            
        game_id = property_obj.game_id
        
        logger.info(f"Emergency auction request from player {player_id} for property {property_id}")
        
        # Start the emergency auction
        result = auction_controller.start_emergency_auction(
            game_id=game_id,
            player_id=player_id,
            property_id=property_id,
            minimum_bid=minimum_bid
        )
        
        # Send the result back to the player
        if result.get('success'):
            emit('emergency_auction_started_confirmation', result, room=sid)
        else:
            emit('auction_error', {'error': result.get('error', 'Failed to start emergency auction')}, room=sid)

    @socketio.on('get_auction_analytics')
    def handle_get_auction_analytics(data):
        logger.info(f"Socket request for auction analytics: {data}")
        
        # Authentication and validation
        admin_key = data.get('admin_key', None)
        if not admin_key or admin_key != app_config.get('ADMIN_KEY'):
            logger.warning("Unauthorized attempt to access auction analytics")
            return {"success": False, "error": "Unauthorized access"}
            
        game_id = data.get('game_id')
        time_period = data.get('time_period')  # 'day', 'week', 'month', or None for all
        
        if not game_id:
            logger.error("Game ID not provided for auction analytics")
            return {"success": False, "error": "Game ID is required"}
            
        # Get analytics from the controller
        analytics_result = auction_controller.get_auction_analytics(game_id, time_period)
        
        # Send the result directly to the requester
        emit('auction_analytics_result', analytics_result)
        return analytics_result
        
    @socketio.on('get_property_auction_history')
    def handle_get_property_auction_history(data):
        logger.info(f"Socket request for property auction history: {data}")
        
        property_id = data.get('property_id')
        player_id = data.get('player_id')
        pin = data.get('pin')
        
        # Validate player if provided (players can only see history of their own properties)
        if player_id and pin:
            player = Player.query.get(player_id)
            if not player or player.pin != pin:
                logger.warning(f"Invalid player credentials for auction history request: {player_id}")
                return {"success": False, "error": "Invalid player credentials"}
                
            # Get the property
            property_obj = Property.query.get(property_id)
            if not property_obj:
                logger.error(f"Property {property_id} not found")
                return {"success": False, "error": "Property not found"}
                
            # Check if player owns the property (unless they're an admin)
            admin_key = data.get('admin_key', None)
            is_admin = admin_key and admin_key == app_config.get('ADMIN_KEY')
            
            if not is_admin and property_obj.owner_id != player_id:
                logger.warning(f"Player {player_id} does not own property {property_id}")
                return {"success": False, "error": "You can only view auction history for properties you own"}
        
        # Get history from the controller
        history_result = auction_controller.get_property_auction_history(property_id)
        
        # Send the result directly to the requester
        emit('property_auction_history_result', history_result)
        return history_result

    logger.info("AuctionController event handlers registered.")

# No HTTP routes defined here anymore, they belong in a routes file if needed. 

def handle_property_declined(self, game_id, player_id, property_id):
    """
    Handles when a player declines to purchase a property, starting an auction.
    
    Args:
        game_id (str): The ID of the game.
        player_id (str): The ID of the player who declined the property.
        property_id (str): The ID of the property declined.
        
    Returns:
        dict: A dictionary with the results of declining the property.
    """
    logger.info(f"Player {player_id} declined property {property_id} in game {game_id}")
    
    try:
        # Get the game state and validate it exists
        game_state = GameState.query.filter_by(game_id=game_id).first()
        if not game_state:
            logger.error(f"Game {game_id} not found")
            return {"success": False, "error": "Game not found"}
        
        # Get the player and validate they exist
        player = Player.query.get(player_id)
        if not player:
            logger.error(f"Player {player_id} not found")
            return {"success": False, "error": "Player not found"}
        
        # Get the property
        property_obj = Property.query.filter_by(id=property_id, game_id=game_id).first()
        if not property_obj:
            logger.error(f"Property {property_id} not found in game {game_id}")
            return {"success": False, "error": "Property not found"}
        
        # Verify the property is not owned
        if property_obj.owner_id is not None:
            logger.warning(f"Property {property_id} is already owned by player {property_obj.owner_id}")
            return {"success": False, "error": "Property is already owned"}
        
        # Add to game log
        log_entry = {
            "type": "property_declined",
            "player_id": player_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if game_state.game_log:
            try:
                current_log = json.loads(game_state.game_log)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse game log for game {game_id}, creating new log")
                current_log = []
        else:
            current_log = []
            
        current_log.append(log_entry)
        game_state.game_log = json.dumps(current_log)
        
        # Update the game state
        db.session.commit()
        
        # Emit an event to notify clients
        self.socketio.emit('property_declined', {
            'game_id': game_id,
            'player_id': player_id,
            'player_name': player.username,
            'property_id': property_id,
            'property_name': property_obj.name
        }, room=game_id)
        
        # Start the auction using the internal logic
        auction_result = self._start_auction_logic(property_id)
        
        # If the auction started successfully, return success, otherwise return error
        if auction_result.get("success", False):
            return {
                "success": True,
                "action": "property_declined",
                "property_id": property_id,
                "property_name": property_obj.name,
                "auction_started": True,
                "auction_id": auction_result.get("auction_id"),
                "message": f"Property {property_obj.name} declined. Auction started."
            }
        else:
            logger.error(f"Failed to start auction for property {property_id}: {auction_result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to start auction: {auction_result.get('error')}",
                "property_declined": True
            }
        
    except Exception as e:
        logger.error(f"Error handling property decline: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)} 
