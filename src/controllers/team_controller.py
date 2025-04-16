import logging
from src.models import db
from src.models.game_state import GameState
from src.models.property import Property
from src.models.player import Player
from src.models.team import Team
from src.models.game_mode import GameMode
from datetime import datetime

class TeamController:
    """Controller for managing team-based gameplay"""
    
    def __init__(self, socketio=None):
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
    
    def create_teams(self, game_id, team_configs):
        """Create teams for a game based on configuration"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode or not game_mode.team_based:
            return {"success": False, "error": "Game not in team mode"}
            
        try:
            teams = []
            for config in team_configs:
                team = Team(
                    game_id=game_id,
                    name=config['name'],
                    color=config['color'],
                    property_sharing_enabled=game_mode.team_property_sharing,
                    rent_immunity_enabled=game_mode.team_rent_immunity,
                    income_sharing_percent=game_mode.team_income_sharing
                )
                teams.append(team)
                db.session.add(team)
            
            db.session.commit()
            
            # Assign players to teams
            self._assign_players_to_teams(game_id, team_configs)
            
            return {
                "success": True,
                "teams": [team.to_dict() for team in teams]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating teams: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating teams: {str(e)}"
            }
    
    def _assign_players_to_teams(self, game_id, team_configs):
        """Assign players to teams based on configuration"""
        players = Player.query.filter_by(game_id=game_id).all()
        teams = Team.query.filter_by(game_id=game_id).all()
        
        # Create team map
        team_map = {team.name: team for team in teams}
        
        # Assign players
        for config in team_configs:
            team = team_map[config['name']]
            for player_id in config.get('player_ids', []):
                player = next((p for p in players if p.id == player_id), None)
                if player:
                    player.team_id = team.id
    
    def process_team_turn(self, game_id):
        """Process team-specific events at the end of each turn"""
        game_state: GameState = GameState.query.get(game_id)
        if not game_state:
            return {"success": False, "error": "Game not found"}
            
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode or not game_mode.team_based:
            return {"success": False, "error": "Game not in team mode"}
            
        try:
            teams = Team.query.filter_by(game_id=game_id, is_active=True).all()
            
            for team in teams:
                # Process income sharing
                if game_mode.team_income_sharing > 0:
                    team.process_income_sharing()
                
                # Update team score
                team.calculate_score()
                
                # Check team status
                team.check_team_status()
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Team turn processed successfully",
                "teams": [team.to_dict() for team in teams]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing team turn: {str(e)}")
            return {
                "success": False,
                "error": f"Error processing team turn: {str(e)}"
            }
    
    def get_team_status(self, game_id):
        """Get current status of all teams"""
        teams = Team.query.filter_by(game_id=game_id).all()
        
        return {
            "success": True,
            "teams": [team.to_dict() for team in teams]
        }
    
    def transfer_property(self, game_id, property_id, from_team_id, to_team_id):
        """Transfer property between teams"""
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode or not game_mode.team_property_sharing:
            return {"success": False, "error": "Property sharing not enabled"}
            
        try:
            property = Property.query.get(property_id)
            if not property:
                return {"success": False, "error": "Property not found"}
                
            from_team = Team.query.get(from_team_id)
            to_team = Team.query.get(to_team_id)
            
            if not from_team or not to_team:
                return {"success": False, "error": "Team not found"}
                
            if property.team_id != from_team_id:
                return {"success": False, "error": "Property not owned by source team"}
                
            property.team_id = to_team_id
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Property transferred from {from_team.name} to {to_team.name}"
            }
            
        except Exception as e:
            self.logger.error(f"Error transferring property: {str(e)}")
            return {
                "success": False,
                "error": f"Error transferring property: {str(e)}"
            }
    
    def check_team_win_condition(self, game_id):
        """Check if a team has won the game"""
        game_mode = GameMode.query.filter_by(game_id=game_id).first()
        if not game_mode or not game_mode.team_based:
            return {"success": False, "error": "Game not in team mode"}
            
        try:
            teams = Team.query.filter_by(game_id=game_id, is_active=True).all()
            
            # If only one team remains, they win
            if len(teams) == 1:
                return {
                    "game_over": True,
                    "winner": teams[0].id,
                    "winner_name": teams[0].name,
                    "reason": "Last team standing"
                }
            
            # Check for time limit win condition
            if game_mode.max_time_minutes:
                game_state: GameState = GameState.query.get(game_id)
                if game_state.end_time and datetime.now() >= game_state.end_time:
                    # Team with highest score wins
                    winning_team = max(teams, key=lambda t: t.score)
                    return {
                        "game_over": True,
                        "winner": winning_team.id,
                        "winner_name": winning_team.name,
                        "reason": "Highest team score at time limit"
                    }
            
            return {
                "game_over": False,
                "reason": "Game still in progress"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking team win condition: {str(e)}")
            return {
                "success": False,
                "error": f"Error checking team win condition: {str(e)}"
            } 