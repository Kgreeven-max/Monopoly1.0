# Social Features System

## Overview

The Social Features System enhances Pi-nopoly with robust player interaction mechanics, communication tools, and reputation systems. These features transform the game from a purely economic simulation into a social experience that rewards diplomacy, cooperation, and strategic alliances while adding depth to player interactions.

## In-Game Chat System

The enhanced chat system facilitates player communication:

### Chat Features

1. **Channel Structure**
   - Global chat for all players
   - Private messaging between specific players
   - Group chats for alliances
   - Contextual channels (e.g., trade negotiations)

2. **Rich Communication**
   - Text messaging with emoji support
   - Reaction system for quick responses
   - Voice chat integration for mobile/desktop
   - Image sharing for screenshots

3. **Notification System**
   - Customizable alert preferences
   - Mention system (@username)
   - Urgent message highlighting
   - Message history and search

```python
class EnhancedChatSystem:
    """Manages enhanced chat functionality"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.channels = {
            "global": {
                "name": "Global",
                "description": "Chat with all players",
                "members": [],  # All players are implicit members
                "messages": [],
                "type": "public"
            }
        }
        self.private_channels = {}  # user_id -> {channel_id -> channel}
        self.message_history = {}   # channel_id -> list of messages
        self.message_count = 0
        self.max_history_per_channel = 200
    
    def create_channel(self, creator_id, name, description, members=None, channel_type="group"):
        """Create a new chat channel"""
        channel_id = f"channel_{uuid.uuid4()}"
        
        if members is None:
            members = [creator_id]
        elif creator_id not in members:
            members.append(creator_id)
        
        # Create channel
        channel = {
            "id": channel_id,
            "name": name,
            "description": description,
            "members": members,
            "created_at": datetime.now().isoformat(),
            "created_by": creator_id,
            "messages": [],
            "type": channel_type
        }
        
        # Store channel
        if channel_type == "public":
            self.channels[channel_id] = channel
        elif channel_type == "private":
            # For private channels, store in each member's private channels
            for member_id in members:
                if member_id not in self.private_channels:
                    self.private_channels[member_id] = {}
                
                self.private_channels[member_id][channel_id] = channel
        
        # Initialize message history
        self.message_history[channel_id] = []
        
        # Notify members
        for member_id in members:
            self.socketio.emit('channel_created', {
                "channel_id": channel_id,
                "name": name,
                "description": description,
                "members": members,
                "type": channel_type
            }, room=f"player_{member_id}")
        
        return {
            "success": True,
            "channel_id": channel_id,
            "channel": channel
        }
    
    def send_message(self, user_id, channel_id, message_text, message_type="text", attachments=None):
        """Send a message to a channel"""
        # Validate user and channel
        user = Player.query.get(user_id)
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Get channel
        channel = self._get_channel(channel_id, user_id)
        if not channel:
            return {
                "success": False,
                "error": "Channel not found or access denied"
            }
        
        # Check if user is member of channel
        if user_id not in channel["members"] and channel["type"] != "public":
            return {
                "success": False,
                "error": "User is not a member of this channel"
            }
        
        # Process message text (filter, check length, etc.)
        if not message_text or len(message_text) > 1000:
            return {
                "success": False,
                "error": "Invalid message length"
            }
        
        # Create message object
        message_id = f"msg_{self.message_count}"
        self.message_count += 1
        
        message = {
            "id": message_id,
            "channel_id": channel_id,
            "user_id": user_id,
            "username": user.username,
            "text": message_text,
            "type": message_type,
            "attachments": attachments or [],
            "timestamp": datetime.now().isoformat(),
            "edited": False,
            "reactions": {}
        }
        
        # Add to channel and history
        if channel_id in self.message_history:
            self.message_history[channel_id].append(message)
            
            # Trim history if needed
            if len(self.message_history[channel_id]) > self.max_history_per_channel:
                self.message_history[channel_id] = self.message_history[channel_id][-self.max_history_per_channel:]
        
        # Broadcast to all members
        for member_id in channel["members"]:
            self.socketio.emit('chat_message', message, room=f"player_{member_id}")
        
        # For public channels, broadcast to all connected players
        if channel["type"] == "public":
            self.socketio.emit('chat_message', message)
        
        return {
            "success": True,
            "message_id": message_id,
            "message": message
        }
    
    def add_reaction(self, user_id, message_id, channel_id, emoji):
        """Add a reaction to a message"""
        # Implementation details...
    
    def _get_channel(self, channel_id, user_id):
        """Get a channel by ID, checking appropriate storage locations"""
        # Check public channels
        if channel_id in self.channels:
            return self.channels[channel_id]
        
        # Check user's private channels
        if user_id in self.private_channels and channel_id in self.private_channels[user_id]:
            return self.private_channels[user_id][channel_id]
        
        return None
```

## Player Interaction System

The system adds depth to player relationships:

### Interaction Features

1. **Alliances**
   - Formal partnerships between players
   - Shared benefits (rent discounts, development cooperation)
   - Alliance-specific chat channels and notifications
   - Public or private alliance options

2. **Reputation System**
   - Trust scores based on fulfilled agreements
   - Fair trading metrics
   - Bankruptcy history tracking
   - Public reputation profiles

3. **Negotiation Framework**
   - Structured negotiation for complex deals
   - Binding and non-binding agreements
   - Conditional offers with triggers
   - Public vs. private negotiations

```python
class AllianceSystem:
    """Manages player alliances and partnerships"""
    
    def __init__(self, socketio, chat_system):
        self.socketio = socketio
        self.chat_system = chat_system
        self.alliances = {}  # alliance_id -> alliance_data
        self.alliance_count = 0
    
    def create_alliance(self, creator_id, name, description, is_public=True):
        """Create a new player alliance"""
        creator = Player.query.get(creator_id)
        if not creator:
            return {
                "success": False,
                "error": "Creator not found"
            }
        
        # Generate alliance ID
        alliance_id = f"alliance_{self.alliance_count}"
        self.alliance_count += 1
        
        # Create alliance object
        alliance = {
            "id": alliance_id,
            "name": name,
            "description": description,
            "creator_id": creator_id,
            "is_public": is_public,
            "members": [creator_id],
            "pending_invites": [],
            "created_at": datetime.now().isoformat(),
            "benefits": {
                "rent_discount": 0.1,  # 10% rent discount between members
                "development_discount": 0.0  # No development discount initially
            },
            "status": "active"
        }
        
        # Store alliance
        self.alliances[alliance_id] = alliance
        
        # Create alliance chat channel
        chat_result = self.chat_system.create_channel(
            creator_id=creator_id,
            name=f"Alliance: {name}",
            description=f"Chat channel for alliance {name}",
            members=[creator_id],
            channel_type="group"
        )
        
        alliance["chat_channel_id"] = chat_result["channel_id"]
        
        # Notify creator
        self.socketio.emit('alliance_created', {
            "alliance_id": alliance_id,
            "alliance": alliance
        }, room=f"player_{creator_id}")
        
        # Notify all players if public
        if is_public:
            self.socketio.emit('public_alliance_created', {
                "alliance_id": alliance_id,
                "name": name,
                "description": description,
                "creator_id": creator_id,
                "creator_name": creator.username
            })
        
        return {
            "success": True,
            "alliance_id": alliance_id,
            "alliance": alliance
        }
    
    def invite_to_alliance(self, alliance_id, inviter_id, invitee_id):
        """Invite a player to join an alliance"""
        # Implementation details...
    
    def accept_alliance_invite(self, alliance_id, player_id):
        """Accept an invitation to join an alliance"""
        # Implementation details...
    
    def calculate_alliance_benefits(self, player1_id, player2_id):
        """Calculate benefits between two players based on alliances"""
        # Find shared alliances
        shared_alliances = []
        
        for alliance_id, alliance in self.alliances.items():
            if player1_id in alliance["members"] and player2_id in alliance["members"]:
                shared_alliances.append(alliance)
        
        if not shared_alliances:
            return {
                "rent_discount": 0.0,
                "development_discount": 0.0,
                "has_alliance": False
            }
        
        # Use the most beneficial alliance if multiple exist
        best_alliance = max(shared_alliances, 
                           key=lambda a: a["benefits"]["rent_discount"] + a["benefits"]["development_discount"])
        
        return {
            "rent_discount": best_alliance["benefits"]["rent_discount"],
            "development_discount": best_alliance["benefits"]["development_discount"],
            "has_alliance": True,
            "alliance_id": best_alliance["id"],
            "alliance_name": best_alliance["name"]
        }
```

## Reputation and Trust System

The reputation system adds consequences to player actions:

### Reputation Features

1. **Trust Score Components**
   - Transaction history (fulfilled vs. defaulted)
   - Trading fairness (balanced vs. exploitative)
   - Alliance loyalty (remained vs. abandoned)
   - Community contributions

2. **Impact of Reputation**
   - Interest rate adjustments based on credit score
   - Trading approval chances
   - Alliance invitation eligibility
   - Community Fund access

```python
class ReputationSystem:
    """Manages player reputation and trust scores"""
    
    def __init__(self):
        self.reputation_scores = {}  # player_id -> reputation_data
        self.transaction_history = {}  # player_id -> list of transactions
        self.reputation_events = {}  # player_id -> list of reputation events
    
    def initialize_player_reputation(self, player_id):
        """Initialize reputation for a new player"""
        self.reputation_scores[player_id] = {
            "overall_score": 50,  # 0-100 scale, 50 is neutral
            "components": {
                "transaction_trust": 50,
                "trading_fairness": 50,
                "alliance_loyalty": 50,
                "community_standing": 50
            },
            "last_updated": datetime.now().isoformat()
        }
        
        self.transaction_history[player_id] = []
        self.reputation_events[player_id] = []
        
        return self.reputation_scores[player_id]
    
    def record_transaction_result(self, player_id, transaction_type, success, details=None):
        """Record the result of a financial transaction"""
        if player_id not in self.reputation_scores:
            self.initialize_player_reputation(player_id)
        
        # Create transaction record
        transaction = {
            "type": transaction_type,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        # Add to history
        self.transaction_history[player_id].append(transaction)
        
        # Update transaction trust score
        self._update_transaction_trust(player_id, success)
        
        # Update overall score
        self._recalculate_overall_score(player_id)
        
        return self.reputation_scores[player_id]
    
    def record_trading_event(self, player_id, trade_fairness, trade_details=None):
        """Record a trading event with fairness rating"""
        # Implementation details...
    
    def record_alliance_event(self, player_id, event_type, alliance_id, details=None):
        """Record an alliance-related event"""
        # Implementation details...
    
    def record_community_event(self, player_id, event_type, impact, details=None):
        """Record a community-impacting event"""
        # Implementation details...
    
    def get_credit_score(self, player_id):
        """Get credit score for loan interest calculations"""
        if player_id not in self.reputation_scores:
            return 50  # Default neutral score
        
        # Credit score is weighted toward transaction trust and community standing
        reputation = self.reputation_scores[player_id]
        
        credit_score = (
            reputation["components"]["transaction_trust"] * 0.6 +
            reputation["components"]["community_standing"] * 0.2 +
            reputation["components"]["alliance_loyalty"] * 0.1 +
            reputation["components"]["trading_fairness"] * 0.1
        )
        
        return max(10, min(100, credit_score))
    
    def calculate_interest_rate_adjustment(self, player_id):
        """Calculate interest rate adjustment based on credit score"""
        credit_score = self.get_credit_score(player_id)
        
        # Convert 0-100 score to interest rate adjustment of +5% to -3%
        # Higher score means lower interest rate
        adjustment = 0.05 - (credit_score / 100 * 0.08)
        
        return max(-0.03, min(0.05, adjustment))
    
    def _update_transaction_trust(self, player_id, success):
        """Update transaction trust component based on success/failure"""
        current_score = self.reputation_scores[player_id]["components"]["transaction_trust"]
        
        if success:
            # Successful transaction improves score
            new_score = current_score + (100 - current_score) * 0.1
        else:
            # Failed transaction reduces score significantly
            new_score = current_score * 0.8
        
        self.reputation_scores[player_id]["components"]["transaction_trust"] = max(0, min(100, new_score))
    
    def _recalculate_overall_score(self, player_id):
        """Recalculate overall reputation score from components"""
        components = self.reputation_scores[player_id]["components"]
        
        # Equal weighting of all components
        overall_score = (
            components["transaction_trust"] +
            components["trading_fairness"] +
            components["alliance_loyalty"] +
            components["community_standing"]
        ) / 4
        
        self.reputation_scores[player_id]["overall_score"] = overall_score
        self.reputation_scores[player_id]["last_updated"] = datetime.now().isoformat()
```

## Community Governance System

The community governance system empowers players to shape the game world:

### Governance Features

1. **Voting System**
   - Democratic process for key decisions
   - Weighted voting based on property holdings
   - Proposal creation and voting interface
   - Referendum and initiative options

2. **Community Projects**
   - Collaborative funding for improvements
   - Infrastructure development with shared benefits
   - Project management and completion tracking
   - Individual contribution recognition

3. **Laws and Regulations**
   - Player-enacted game rules
   - Tax policy adjustments
   - Zoning regulation changes
   - Enforcement mechanisms

```python
class CommunityGovernance:
    """Manages community voting, projects, and regulations"""
    
    def __init__(self, socketio, community_fund):
        self.socketio = socketio
        self.community_fund = community_fund
        self.proposals = {}  # proposal_id -> proposal_data
        self.votes = {}  # proposal_id -> {player_id -> vote}
        self.projects = {}  # project_id -> project_data
        self.laws = {}  # law_id -> law_data
        self.next_ids = {
            "proposal": 1,
            "project": 1,
            "law": 1
        }
    
    def create_proposal(self, creator_id, title, description, proposal_type, options, voting_ends_in_turns):
        """Create a new community proposal"""
        creator = Player.query.get(creator_id)
        if not creator:
            return {
                "success": False,
                "error": "Creator not found"
            }
        
        # Generate ID
        proposal_id = f"prop_{self.next_ids['proposal']}"
        self.next_ids["proposal"] += 1
        
        # Get game state for turn tracking
        game_state = GameState.query.first()
        current_turn = game_state.current_turn
        
        # Create proposal
        proposal = {
            "id": proposal_id,
            "title": title,
            "description": description,
            "creator_id": creator_id,
            "creator_name": creator.username,
            "type": proposal_type,
            "options": options,
            "created_turn": current_turn,
            "voting_ends_turn": current_turn + voting_ends_in_turns,
            "status": "active",
            "result": None
        }
        
        # Store proposal
        self.proposals[proposal_id] = proposal
        self.votes[proposal_id] = {}
        
        # Notify all players
        self.socketio.emit('proposal_created', {
            "proposal_id": proposal_id,
            "title": title,
            "creator_name": creator.username,
            "type": proposal_type,
            "voting_ends_turn": proposal["voting_ends_turn"]
        })
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "proposal": proposal
        }
    
    def cast_vote(self, player_id, proposal_id, selected_option):
        """Cast a vote on a proposal"""
        player = Player.query.get(player_id)
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check if proposal exists and is active
        if proposal_id not in self.proposals:
            return {
                "success": False,
                "error": "Proposal not found"
            }
        
        proposal = self.proposals[proposal_id]
        if proposal["status"] != "active":
            return {
                "success": False,
                "error": f"Proposal is not active (status: {proposal['status']})"
            }
        
        # Check if option is valid
        if selected_option not in proposal["options"]:
            return {
                "success": False,
                "error": "Invalid option"
            }
        
        # Calculate vote weight based on property holdings
        vote_weight = self._calculate_vote_weight(player_id)
        
        # Record vote
        self.votes[proposal_id][player_id] = {
            "option": selected_option,
            "weight": vote_weight,
            "timestamp": datetime.now().isoformat()
        }
        
        # Notify voters
        self.socketio.emit('vote_cast', {
            "proposal_id": proposal_id,
            "player_id": player_id,
            "player_name": player.username,
            "option": selected_option,
            "weight": vote_weight
        })
        
        return {
            "success": True,
            "vote_weight": vote_weight
        }
    
    def check_proposal_status(self, proposal_id):
        """Check if a proposal's voting period has ended and process results"""
        # Implementation details...
    
    def _calculate_vote_weight(self, player_id):
        """Calculate a player's voting weight based on property holdings"""
        player = Player.query.get(player_id)
        if not player:
            return 1.0  # Default weight
        
        # Base weight is 1.0
        weight = 1.0
        
        # Add weight for owned properties
        properties = Property.query.filter_by(owner_id=player_id).all()
        property_value = sum(p.current_price for p in properties)
        
        # 0.1 additional weight per $500 of property value, max 3.0 from properties
        property_weight = min(3.0, property_value / 5000)
        weight += property_weight
        
        # Reputation bonus (up to 0.5)
        reputation_system = ReputationSystem()
        reputation_score = reputation_system.get_credit_score(player_id)
        reputation_bonus = (reputation_score - 50) / 100  # -0.5 to +0.5
        weight += max(0, reputation_bonus)  # Only positive reputation adds weight
        
        return weight
```

## Social UI Enhancements

The social UI provides intuitive access to social features:

### UI Components

1. **Chat Interface**
   - Channel/conversation navigation
   - Message composition with formatting
   - Emoji selector and GIF support
   - Notification badges

2. **Reputation Dashboard**
   - Visual reputation score display
   - History of reputation-affecting events
   - Comparative ranking among players
   - Improvement recommendations

3. **Alliance Management**
   - Alliance creation wizard
   - Member management interface
   - Benefit configuration controls
   - Alliance activity feed

4. **Community Governance Portal**
   - Proposal creation forms
   - Voting interface with visual results
   - Law and regulation reference
   - Project contribution tracking

## Implementation Timeline

The Social Features System will be implemented in three phases:

### Phase 1: Chat and Communication
- Enhanced chat system with channels
- Emoji reactions and rich messaging
- Chat notification system
- User preferences

### Phase 2: Reputation and Alliances
- Core reputation tracking
- Alliance creation and management
- Benefit calculations for allied players
- Social impact on gameplay mechanics

### Phase 3: Community Governance
- Proposal and voting system
- Community project creation
- Law enactment mechanics
- Governance UI 