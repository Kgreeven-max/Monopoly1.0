# Auction System

## Overview

The Auction System adds dynamic pricing and competitive bidding to Pi-nopoly, enabling properties to be sold to the highest bidder when players decline to purchase them at the listed price or when properties need to be liquidated due to foreclosure.

## Auction Types

The system supports two primary auction types:

1. **Standard Property Auctions**
   - Triggered when a player lands on an unowned property but declines to purchase it at list price
   - Starting minimum bid is typically 50% of list price
   - All players are eligible to participate

2. **Foreclosure Auctions**
   - Triggered when a property with an unpaid loan or mortgage needs to be liquidated
   - Starting minimum bid is the outstanding loan amount plus 10%
   - Excludes the foreclosed player from bidding

## Auction Process

Each auction follows a standardized process:

### 1. Auction Initialization
- Property details are announced to all players
- Minimum bid is set based on auction type
- Eligible players are determined
- Timer is set (typically 30 seconds for initial bidding)

### 2. Bidding Phase
- Players take turns placing bids in real-time
- Each bid must exceed the previous bid by at least a minimum increment
- Players can pass their turn (skip bidding)
- Timer resets to 10 seconds with each new bid
- Players who pass cannot re-enter the auction

### 3. Auction Resolution
- When the timer expires with no new bids, the highest bidder wins
- Property transfers to the winning bidder
- Transaction is recorded in game history
- If no bids are placed, property remains with or returns to the bank

## Core Architecture

```python
class AuctionSystem:
    """Manages property auctions in Pi-nopoly"""
    
    def __init__(self, socketio, banker, community_fund):
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
        self.active_auctions = {}  # auction_id -> auction_data
        self.next_auction_id = 1
    
    def start_auction(self, property_id, auction_type="standard", minimum_bid=None, eligible_players=None):
        """Start a new property auction"""
        # Verify property
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {
                "success": False,
                "error": "Property not found"
            }
        
        # Generate auction ID
        auction_id = str(self.next_auction_id)
        self.next_auction_id += 1
        
        # Set default minimum bid if not provided
        if minimum_bid is None:
            if auction_type == "standard":
                # 50% of list price for standard auctions
                minimum_bid = int(property_obj.current_price * 0.5)
            elif auction_type == "foreclosure":
                # Amount owed on loan + 10% for foreclosure auctions
                minimum_bid = int(property_obj.lien_amount * 1.1)
            else:
                minimum_bid = 10  # Absolute minimum
        
        # Set eligible players if not provided
        if eligible_players is None:
            # All in-game players by default
            eligible_players = [p.id for p in Player.query.filter_by(in_game=True).all()]
        
        # Create auction object
        auction = {
            "id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "auction_type": auction_type,
            "minimum_bid": minimum_bid,
            "eligible_players": eligible_players,
            "current_bid": 0,
            "current_bidder": None,
            "bids": [],
            "players_passed": [],
            "start_time": datetime.now().isoformat(),
            "auction_timer": 30,  # Initial timer in seconds
            "current_timer": 30,
            "status": "active"
        }
        
        # Store auction
        self.active_auctions[auction_id] = auction
        
        # Start auction timer
        self._start_auction_timer(auction_id)
        
        # Broadcast auction start
        self.socketio.emit('auction_started', {
            "auction_id": auction_id,
            "property_id": property_id,
            "property_name": property_obj.name,
            "auction_type": auction_type,
            "minimum_bid": minimum_bid,
            "seconds": auction["auction_timer"]
        })
        
        return {
            "success": True,
            "auction_id": auction_id,
            "auction": auction
        }
    
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
        
        # Broadcast update
        self.socketio.emit('auction_bid', {
            "auction_id": auction_id,
            "property_id": auction["property_id"],
            "property_name": auction["property_name"],
            "player_id": player_id,
            "player_name": player.username,
            "bid_amount": bid_amount,
            "seconds_remaining": auction["current_timer"]
        })
        
        return {
            "success": True,
            "bid": bid
        }
    
    def pass_auction(self, auction_id, player_id):
        """Player passes on bidding in an auction"""
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
                "error": "Player not eligible to pass"
            }
        
        # Add player to passed list
        auction["players_passed"].append(player_id)
        
        # Broadcast update
        player = Player.query.get(player_id)
        self.socketio.emit('auction_pass', {
            "auction_id": auction_id,
            "player_id": player_id,
            "player_name": player.username if player else "Unknown"
        })
        
        # Check if all players have passed
        active_bidders = [p for p in auction["eligible_players"] if p not in auction["players_passed"]]
        
        if len(active_bidders) == 0:
            # No one is bidding, end the auction
            self._end_auction(auction_id)
        elif len(active_bidders) == 1 and auction["current_bidder"] in active_bidders:
            # Only the current winning bidder is left
            self._end_auction(auction_id)
        
        return {
            "success": True
        }
    
    def _end_auction(self, auction_id):
        """End an auction and process the result"""
        if auction_id not in self.active_auctions:
            return
        
        auction = self.active_auctions[auction_id]
        auction["status"] = "completed"
        auction["end_time"] = datetime.now().isoformat()
        
        # Get property
        property_obj = Property.query.get(auction["property_id"])
        if not property_obj:
            # Something went wrong - property doesn't exist
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "error",
                "error": "Property not found"
            })
            del self.active_auctions[auction_id]
            return
        
        # Check if there was a winning bid
        if auction["current_bidder"] is not None:
            # Get winning player
            winner = Player.query.get(auction["current_bidder"])
            if not winner:
                # Winner doesn't exist
                self.socketio.emit('auction_ended', {
                    "auction_id": auction_id,
                    "status": "error",
                    "error": "Winning bidder not found"
                })
                del self.active_auctions[auction_id]
                return
            
            # Check if winner still has enough cash
            if winner.cash < auction["current_bid"]:
                # Winner can't afford it anymore
                self.socketio.emit('auction_ended', {
                    "auction_id": auction_id,
                    "status": "error",
                    "error": "Winning bidder cannot afford the bid",
                    "property_id": property_obj.id,
                    "property_name": property_obj.name
                })
                del self.active_auctions[auction_id]
                return
            
            # Process purchase
            winning_bid = auction["current_bid"]
            list_price = property_obj.current_price
            
            # Calculate overbid amount (for community fund)
            overbid = max(0, winning_bid - list_price)
            community_fund_amount = int(overbid * 0.1)  # 10% of overbid
            
            # Process payment
            winner.cash -= winning_bid
            property_obj.owner_id = winner.id
            db.session.commit()
            
            # Add overbid to community fund if applicable
            if community_fund_amount > 0:
                community_fund = CommunityFund.get_instance()
                community_fund.add(
                    community_fund_amount, 
                    "auction_overbid", 
                    winner.id, 
                    f"10% of overbid for {property_obj.name}"
                )
            
            # Broadcast result
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "sold",
                "property_id": property_obj.id,
                "property_name": property_obj.name,
                "winner_id": winner.id,
                "winner_name": winner.username,
                "winning_bid": winning_bid,
                "list_price": list_price,
                "overbid": overbid,
                "community_fund_amount": community_fund_amount
            })
        else:
            # No winning bid
            self.socketio.emit('auction_ended', {
                "auction_id": auction_id,
                "status": "no_sale",
                "property_id": property_obj.id,
                "property_name": property_obj.name
            })
        
        # Remove auction from active list
        del self.active_auctions[auction_id]
```

## Auction Mechanics

### Minimum Bids
- **Standard Auctions**: 50% of property list price
- **Foreclosure Auctions**: Outstanding loan/mortgage amount plus 10%
- **Custom Auctions**: Configurable during creation

### Bidding Timer
- Initial timer: 30 seconds
- Reset to 10 seconds on each new bid
- When timer expires, highest bidder wins

### Community Fund Contribution
When a property sells at auction above its list price:
- 10% of the overbid amount goes to the Community Fund
- This encourages competitive bidding while supporting game economy balance

## User Interface

The auction interface includes:

### 1. Auction Information Panel
- Property details (name, group, base rent)
- Current high bid and bidder
- Auction timer countdown
- Minimum bid indicator

### 2. Bidding Controls
- Bid amount input (with suggested increments)
- Quick bid buttons (+$10, +$50, etc.)
- "Place Bid" button
- "Pass" button

### 3. Bid History
- List of recent bids with player names and amounts
- Indication of players who have passed
- Time of each bid

## Edge Cases and Special Handling

### 1. No Bids Placed
- Property remains with or returns to the bank
- Property becomes available for purchase at list price on next landing

### 2. Winning Bidder Can't Pay
- If a winning bidder lacks funds when the auction concludes:
  - Auction is invalidated
  - Property remains with or returns to the bank
  - Player receives a penalty for invalid bidding

### 3. All Players Pass
- Auction ends immediately
- Property remains with the bank

### 4. Player Disconnection
- If a player disconnects during an auction:
  - Their status automatically changes to "passed"
  - Auction continues with remaining players

## Bot Player Bidding Strategies

Different AI personalities will have different bidding strategies:

### Conservative Bot
- Will never bid above 90% of list price
- Only bids on properties that complete or enhance existing holdings
- Places minimal initial bids
- Avoids bidding wars

### Aggressive Bot
- Will bid up to 150% of list price for desired properties
- Engages in bidding wars to prevent opponents from getting properties
- Places strong initial bids to discourage competition
- Prioritizes high-value properties

### Strategic Bot
- Analyzes value based on board position and existing holdings
- Bid limit varies based on property's strategic value
- May drive up prices on properties it doesn't want
- Adaptive to player bidding patterns

### Opportunistic Bot
- Focuses on getting properties at discount (below 70% of list price)
- Waits until late in auction to place bids
- Rarely initiates bidding
- Primarily targets distressed properties in foreclosure auctions

## Implementation Timeline

The Auction System implementation will be completed in three phases:

### Phase 1: Core Functionality (Week 1)
- Base auction mechanism
- Bidding and timing system
- Basic UI
- Standard property auctions

### Phase 2: Advanced Features (Week 2)
- Foreclosure auctions
- Community Fund integration
- Enhanced UI with bid history
- Bot bidding strategies

### Phase 3: Optimization and Testing (Week 3)
- Performance optimizations
- Mobile device compatibility
- Comprehensive testing
- Edge case handling 