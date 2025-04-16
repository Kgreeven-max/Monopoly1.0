# src/models/bot_events/bot_challenge.py

import random
import logging
from .base_event import BotEvent
from .. import db # Relative import
from ..player import Player # Relative import
from ..transaction import Transaction # Relative import

logger = logging.getLogger(__name__)

class BotChallenge(BotEvent):
    """Bot challenges other players to a mini-game"""
    
    def __init__(self, game_state, player_id):
        self.game_state = game_state
        self.bot_id = player_id
        self.bot = Player.query.get(player_id)
        self.challenge_type = None
        self.reward = {}

        if not self.bot:
            logger.warning(f"BotChallenge initiated for non-existent player_id: {player_id}")
            return

        self.challenge_type = self._select_challenge_type()
        self.reward = self._determine_reward()
    
    @staticmethod
    def is_valid(game_state, player_id):
        """Check if this event is valid in the current game state"""
        # Need human players to challenge
        human_players = Player.query.filter(
            Player.in_game == True,
            Player.is_bot == False
        ).count()
        
        return human_players > 0
    
    def _select_challenge_type(self):
        """Select a type of challenge to issue"""
        challenges = [
            "dice_prediction",  # Predict total of next dice roll
            "property_quiz",    # Quiz about properties on the board
            "price_guess",      # Guess the exact price of a property
            "quick_calculation" # Simple math problem
        ]
        
        return random.choice(challenges)
    
    def _determine_reward(self):
        """Determine the reward for completing the challenge"""
        # Base reward is cash
        base_amount = random.randint(5, 15) * 10  # $50-$150
        
        # There's a small chance of a more valuable reward
        if random.random() < 0.2:  # 20% chance
            base_amount *= 2  # Double the reward
        
        return {
            "type": "cash",
            "amount": base_amount
        }
    
    def get_event_data(self):
        """Return data about this event"""
        if not self.bot or not self.challenge_type:
             return {"success": False, "message": "Invalid bot challenge event."}

        challenge_names = {
            "dice_prediction": "Dice Prediction",
            "property_quiz": "Property Quiz",
            "price_guess": "Price Guessing",
            "quick_calculation": "Quick Math"
        }
        
        challenge_display = challenge_names.get(self.challenge_type, self.challenge_type)
        
        return {
            "event_type": "bot_challenge",
            "success": True,
            "bot_id": self.bot_id,
            "bot_name": self.bot.username,
            "challenge_type": self.challenge_type,
            "reward": self.reward,
            "message": f"{self.bot.username} challenges everyone to a {challenge_display} contest! Win ${self.reward.get('amount', 0)} if you succeed!"
        }
    
    def execute(self, winner_id=None):
        """Execute the challenge result"""
        if not self.bot:
             return {"success": False, "message": "Challenge event invalid (no bot)."}

        if not winner_id:
            return {
                "success": True,
                "message": f"No one completed {self.bot.username}'s challenge."
            }
        
        try:
            # Find the winning player
            winner = Player.query.get(winner_id)
            if not winner:
                return {
                    "success": False,
                    "message": "Winner not found."
                }
            
            # Award the prize
            reward_amount = self.reward.get("amount", 0)
            if self.reward.get("type") == "cash" and reward_amount > 0:
                winner.cash += reward_amount
                
                # Record transaction
                transaction = Transaction(
                    from_player_id=self.bot_id,
                    to_player_id=winner_id,
                    amount=reward_amount,
                    transaction_type="challenge_reward",
                    description=f"Challenge reward from {self.bot.username}"
                )
                db.session.add(transaction)
            else:
                 # If reward type is not cash or amount is zero, log it but don't fail
                 logger.warning(f"Invalid reward type or amount for BotChallenge: {self.reward}")
                 return {"success": True, "message": f"{winner.username} completed the challenge, but there was no reward."}

            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"{winner.username} won {self.bot.username}'s challenge and received ${reward_amount}!"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing challenge reward: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Challenge reward failed due to an error: {str(e)}"
            } 