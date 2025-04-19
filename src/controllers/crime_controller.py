import logging
import random
from datetime import datetime, timedelta
from flask_socketio import emit
from src.models import db
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState
from src.models.crime import Crime, Theft, PropertyVandalism, RentEvasion, Forgery, TaxEvasion

logger = logging.getLogger(__name__)

class CrimeController:
    """Controller for the crime system that manages criminal activities in the game"""
    
    def __init__(self, socketio=None):
        """Initialize the crime controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time notifications
        """
        self.socketio = socketio
        self.last_police_patrol = datetime.now()
        # Default settings
        self.crime_probability = 0.2  # 20% chance of a player committing a crime
        self.police_patrol_enabled = True  # Enable police patrols
        self.police_patrol_interval = 45  # Minutes between police patrols
        self.police_catch_probability = 0.3  # 30% base chance to catch criminals
        self.jail_turns = 3  # Default jail time in turns
        self.fine_multiplier = 1.5  # Multiplier for fines
        # Crime types that are enabled
        self.crime_types = ['theft', 'property_vandalism', 'rent_evasion', 'forgery', 'tax_evasion']
        
        # Try to load settings from configuration if available
        self._load_settings_from_config()
        
    def commit_crime(self, player_id, crime_type, **params):
        """Commit a crime
        
        Args:
            player_id: ID of the player committing the crime
            crime_type: Type of crime to commit
            **params: Additional parameters for the specific crime type
            
        Returns:
            dict: Result of the crime
        """
        try:
            # Get player
            player = Player.query.get(player_id)
            if not player or not player.in_game:
                return {
                    "success": False,
                    "message": "Player not found or not in game"
                }
                
            # Check if player is in jail
            if player.in_jail:
                return {
                    "success": False,
                    "message": "Cannot commit crimes while in jail"
                }
                
            # Call the player's crime method
            crime = player.commit_crime(crime_type, **params)
            
            # If socketio is available, send events
            if self.socketio:
                # If crime was detected, announce it
                if crime.detected:
                    self._broadcast_crime_detection(crime)
                else:
                    # Only notify player of success privately
                    self._notify_player_of_crime(crime)
                    
            # Return results
            return {
                "success": True,
                "crime": crime.to_dict(),
                "detected": crime.detected,
                "message": crime.details
            }
                
        except Exception as e:
            logger.error(f"Error committing crime: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def get_player_crimes(self, player_id):
        """Get a player's crime history
        
        Args:
            player_id: ID of the player
            
        Returns:
            dict: Player's crime history
        """
        try:
            # Get player
            player = Player.query.get(player_id)
            if not player:
                return {
                    "success": False,
                    "message": "Player not found"
                }
                
            # Get crimes (only detected ones for API safety)
            crimes = Crime.query.filter_by(player_id=player_id, detected=True).all()
            
            return {
                "success": True,
                "player_id": player_id,
                "player_name": player.username,
                "criminal_record": player.criminal_record,
                "crimes": [crime.to_dict() for crime in crimes]
            }
                
        except Exception as e:
            logger.error(f"Error getting player crimes: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def check_for_police_patrol(self):
        """Periodically check for random police patrol that might detect recent crimes
        
        Returns:
            dict: Result of the police patrol
        """
        # Check if enough time has passed since last patrol (30 minutes minimum)
        current_time = datetime.now()
        if (current_time - self.last_police_patrol) < timedelta(minutes=30):
            return {
                "success": False,
                "message": "Too soon for another police patrol"
            }
            
        self.last_police_patrol = current_time
        
        # Get game state
        game_state = GameState.query.first()
        if not game_state:
            return {
                "success": False,
                "message": "Game state not found"
            }
            
        # Get recent undetected crimes from the past 24 hours
        recent_crimes = Crime.query.filter_by(detected=False)\
            .filter(Crime.timestamp > (current_time - timedelta(hours=24)))\
            .all()
            
        if not recent_crimes:
            return {
                "success": True,
                "message": "Police patrol found no suspicious activity",
                "detected_crimes": 0
            }
            
        # Determine how many crimes to detect based on difficulty
        detection_count = 0
        detection_chances = {
            'easy': 0.4,    # 40% chance per crime
            'normal': 0.3,  # 30% chance
            'hard': 0.2     # 20% chance
        }
        
        detected_crimes = []
        
        # Check each crime
        for crime in recent_crimes:
            # Get the chance based on difficulty
            detection_chance = detection_chances.get(game_state.difficulty, 0.3)
            
            # Roll for detection
            if random.random() < detection_chance:
                # Crime detected by patrol
                crime.detected = True
                crime.details += " (Detected by police patrol)"
                db.session.add(crime)
                
                # Update player's criminal record
                player = Player.query.get(crime.player_id)
                if player:
                    player.criminal_record += 1
                    player.community_standing = max(0, player.community_standing - 5)
                    db.session.add(player)
                
                # Apply consequences
                crime.apply_consequences()
                
                # Track for notifications
                detected_crimes.append(crime)
                detection_count += 1
        
        db.session.commit()
        
        # Send notifications for detected crimes
        if self.socketio and detected_crimes:
            for crime in detected_crimes:
                self._broadcast_crime_detection(crime, is_patrol=True)
        
        return {
            "success": True,
            "message": f"Police patrol completed with {detection_count} crimes detected",
            "detected_crimes": detection_count
        }
    
    def _broadcast_crime_detection(self, crime, is_patrol=False):
        """Broadcast crime detection to all players
        
        Args:
            crime: The crime that was detected
            is_patrol: Whether the detection was from a patrol
        """
        if not self.socketio:
            return
            
        # Get player name
        player = Player.query.get(crime.player_id)
        player_name = player.username if player else f"Player {crime.player_id}"
        
        # Create notification data
        notification_data = {
            'event_type': 'crime_detected',
            'crime_type': crime.crime_type,
            'player_id': crime.player_id,
            'player_name': player_name,
            'detected_by': 'police_patrol' if is_patrol else 'immediate',
            'timestamp': datetime.now().isoformat(),
            'message': f"{player_name} was caught committing {crime.crime_type.replace('_', ' ')}!",
            'details': crime.details
        }
        
        # Broadcast to all players
        self.socketio.emit('game_event', notification_data)
        
        # Log the event
        logger.info(f"Crime detected: {crime.crime_type} by {player_name}")
    
    def _notify_player_of_crime(self, crime):
        """Privately notify the player of their successful crime
        
        Args:
            crime: The successful crime
        """
        if not self.socketio:
            return
            
        # Get player
        player = Player.query.get(crime.player_id)
        if not player:
            return
            
        # Create notification data
        notification_data = {
            'event_type': 'crime_success',
            'crime_type': crime.crime_type,
            'timestamp': datetime.now().isoformat(),
            'message': f"Your {crime.crime_type.replace('_', ' ')} was successful!",
            'details': crime.details
        }
        
        # Send private notification to the player
        if hasattr(player, 'socket_id') and player.socket_id:
            self.socketio.emit('player_notification', notification_data, room=player.socket_id)
            
    def get_crime_statistics(self):
        """Get overall crime statistics
        
        Returns:
            dict: Crime statistics
        """
        try:
            # Get counts of different crime types
            total_crimes = Crime.query.count()
            detected_crimes = Crime.query.filter_by(detected=True).count()
            successful_crimes = Crime.query.filter_by(success=True, detected=False).count()
            
            # Count by crime type
            theft_count = Crime.query.filter_by(crime_type='theft').count()
            vandalism_count = Crime.query.filter_by(crime_type='property_vandalism').count()
            rent_evasion_count = Crime.query.filter_by(crime_type='rent_evasion').count()
            forgery_count = Crime.query.filter_by(crime_type='forgery').count()
            tax_evasion_count = Crime.query.filter_by(crime_type='tax_evasion').count()
            
            # Players with criminal records
            criminals = Player.query.filter(Player.criminal_record > 0).count()
            
            return {
                "success": True,
                "total_crimes": total_crimes,
                "detected_crimes": detected_crimes,
                "successful_crimes": successful_crimes,
                "detection_rate": detected_crimes / total_crimes if total_crimes > 0 else 0,
                "crime_types": {
                    "theft": theft_count,
                    "property_vandalism": vandalism_count,
                    "rent_evasion": rent_evasion_count,
                    "forgery": forgery_count,
                    "tax_evasion": tax_evasion_count
                },
                "criminals": criminals
            }
                
        except Exception as e:
            logger.error(f"Error getting crime statistics: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def process_property_damage_repair(self, effect):
        """Process property damage repair from the game state effects
        
        Args:
            effect: The property damage repair effect
        """
        try:
            # Get property
            property_id = effect.get('property_id')
            property = Property.query.get(property_id)
            
            if not property:
                return False
                
            # Restore property value and clear damage
            property.current_price = effect.get('original_price')
            property.damage_amount = 0
            
            db.session.add(property)
            db.session.commit()
            
            # Notify property owner if socketio is available
            if self.socketio and property.owner_id:
                owner = Player.query.get(property.owner_id)
                if owner:
                    notification = {
                        'event_type': 'property_repaired',
                        'property_id': property.id,
                        'property_name': property.name,
                        'message': f"Repairs on {property.name} have been completed!"
                    }
                    
                    if hasattr(owner, 'socket_id') and owner.socket_id:
                        self.socketio.emit('player_notification', notification, room=owner.socket_id)
                    else:
                        self.socketio.emit('player_notification', notification)
            
            return True
                
        except Exception as e:
            logger.error(f"Error processing property damage repair: {str(e)}")
            return False
            
    def get_settings(self):
        """Get current crime system settings
        
        Returns:
            dict: Current crime settings
        """
        return {
            "crime_probability": self.crime_probability,
            "police_patrol_enabled": self.police_patrol_enabled,
            "police_patrol_interval": self.police_patrol_interval,
            "police_catch_probability": self.police_catch_probability,
            "jail_turns": self.jail_turns,
            "fine_multiplier": self.fine_multiplier,
            "crime_types": self.crime_types,
            "last_police_patrol": self.last_police_patrol.isoformat() if self.last_police_patrol else None
        }
    
    def save_settings(self):
        """Save current settings to persistent storage if available
        
        Returns:
            bool: Whether settings were successfully saved
        """
        try:
            # Try to save to Flask app config
            from flask import current_app
            if current_app:
                # Save selected settings to app config for persistence across restarts
                config = current_app.config
                config['POLICE_PATROL_ENABLED'] = self.police_patrol_enabled
                config['POLICE_PATROL_INTERVAL'] = self.police_patrol_interval
                
                # Log the update
                logger.info(f"Saved crime controller settings to app config")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving crime controller settings: {str(e)}")
            return False
    
    def _load_settings_from_config(self):
        """Load settings from Flask app config if available"""
        try:
            from flask import current_app
            if current_app:
                config = current_app.config
                # Load settings with fallbacks
                self.police_patrol_enabled = config.get('POLICE_PATROL_ENABLED', self.police_patrol_enabled)
                self.police_patrol_interval = config.get('POLICE_PATROL_INTERVAL', self.police_patrol_interval)
                
                logger.debug(f"Loaded crime controller settings from app config")
        except Exception as e:
            logger.warning(f"Could not load crime controller settings from config: {str(e)}") 