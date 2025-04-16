from . import db
from datetime import datetime
import random
import logging
from .player import Player
from .game_state import GameState
from .property import Property
from .transaction import Transaction

logger = logging.getLogger(__name__)

class Crime(db.Model):
    """Base model for criminal activities in the game"""
    __tablename__ = 'crimes'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    crime_type = db.Column(db.String(50), nullable=False)
    target_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    target_property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, default=False)
    detected = db.Column(db.Boolean, default=False)
    punishment_served = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)
    
    # Relationships
    player = db.relationship('Player', foreign_keys=[player_id], back_populates='crimes')
    target_player = db.relationship('Player', foreign_keys=[target_player_id])
    target_property = db.relationship('Property', foreign_keys=[target_property_id])
    
    __mapper_args__ = {
        'polymorphic_on': crime_type,
        'polymorphic_identity': 'crime'
    }
    
    def __repr__(self):
        return f'<Crime {self.crime_type} by Player {self.player_id}>'
    
    def execute(self):
        """Execute the crime (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def detect(self, game_state=None):
        """Check if the crime is detected"""
        if not game_state:
            game_state = GameState.query.get(1)
            
        # Base detection rates based on difficulty
        base_detection_rates = {
            'easy': 0.6,  # 60% chance of being caught
            'normal': 0.5,  # 50% chance
            'hard': 0.4   # 40% chance
        }
        
        # Get base detection rate
        detection_rate = base_detection_rates.get(game_state.difficulty, 0.5)
        
        # Adjust based on player's community standing
        # Lower standing = higher chance of detection
        community_standing = self.player.community_standing
        standing_factor = 1.0 + ((50 - community_standing) / 100)  # 0.5 to 1.5 range
        detection_rate *= standing_factor
        
        # Cap detection rate between 0.1 and 0.9
        detection_rate = min(0.9, max(0.1, detection_rate))
        
        # Roll for detection
        self.detected = random.random() < detection_rate
        db.session.add(self)
        db.session.commit()
        
        return self.detected
    
    def apply_consequences(self):
        """Apply consequences if crime is detected"""
        if not self.detected:
            return False
            
        # Update player's community standing
        self.player.community_standing = max(0, self.player.community_standing - 10)
        
        # Base implementation - go to jail
        self.player.go_to_jail()
        self.punishment_served = True
        db.session.add(self.player)
        db.session.add(self)
        db.session.commit()
        
        return True
    
    def to_dict(self):
        """Convert crime to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': self.player.username if self.player else None,
            'crime_type': self.crime_type,
            'target_player_id': self.target_player_id,
            'target_player_name': self.target_player.username if self.target_player else None,
            'target_property_id': self.target_property_id,
            'target_property_name': self.target_property.name if self.target_property else None,
            'amount': self.amount,
            'success': self.success,
            'detected': self.detected,
            'punishment_served': self.punishment_served,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


class Theft(Crime):
    """Crime involving stealing money from another player"""
    __mapper_args__ = {
        'polymorphic_identity': 'theft'
    }
    
    def execute(self):
        """Execute a theft crime"""
        # Get target player
        target_player = Player.query.get(self.target_player_id)
        if not target_player:
            self.success = False
            self.details = "Target player not found"
            db.session.add(self)
            db.session.commit()
            return False
            
        # Determine amount to steal
        if not self.amount:
            # Default to 10-20% of target's cash
            steal_percentage = random.uniform(0.1, 0.2)
            self.amount = int(target_player.money * steal_percentage)
            # Cap at 200
            self.amount = min(200, self.amount)
        
        # Ensure target has enough money
        if target_player.money < self.amount:
            self.amount = target_player.money
        
        # If amount is 0, fail
        if self.amount <= 0:
            self.success = False
            self.details = "Target has no money to steal"
            db.session.add(self)
            db.session.commit()
            return False
        
        # Attempt the theft
        self.success = True
        
        # Check if detected
        if self.detect():
            # Theft was detected, consequences will be applied
            self.details = f"Theft detected! Attempted to steal ${self.amount}"
            db.session.add(self)
            db.session.commit()
            return False
        
        # Successful undetected theft
        target_player.pay(self.amount)
        self.player.receive(self.amount)
        
        # Record transaction with special type
        transaction = Transaction(
            from_player_id=self.target_player_id,
            to_player_id=self.player_id,
            amount=self.amount,
            transaction_type="theft",
            description="Theft of money"
        )
        
        db.session.add(target_player)
        db.session.add(self.player)
        db.session.add(transaction)
        db.session.add(self)
        db.session.commit()
        
        self.details = f"Successfully stole ${self.amount} from {target_player.username}"
        db.session.add(self)
        db.session.commit()
        
        return True


class PropertyVandalism(Crime):
    """Crime involving damaging a property to reduce its value or rent"""
    __mapper_args__ = {
        'polymorphic_identity': 'property_vandalism'
    }
    
    def execute(self):
        """Execute property vandalism"""
        # Get target property
        property = Property.query.get(self.target_property_id)
        if not property:
            self.success = False
            self.details = "Target property not found"
            db.session.add(self)
            db.session.commit()
            return False
        
        # Ensure property has an owner that's not the player
        if not property.owner_id or property.owner_id == self.player_id:
            self.success = False
            self.details = "Cannot vandalize unowned property or own property"
            db.session.add(self)
            db.session.commit()
            return False
        
        # Set damage amount if not provided
        if not self.amount:
            # Damage is 10-30% of property value
            damage_percentage = random.uniform(0.1, 0.3)
            self.amount = int(property.current_price * damage_percentage)
        
        # Attempt vandalism
        self.success = True
        
        # Check if detected
        if self.detect():
            # Vandalism detected, consequences will be applied
            self.details = f"Vandalism detected! Attempted to damage property worth ${self.amount}"
            db.session.add(self)
            db.session.commit()
            return False
        
        # Apply damage to property
        property.damage_amount = self.amount if not property.damage_amount else property.damage_amount + self.amount
        
        # Reduce property value temporarily
        original_price = property.current_price
        property.current_price = max(int(property.current_price * 0.7), property.base_price // 2)
        
        # Add temporary effect to game state to restore property value after 3 turns
        game_state = GameState.query.first()
        game_state.add_temporary_effect({
            'type': 'property_damage_repair',
            'property_id': property.id,
            'original_price': original_price,
            'damage_amount': self.amount,
            'remaining_turns': 3,
            'description': f"Repairs in progress for {property.name}"
        })
        
        # Update details
        self.details = f"Successfully vandalized {property.name}, causing ${self.amount} in damage"
        
        db.session.add(property)
        db.session.add(self)
        db.session.commit()
        
        return True


class RentEvasion(Crime):
    """Crime involving avoiding rent payment"""
    __mapper_args__ = {
        'polymorphic_identity': 'rent_evasion'
    }
    
    def execute(self, rent_amount=None, property_id=None):
        """Execute rent evasion
        
        Args:
            rent_amount: Amount of rent being evaded (optional)
            property_id: ID of the property whose rent is being evaded (optional)
        """
        # Set passed parameters if provided
        if rent_amount:
            self.amount = rent_amount
        if property_id:
            self.target_property_id = property_id
            
        # Validate we have required data
        if not self.amount or not self.target_property_id:
            self.success = False
            self.details = "Missing rent amount or property information"
            db.session.add(self)
            db.session.commit()
            return False
            
        # Get property information
        property = Property.query.get(self.target_property_id)
        if not property or not property.owner_id:
            self.success = False
            self.details = "Invalid property or unowned property"
            db.session.add(self)
            db.session.commit()
            return False
            
        # Set target player to property owner
        self.target_player_id = property.owner_id
        
        # Attempt evasion
        self.success = True
        
        # Check if detected
        if self.detect():
            # Evasion detected, consequences will be applied
            self.details = f"Rent evasion detected! Must pay ${self.amount} plus penalty"
            
            # Pay original rent amount plus 50% penalty
            penalty_amount = int(self.amount * 0.5)
            total_due = self.amount + penalty_amount
            
            # Try to collect payment
            if self.player.money >= total_due:
                self.player.pay(total_due)
                property.owner.receive(total_due)
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=self.player_id,
                    to_player_id=property.owner_id,
                    amount=total_due,
                    transaction_type="rent_penalty",
                    property_id=property.id,
                    description=f"Rent payment with evasion penalty for {property.name}"
                )
                db.session.add(transaction)
                
                self.details += f" - Paid ${total_due} (including ${penalty_amount} penalty)"
            else:
                # Player can't pay - they'll be handled by the bankruptcy system
                self.details += f" - Insufficient funds to pay ${total_due} (including ${penalty_amount} penalty)"
                
            db.session.add(self)
            db.session.commit()
            return False
        
        # Successful undetected evasion
        self.details = f"Successfully evaded ${self.amount} rent payment for {property.name}"
        db.session.add(self)
        db.session.commit()
        
        return True


class Forgery(Crime):
    """Crime involving forging bank notes or documents for financial gain"""
    __mapper_args__ = {
        'polymorphic_identity': 'forgery'
    }
    
    def execute(self):
        """Execute forgery crime"""
        # Set amount if not provided
        if not self.amount:
            # Amount is random between $100-$300
            self.amount = random.randint(100, 300)
            
        # Attempt forgery
        self.success = True
        
        # Check if detected
        if self.detect():
            # Forgery detected, consequences will be applied
            self.details = f"Forgery detected! Attempted to forge ${self.amount}"
            db.session.add(self)
            db.session.commit()
            
            # Apply extra consequences - higher fine
            fine_amount = int(self.amount * 2)
            if self.player.money >= fine_amount:
                self.player.pay(fine_amount)
                
                # Update community fund
                game_state = GameState.query.first()
                game_state.community_fund += fine_amount
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=self.player_id,
                    to_player_id=None,  # Community fund
                    amount=fine_amount,
                    transaction_type="forgery_fine",
                    description="Fine for attempted forgery"
                )
                
                db.session.add(transaction)
                db.session.add(game_state)
                self.details += f" - Fined ${fine_amount} (sent to community fund)"
            else:
                # Player can't pay - they'll be handled by the bankruptcy system
                self.details += f" - Insufficient funds to pay ${fine_amount} fine"
                
            db.session.add(self)
            db.session.commit()
            return False
        
        # Successful undetected forgery
        self.player.receive(self.amount)
        
        # Record transaction with special type
        transaction = Transaction(
            from_player_id=None,  # From the bank
            to_player_id=self.player_id,
            amount=self.amount,
            transaction_type="forgery",
            description="Successfully forged bank notes"
        )
        
        db.session.add(self.player)
        db.session.add(transaction)
        
        self.details = f"Successfully forged ${self.amount}"
        db.session.add(self)
        db.session.commit()
        
        return True


class TaxEvasion(Crime):
    """Crime involving evading tax payments"""
    __mapper_args__ = {
        'polymorphic_identity': 'tax_evasion'
    }
    
    def execute(self, tax_amount=None):
        """Execute tax evasion
        
        Args:
            tax_amount: Amount of tax being evaded (optional)
        """
        # Set amount if provided
        if tax_amount:
            self.amount = tax_amount
            
        # If still no amount, calculate based on net worth
        if not self.amount:
            # Calculate tax as percentage of net worth
            net_worth = self.player.calculate_net_worth()
            game_state = GameState.query.first()
            tax_rate = game_state.tax_rate
            self.amount = int(net_worth * tax_rate)
            
        # Attempt evasion
        self.success = True
        
        # Check if detected
        if self.detect():
            # Tax evasion detected, consequences will be applied
            self.details = f"Tax evasion detected! Must pay ${self.amount} plus penalty"
            
            # Pay original tax amount plus 100% penalty
            penalty_amount = self.amount
            total_due = self.amount * 2
            
            # Try to collect payment
            if self.player.money >= total_due:
                self.player.pay(total_due)
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=self.player_id,
                    to_player_id=None,  # To the bank
                    amount=total_due,
                    transaction_type="tax_penalty",
                    description="Tax payment with evasion penalty"
                )
                db.session.add(transaction)
                
                self.details += f" - Paid ${total_due} (including ${penalty_amount} penalty)"
            else:
                # Player can't pay - they'll be handled by the bankruptcy system
                self.details += f" - Insufficient funds to pay ${total_due} (including ${penalty_amount} penalty)"
                
            db.session.add(self)
            db.session.commit()
            return False
        
        # Successful undetected tax evasion
        self.details = f"Successfully evaded ${self.amount} in taxes"
        db.session.add(self)
        db.session.commit()
        
        return True 