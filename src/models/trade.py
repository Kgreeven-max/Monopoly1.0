from . import db
from datetime import datetime

class Trade(db.Model):
    """Model for player-to-player trades"""
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    proposer_cash = db.Column(db.Integer, default=0)
    receiver_cash = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, rejected, expired, flagged
    details = db.Column(db.Text, nullable=True)  # JSON string with additional details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    proposer = db.relationship('Player', foreign_keys=[proposer_id], backref='proposed_trades')
    receiver = db.relationship('Player', foreign_keys=[receiver_id], backref='received_trades')
    items = db.relationship('TradeItem', backref='trade', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trade {self.id}: {self.status}, {self.proposer_id} -> {self.receiver_id}>'
    
    def to_dict(self):
        """Convert trade to dictionary for API responses"""
        import json
        
        result = {
            'id': self.id,
            'proposer_id': self.proposer_id,
            'receiver_id': self.receiver_id,
            'proposer_cash': self.proposer_cash,
            'receiver_cash': self.receiver_cash,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'proposer_properties': [],
            'receiver_properties': []
        }
        
        # Add trade items
        for item in self.items:
            if item.is_from_proposer:
                result['proposer_properties'].append(item.property_id)
            else:
                result['receiver_properties'].append(item.property_id)
        
        # Add details if available
        if self.details:
            details = json.loads(self.details)
            if 'proposer_jail_cards' in details:
                result['proposer_jail_cards'] = details['proposer_jail_cards']
            if 'receiver_jail_cards' in details:
                result['receiver_jail_cards'] = details['receiver_jail_cards']
        
        return result


class TradeItem(db.Model):
    """Model for items included in a trade"""
    __tablename__ = 'trade_items'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    is_from_proposer = db.Column(db.Boolean, default=True)  # True if proposer is offering, False if receiver
    
    # Relationships
    property = db.relationship('Property')
    
    def __repr__(self):
        direction = "proposer -> receiver" if self.is_from_proposer else "receiver -> proposer"
        return f'<TradeItem {self.id}: Property {self.property_id}, {direction}>' 