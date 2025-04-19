from enum import Enum
from . import db
from datetime import datetime

class EventType(Enum):
    """Types of game events"""
    ECONOMIC = "economic"
    DISASTER = "disaster"
    COMMUNITY = "community"
    SPECIAL = "special"
    ADMIN = "admin"
    GAME = "game"

class EventStatus(Enum):
    """Status of an event"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(db.Model):
    """Model for game events"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default=EventStatus.SCHEDULED.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    parameters = db.Column(db.Text, nullable=True)  # JSON serialized parameters
    
    def __repr__(self):
        return f'<Event {self.id}: {self.name}, {self.status}>'
    
    def to_dict(self):
        """Convert event to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'parameters': self.parameters
        } 