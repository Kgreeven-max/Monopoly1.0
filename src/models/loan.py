from . import db
from datetime import datetime
import logging

class Loan(db.Model):
    """Model for player loans and CDs"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    start_lap = db.Column(db.Integer, nullable=False)
    length_laps = db.Column(db.Integer, nullable=False)
    is_cd = db.Column(db.Boolean, default=False)  # True for CD, False for loan
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)  # For HELOC
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    original_interest_rate = db.Column(db.Float, nullable=True)  # Store original rate for tracking changes
    
    # Relationships
    property = db.relationship('Property', backref='loans', lazy=True)
    
    def __repr__(self):
        loan_type = "CD" if self.is_cd else "Loan"
        return f'<{loan_type} {self.id}: ${self.amount} for Player {self.player_id}>'
    
    def to_dict(self):
        """Convert loan to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'amount': self.amount,
            'interest_rate': self.interest_rate,
            'start_lap': self.start_lap,
            'length_laps': self.length_laps,
            'is_cd': self.is_cd,
            'property_id': self.property_id,
            'is_active': self.is_active,
            'remaining_laps': self.calculate_remaining_laps(),
            'current_value': self.calculate_current_value(),
            'original_interest_rate': self.original_interest_rate or self.interest_rate
        }
    
    def calculate_remaining_laps(self, current_lap=None):
        """Calculate remaining laps until loan/CD completion"""
        if current_lap is None:
            # Get current lap from game state
            from .game_state import GameState
            game_state = GameState.query.first()
            if game_state:
                current_lap = game_state.current_lap
            else:
                current_lap = 0
        
        return max(0, self.start_lap + self.length_laps - current_lap)
    
    def calculate_current_value(self, current_lap=None):
        """Calculate current value of loan/CD with interest"""
        if current_lap is None:
            # Get current lap from game state
            from .game_state import GameState
            game_state = GameState.query.first()
            if game_state:
                current_lap = game_state.current_lap
            else:
                current_lap = 0
        
        # Calculate laps that have passed
        laps_passed = max(0, current_lap - self.start_lap)
        
        if self.is_cd:
            # For CDs, calculate interest earned
            value = self.amount * (1 + self.interest_rate) ** laps_passed
        else:
            # For loans, calculate interest owed
            value = self.amount * (1 + self.interest_rate) ** laps_passed
        
        return int(value)
        
    def adjust_interest_rate(self, change_amount):
        """
        Adjust the interest rate of this loan or CD
        
        Args:
            change_amount: The amount to change the interest rate by (positive or negative)
        
        Returns:
            The new interest rate
        """
        # Store original rate if not already saved
        if self.original_interest_rate is None:
            self.original_interest_rate = self.interest_rate
            
        # Calculate new rate
        new_rate = max(0.01, self.interest_rate + change_amount)  # Ensure minimum 1% rate
        
        # Apply the new rate
        self.interest_rate = new_rate
        db.session.add(self)
        db.session.commit()
        
        # Log the change
        logger = logging.getLogger("loan")
        loan_type = "CD" if self.is_cd else "Loan"
        logger.info(f"Adjusted {loan_type} #{self.id} interest rate from {self.original_interest_rate} to {new_rate}")
        
        return new_rate
        
    def mark_paid(self):
        """Mark a loan as paid off"""
        self.is_active = False
        db.session.add(self)
        db.session.commit()
        
        return True
        
    @property
    def is_paid_off(self):
        """Check if a loan is paid off"""
        return not self.is_active
        
    @classmethod
    def create_loan(cls, player_id, amount, interest_rate, length_laps, current_lap, property_id=None, is_cd=False):
        """Create a new loan or CD"""
        loan = cls(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            original_interest_rate=interest_rate,
            start_lap=current_lap,
            length_laps=length_laps,
            is_cd=is_cd,
            property_id=property_id,
            is_active=True
        )
        
        db.session.add(loan)
        db.session.commit()
        
        return loan 