from . import db
import uuid
from datetime import datetime

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    # Use UUID for a potentially more robust public/shareable game ID if needed later
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(50), nullable=False, default='Waiting') # e.g., Waiting, InProgress, Finished
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    # Relationship to players (one game has many players)
    players = db.relationship('Player', back_populates='game', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Game {self.id} ({self.status})>'

    def to_dict(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'player_count': len(self.players) # Example derived property
        } 