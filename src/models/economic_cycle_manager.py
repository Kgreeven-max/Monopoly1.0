from datetime import datetime
import logging
from src.models import db
from src.models.game_state import GameState
from src.models.economic_phase_change import EconomicPhaseChange
from src.models.finance.loan import Loan

logger = logging.getLogger(__name__)

class EconomicCycleManager:
    """Manages the economic cycle, interest rates, and inflation"""
    
    def __init__(self, socketio=None, banker=None):
        """Initialize the economic cycle manager
        
        Args:
            socketio: SocketIO instance for emitting events
            banker: Banker instance for updating loan rates
        """
        self.socketio = socketio
        self.banker = banker
        self.base_interest_rate = 0.05  # 5% starting base rate
        self.inflation_target = 0.03    # 3% target inflation
        self.inflation_rate = 0.03      # Current inflation rate
        self.cycle_position = 0.0       # 0.0 to 1.0 position in cycle
        self.cycle_direction = 0.01     # Cycle movement per update
        self.last_update = datetime.now()
        self.logger = logging.getLogger(__name__)
    
    def update_economic_cycle(self):
        """Update the economic cycle position and related factors
        
        Returns:
            Dict with economic state information
        """
        self.logger.info("Updating economic cycle")
        
        try:
            # Move cycle position
            self.cycle_position += self.cycle_direction
            
            # Check for cycle boundaries and reverse if needed
            if self.cycle_position >= 1.0:
                self.cycle_position = 1.0
                self.cycle_direction = -0.01  # Start moving backward
                self.logger.info("Economic cycle reached peak, now moving backward")
            elif self.cycle_position <= 0.0:
                self.cycle_position = 0.0
                self.cycle_direction = 0.01   # Start moving forward
                self.logger.info("Economic cycle reached bottom, now moving forward")
            
            # Determine economic state based on cycle position
            prev_economic_state = None
            game_state = GameState.query.first()
            if game_state:
                prev_economic_state = game_state.inflation_state
            
            if self.cycle_position < 0.25:
                economic_state = "recession"
            elif self.cycle_position < 0.5:
                economic_state = "normal"
            elif self.cycle_position < 0.75:
                economic_state = "growth"
            else:
                economic_state = "boom"
            
            self.logger.info(f"Economic state: {economic_state} (cycle position: {self.cycle_position:.2f})")
            
            # Update inflation rate based on cycle position
            # Higher inflation in boom, lower in recession
            cycle_inflation_effect = (self.cycle_position - 0.5) * 0.04
            self.inflation_rate = self.inflation_target + cycle_inflation_effect
            
            # Adjust base interest rate to counter inflation
            # Increase rates when inflation is above target
            inflation_gap = self.inflation_rate - self.inflation_target
            if abs(inflation_gap) > 0.01:  # Only adjust if gap is significant
                rate_adjustment = inflation_gap * 1.5  # 1.5x response factor
                self.base_interest_rate += rate_adjustment * 0.1  # Gradual adjustment
            
            # Apply bounds to interest rate
            self.base_interest_rate = max(0.01, min(0.15, self.base_interest_rate))
            
            self.logger.info(f"Inflation rate: {self.inflation_rate:.2f}, Base interest rate: {self.base_interest_rate:.2f}")
            
            # Update game state
            if game_state:
                # Record phase change if state changed
                if prev_economic_state and prev_economic_state != economic_state:
                    self._record_economic_phase_change(game_state, prev_economic_state, economic_state)
                
                game_state.inflation_state = economic_state
                game_state.inflation_rate = self.inflation_rate
                game_state.base_interest_rate = self.base_interest_rate
                db.session.commit()
            else:
                self.logger.warning("Could not find game state to update economic cycle")
                return {
                    "success": False,
                    "error": "Game state not found"
                }
            
            # Update all loans with new base rate
            if self.banker:
                self.banker.update_loan_rates(self.base_interest_rate)
            else:
                self.logger.warning("Banker not available, loan rates not updated")
            
            # Broadcast update
            if self.socketio:
                self.socketio.emit('economic_update', {
                    "economic_state": economic_state,
                    "cycle_position": self.cycle_position,
                    "inflation_rate": self.inflation_rate,
                    "base_interest_rate": self.base_interest_rate
                })
            
            self.last_update = datetime.now()
            
            return {
                "success": True,
                "economic_state": economic_state,
                "inflation_rate": self.inflation_rate,
                "base_interest_rate": self.base_interest_rate,
                "cycle_position": self.cycle_position
            }
            
        except Exception as e:
            self.logger.error(f"Error updating economic cycle: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error updating economic cycle: {str(e)}"
            }
    
    def _record_economic_phase_change(self, game_state, old_state, new_state):
        """Record an economic phase change in the database
        
        Args:
            game_state: Current GameState
            old_state: Previous economic state
            new_state: New economic state
        """
        try:
            # Calculate economic metrics
            total_cash = self._calculate_total_cash_in_circulation()
            total_property_value = self._calculate_total_property_value()
            
            # Create phase change record
            phase_change = EconomicPhaseChange(
                lap_number=game_state.current_lap,
                old_state=old_state,
                new_state=new_state,
                inflation_factor=game_state.inflation_factor,
                total_cash=total_cash,
                total_property_value=total_property_value,
                description=f"Economy shifted from {old_state} to {new_state}"
            )
            
            db.session.add(phase_change)
            db.session.commit()
            
            self.logger.info(f"Recorded economic phase change: {old_state} -> {new_state}")
            
        except Exception as e:
            self.logger.error(f"Error recording economic phase change: {str(e)}", exc_info=True)
    
    def _calculate_total_cash_in_circulation(self):
        """Calculate the total cash held by all players
        
        Returns:
            Total cash in circulation
        """
        from src.models.player import Player
        
        try:
            players = Player.query.filter_by(in_game=True).all()
            return sum(player.money for player in players)
        except Exception as e:
            self.logger.error(f"Error calculating total cash: {str(e)}", exc_info=True)
            return 0
    
    def _calculate_total_property_value(self):
        """Calculate the total value of all properties
        
        Returns:
            Total property value
        """
        from src.models.property import Property
        
        try:
            properties = Property.query.all()
            return sum(prop.current_price for prop in properties)
        except Exception as e:
            self.logger.error(f"Error calculating total property value: {str(e)}", exc_info=True)
            return 0
    
    def get_current_economic_state(self):
        """Get the current economic state
        
        Returns:
            Dict with current economic state
        """
        game_state = GameState.query.first()
        if not game_state:
            return {
                "success": False,
                "error": "Game state not found"
            }
        
        return {
            "success": True,
            "economic_state": game_state.inflation_state,
            "inflation_rate": game_state.inflation_rate,
            "base_interest_rate": game_state.base_interest_rate,
            "cycle_position": self.cycle_position
        }
    
    def force_economic_state(self, state, admin_key=None):
        """Force the economic cycle to a specific state (admin function)
        
        Args:
            state: Target economic state ("recession", "normal", "growth", "boom")
            admin_key: Admin authentication key
            
        Returns:
            Dict with result of operation
        """
        from flask import current_app
        
        # Verify admin key
        if admin_key != current_app.config.get('ADMIN_KEY'):
            return {
                "success": False,
                "error": "Invalid admin key"
            }
        
        # Map state to cycle position
        state_positions = {
            "recession": 0.1,
            "normal": 0.4,
            "growth": 0.6,
            "boom": 0.9
        }
        
        if state not in state_positions:
            return {
                "success": False,
                "error": f"Invalid economic state: {state}"
            }
        
        # Set cycle position
        self.cycle_position = state_positions[state]
        
        # Update economic cycle
        result = self.update_economic_cycle()
        
        if result["success"]:
            self.logger.info(f"Economic state forced to {state} by admin")
            return {
                "success": True,
                "message": f"Economic state forced to {state}",
                "new_state": result
            }
        else:
            return result 