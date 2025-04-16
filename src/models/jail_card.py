from . import db
from datetime import datetime

class JailCard(db.Model):
    """Model for get-out-of-jail cards"""
    __tablename__ = 'jail_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)  # Null if not owned
    card_type = db.Column(db.String(20), default='chance')  # chance or community_chest
    used = db.Column(db.Boolean, default=False)
    acquired_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<JailCard {self.id}: {self.card_type}, Player {self.player_id}>'
    
    def to_dict(self):
        """Convert jail card to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'card_type': self.card_type,
            'used': self.used,
            'acquired_at': self.acquired_at.isoformat(),
            'used_at': self.used_at.isoformat() if self.used_at else None
        }
    
    def use_card(self):
        """Mark card as used"""
        if not self.used:
            self.used = True
            self.used_at = datetime.utcnow()
            return True
        return False 