from . import db
from datetime import datetime
import logging

class Player(db.Model):
    """Player model representing users in the game"""
    __tablename__ = 'players' # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pin = db.Column(db.String(120), nullable=False) # Consider hashing this!
    is_admin = db.Column(db.Boolean, default=False)
    is_bot = db.Column(db.Boolean, default=False)
    in_game = db.Column(db.Boolean, default=True)
    money = db.Column(db.Integer, default=1500)
    position = db.Column(db.Integer, default=0)
    turn_order = db.Column(db.Integer, nullable=True)
    in_jail = db.Column(db.Boolean, default=False)
    jail_turns = db.Column(db.Integer, default=0)
    get_out_of_jail_cards = db.Column(db.Integer, default=0)
    consecutive_doubles_count = db.Column(db.Integer, default=0) # Added for tracking doubles
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    community_standing = db.Column(db.Integer, default=50)  # 0-100 scale, 50 is neutral
    criminal_record = db.Column(db.Integer, default=0)  # Number of detected crimes
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    credit_score = db.Column(db.Integer, default=700)  # Credit score range: 300-850
    times_passed_go = db.Column(db.Integer, default=0)  # Track number of times passed GO
    
    # Foreign Key to link Player to a Game
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    # Relationship back to the Game (many players belong to one game)
    game = db.relationship('Game', back_populates='players')
    
    # Add ForeignKey to link to Team model
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    
    # Relationships
    properties = db.relationship(
        'Property',
        primaryjoin='Player.id == Property.owner_id',
        back_populates='owner'
    )
    crimes = db.relationship('Crime', foreign_keys='Crime.player_id', back_populates='player')
    # The 'team' backref is automatically created by the relationship in Team model
    
    def __repr__(self):
        return f'<Player {self.username} (ID: {self.id})>'
    
    def pay(self, amount):
        """Deduct money from player"""
        if amount <= 0:
            return False
        
        if self.money < amount:
            return False
        
        self.money -= amount
        return True
    
    def receive(self, amount):
        """Add money to player"""
        if amount <= 0:
            return False
        
        self.money += amount
        return True
    
    def move_to(self, position):
        """Move player to a specific position"""
        old_position = self.position
        self.position = position
        
        # Check if passed GO (moved to a lower position number)
        if position < old_position:
            self.times_passed_go += 1  # Increment times_passed_go counter
            passed_go = True
        else:
            passed_go = False
            
        return {
            'old_position': old_position,
            'new_position': position,
            'passed_go': passed_go
        }
    
    def move(self, spaces):
        """Move player forward by a number of spaces"""
        board_size = 40  # Standard monopoly board size
        old_position = self.position
        self.position = (self.position + spaces) % board_size
        
        # Check if passed GO
        if (old_position + spaces) >= board_size:
            self.times_passed_go += 1  # Increment times_passed_go counter
            passed_go = True
        else:
            passed_go = False
        
        return {
            'old_position': old_position,
            'new_position': self.position,
            'spaces_moved': spaces,
            'passed_go': passed_go
        }
    
    def go_to_jail(self):
        """Send player to jail"""
        jail_position = 10  # Standard jail position
        self.position = jail_position
        self.in_jail = True
        self.jail_turns = 0
        return True
    
    def get_out_of_jail(self):
        """Get player out of jail"""
        if not self.in_jail:
            return False
        
        self.in_jail = False
        self.jail_turns = 0
        return True
    
    def use_jail_card(self):
        """Use a get out of jail free card"""
        if not self.in_jail or self.get_out_of_jail_cards <= 0:
            return False
        
        self.get_out_of_jail_cards -= 1
        return self.get_out_of_jail()
    
    def to_dict(self, include_properties=False):
        """Convert player to dictionary for JSON serialization"""
        player_dict = {
            'id': self.id,
            'username': self.username,
            'is_bot': self.is_bot,
            'in_game': self.in_game,
            'money': self.money,
            'position': self.position,
            'turn_order': self.turn_order,
            'in_jail': self.in_jail,
            'jail_turns': self.jail_turns,
            'get_out_of_jail_cards': self.get_out_of_jail_cards,
            'community_standing': self.community_standing,
            'criminal_record': self.criminal_record,
            'game_id': self.game_id,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'credit_score': self.credit_score,
            'times_passed_go': self.times_passed_go,
        }
        if include_properties:
            player_dict['properties'] = [prop.to_dict() for prop in self.properties]
        return player_dict
    
    def calculate_net_worth(self):
        """Calculate player's total net worth including properties"""
        net_worth = self.money
        
        # Add property values
        for property in self.properties:
            net_worth += property.current_price
        
        # Subtract active loans
        for loan in self.loans:
            if loan.is_active and not loan.is_cd:
                net_worth -= loan.amount
            elif loan.is_active and loan.is_cd:
                net_worth += loan.amount
        
        return net_worth
        
    def send_notification(self, message, socketio=None):
        """Send a notification to the player"""
        if not socketio:
            # If no socketio instance provided, log the message for debugging
            logger = logging.getLogger("player")
            logger.info(f"Notification for {self.username}: {message}")
            return
            
        # Create notification data
        notification_data = {
            'player_id': self.id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to specific player if socket_id is available
        if hasattr(self, 'socket_id') and self.socket_id:
            socketio.emit('player_notification', notification_data, room=self.socket_id)
        else:
            # Fallback to game-wide broadcast with player filtering
            socketio.emit('player_notification', notification_data)
            
    @property
    def is_active(self):
        """Check if the player is active in the game"""
        return self.in_game and not self.is_bankrupt
            
    @property
    def is_bankrupt(self):
        """Check if the player is bankrupt"""
        # A player is bankrupt if they have negative net worth and no properties
        if self.money < 0 and len(self.properties) == 0:
            return True
            
        # Or if they have been explicitly marked as bankrupt
        return not self.in_game and self.money <= 0
        
    def commit_crime(self, crime_type, **kwargs):
        """Commit a crime of the specified type
        
        Args:
            crime_type: Type of crime to commit (theft, property_vandalism, etc.)
            **kwargs: Additional parameters for the specific crime type
            
        Returns:
            Crime: The crime instance
        """
        from .crime import Crime, Theft, PropertyVandalism, RentEvasion, Forgery, TaxEvasion
        
        # Map crime type to class
        crime_classes = {
            'theft': Theft,
            'property_vandalism': PropertyVandalism,
            'rent_evasion': RentEvasion,
            'forgery': Forgery,
            'tax_evasion': TaxEvasion
        }
        
        # Get the appropriate crime class
        crime_class = crime_classes.get(crime_type)
        if not crime_class:
            raise ValueError(f"Unknown crime type: {crime_type}")
            
        # Create crime instance
        crime = crime_class(player_id=self.id, **kwargs)
        db.session.add(crime)
        db.session.commit()
        
        # Execute the crime
        result = crime.execute()
        
        # Update criminal record if detected
        if crime.detected:
            self.criminal_record += 1
            self.community_standing = max(0, self.community_standing - 5)
            db.session.add(self)
            db.session.commit()
            
            # Apply consequences
            crime.apply_consequences()
        
        return crime
    
    def update_credit_score(self, action_type, amount=None, success=True):
        """Update credit score based on financial activities
        
        Args:
            action_type: Type of financial action (loan_payment, cd_creation, bankruptcy, etc.)
            amount: Amount of transaction (if applicable)
            success: Whether the action was successful
            
        Returns:
            New credit score
        """
        # Save original credit score to check for changes
        original_score = self.credit_score
        
        # Credit score adjustment factors
        adjustments = {
            'loan_payment': 5,      # Regular loan payment (positive)
            'loan_payment_late': -15,  # Late loan payment (negative)
            'loan_default': -75,    # Loan default (very negative)
            'cd_creation': 3,       # Creating a CD (slightly positive)
            'heloc_creation': 2,    # Creating a HELOC (slightly positive)
            'bankruptcy': -150,     # Declaring bankruptcy (severely negative)
            'mortgage_payment': 5,  # Regular mortgage payment (positive)
            'property_purchase': 2, # Purchasing property (slightly positive)
            'sell_property': 0,     # Neutral action
        }
        
        # Base adjustment
        adjustment = adjustments.get(action_type, 0)
        
        # Adjust based on success/failure
        if not success:
            adjustment = -abs(adjustment) * 2  # Double negative impact for failures
            
        # Adjust based on amount (for large transactions)
        if amount and amount > 1000:
            # Larger amounts have slightly more impact (max 20% increase)
            scale_factor = min(1.2, 1 + (amount - 1000) / 10000)
            adjustment = int(adjustment * scale_factor)
            
        # Apply adjustment with bounds checking
        self.credit_score += adjustment
        self.credit_score = max(300, min(850, self.credit_score))  # Enforce 300-850 range
        
        # Emit a socket event if the score changed
        if self.credit_score != original_score:
            try:
                from flask import current_app
                socketio = current_app.config.get('socketio')
                if socketio:
                    socketio.emit('credit_score_updated', {
                        'player_id': self.id,
                        'player_name': self.username,
                        'old_score': original_score,
                        'new_score': self.credit_score,
                        'change': self.credit_score - original_score,
                        'action_type': action_type,
                        'rating': self.get_credit_rating()
                    })
            except Exception as e:
                # Log error but don't fail the method
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error emitting credit_score_updated event: {str(e)}")
        
        return self.credit_score
        
    def get_credit_rating(self):
        """Get credit rating category based on credit score
        
        Returns:
            String representing credit rating (poor, fair, good, excellent)
        """
        if self.credit_score < 550:
            return "poor"
        elif self.credit_score < 650:
            return "fair"
        elif self.credit_score < 750:
            return "good"
        else:
            return "excellent" 