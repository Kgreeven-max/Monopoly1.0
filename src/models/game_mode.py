from . import db
from datetime import datetime
import json

class GameMode(db.Model):
    """Model for game modes and their specific settings"""
    __tablename__ = 'game_modes'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game_state.id'), nullable=False)
    mode_type = db.Column(db.String(20), default='classic')  # classic, speed, cooperative, tycoon, market_crash, team_battle
    name = db.Column(db.String(50), nullable=False)
    
    # Common settings
    starting_cash = db.Column(db.Integer, default=1500)
    go_salary = db.Column(db.Integer, default=200)
    free_parking_collects_fees = db.Column(db.Boolean, default=False)
    auction_enabled = db.Column(db.Boolean, default=True)
    max_turns = db.Column(db.Integer, nullable=True)  # None = unlimited
    max_time_minutes = db.Column(db.Integer, nullable=True)  # None = unlimited
    bankruptcy_threshold = db.Column(db.Integer, default=0)
    event_frequency = db.Column(db.Float, default=0.15)
    disaster_impact = db.Column(db.Float, default=1.0)
    inflation_factor = db.Column(db.Float, default=1.0)
    development_levels_enabled = db.Column(db.Boolean, default=True)
    turn_timer_seconds = db.Column(db.Integer, nullable=True)
    
    # Mode-specific settings
    _custom_settings = db.Column(db.Text, nullable=True)  # JSON string for mode-specific settings
    
    # Team battle settings
    team_based = db.Column(db.Boolean, default=False)
    team_trading_enabled = db.Column(db.Boolean, default=False)
    team_property_sharing = db.Column(db.Boolean, default=False)
    team_rent_immunity = db.Column(db.Boolean, default=False)
    team_income_sharing = db.Column(db.Float, default=0.0)
    
    # Win condition
    win_condition = db.Column(db.String(30), default='last_standing')  # last_standing, net_worth, property_development, team_domination
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    game = db.relationship('GameState', backref=db.backref('game_mode', uselist=False))
    
    def __repr__(self):
        return f'<GameMode {self.id}: {self.mode_type} for Game {self.game_id}>'
    
    @property
    def custom_settings(self):
        """Get custom settings as Python dict"""
        try:
            return json.loads(self._custom_settings) if self._custom_settings else {}
        except:
            return {}
            
    @custom_settings.setter
    def custom_settings(self, settings_dict):
        """Store custom settings as JSON string"""
        self._custom_settings = json.dumps(settings_dict)
    
    def to_dict(self):
        """Convert game mode to dictionary for API responses"""
        mode_dict = {
            'id': self.id,
            'game_id': self.game_id,
            'mode_type': self.mode_type,
            'name': self.name,
            'starting_cash': self.starting_cash,
            'go_salary': self.go_salary,
            'free_parking_collects_fees': self.free_parking_collects_fees,
            'auction_enabled': self.auction_enabled,
            'max_turns': self.max_turns,
            'max_time_minutes': self.max_time_minutes,
            'bankruptcy_threshold': self.bankruptcy_threshold,
            'event_frequency': self.event_frequency,
            'disaster_impact': self.disaster_impact,
            'inflation_factor': self.inflation_factor,
            'development_levels_enabled': self.development_levels_enabled,
            'turn_timer_seconds': self.turn_timer_seconds,
            'win_condition': self.win_condition,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Add team settings if applicable
        if self.team_based:
            mode_dict.update({
                'team_based': self.team_based,
                'team_trading_enabled': self.team_trading_enabled,
                'team_property_sharing': self.team_property_sharing,
                'team_rent_immunity': self.team_rent_immunity,
                'team_income_sharing': self.team_income_sharing
            })
        
        # Add custom settings
        mode_dict['custom_settings'] = self.custom_settings
        
        return mode_dict
        
    @classmethod
    def create_for_game(cls, game_id, mode_type, settings=None):
        """Factory method to create the appropriate game mode for a game"""
        if settings is None:
            settings = {}
            
        # Create basic mode
        game_mode = cls(
            game_id=game_id,
            mode_type=mode_type,
            name=cls.get_mode_name(mode_type)
        )
        
        # Apply standard settings based on mode type
        if mode_type == "classic":
            cls._configure_classic_mode(game_mode)
        elif mode_type == "speed":
            cls._configure_speed_mode(game_mode)
        elif mode_type == "cooperative":
            cls._configure_cooperative_mode(game_mode)
        elif mode_type == "tycoon":
            cls._configure_tycoon_mode(game_mode)
        elif mode_type == "market_crash":
            cls._configure_market_crash_mode(game_mode)
        elif mode_type == "team_battle":
            cls._configure_team_battle_mode(game_mode)
        
        # Override with any provided settings
        for key, value in settings.items():
            if hasattr(game_mode, key):
                setattr(game_mode, key, value)
            else:
                # Store in custom settings
                custom = game_mode.custom_settings
                custom[key] = value
                game_mode.custom_settings = custom
        
        return game_mode
    
    @staticmethod
    def get_mode_name(mode_type):
        """Get the display name for a mode type"""
        mode_names = {
            "classic": "Classic Mode",
            "speed": "Speed Mode",
            "cooperative": "Co-op Mode",
            "tycoon": "Tycoon Mode",
            "market_crash": "Market Crash Mode",
            "team_battle": "Team Battle Mode"
        }
        return mode_names.get(mode_type, "Custom Mode")
    
    @staticmethod
    def _configure_classic_mode(game_mode):
        """Configure settings for classic mode"""
        game_mode.starting_cash = 1500
        game_mode.go_salary = 200
        game_mode.free_parking_collects_fees = False
        game_mode.auction_enabled = True
        game_mode.max_turns = None
        game_mode.max_time_minutes = None
        game_mode.bankruptcy_threshold = 0
        game_mode.event_frequency = 0.15
        game_mode.disaster_impact = 1.0
        game_mode.inflation_factor = 1.0
        game_mode.development_levels_enabled = True
        game_mode.win_condition = "last_standing"
    
    @staticmethod
    def _configure_speed_mode(game_mode):
        """Configure settings for speed mode"""
        game_mode.starting_cash = 3000
        game_mode.go_salary = 400
        game_mode.free_parking_collects_fees = True
        game_mode.auction_enabled = True
        game_mode.max_turns = 20
        game_mode.max_time_minutes = 30
        game_mode.bankruptcy_threshold = -1000
        game_mode.event_frequency = 0.25
        game_mode.disaster_impact = 0.8
        game_mode.inflation_factor = 1.2
        game_mode.development_levels_enabled = True
        game_mode.turn_timer_seconds = 60
        game_mode.win_condition = "net_worth"
    
    @staticmethod
    def _configure_cooperative_mode(game_mode):
        """Configure settings for cooperative mode"""
        game_mode.starting_cash = 1200
        game_mode.go_salary = 150
        game_mode.free_parking_collects_fees = True
        game_mode.auction_enabled = False
        game_mode.max_turns = 30
        game_mode.bankruptcy_threshold = -500
        game_mode.event_frequency = 0.2
        game_mode.disaster_impact = 1.5
        game_mode.inflation_factor = 0.9
        game_mode.development_levels_enabled = True
        game_mode.team_based = True
        game_mode.team_trading_enabled = True
        game_mode.team_property_sharing = True
        game_mode.team_rent_immunity = True
        game_mode.win_condition = "property_development"
    
    @staticmethod
    def _configure_tycoon_mode(game_mode):
        """Configure settings for tycoon mode"""
        game_mode.starting_cash = 2000
        game_mode.go_salary = 200
        game_mode.free_parking_collects_fees = False
        game_mode.auction_enabled = True
        game_mode.max_turns = None
        game_mode.bankruptcy_threshold = 0
        game_mode.event_frequency = 0.15
        game_mode.disaster_impact = 1.0
        game_mode.inflation_factor = 1.0
        game_mode.development_levels_enabled = True
        game_mode.win_condition = "property_development"
        
        # Custom tycoon settings
        custom_settings = {
            "development_levels": 5,
            "advanced_improvement_types": True,
            "development_milestones": {
                "bronze": 5,  # Number of properties at level 2+
                "silver": 8,  # Number of properties at level 3+
                "gold": 3     # Number of properties at level 5
            }
        }
        game_mode.custom_settings = custom_settings
    
    @staticmethod
    def _configure_market_crash_mode(game_mode):
        """Configure settings for market crash mode"""
        game_mode.starting_cash = 2500
        game_mode.go_salary = 200
        game_mode.free_parking_collects_fees = True
        game_mode.auction_enabled = True
        game_mode.max_turns = None
        game_mode.bankruptcy_threshold = -500
        game_mode.event_frequency = 0.3
        game_mode.disaster_impact = 1.5
        game_mode.inflation_factor = 0.7
        game_mode.development_levels_enabled = True
        game_mode.win_condition = "net_worth"
        
        # Custom market crash settings
        custom_settings = {
            "market_volatility": 2.0,  # Higher means more frequent price changes
            "crash_threshold": 0.5,    # Property value drops below this trigger crash
            "recovery_rate": 0.1,      # Rate at which property values recover
            "crash_events": {
                "frequency": 0.2,      # Chance of crash event per turn
                "duration": 3,         # Turns a crash event lasts
                "impact": 0.3          # How much values drop during crash
            }
        }
        game_mode.custom_settings = custom_settings
    
    @staticmethod
    def _configure_team_battle_mode(game_mode):
        """Configure settings for team battle mode"""
        game_mode.starting_cash = 2000
        game_mode.go_salary = 200
        game_mode.free_parking_collects_fees = True
        game_mode.auction_enabled = True
        game_mode.max_turns = None
        game_mode.max_time_minutes = 120
        game_mode.bankruptcy_threshold = 0
        game_mode.event_frequency = 0.15
        game_mode.disaster_impact = 1.0
        game_mode.inflation_factor = 1.0
        game_mode.development_levels_enabled = True
        game_mode.team_based = True
        game_mode.team_trading_enabled = True
        game_mode.team_property_sharing = True
        game_mode.team_rent_immunity = True
        game_mode.team_income_sharing = 0.1
        game_mode.win_condition = "team_domination"
        
        # Custom team battle settings
        custom_settings = {
            "min_teams": 2,
            "max_teams": 4,
            "players_per_team": {"min": 1, "max": 3},
            "team_elimination_threshold": 1  # Number of active players needed to keep team alive
        }
        game_mode.custom_settings = custom_settings 