import logging
import random
from datetime import datetime, timedelta
from src.models import db
from src.models.player import Player
from src.models.property import Property
from src.models.game_state import GameState

logger = logging.getLogger(__name__)

class AdaptiveDifficultyController:
    """Controls the adaptive difficulty system for AI players
    
    This system monitors the performance of human players compared to bot players
    and dynamically adjusts bot difficulty to maintain competitive balance.
    """
    
    def __init__(self, socketio=None):
        """Initialize the adaptive difficulty controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time notifications
        """
        self.socketio = socketio
        self.last_assessment_time = None
        self.difficulty_adjustments = {
            "easy": {"decision_accuracy": -0.15, "value_estimation_error": 0.10, "planning_horizon": -1},
            "medium": {"decision_accuracy": 0.0, "value_estimation_error": 0.0, "planning_horizon": 0},
            "hard": {"decision_accuracy": 0.10, "value_estimation_error": -0.05, "planning_horizon": 1}
        }
        
    def assess_game_balance(self):
        """Assess the current game balance between human and bot players
        
        Returns:
            dict: Assessment results with performance metrics
        """
        # Check if enough time has passed since last assessment (at least 5 minutes)
        current_time = datetime.now()
        if (self.last_assessment_time and 
                (current_time - self.last_assessment_time) < timedelta(minutes=5)):
            return {"success": False, "message": "Assessment performed too recently"}
            
        self.last_assessment_time = current_time
        
        # Get all active players
        human_players = Player.query.filter_by(is_bot=False, in_game=True).all()
        bot_players = Player.query.filter_by(is_bot=True, in_game=True).all()
        
        if not human_players or not bot_players:
            return {"success": False, "message": "Not enough players for assessment"}
            
        # Calculate performance metrics
        human_metrics = self._calculate_player_metrics(human_players)
        bot_metrics = self._calculate_player_metrics(bot_players)
        
        # Calculate performance ratio (human:bot)
        net_worth_ratio = human_metrics['avg_net_worth'] / max(1, bot_metrics['avg_net_worth'])
        property_ratio = human_metrics['avg_properties'] / max(1, bot_metrics['avg_properties'])
        cash_ratio = human_metrics['avg_cash'] / max(1, bot_metrics['avg_cash'])
        
        # Calculate overall balance score
        # 1.0 = perfectly balanced, <1.0 = bots ahead, >1.0 = humans ahead
        balance_score = (net_worth_ratio * 0.6) + (property_ratio * 0.3) + (cash_ratio * 0.1)
        
        # Determine if adjustment is needed
        needs_adjustment = False
        adjustment_direction = None
        
        if balance_score < 0.7:
            # Bots are significantly ahead - make them easier
            needs_adjustment = True
            adjustment_direction = "easier"
        elif balance_score > 1.3:
            # Humans are significantly ahead - make bots harder
            needs_adjustment = True
            adjustment_direction = "harder"
            
        assessment = {
            "success": True,
            "timestamp": current_time.isoformat(),
            "human_metrics": human_metrics,
            "bot_metrics": bot_metrics,
            "balance_score": balance_score,
            "needs_adjustment": needs_adjustment,
            "adjustment_direction": adjustment_direction
        }
        
        # Log the assessment
        logger.info(f"Game balance assessment: {assessment}")
        
        return assessment
        
    def adjust_difficulty(self, adjustment_direction):
        """Adjust bot difficulty based on the assessment
        
        Args:
            adjustment_direction: 'easier' or 'harder'
            
        Returns:
            dict: Results of the adjustment
        """
        if adjustment_direction not in ['easier', 'harder']:
            return {"success": False, "error": "Invalid adjustment direction"}
            
        # Get all active bot players
        bot_players = Player.query.filter_by(is_bot=True, in_game=True).all()
        
        if not bot_players:
            return {"success": False, "error": "No bot players to adjust"}
            
        # Get active bots dictionary
        from src.controllers.bot_controller import active_bots
        
        adjustments_made = 0
        
        for bot_player in bot_players:
            if bot_player.id not in active_bots:
                continue
                
            bot = active_bots[bot_player.id]
            current_difficulty = bot.difficulty
            
            # Determine new difficulty level
            new_difficulty = self._calculate_new_difficulty(current_difficulty, adjustment_direction)
            
            if new_difficulty != current_difficulty:
                # Update bot difficulty
                bot.difficulty = new_difficulty
                
                # Apply difficulty parameter adjustments
                self._apply_difficulty_adjustments(bot)
                
                adjustments_made += 1
                
                # Log the change
                logger.info(f"Adjusted bot {bot_player.username} difficulty from {current_difficulty} to {new_difficulty}")
                
                # Notify admin if socketio is available
                if self.socketio:
                    self.socketio.emit('bot_difficulty_adjusted', {
                        'bot_id': bot_player.id,
                        'bot_name': bot_player.username,
                        'old_difficulty': current_difficulty,
                        'new_difficulty': new_difficulty,
                        'reason': f"Game balance adjustment: {adjustment_direction}"
                    }, room='admin')
        
        return {
            "success": True,
            "adjustment_direction": adjustment_direction,
            "adjustments_made": adjustments_made
        }
        
    def _calculate_player_metrics(self, players):
        """Calculate performance metrics for a group of players
        
        Args:
            players: List of Player objects
            
        Returns:
            dict: Calculated metrics
        """
        if not players:
            return {
                'avg_net_worth': 0,
                'avg_properties': 0,
                'avg_cash': 0,
                'player_count': 0
            }
            
        total_net_worth = 0
        total_properties = 0
        total_cash = 0
        
        for player in players:
            # Calculate net worth
            net_worth = player.cash
            
            # Add property values
            properties = Property.query.filter_by(owner_id=player.id).all()
            property_value = sum(p.current_price for p in properties)
            net_worth += property_value
            
            # Add to totals
            total_net_worth += net_worth
            total_properties += len(properties)
            total_cash += player.cash
            
        player_count = len(players)
        
        return {
            'avg_net_worth': total_net_worth / player_count,
            'avg_properties': total_properties / player_count,
            'avg_cash': total_cash / player_count,
            'player_count': player_count
        }
        
    def _calculate_new_difficulty(self, current_difficulty, adjustment_direction):
        """Calculate a new difficulty level based on the current one and adjustment direction
        
        Args:
            current_difficulty: Current difficulty level ('easy', 'medium', 'hard')
            adjustment_direction: Direction to adjust ('easier' or 'harder')
            
        Returns:
            str: New difficulty level
        """
        difficulties = ['easy', 'medium', 'hard']
        current_index = difficulties.index(current_difficulty)
        
        if adjustment_direction == 'easier':
            # Move toward easier difficulty
            new_index = max(0, current_index - 1)
        else:  # harder
            # Move toward harder difficulty
            new_index = min(len(difficulties) - 1, current_index + 1)
            
        return difficulties[new_index]
        
    def _apply_difficulty_adjustments(self, bot):
        """Apply difficulty-based adjustments to bot parameters
        
        Args:
            bot: Bot object to adjust
        """
        # Apply standard difficulty parameters
        if bot.difficulty == 'easy':
            bot.decision_accuracy = 0.7
            bot.value_estimation_error = 0.2
            bot.planning_horizon = 2
        elif bot.difficulty == 'medium':
            bot.decision_accuracy = 0.85
            bot.value_estimation_error = 0.1
            bot.planning_horizon = 4
        else:  # hard
            bot.decision_accuracy = 0.95
            bot.value_estimation_error = 0.05
            bot.planning_horizon = 6
            
        # Apply bot-type specific modifiers
        bot_type = type(bot).__name__
        
        if bot_type == 'ConservativeBot':
            bot.risk_tolerance *= 0.7
        elif bot_type == 'AggressiveBot':
            bot.risk_tolerance *= 1.3
        elif bot_type == 'OpportunisticBot':
            bot.risk_tolerance = min(bot.risk_tolerance * 1.3, 0.9)
            bot.planning_horizon = max(1, bot.planning_horizon - 1)
        elif bot_type == 'SharkBot':
            bot.risk_tolerance = min(bot.risk_tolerance * 1.4, 0.95)
            bot.value_estimation_error *= 0.7
        elif bot_type == 'InvestorBot':
            bot.value_estimation_error *= 0.6
            bot.planning_horizon += 2 