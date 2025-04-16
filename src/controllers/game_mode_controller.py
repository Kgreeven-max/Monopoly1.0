import json
import logging
from flask import current_app
from src.models import db
from src.models.game_mode import GameMode
from src.models.game_state import GameState
from src.models.player import Player
from src.models.property import Property
from datetime import datetime, timedelta
import random

class GameModeController:
    """Controller for managing different game modes in Pi-nopoly"""
    
    def __init__(self, socketio=None):
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
        
    def get_available_modes(self):
        """Return list of available game modes with descriptions"""
        return {
            "standard": [
                {
                    "id": "classic",
                    "name": "Classic Mode",
                    "description": "Traditional Pi-nopoly experience with standard rules",
                    "objective": "Accumulate wealth and drive opponents to bankruptcy",
                    "win_condition": "Last player remaining solvent",
                    "estimated_time": "1-3 hours",
                    "difficulty": "Standard"
                },
                {
                    "id": "speed",
                    "name": "Speed Mode",
                    "description": "Faster-paced version designed for shorter play sessions",
                    "objective": "Same as classic, but accelerated",
                    "win_condition": "Player with highest net worth after fixed time/turns",
                    "estimated_time": "30 minutes",
                    "difficulty": "Standard"
                },
                {
                    "id": "cooperative",
                    "name": "Co-op Mode",
                    "description": "Cooperative experience where players work together against the game system",
                    "objective": "Collectively develop all properties before economic collapse",
                    "win_condition": "All properties developed to at least level 2",
                    "estimated_time": "1 hour",
                    "difficulty": "Hard"
                }
            ],
            "specialty": [
                {
                    "id": "tycoon",
                    "name": "Tycoon Mode",
                    "description": "Development-focused mode emphasizing property improvement",
                    "objective": "Build the most impressive property empire",
                    "win_condition": "First to achieve specified development milestones",
                    "estimated_time": "1-2 hours",
                    "difficulty": "Medium"
                },
                {
                    "id": "market_crash",
                    "name": "Market Crash Mode",
                    "description": "Challenging mode centered around economic instability",
                    "objective": "Survive and thrive during economic turmoil",
                    "win_condition": "Highest net worth after market stabilizes",
                    "estimated_time": "1-2 hours",
                    "difficulty": "Hard"
                },
                {
                    "id": "team_battle",
                    "name": "Team Battle Mode",
                    "description": "Competitive mode pitting teams of players against each other",
                    "objective": "Establish team monopolies and bankrupt opposing teams",
                    "win_condition": "First team to bankrupt all opponents or highest team net worth after time limit",
                    "estimated_time": "1-2 hours",
                    "difficulty": "Medium"
                }
            ]
        }
    
    def initialize_game_mode(self, game_id, mode_id):
        """Initialize a game with the selected game mode settings"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        # Create game mode using factory method
        game_mode = GameMode.create_for_game(game_id, mode_id)
        
        # Save to database
        db.session.add(game_mode)
        db.session.commit()
        
        # Initialize game systems based on mode settings
        initialization_result = self._initialize_game_systems(game_id, game_mode)
        
        # Broadcast game mode selection
        if self.socketio:
            self.socketio.emit('game_mode_selected', {
                'game_id': game_id,
                'mode': mode_id,
                'settings': game_mode.to_dict()
            })
        
        return {
            "success": True,
            "mode": mode_id,
            "settings": game_mode.to_dict(),
            "initialization": initialization_result
        }
    
    def update_game_mode_settings(self, game_id, settings):
        """Update specific game mode settings"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
        
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode:
            return {"success": False, "error": "Game mode not found"}
        
        # Update standard fields
        for key, value in settings.items():
            if hasattr(game_mode, key) and key not in ['id', 'game_id', 'created_at', 'updated_at']:
                setattr(game_mode, key, value)
            elif key not in ['id', 'game_id', 'created_at', 'updated_at']:
                # Store in custom settings
                custom = game_mode.custom_settings
                custom[key] = value
                game_mode.custom_settings = custom
        
        # Save changes
        db.session.commit()
        
        # Apply changes to game systems
        self._update_game_systems(game_id, game_mode)
        
        # Broadcast settings update
        if self.socketio:
            self.socketio.emit('game_mode_updated', {
                'game_id': game_id,
                'settings': game_mode.to_dict()
            })
        
        return {
            "success": True,
            "mode": game_mode.mode_type,
            "settings": game_mode.to_dict()
        }
    
    def get_game_mode_settings(self, game_id):
        """Get current game mode settings"""
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode:
            return {"success": False, "error": "Game mode not found"}
        
        return {
            "success": True,
            "game_id": game_id,
            "mode": game_mode.mode_type,
            "settings": game_mode.to_dict()
        }
    
    def _initialize_game_systems(self, game_id, game_mode):
        """Initialize game systems based on game mode settings"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
        
        try:
            # Set starting cash for all players
            for player in game_state.players:
                player.cash = game_mode.starting_cash
            
            # Set game end time if applicable
            if game_mode.max_time_minutes:
                game_state.end_time = datetime.now() + timedelta(minutes=game_mode.max_time_minutes)
            
            # Set game state parameters
            game_state.mode = game_mode.mode_type
            game_state.inflation_factor = game_mode.inflation_factor
            game_state.event_frequency = game_mode.event_frequency
            game_state.turn_timer = game_mode.turn_timer_seconds
            
            # Configure property settings based on game mode
            self._configure_properties(game_id, game_mode)
            
            # Configure team settings if applicable
            if game_mode.team_based:
                self._configure_teams(game_id, game_mode)
            
            # Commit changes
            db.session.commit()
            
            # Return success
            return {
                "success": True,
                "message": f"Game initialized with {game_mode.mode_type} mode settings"
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing game systems: {str(e)}")
            return {
                "success": False,
                "error": f"Error initializing game systems: {str(e)}"
            }
    
    def _update_game_systems(self, game_id, game_mode):
        """Update game systems based on changed game mode settings"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
        
        try:
            # Update game state parameters
            game_state.mode = game_mode.mode_type
            game_state.inflation_factor = game_mode.inflation_factor
            game_state.event_frequency = game_mode.event_frequency
            game_state.turn_timer = game_mode.turn_timer_seconds
            
            # Update property settings if needed
            if game_mode.mode_type in ["tycoon", "market_crash"]:
                self._configure_properties(game_id, game_mode)
            
            # Commit changes
            db.session.commit()
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Error updating game systems: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _configure_properties(self, game_id, game_mode):
        """Configure properties based on game mode settings"""
        properties = Property.query.filter_by(game_id=game_id).all()
        
        # Apply mode-specific property configuration
        for prop in properties:
            # Market crash mode starts with reduced property values
            if game_mode.mode_type == "market_crash":
                # Apply initial market crash settings
                prop.current_price = int(prop.base_price * game_mode.inflation_factor)
                prop.current_rent = int(prop.base_rent * game_mode.inflation_factor)
                
                # Add market crash specific properties
                prop.market_crash_data = {
                    "original_price": prop.base_price,
                    "original_rent": prop.base_rent,
                    "crash_count": 0,
                    "recovery_turns": 0,
                    "in_crash": False
                }
            
            # Tycoon mode might have higher property values
            elif game_mode.mode_type == "tycoon":
                # Get advanced development levels from custom settings
                dev_levels = game_mode.custom_settings.get("development_levels", 5)
                prop.max_development_level = dev_levels
            
        db.session.commit()
    
    def _configure_teams(self, game_id, game_mode):
        """Configure team settings for team-based game modes"""
        # This would be implemented when team model is created
        # For now, just log that teams would be configured
        self.logger.info(f"Team configuration for game {game_id} with mode {game_mode.mode_type}")
        
        # In future: Set up team assignments, sharing rules, etc.
        pass
    
    def check_win_condition(self, game_id):
        """Check if win condition is met for the current game mode"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
        
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode:
            return {"success": False, "error": "Game mode not found"}
        
        try:
            # Default result - no winner yet
            result = {
                "game_over": False,
                "winner": None,
                "reason": "Game still in progress"
            }
            
            # Check win conditions based on mode
            if game_mode.win_condition == "last_standing":
                # Classic mode: last player standing wins
                active_players = Player.query.filter_by(game_id=game_id, status="active").count()
                if active_players == 1:
                    winner = Player.query.filter_by(game_id=game_id, status="active").first()
                    result = {
                        "game_over": True,
                        "winner": winner.id,
                        "winner_name": winner.name,
                        "reason": "Last player standing"
                    }
            
            elif game_mode.win_condition == "net_worth":
                # Speed mode: highest net worth after time/turn limit
                if game_state.turn_number >= game_mode.max_turns or \
                   (game_state.end_time and datetime.now() >= game_state.end_time):
                    # Find player with highest net worth
                    players = Player.query.filter_by(game_id=game_id, status="active").all()
                    if players:
                        # Calculate each player's net worth
                        player_worths = {}
                        for player in players:
                            net_worth = player.cash
                            # Add property values
                            for prop in player.properties:
                                net_worth += prop.current_price
                                if prop.development_level > 0:
                                    net_worth += prop.development_level * (prop.current_price * 0.5)
                            player_worths[player.id] = net_worth
                        
                        # Find highest
                        highest_id = max(player_worths.keys(), key=lambda x: player_worths[x])
                        winner = Player.query.get(highest_id)
                        
                        result = {
                            "game_over": True,
                            "winner": winner.id,
                            "winner_name": winner.name,
                            "net_worth": player_worths[winner.id],
                            "reason": "Highest net worth at game end"
                        }
            
            elif game_mode.win_condition == "property_development":
                # Cooperative or Tycoon mode: development goals achieved
                if game_mode.mode_type == "cooperative":
                    # Check if all properties are developed to at least level 2
                    properties = Property.query.filter_by(game_id=game_id).all()
                    all_developed = all(p.development_level >= 2 for p in properties)
                    
                    if all_developed:
                        result = {
                            "game_over": True,
                            "winner": "team",  # Cooperative win
                            "reason": "All properties developed to required level"
                        }
                
                elif game_mode.mode_type == "tycoon":
                    # Check for development milestones
                    milestones = game_mode.custom_settings.get("development_milestones", {})
                    gold_threshold = milestones.get("gold", 3)
                    
                    # Check if any player has reached the gold milestone
                    players = Player.query.filter_by(game_id=game_id, status="active").all()
                    for player in players:
                        # Count properties at level 5
                        level5_count = Property.query.filter_by(
                            owner_id=player.id, 
                            development_level=5
                        ).count()
                        
                        if level5_count >= gold_threshold:
                            result = {
                                "game_over": True,
                                "winner": player.id,
                                "winner_name": player.name,
                                "reason": f"Achieved gold development milestone ({gold_threshold} properties at level 5)"
                            }
                            break
            
            elif game_mode.win_condition == "team_domination":
                # Team Battle mode: one team left or highest team net worth
                # This would be implemented when team model is created
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error checking win condition: {str(e)}")
            return {
                "success": False,
                "error": f"Error checking win condition: {str(e)}"
            }

    def process_market_crash_events(self, game_id):
        """Process market crash events for the current turn"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode or game_mode.mode_type != "market_crash":
            return {"success": False, "error": "Not in market crash mode"}
            
        try:
            properties = Property.query.filter_by(game_id=game_id).all()
            crash_settings = game_mode.custom_settings
            crash_events = crash_settings.get("crash_events", {})
            
            # Process each property
            for prop in properties:
                crash_data = prop.market_crash_data
                
                # Check for new crash event
                if not crash_data["in_crash"] and random.random() < crash_events["frequency"]:
                    crash_data["in_crash"] = True
                    crash_data["crash_count"] += 1
                    crash_data["recovery_turns"] = crash_events["duration"]
                    
                    # Apply crash impact
                    crash_impact = crash_events["impact"]
                    prop.current_price = int(prop.current_price * (1 - crash_impact))
                    prop.current_rent = int(prop.current_rent * (1 - crash_impact))
                
                # Process recovery if in crash
                elif crash_data["in_crash"]:
                    crash_data["recovery_turns"] -= 1
                    if crash_data["recovery_turns"] <= 0:
                        crash_data["in_crash"] = False
                        # Gradual recovery
                        recovery_rate = crash_settings.get("recovery_rate", 0.1)
                        prop.current_price = int(prop.current_price * (1 + recovery_rate))
                        prop.current_rent = int(prop.current_rent * (1 + recovery_rate))
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Market crash events processed",
                "properties_updated": len(properties)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing market crash events: {str(e)}")
            return {
                "success": False,
                "error": f"Error processing market crash events: {str(e)}"
            }

    def apply_win_conditions(self, game_id):
        """Check and apply game mode specific win conditions"""
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode:
            return {"success": False, "error": "Game mode not set"}
            
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        if game_state.is_over:
            # Check for time limit
            if game_mode.max_time_minutes:
                start_time = game_state.start_time
                if start_time and (datetime.now() - start_time).total_seconds() / 60 >= game_mode.max_time_minutes:
                    winner = self._determine_winner_by_score(game_id)
                    game_state.end_game(winner_id=winner['id'] if winner else None,
                                      reason=f"Time limit of {game_mode.max_time_minutes} minutes reached")
                    return {"success": True, "game_over": True, "winner": winner, "reason": "Time limit"}
            
            # Check for lap limit
            if game_mode.max_laps and game_state.current_lap >= game_mode.max_laps:
                winner = self._determine_winner_by_score(game_id)
                game_state.end_game(winner_id=winner['id'] if winner else None, 
                                  reason=f"Lap limit of {game_mode.max_laps} reached")
                return {"success": True, "game_over": True, "winner": winner, "reason": "Lap limit"}
            
            # Check for score limit
            # ... existing code ...

    def apply_turn_based_effects(self, game_id):
        """Apply game mode effects that occur each turn"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        # ... existing code ...

    def apply_lap_based_effects(self, game_id):
        """Apply game mode effects that occur each lap"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        # ... existing code ... 