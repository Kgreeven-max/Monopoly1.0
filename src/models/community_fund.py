from datetime import datetime
import logging
from typing import Dict, List, Optional

from src.models import db
from src.models.game_state import GameState

# Set up logger
logger = logging.getLogger(__name__)

class CommunityFund:
    """Class to manage the community fund (public money pool)"""
    
    def __init__(self, socketio=None, game_state=None):
        """Initialize community fund
        
        Args:
            socketio: SocketIO instance for broadcasting events
            game_state: GameState instance
        """
        self.socketio = socketio
        self.game_state = game_state or GameState.query.first()
        self._funds = self.game_state.settings.get("community_fund", 0) if self.game_state else 0
    
    @property
    def funds(self) -> int:
        """Get the current community fund amount"""
        return self._funds
    
    def add_funds(self, amount: int, reason: str = "General contribution") -> int:
        """Add funds to the community fund
        
        Args:
            amount: Amount to add
            reason: Reason for adding funds
            
        Returns:
            New fund balance
        """
        if amount <= 0:
            return self._funds
            
        # Update funds
        self._funds += amount
        
        # Update game state
        if self.game_state:
            settings = self.game_state.settings
            settings["community_fund"] = self._funds
            self.game_state.settings = settings
            db.session.add(self.game_state)
            db.session.commit()
            
        # Log transaction
        logger.info(f"Added ${amount} to community fund ({reason}). New balance: ${self._funds}")
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('community_fund_update', {
                "action": "add",
                "amount": amount,
                "reason": reason,
                "balance": self._funds,
                "timestamp": datetime.now().isoformat()
            })
            
        return self._funds
    
    def withdraw_funds(self, amount: int, reason: str = "General withdrawal") -> Dict:
        """Withdraw funds from the community fund
        
        Args:
            amount: Amount to withdraw
            reason: Reason for withdrawing funds
            
        Returns:
            Dictionary with withdrawal results
        """
        # Check if enough funds available
        if amount > self._funds:
            return {
                "success": False,
                "error": f"Not enough funds. Requested: ${amount}, Available: ${self._funds}",
                "available": self._funds
            }
            
        if amount <= 0:
            return {
                "success": False,
                "error": "Invalid withdrawal amount"
            }
            
        # Update funds
        self._funds -= amount
        
        # Update game state
        if self.game_state:
            settings = self.game_state.settings
            settings["community_fund"] = self._funds
            self.game_state.settings = settings
            db.session.add(self.game_state)
            db.session.commit()
            
        # Log transaction
        logger.info(f"Withdrew ${amount} from community fund ({reason}). New balance: ${self._funds}")
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('community_fund_update', {
                "action": "withdraw",
                "amount": amount,
                "reason": reason,
                "balance": self._funds,
                "timestamp": datetime.now().isoformat()
            })
            
        return {
            "success": True,
            "amount": amount,
            "reason": reason,
            "balance": self._funds
        }
    
    def clear_funds(self, reason: str = "Fund cleared") -> int:
        """Clear all funds from the community fund
        
        Args:
            reason: Reason for clearing funds
            
        Returns:
            Amount cleared
        """
        # Store current amount for return
        cleared_amount = self._funds
        
        # Reset funds
        self._funds = 0
        
        # Update game state
        if self.game_state:
            settings = self.game_state.settings
            settings["community_fund"] = 0
            self.game_state.settings = settings
            db.session.add(self.game_state)
            db.session.commit()
            
        # Log transaction
        logger.info(f"Cleared community fund (${cleared_amount}) ({reason}).")
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('community_fund_update', {
                "action": "clear",
                "amount": cleared_amount,
                "reason": reason,
                "balance": 0,
                "timestamp": datetime.now().isoformat()
            })
            
        return cleared_amount
    
    def get_info(self) -> Dict:
        """Get information about the community fund
        
        Returns:
            Dictionary with community fund information
        """
        return {
            "balance": self._funds,
            "updated_at": datetime.now().isoformat()
        }

    def get_balance(self) -> int:
        """Get the current balance of the community fund
        
        Returns:
            Current fund balance
        """
        return self._funds 