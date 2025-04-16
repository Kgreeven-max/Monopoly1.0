from datetime import datetime
import threading
import uuid
import logging
from flask_socketio import emit

from . import db
from .property import Property
from .player import Player
from .transaction import Transaction
from .community_fund import CommunityFund

logger = logging.getLogger(__name__)

class AuctionSystem:
    """Manages property auctions in Pi-nopoly"""
    
    def __init__(self, socketio, banker):
        self.socketio = socketio
        self.banker = banker
        self.active_auctions = {}  # auction_id -> auction_data
        self.next_auction_id = 1
        self.logger = logging.getLogger("auction_system")
    
    def start_auction(self, property_id):
        """Start a new auction for a property"""
        # Check if property exists and is available
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if property_obj.owner_id is not None:
            return {
                "success": False,
                "error": "Property already has an owner"
            }
        
        # Generate auction ID
        auction_id = str(self.next_auction_id)
        self.next_auction_id += 1
        
        # Get active players
        players = Player.query.filter_by(in_game=True).all()
        player_ids = [p.id for p in players]
        
        # Create auction object
        minimum_bid = int(property_obj.current_price * 0.7)  # Start at 70% of list price
        auction = {
            "id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "current_bid": minimum_bid - 1,  # So first valid bid is minimum
            "current_bidder": None,
            "eligible_players": player_ids,
            "players_passed": [],
            "bids": [],
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "timer": 30,  # 30 second initial timer
            "current_timer": 30
        }
        
        # Store auction
        self.active_auctions[auction_id] = auction
        
        # Notify all players
        self.socketio.emit('auction_started', {
            "auction_id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "timer": auction["timer"]
        })
        
        # Start auction timer
        self._start_auction_timer(auction_id)
        
        return {
            "success": True,
            "auction_id": auction_id,
            "auction": auction
        }
    
    def start_foreclosure_auction(self, property_id, owner_id, minimum_bid=None):
        """Start a foreclosure auction for a property with delinquent loans"""
        # Check if property exists and owner matches
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        if property_obj.owner_id != owner_id:
            return {
                "success": False,
                "error": "Property owner doesn't match"
            }
        
        # Generate auction ID
        auction_id = str(self.next_auction_id)
        self.next_auction_id += 1
        
        # Get active players (excluding owner)
        players = Player.query.filter_by(in_game=True).all()
        player_ids = [p.id for p in players if p.id != owner_id]
        
        # Set minimum bid (if not provided)
        if minimum_bid is None:
            minimum_bid = int(property_obj.current_price * 0.6)  # 60% of current price
        
        # Create auction object
        auction = {
            "id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "is_foreclosure": True,
            "owner_id": owner_id,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "current_bid": minimum_bid - 1,  # So first valid bid is minimum
            "current_bidder": None,
            "eligible_players": player_ids,
            "players_passed": [],
            "bids": [],
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "timer": 60,  # 60 second timer for foreclosures
            "current_timer": 60
        }
        
        # Store auction
        self.active_auctions[auction_id] = auction
        
        # Notify all players
        self.socketio.emit('foreclosure_auction_started', {
            "auction_id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "owner_id": owner_id,
            "minimum_bid": minimum_bid,
            "start_price": property_obj.current_price,
            "timer": auction["timer"],
            "is_foreclosure": True
        })
        
        # Start auction timer
        self._start_auction_timer(auction_id)
        
        return {
            "success": True,
            "auction_id": auction_id,
            "auction": auction
        }
    
    def _start_auction_timer(self, auction_id):
        """Start a timer for the auction"""
        def auction_tick():
            # Check if auction still exists
            if auction_id not in self.active_auctions:
                return
            
            auction = self.active_auctions[auction_id]
            
            # Decrement timer
            auction["current_timer"] -= 1
            
            # Broadcast timer update
            if auction["current_timer"] % 5 == 0 or auction["current_timer"] <= 10:
                self.socketio.emit('auction_timer', {
                    "auction_id": auction_id,
                    "seconds_remaining": auction["current_timer"]
                })
            
            # Check if timer expired
            if auction["current_timer"] <= 0:
                self._end_auction(auction_id)
            else:
                # Schedule next tick
                threading.Timer(1.0, auction_tick).start()
        
        # Start first tick
        threading.Timer(1.0, auction_tick).start()
    
    def place_bid(self, auction_id, player_id, bid_amount):
        """Place a bid in an auction"""
        # Check if auction exists and is active
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Auction not found"
            }
        
        auction = self.active_auctions[auction_id]
        if auction["status"] != "active":
            return {
                "success": False,
                "error": "Auction is not active"
            }
        
        # Check if player is eligible
        if player_id not in auction["eligible_players"] or player_id in auction["players_passed"]:
            return {
                "success": False,
                "error": "Player not eligible to bid"
            }
        
        # Check if bid is high enough
        if bid_amount <= auction["current_bid"]:
            return {
                "success": False,
                "error": "Bid must be higher than current bid"
            }
        
        if bid_amount < auction["minimum_bid"] and auction["current_bid"] < auction["minimum_bid"]:
            return {
                "success": False,
                "error": f"First bid must be at least {auction['minimum_bid']}"
            }
        
        # Check if player has enough cash
        player = Player.query.get(player_id)
        if not player or player.cash < bid_amount:
            return {
                "success": False,
                "error": "Not enough cash to place bid"
            }
        
        # Update auction
        auction["current_bid"] = bid_amount
        auction["current_bidder"] = player_id
        
        # Record bid
        bid = {
            "player_id": player_id,
            "amount": bid_amount,
            "time": datetime.now().isoformat()
        }
        auction["bids"].append(bid)
        
        # Reset timer to 10 seconds after a new bid
        auction["current_timer"] = 10
        
        # Notify players
        self.socketio.emit('auction_bid_placed', {
            "auction_id": auction_id,
            "player_id": player_id,
            "player_name": player.username, # Fetch username
            "bid_amount": bid_amount
        })
        
        return {"success": True}
    
    def pass_bid(self, auction_id, player_id):
        """Mark a player as passed for an auction"""
        # Check if auction exists and is active
        if auction_id not in self.active_auctions:
            return {
                "success": False,
                "error": "Auction not found"
            }
        
        auction = self.active_auctions[auction_id]
        if auction["status"] != "active":
            return {
                "success": False,
                "error": "Auction is not active"
            }
        
        # Check if player is eligible
        if player_id not in auction["eligible_players"] or player_id in auction["players_passed"]:
            # Might already be passed, that's okay
            return {"success": True, "message": "Player already passed or not eligible"}
        
        # Mark player as passed
        auction["players_passed"].append(player_id)
        
        # Notify players
        self.socketio.emit('auction_player_passed', {
            "auction_id": auction_id,
            "player_id": player_id
        })
        
        # Check if only one bidder remains
        remaining_bidders = [pid for pid in auction["eligible_players"] if pid not in auction["players_passed"]]
        if len(remaining_bidders) <= 1:
            self._end_auction(auction_id)
            
        return {"success": True}
    
    def _end_auction(self, auction_id):
        """End an auction and assign property if winner exists"""
        if auction_id not in self.active_auctions:
            return
            
        auction = self.active_auctions[auction_id]
        if auction["status"] != "active":
            return
            
        auction["status"] = "ended"
        auction["end_time"] = datetime.now().isoformat()
        
        winner_id = auction["current_bidder"]
        winning_bid = auction["current_bid"]
        property_id = auction["property_id"]
        
        if winner_id is not None:
            # Assign property
            property_obj = Property.query.get(property_id)
            player = Player.query.get(winner_id)
            
            if not property_obj or not player:
                # Error case - should not happen ideally
                self.logger.error(f"Error ending auction {auction_id}: Property or winning player not found.")
                self.socketio.emit('auction_error', {
                    "auction_id": auction_id,
                    "error": "Error assigning property after auction."
                })
            else:
                # Process payment
                transaction_result = self.banker.player_pays_bank(winner_id, winning_bid, f"Auction win for {property_obj.name}")
                
                if transaction_result["success"]:
                    # Assign ownership
                    property_obj.owner_id = winner_id
                    db.session.add(property_obj)
                    db.session.commit()
                    
                    # Notify players
                    self.socketio.emit('auction_ended', {
                        "auction_id": auction_id,
                        "property_id": property_id,
                        "winner_id": winner_id,
                        "winner_name": player.username,
                        "winning_bid": winning_bid
                    })
                    
                    self.logger.info(f"Auction {auction_id} ended. Property {property_id} awarded to player {winner_id} for ${winning_bid}.")
                else:
                    # Payment failed - property remains unowned? Goes back to bank?
                    # For simplicity, assume it stays unowned for now
                    self.logger.error(f"Auction {auction_id} winner {winner_id} failed to pay ${winning_bid}. Property {property_id} remains unowned.")
                    self.socketio.emit('auction_error', {
                        "auction_id": auction_id,
                        "error": f"Winner {player.username} failed to pay the winning bid."
                    })
                    self.socketio.emit('auction_ended', {
                        "auction_id": auction_id,
                        "property_id": property_id,
                        "winner_id": None, 
                        "winning_bid": winning_bid,
                        "error": "Payment failed"
                    })
        else:
            # No bidder
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "property_id": property_id,
                "winner_id": None,
                "winning_bid": None,
                "message": "No bids received, property remains unowned."
            })
            self.logger.info(f"Auction {auction_id} for property {property_id} ended with no bids.")
        
        # Clean up auction data
        del self.active_auctions[auction_id]

# Example usage:
# auction_system = AuctionSystem(socketio, banker)
# result = auction_system.start_auction(property_id=5) # Start auction for Reading Railroad
# if result["success"]:
#     auction_id = result["auction_id"]
#     # ... wait for bids ...
#     auction_system.place_bid(auction_id, player_id=1, bid_amount=150)
