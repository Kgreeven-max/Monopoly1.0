from . import db
from datetime import datetime
import json
import logging

# Import necessary model for loan accrual
from .finance.loan import Loan

class GameState(db.Model):
    """Model for overall game state"""
    __tablename__ = 'game_state'
    
    id = db.Column(db.Integer, primary_key=True, default=1)
    current_player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    player_order = db.Column(db.Text, nullable=True) # Comma-separated list of player IDs in order
    current_lap = db.Column(db.Integer, default=0)
    total_laps = db.Column(db.Integer, default=0)  # For limited-lap games
    community_fund = db.Column(db.Integer, default=0)
    community_fund_enabled = db.Column(db.Boolean, default=True)  # Enable community fund feature
    inflation_state = db.Column(db.String(20), default='stable')  # stable, inflation, deflation, recession, boom
    inflation_factor = db.Column(db.Float, default=1.0)
    inflation_rate = db.Column(db.Float, default=0.03)  # Added missing attribute
    base_interest_rate = db.Column(db.Float, default=0.05)  # Added missing attribute
    tax_rate = db.Column(db.Float, default=0.1)  # 10% default
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)  # When the game actually started (not just created)
    end_time = db.Column(db.DateTime, nullable=True)  # End time for timed games
    ended_at = db.Column(db.DateTime, nullable=True)  # When the game actually ended
    status = db.Column(db.String(20), default='Waiting') # Waiting, Setup, In Progress, Paused, Ended
    difficulty = db.Column(db.String(10), default='normal')  # easy, normal, hard
    game_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID for socket room
    _temporary_effects = db.Column(db.Text, default='[]')  # JSON string for temporary effects
    last_event_lap = db.Column(db.Integer, default=0)
    police_activity = db.Column(db.Float, default=1.0)  # Multiplier for crime detection rates
    turn_timer = db.Column(db.Integer, nullable=True)  # Timer for turns in seconds
    turn_number = db.Column(db.Integer, default=0)  # Total number of turns taken
    mode = db.Column(db.String(20), default='classic')  # Game mode
    _settings = db.Column(db.Text, nullable=True)  # JSON string for game settings
    _community_chest_cards_json = db.Column(db.Text, nullable=True)  # JSON string for community chest cards
    game_log = db.Column(db.Text, nullable=True)  # JSON string for game logs
    
    # Game configuration
    auction_required = db.Column(db.Boolean, default=True)  # Whether properties must be auctioned if declined
    property_multiplier = db.Column(db.Float, default=1.0)  # Property value multiplier
    rent_multiplier = db.Column(db.Float, default=1.0)  # Rent multiplier
    improvement_cost_factor = db.Column(db.Float, default=0.5)  # Improvement cost as percentage of property value
    event_frequency = db.Column(db.Float, default=0.15)  # Frequency of random events
    
    # --- Fields for Action Validation --- 
    expected_action_type = db.Column(db.String(50), nullable=True) # e.g., 'buy_or_auction_prompt', 'pay_rent', 'draw_chance'
    _expected_action_details_json = db.Column(db.Text, nullable=True) # JSON string, e.g., '{"property_id": 12}'
    
    # Relationships
    current_player = db.relationship('Player', foreign_keys=[current_player_id])
    
    @property
    def game_running(self):
        """Check if game is currently running (active)"""
        return self.status == 'active'
        
    @game_running.setter
    def game_running(self, value):
        """Set game running status by updating the status field"""
        if value:
            self.status = 'active'
        # If setting to False and currently active, set to Paused
        elif self.status == 'active':
            self.status = 'Paused'
    
    def __repr__(self):
        return f'<GameState ID: {self.game_id} Status: {self.status} Turn: {self.turn_number} Player: {self.current_player_id}>'
    
    @property
    def temporary_effects(self):
        """Get temporary effects as Python list"""
        try:
            return json.loads(self._temporary_effects)
        except (TypeError, json.JSONDecodeError):
            return []
            
    @temporary_effects.setter
    def temporary_effects(self, effects_list):
        """Store temporary effects as JSON string"""
        self._temporary_effects = json.dumps(effects_list)
    
    @property
    def settings(self):
        """Get game settings as Python dict"""
        try:
            return json.loads(self._settings) if self._settings else {}
        except (TypeError, json.JSONDecodeError):
            return {}
            
    @settings.setter
    def settings(self, settings_dict):
        """Store game settings as JSON string"""
        self._settings = json.dumps(settings_dict)

    @property
    def expected_action_details(self):
        """Get expected action details as Python dict"""
        try:
            return json.loads(self._expected_action_details_json) if self._expected_action_details_json else None
        except (TypeError, json.JSONDecodeError):
            return None # Return None if JSON is invalid
            
    @expected_action_details.setter
    def expected_action_details(self, details_dict):
        """Store expected action details as JSON string"""
        if details_dict is None:
            self._expected_action_details_json = None
        else:
            self._expected_action_details_json = json.dumps(details_dict)
    
    @property
    def community_chest_cards(self):
        """Get community chest cards as Python list"""
        try:
            return json.loads(self._community_chest_cards_json) if self._community_chest_cards_json else []
        except (TypeError, json.JSONDecodeError):
            return []
            
    @community_chest_cards.setter
    def community_chest_cards(self, cards_list):
        """Store community chest cards as JSON string"""
        self._community_chest_cards_json = json.dumps(cards_list)
    
    def to_dict(self):
        """Convert game state to dictionary for API responses"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'status': self.status, # Use status field
            'current_player_id': self.current_player_id,
            'player_order': [int(pid) for pid in self.player_order.split(',') if pid] if self.player_order else [],
            'current_lap': self.current_lap,
            'total_laps': self.total_laps,
            'turn_number': self.turn_number,
            'community_fund': self.community_fund,
            'community_fund_enabled': self.community_fund_enabled,
            'inflation_state': self.inflation_state,
            'inflation_factor': self.inflation_factor,
            'inflation_rate': self.inflation_rate,
            'base_interest_rate': self.base_interest_rate,
            'tax_rate': self.tax_rate,
            'difficulty': self.difficulty,
            'game_duration_minutes': self.calculate_duration_minutes(),
            'temporary_effects': self.temporary_effects,
            'police_activity': self.police_activity,
            'mode': self.mode,
            'settings': self.settings,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'turn_timer': self.turn_timer,
            'expected_action_type': self.expected_action_type, # Include expected action
            'expected_action_details': self.expected_action_details, # Include details
            'community_chest_cards': self.community_chest_cards
        }
    
    def calculate_duration_minutes(self):
        """Calculate game duration in minutes"""
        if not self.start_time: return 0
        now = datetime.utcnow()
        duration = now - self.start_time
        return int(duration.total_seconds() / 60)
    
    @classmethod
    def get_instance(cls):
        """Get the singleton game state instance"""
        # Assuming only one game runs at a time for simplicity with singleton pattern
        game_state = cls.query.first()
        if not game_state:
            # Need a default game_id if creating a new one
            import uuid
            game_state = cls(game_id=str(uuid.uuid4()))
            db.session.add(game_state)
            db.session.commit()
        return game_state
        
    def add_temporary_effect(self, effect):
        """Add a temporary effect to the game state"""
        effects = self.temporary_effects
        effects.append(effect)
        self.temporary_effects = effects
        # db.session.add(self) # No need to add, just modify
        # db.session.commit() # Commit should happen after the action that adds the effect
        
    def process_turn_end(self):
        """Process end of turn updates including temporary effects"""
        # THIS METHOD SEEMS REDUNDANT if turn ending is handled by GameController._internal_end_turn
        # Refactor or remove if logic is duplicated in GameController
        logger = logging.getLogger(__name__)
        logger.warning("GameState.process_turn_end() may be redundant, check GameController._internal_end_turn")
        # ... (rest of existing logic) ...
        pass
        
    def advance_lap(self):
        """Increment the lap counter and process lap-based mechanics"""
        # THIS METHOD SEEMS REDUNDANT if lap advancement is handled by GameController._internal_end_turn
        # Refactor or remove if logic is duplicated
        logger = logging.getLogger(__name__)
        logger.warning("GameState.advance_lap() may be redundant, check GameController._internal_end_turn")
        # ... (rest of existing logic) ...
        pass 
        
    def process_economic_cycle(self):
        """Process economic changes based on current lap"""
        # This might still be useful if called from GameController._internal_end_turn during lap change
        logger = logging.getLogger(__name__)
        
        try:
            from flask import current_app
            
            # Get or create EconomicCycleManager from app config
            economic_manager = current_app.config.get('economic_manager')
            
            if not economic_manager:
                logger.warning("EconomicCycleManager not found in app config, creating new instance")
                from src.models.economic_cycle_manager import EconomicCycleManager
                
                # Create with minimal dependencies - these may be unavailable at this point
                economic_manager = EconomicCycleManager()
                current_app.config['economic_manager'] = economic_manager
            
            # Update the economic cycle
            result = economic_manager.update_economic_cycle()
            
            if not result.get('success', False):
                logger.error(f"Error updating economic cycle: {result.get('error', 'Unknown error')}")
                return False
            
            logger.info(f"Economic cycle updated: {result['economic_state']} (inflation: {result['inflation_rate']:.2f}, interest: {result['base_interest_rate']:.2f})")
            
            # Potentially update property values based on new economic state
            if current_app.config.get('PROPERTY_VALUES_FOLLOW_ECONOMY', True):
                self._update_property_values(result['economic_state'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error in process_economic_cycle: {str(e)}", exc_info=True)
            return False
            
    def _update_property_values(self, economic_state):
        """Update property values based on economic state
        
        Args:
            economic_state: Current economic state
        """
        logger = logging.getLogger(__name__)
        
        try:
            from src.models.property import Property
            
            # Define economic multipliers for property values
            economic_multipliers = {
                "recession": 0.9,  # Properties lose value in recession
                "normal": 1.0,     # Normal state is baseline
                "growth": 1.1,     # Properties gain value in growth
                "boom": 1.25       # Properties gain significant value in boom
            }
            
            multiplier = economic_multipliers.get(economic_state, 1.0)
            
            # Don't apply full multiplier at once - gradual change
            adjustment_factor = 0.1  # Apply 10% of the difference
            effective_multiplier = 1.0 + (multiplier - 1.0) * adjustment_factor
            
            # Get all properties
            properties = Property.query.all()
            
            # Update property values
            for prop in properties:
                # Calculate new current price (with limits to prevent extreme changes)
                new_price = int(prop.current_price * effective_multiplier)
                
                # Ensure price doesn't go below base price or above 3x base price
                min_price = prop.price
                max_price = prop.price * 3
                
                prop.current_price = max(min_price, min(new_price, max_price))
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Updated property values based on economic state: {economic_state} (multiplier: {effective_multiplier:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating property values: {str(e)}", exc_info=True)
            
    def _update_police_activity(self):
        """Update police activity level randomly"""
        # This might still be useful if called from GameController._internal_end_turn during lap change
        # ... (rest of existing logic) ...
        pass
    
    def process_game_mode_lap_effects(self):
        """Process lap-based effects specific to the current game mode"""
        # This might still be useful if called from GameController._internal_end_turn during lap change
        # ... (rest of existing logic) ...
        pass

    def reset(self):
        """Reset the game state but keep the same ID"""
        logging.getLogger(__name__).info(f"Resetting GameState for game_id: {self.game_id}")
        
        # Generate a new UUID for the game
        import uuid
        self.game_id = str(uuid.uuid4())
        
        # Reset all game state fields to defaults
        self.current_player_id = None
        self.player_order = None
        self.current_lap = 0
        self.total_laps = 0
        self.community_fund = 0
        self.community_fund_enabled = True  # Make sure this is enabled by default
        self.inflation_state = 'stable'
        self.inflation_factor = 1.0
        self.inflation_rate = 0.03
        self.base_interest_rate = 0.05
        self.tax_rate = 0.1
        self.start_time = datetime.utcnow()
        self.started_at = None  # Reset the started_at timestamp
        self.end_time = None
        self.ended_at = None  # Also reset the ended_at timestamp for consistency
        self.status = 'setup'
        # Keep the difficulty setting
        # self.difficulty = 'normal'
        self._temporary_effects = '[]'
        self._community_chest_cards_json = None
        self.game_log = None
        self.last_event_lap = 0
        self.police_activity = 1.0
        self.turn_timer = None
        self.turn_number = 0
        # Keep the mode setting
        # self.mode = 'classic'
        self._settings = None
        self.expected_action_type = None
        self._expected_action_details_json = None
        
        # Don't commit here - let the caller handle the commit
        # This prevents issues with the caller's transaction management
        
    def refresh_from_db(self, game_id=None):
        """Refresh the instance from database to ensure it has the latest data
        
        Args:
            game_id: Optionally specify a game_id to get a specific game instead of the current one
            
        Returns:
            True if refresh was successful, False otherwise
        """
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Refreshing game state from database, game_id={game_id}")
            
            if game_id:
                # Get a specific game by its game_id
                db_instance = GameState.query.filter_by(game_id=game_id).first()
                if not db_instance:
                    logger.error(f"Game not found with game_id={game_id}")
                    return False
            else:
                # Get the current instance by its primary key
                db_instance = GameState.query.get(self.id)
                if not db_instance:
                    logger.error(f"Current game state not found in database with id={self.id}")
                    return False
            
            # Copy all attributes from database instance to this instance
            logger.info(f"Found game state in database, copying attributes. Mode: {db_instance.mode}")
            
            # Get all attributes from the database instance
            for column in self.__table__.columns:
                column_name = column.name
                if hasattr(db_instance, column_name):
                    current_value = getattr(self, column_name)
                    new_value = getattr(db_instance, column_name)
                    if current_value != new_value:
                        logger.debug(f"Updating {column_name}: {current_value} -> {new_value}")
                    setattr(self, column_name, new_value)
            
            logger.info(f"Game state refreshed successfully. Mode is now: {self.mode}")
            return True
        except Exception as e:
            logger.error(f"Error refreshing game state: {str(e)}", exc_info=True)
            return False

    def get_players(self):
        """Get all players in the current game
        
        Returns:
            List of player objects from the database
        """
        try:
            from src.models.player import Player
            
            if not self.player_order:
                return []
                
            player_ids = [int(pid) for pid in self.player_order.split(',') if pid]
            players = Player.query.filter(Player.id.in_(player_ids)).all()
            
            # Sort players according to player_order
            player_dict = {player.id: player for player in players}
            sorted_players = [player_dict.get(pid) for pid in player_ids if pid in player_dict]
            
            return sorted_players
        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting players: {str(e)}")
            return []

# End of GameState class 