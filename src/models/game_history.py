from . import db
from datetime import datetime

class GameHistory(db.Model):
    """Model for completed game records"""
    __tablename__ = 'game_history'
    
    id = db.Column(db.Integer, primary_key=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    end_reason = db.Column(db.String(50), default='normal')  # normal, time_limit, abandoned
    duration_minutes = db.Column(db.Integer, nullable=False)
    total_laps = db.Column(db.Integer, nullable=False)
    player_count = db.Column(db.Integer, nullable=False)
    bot_count = db.Column(db.Integer, nullable=False)
    final_inflation_state = db.Column(db.String(20), nullable=False)
    player_stats = db.Column(db.Text, nullable=False)  # JSON string of player stats
    property_stats = db.Column(db.Text, nullable=False)  # JSON string of property distribution
    economic_stats = db.Column(db.Text, nullable=False)  # JSON string of economic history
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    winner = db.relationship('Player', foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<GameHistory {self.id}: Winner {self.winner_id}, {self.duration_minutes} minutes>'
    
    def to_dict(self):
        """Convert game history to dictionary for API responses"""
        import json
        
        return {
            'id': self.id,
            'winner_id': self.winner_id,
            'end_reason': self.end_reason,
            'duration_minutes': self.duration_minutes,
            'total_laps': self.total_laps,
            'player_count': self.player_count,
            'bot_count': self.bot_count,
            'final_inflation_state': self.final_inflation_state,
            'player_stats': json.loads(self.player_stats),
            'property_stats': json.loads(self.property_stats),
            'economic_stats': json.loads(self.economic_stats),
            'created_at': self.created_at.isoformat()
        } 