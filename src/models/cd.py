from . import db
from datetime import datetime, timedelta

class CD(db.Model):
    """Model for Certificate of Deposits"""
    __tablename__ = 'certificates_of_deposit'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    game_id = db.Column(db.String(36), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    maturity_date = db.Column(db.DateTime, nullable=False)
    is_matured = db.Column(db.Boolean, default=False)
    is_cashed_out = db.Column(db.Boolean, default=False)
    penalty_percentage = db.Column(db.Float, default=0.1)  # 10% penalty for early withdrawal
    is_variable_rate = db.Column(db.Boolean, default=False)  # Whether interest rate can change with economy
    history = db.Column(db.Text, nullable=True)  # JSON string for rate change history
    
    # Relationships
    player = db.relationship('Player', backref='certificates_of_deposit')
    
    # Add active property for compatibility with economic cycle controller
    @property
    def active(self):
        """Return True if the CD is active (not cashed out)"""
        return not self.is_cashed_out
    
    def __init__(self, player_id, game_id, amount, interest_rate, term_months, 
                 start_date=None, penalty_percentage=0.1):
        """
        Initialize a new CD
        
        Args:
            player_id: ID of the player owning the CD
            game_id: ID of the game
            amount: Principal amount
            interest_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            term_months: Term in months
            start_date: Start date (defaults to now)
            penalty_percentage: Penalty for early withdrawal (default 10%)
        """
        self.player_id = player_id
        self.game_id = game_id
        self.amount = amount
        self.interest_rate = interest_rate
        self.term_months = term_months
        
        if start_date is None:
            start_date = datetime.utcnow()
        self.start_date = start_date
        
        # Calculate maturity date
        self.maturity_date = start_date + timedelta(days=30 * term_months)
        self.penalty_percentage = penalty_percentage
    
    def calculate_current_value(self, current_date=None):
        """
        Calculate the current value of the CD
        
        Args:
            current_date: Date for calculation (defaults to now)
            
        Returns:
            Current value of the CD
        """
        if current_date is None:
            current_date = datetime.utcnow()
            
        if self.is_cashed_out:
            return 0
            
        # If matured, calculate full value
        if current_date >= self.maturity_date or self.is_matured:
            months_held = self.term_months
            self.is_matured = True
        else:
            # Calculate partial value based on time held
            days_held = (current_date - self.start_date).days
            months_held = days_held / 30
            
        # Apply compound interest formula
        monthly_rate = self.interest_rate / 12
        value = self.amount * (1 + monthly_rate) ** months_held
        
        return int(value)
    
    def cash_out(self, current_date=None):
        """
        Cash out the CD and calculate the final value
        
        Args:
            current_date: Date for calculation (defaults to now)
            
        Returns:
            Amount paid out
        """
        if current_date is None:
            current_date = datetime.utcnow()
            
        if self.is_cashed_out:
            return 0
            
        value = self.calculate_current_value(current_date)
        
        # Apply penalty for early withdrawal
        if current_date < self.maturity_date and not self.is_matured:
            penalty = value * self.penalty_percentage
            value -= penalty
            
        self.is_cashed_out = True
        db.session.commit()
        
        return int(value)
    
    def to_dict(self):
        """Convert CD to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'game_id': self.game_id,
            'amount': self.amount,
            'interest_rate': self.interest_rate,
            'term_months': self.term_months,
            'start_date': self.start_date.isoformat(),
            'maturity_date': self.maturity_date.isoformat(),
            'is_matured': self.is_matured,
            'is_cashed_out': self.is_cashed_out,
            'penalty_percentage': self.penalty_percentage,
            'current_value': self.calculate_current_value()
        } 