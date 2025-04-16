from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models import db
import uuid

class ReputationScore(db.Model):
    """Player reputation score model"""
    __tablename__ = 'reputation_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False, unique=True)
    overall_score = db.Column(db.Integer, default=50)  # 0-100 score, 50 is neutral
    trade_score = db.Column(db.Integer, default=50)  # Trade fairness score
    agreement_score = db.Column(db.Integer, default=50)  # Keeping agreements score
    community_score = db.Column(db.Integer, default=50)  # Community contribution score
    financial_score = db.Column(db.Integer, default=50)  # Financial reliability score
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('ReputationEvent', backref='reputation_score', lazy='dynamic', 
                            cascade='all, delete-orphan', 
                            order_by='desc(ReputationEvent.timestamp)')
    
    def to_dict(self):
        """Convert reputation score to dictionary"""
        return {
            'player_id': self.player_id,
            'overall_score': self.overall_score,
            'trade_score': self.trade_score,
            'agreement_score': self.agreement_score,
            'community_score': self.community_score,
            'financial_score': self.financial_score,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'rating': self.get_rating(),
            'recent_events': [event.to_dict() for event in self.events.limit(5).all()]
        }
    
    def get_rating(self):
        """Get textual rating based on overall score"""
        if self.overall_score >= 90:
            return "Exceptional"
        elif self.overall_score >= 75:
            return "Excellent"
        elif self.overall_score >= 60:
            return "Good"
        elif self.overall_score >= 40:
            return "Average"
        elif self.overall_score >= 25:
            return "Poor"
        else:
            return "Unreliable"
    
    def record_event(self, event_type, description, impact, category=None):
        """Record a reputation-affecting event"""
        if category is None:
            # Default to most appropriate category based on event type
            category_map = {
                'trade_completed': 'trade',
                'trade_rejected': 'trade',
                'agreement_kept': 'agreement',
                'agreement_broken': 'agreement',
                'loan_repaid': 'financial',
                'loan_defaulted': 'financial',
                'community_contribution': 'community',
                'property_improvement': 'community',
                'rent_paid': 'financial',
                'alliance_formed': 'community',
                'alliance_disbanded': 'community'
            }
            category = category_map.get(event_type, 'overall')
        
        # Create new event
        event = ReputationEvent(
            reputation_id=self.id,
            player_id=self.player_id,
            event_type=event_type,
            description=description,
            impact=impact,
            category=category
        )
        db.session.add(event)
        
        # Update appropriate score
        if category == 'trade':
            self.trade_score = max(0, min(100, self.trade_score + impact))
        elif category == 'agreement':
            self.agreement_score = max(0, min(100, self.agreement_score + impact))
        elif category == 'community':
            self.community_score = max(0, min(100, self.community_score + impact))
        elif category == 'financial':
            self.financial_score = max(0, min(100, self.financial_score + impact))
        
        # Update overall score (weighted average)
        self.overall_score = int((
            self.trade_score * 0.25 +
            self.agreement_score * 0.25 +
            self.community_score * 0.20 +
            self.financial_score * 0.30
        ))
        
        self.updated_at = datetime.utcnow()
        return event


class ReputationEvent(db.Model):
    """Reputation event model for tracking reputation changes"""
    __tablename__ = 'reputation_events'
    
    id = db.Column(db.Integer, primary_key=True)
    reputation_id = db.Column(db.Integer, db.ForeignKey('reputation_scores.id'), nullable=False)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    impact = db.Column(db.Integer, nullable=False)  # Positive or negative impact on reputation
    category = db.Column(db.String(20), default='overall')  # overall, trade, agreement, community, financial
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    game_id = db.Column(db.String(36))  # Optional reference to game where this occurred
    
    def to_dict(self):
        """Convert reputation event to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'event_type': self.event_type,
            'description': self.description,
            'impact': self.impact,
            'category': self.category,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'game_id': self.game_id
        } 