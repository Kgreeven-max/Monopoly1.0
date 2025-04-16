from . import db
from datetime import datetime

class EconomicPhaseChange(db.Model):
    """Model for tracking economic phase changes"""
    __tablename__ = 'economic_phase_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    lap_number = db.Column(db.Integer, nullable=False)
    old_state = db.Column(db.String(20), nullable=False)
    new_state = db.Column(db.String(20), nullable=False)
    inflation_factor = db.Column(db.Float, nullable=False)
    total_cash = db.Column(db.Integer, nullable=False)  # Total cash in circulation
    total_property_value = db.Column(db.Integer, nullable=False)  # Total value of all properties
    description = db.Column(db.String(200), nullable=True)  # Explanation of change
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EconomicPhaseChange: {self.old_state} -> {self.new_state}, Lap {self.lap_number}>'
    
    def to_dict(self):
        """Convert economic phase change to dictionary for API responses"""
        return {
            'id': self.id,
            'lap_number': self.lap_number,
            'old_state': self.old_state,
            'new_state': self.new_state,
            'inflation_factor': self.inflation_factor,
            'total_cash': self.total_cash,
            'total_property_value': self.total_property_value,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        } 