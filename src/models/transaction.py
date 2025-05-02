from . import db
from datetime import datetime

class Transaction(db.Model):
    """Model for financial transactions"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    from_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # Null for bank-to-player
    to_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # Null for player-to-bank
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # rent, purchase, improvement, loan, etc.
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lap_number = db.Column(db.Integer, nullable=True)  # Game lap when transaction occurred
    
    # Relationships - Fix backref conflict by removing them
    from_player = db.relationship('Player', foreign_keys=[from_player_id], back_populates='outgoing_transactions')
    to_player = db.relationship('Player', foreign_keys=[to_player_id], back_populates='incoming_transactions')
    property = db.relationship('Property', backref='transactions')
    loan = db.relationship('Loan', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.id}: ${self.amount}, {self.transaction_type}>'
    
    def to_dict(self):
        """Convert transaction to dictionary for API responses"""
        return {
            'id': self.id,
            'from_player_id': self.from_player_id,
            'to_player_id': self.to_player_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'property_id': self.property_id,
            'loan_id': self.loan_id,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'lap_number': self.lap_number
        }
        
    @classmethod
    def create(cls, player_id=None, from_player_id=None, to_player_id=None, 
               amount=0, transaction_type="generic", description=None,
               property_id=None, loan_id=None, lap_number=None):
        """
        Create a new transaction record
        
        Args:
            player_id: If provided, used to determine from_player_id or to_player_id based on amount sign
            from_player_id: ID of player sending money (None for bank-to-player)
            to_player_id: ID of player receiving money (None for player-to-bank)
            amount: Transaction amount (positive for receiving, negative for spending)
            transaction_type: Type of transaction (rent, purchase, loan, etc.)
            description: Optional description of the transaction
            property_id: Optional property ID related to the transaction
            loan_id: Optional loan ID related to the transaction
            lap_number: Optional game lap number when the transaction occurred
            
        Returns:
            The newly created Transaction object
        """
        # If a game_state is needed to get lap_number:
        if lap_number is None:
            try:
                from .game_state import GameState
                game_state = GameState.get_instance()
                lap_number = game_state.current_lap
            except:
                lap_number = 0
                
        # If only player_id is provided, determine direction based on amount
        if player_id is not None and from_player_id is None and to_player_id is None:
            if amount < 0:
                # Money going out from player (spending)
                from_player_id = player_id
                to_player_id = None
                amount = abs(amount)  # Store as positive
            else:
                # Money coming in to player (income)
                from_player_id = None
                to_player_id = player_id
                
        # Create transaction
        transaction = cls(
            from_player_id=from_player_id,
            to_player_id=to_player_id,
            amount=amount,
            transaction_type=transaction_type,
            property_id=property_id,
            loan_id=loan_id,
            description=description,
            lap_number=lap_number
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction 