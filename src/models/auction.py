from datetime import datetime
import json
from . import db

class Auction(db.Model):
    """Persistent model for property auctions"""
    __tablename__ = 'auctions'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)  # Add game_id field
    status = db.Column(db.String(20), nullable=False, default='active', index=True) # active, completed, cancelled
    minimum_bid = db.Column(db.Integer, nullable=False)
    current_bid = db.Column(db.Integer, nullable=True)
    current_bidder_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    last_bid_time = db.Column(db.DateTime, nullable=True) # Time of the last valid bid
    is_foreclosure = db.Column(db.Boolean, default=False)
    original_owner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True) # For foreclosures

    # Store lists as JSON strings for simplicity initially
    eligible_players = db.Column(db.Text, nullable=True) # JSON list of player IDs
    players_passed = db.Column(db.Text, nullable=True) # JSON list of player IDs who passed

    # Relationships
    property = db.relationship('Property')
    current_bidder = db.relationship('Player', foreign_keys=[current_bidder_id])
    original_owner = db.relationship('Player', foreign_keys=[original_owner_id])
    # Add relationship to Game
    game = db.relationship('Game', foreign_keys=[game_id])
    # Consider adding a relationship to a Bid model later for detailed history

    def __init__(self, **kwargs):
        """Initialize an auction, handling backward compatibility with different parameter names"""
        # Handle starting_bid parameter by mapping it to minimum_bid
        if 'starting_bid' in kwargs and 'minimum_bid' not in kwargs:
            kwargs['minimum_bid'] = kwargs.pop('starting_bid')
            
        # Handle current_winner_id parameter (used in some places instead of current_bidder_id)
        if 'current_winner_id' in kwargs and 'current_bidder_id' not in kwargs:
            kwargs['current_bidder_id'] = kwargs.pop('current_winner_id')
            
        super(Auction, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Auction {self.id} for Property {self.property_id}, Status: {self.status}>'

    def set_eligible_players(self, player_ids: list):
        self.eligible_players = json.dumps(player_ids)

    def get_eligible_players(self) -> list:
        return json.loads(self.eligible_players) if self.eligible_players else []

    def add_passed_player(self, player_id: int):
        passed_list = self.get_passed_players()
        if player_id not in passed_list:
            passed_list.append(player_id)
            self.players_passed = json.dumps(passed_list)

    def get_passed_players(self) -> list:
        return json.loads(self.players_passed) if self.players_passed else []

    def to_dict(self):
        """Convert auction to dictionary for API responses or internal use"""
        return {
            'id': self.id,
            'property_id': self.property_id,
            'game_id': self.game_id,  # Add game_id
            'property_name': self.property.name if self.property else None,
            'status': self.status,
            'minimum_bid': self.minimum_bid,
            'current_bid': self.current_bid,
            'current_bidder_id': self.current_bidder_id,
            'current_bidder_name': self.current_bidder.username if self.current_bidder else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'last_bid_time': self.last_bid_time.isoformat() if self.last_bid_time else None,
            'is_foreclosure': self.is_foreclosure,
            'original_owner_id': self.original_owner_id,
            'original_owner_name': self.original_owner.username if self.original_owner else None,
            'eligible_players': self.get_eligible_players(),
            'players_passed': self.get_passed_players()
            # Add bids history if Bid model is implemented
        } 