from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from src.models import Base

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(36), nullable=False)
    from_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    to_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - modified to avoid conflicts
    # Don't create back_populates as it's already defined in the Player model
    from_player = relationship("Player", foreign_keys=[from_player_id])
    to_player = relationship("Player", foreign_keys=[to_player_id])
    
    def __init__(self, game_id, amount, transaction_type, description=None, from_player_id=None, to_player_id=None):
        self.game_id = game_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description
        self.from_player_id = from_player_id
        self.to_player_id = to_player_id 