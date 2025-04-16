from . import db
from datetime import datetime
from sqlalchemy.orm import relationship # Import relationship explicitly

class Team(db.Model):
    """Model for teams in team-based game modes"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game_state.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Team resources
    shared_cash = db.Column(db.Integer, default=0)
    property_sharing_enabled = db.Column(db.Boolean, default=True)
    rent_immunity_enabled = db.Column(db.Boolean, default=True)
    income_sharing_percent = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    game = db.relationship('GameState', backref=db.backref('teams', lazy=True))
    players = relationship('Player', foreign_keys='Player.team_id', backref='team', lazy=True)
    properties = relationship('Property', foreign_keys='Property.team_id', backref='team', lazy=True)
    
    def __repr__(self):
        return f'<Team {self.id}: {self.name} in Game {self.game_id}>'
    
    def to_dict(self):
        """Convert team to dictionary for API responses"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'name': self.name,
            'color': self.color,
            'score': self.score,
            'is_active': self.is_active,
            'shared_cash': self.shared_cash,
            'property_sharing_enabled': self.property_sharing_enabled,
            'rent_immunity_enabled': self.rent_immunity_enabled,
            'income_sharing_percent': self.income_sharing_percent,
            'player_count': len(self.players),
            'property_count': len(self.properties),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_score(self):
        """Calculate team score based on various factors"""
        score = 0
        
        # Base score from shared cash
        score += self.shared_cash
        
        # Add property values
        for prop in self.properties:
            score += prop.current_price
        
        # Add player cash
        for player in self.players:
            if player.status == 'active':
                score += player.cash
        
        self.score = score
        return score
    
    def process_income_sharing(self):
        """Process income sharing among team members"""
        if self.income_sharing_percent <= 0:
            return
            
        total_income = 0
        active_players = [p for p in self.players if p.status == 'active']
        
        # Calculate total income to share
        for player in active_players:
            share_amount = int(player.cash * self.income_sharing_percent)
            player.cash -= share_amount
            total_income += share_amount
        
        # Distribute shared income equally
        if active_players:
            share_per_player = total_income // len(active_players)
            for player in active_players:
                player.cash += share_per_player
    
    def check_team_status(self):
        """Check if team should be eliminated"""
        active_players = [p for p in self.players if p.status == 'active']
        if not active_players:
            self.is_active = False
            return False
        return True 