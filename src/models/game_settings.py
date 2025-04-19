from src.models import db
import json
from datetime import datetime

class GameSettings(db.Model):
    """Model for game settings that control various game behavior"""
    
    __tablename__ = "game_settings"
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game_state.id"), nullable=False)
    
    # General game settings as JSON
    settings_json = db.Column(db.Text, nullable=False, default="{}")
    
    # Common individual settings for quick access
    free_parking_collects_fees = db.Column(db.Boolean, default=False)
    taxes_to_community_fund = db.Column(db.Boolean, default=True)
    salary_multiplier = db.Column(db.Float, default=1.0)
    go_salary = db.Column(db.Integer, default=200)
    
    # Jail settings
    jail_fine = db.Column(db.Integer, default=50)
    max_jail_turns = db.Column(db.Integer, default=3)
    
    # Economic settings
    enable_economic_cycles = db.Column(db.Boolean, default=True)
    economic_cycle_interval = db.Column(db.Integer, default=10)  # Turns between cycles
    property_values_follow_economy = db.Column(db.Boolean, default=True)
    
    # Game progression
    max_laps = db.Column(db.Integer, default=20)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, game_id, settings_dict=None):
        """Initialize game settings
        
        Args:
            game_id: ID of the game
            settings_dict: Optional dictionary of initial settings
        """
        self.game_id = game_id
        
        if settings_dict:
            self.update_settings(settings_dict)
        else:
            self.settings_json = "{}"
    
    def update_settings(self, settings_dict):
        """Update settings from a dictionary
        
        Args:
            settings_dict: Dictionary containing settings to update
        """
        # First update the JSON
        current_settings = self.get_all_settings()
        current_settings.update(settings_dict)
        self.settings_json = json.dumps(current_settings)
        
        # Then update individual fields if they're in the dict
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_all_settings(self):
        """Get all settings as a dictionary
        
        Returns:
            Dictionary of all settings
        """
        try:
            settings_dict = json.loads(self.settings_json)
        except (json.JSONDecodeError, TypeError):
            settings_dict = {}
        
        # Add individual columns to the dictionary
        for column in self.__table__.columns:
            column_name = column.name
            if column_name not in ['id', 'game_id', 'settings_json', 'created_at', 'updated_at']:
                settings_dict[column_name] = getattr(self, column_name)
        
        return settings_dict
    
    def get_setting(self, key, default=None):
        """Get a specific setting
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        # Check if it's an individual column
        if hasattr(self, key):
            return getattr(self, key)
        
        # Otherwise look in the JSON
        settings = self.get_all_settings()
        return settings.get(key, default) 