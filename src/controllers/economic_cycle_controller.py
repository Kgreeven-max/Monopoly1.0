import logging
import random
import json
from datetime import datetime, timedelta
from flask_socketio import SocketIO
from sqlalchemy.exc import SQLAlchemyError
from flask.globals import _app_ctx_stack
from flask import current_app
import traceback

from src.models import db
from src.models.game_state import GameState
from src.models.property import Property
from src.models.finance.loan import Loan
from src.models.cd import CD
from src.models.player import Player

logger = logging.getLogger(__name__)

# Economic cycle states and their effects
ECONOMIC_STATES = {
    "boom": {
        "description": "Economic Boom - Property values rise, interest rates increase",
        "property_value_modifier": 1.15,
        "loan_interest_modifier": 1.2,
        "cd_interest_modifier": 1.3,
        "heloc_interest_modifier": 1.1,
        "inflation_modifier": 0.02,
        "bank_money_multiplier": 1.2,
        "next_states": ["stable", "stable", "boom", "recession"],
        "probability": 0.25,
        "color": "#4CAF50"  # Green
    },
    "stable": {
        "description": "Stable Economy - Balanced economic conditions",
        "property_value_modifier": 1.0,
        "loan_interest_modifier": 1.0,
        "cd_interest_modifier": 1.0,
        "heloc_interest_modifier": 1.0,
        "inflation_modifier": 0.0,
        "bank_money_multiplier": 1.0,
        "next_states": ["boom", "stable", "stable", "recession"],
        "probability": 0.4,
        "color": "#2196F3"  # Blue
    },
    "recession": {
        "description": "Recession - Property values drop, interest rates decrease",
        "property_value_modifier": 0.85,
        "loan_interest_modifier": 0.8,
        "cd_interest_modifier": 0.7,
        "heloc_interest_modifier": 0.9,
        "inflation_modifier": -0.02,
        "bank_money_multiplier": 0.8,
        "next_states": ["depression", "recession", "stable"],
        "probability": 0.25,
        "color": "#FFC107"  # Amber
    },
    "depression": {
        "description": "Economic Depression - Severe economic downturn",
        "property_value_modifier": 0.7,
        "loan_interest_modifier": 0.7,
        "cd_interest_modifier": 0.6,
        "heloc_interest_modifier": 0.75,
        "inflation_modifier": -0.04,
        "bank_money_multiplier": 0.6,
        "next_states": ["recession", "depression"],
        "probability": 0.1,
        "color": "#F44336"  # Red
    },
}

class EconomicCycleController:
    """Controller for managing economic cycles in the game."""
    
    def __init__(self, socketio: SocketIO, app=None):
        """
        Initialize the EconomicCycleController.
        
        Args:
            socketio: SocketIO instance for emitting events
            app: Flask application instance
        """
        self.socketio = socketio
        self.logger = logger
        self.app = app
        logger.info("EconomicCycleController initialized")
    
    def process_economic_cycle(self, game_id):
        """Process economic cycle changes for a game"""
        try:
            # Get the Flask app from the instance
            app = self.app
            if not app:
                self.logger.error("Flask app not found")
                return {'success': False, 'error': 'Flask app not found'}
                
            # Use the app context for database operations
            with app.app_context():
                game_state = GameState.query.filter_by(game_id=game_id).first()
                if not game_state:
                    self.logger.error(f"Game state not found for game {game_id}")
                    return {'success': False, 'error': 'Game state not found'}
                
                # Get current economic state
                current_state = game_state.economic_state or 'stable'
                current_cycle_position = game_state.economic_cycle_position or 0
                
                # Get cycle period from game settings (defaults to 5 if not set)
                cycle_period = game_state.economic_cycle_period or 5
                
                # Calculate average number of times players have passed GO
                active_players = Player.query.filter_by(game_id=game_id, is_active=True).all()
                if not active_players:
                    return {'success': False, 'error': 'No active players found'}
                
                total_go_passes = sum(player.times_passed_go for player in active_players)
                avg_go_passes = total_go_passes / len(active_players)
                
                # Calculate new cycle position based on average GO passes
                # One full cycle should take exactly cycle_period average passes of GO
                new_cycle_position = (avg_go_passes % cycle_period) / cycle_period
                
                # Only update if position has changed significantly (avoid floating point issues)
                if abs(new_cycle_position - current_cycle_position) < 0.01:
                    return {
                        'success': True,
                        'previous_state': current_state,
                        'new_state': current_state,
                        'cycle_position': current_cycle_position,
                        'avg_go_passes': avg_go_passes
                    }
                
                # Determine economic state based on cycle position
                if new_cycle_position < 0.25:
                    new_state = 'recovery'
                elif new_cycle_position < 0.5:
                    new_state = 'boom'
                elif new_cycle_position < 0.75:
                    new_state = 'stable'
                else:
                    new_state = 'recession'
                
                # Only update if state has changed
                if new_state != current_state:
                    self.logger.info(f"Economic state changing from {current_state} to {new_state} (avg GO passes: {avg_go_passes:.1f})")
                    
                    # Update game state
                    game_state.economic_state = new_state
                    game_state.economic_cycle_position = new_cycle_position
                    
                    # Update inflation and interest rates based on new state
                    if new_state == 'boom':
                        inflation_rate = 0.03
                        base_interest_rate = 0.02
                    elif new_state == 'stable':
                        inflation_rate = 0.02
                        base_interest_rate = 0.01
                    elif new_state == 'recession':
                        inflation_rate = 0.01
                        base_interest_rate = 0.04
                    else:  # recovery
                        inflation_rate = 0.02
                        base_interest_rate = 0.03
                    
                    game_state.inflation_rate = inflation_rate
                    game_state.base_interest_rate = base_interest_rate
                    
                    # Update property values based on economic state
                    if new_state == 'boom':
                        multiplier = 1.15  # 15% increase
                    elif new_state == 'stable':
                        multiplier = 1.00  # No change
                    elif new_state == 'recession':
                        multiplier = 0.85  # 15% decrease
                    else:  # recovery
                        multiplier = 1.05  # 5% increase
                    
                    # Update all property values
                    properties = Property.query.filter_by(game_id=game_id).all()
                    for property in properties:
                        property.current_price = int(property.base_price * multiplier)
                        property.current_rent = int(property.base_rent * multiplier)
                    
                    # Commit changes
                    db.session.commit()
                
                return {
                    'success': True,
                    'previous_state': current_state,
                    'new_state': new_state,
                    'cycle_position': new_cycle_position,
                    'avg_go_passes': avg_go_passes,
                    'inflation_rate': inflation_rate if new_state != current_state else game_state.inflation_rate,
                    'base_interest_rate': base_interest_rate if new_state != current_state else game_state.base_interest_rate
                }
                
        except Exception as e:
            self.logger.error(f"Error processing economic cycle: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_current_economic_state(self, game_id):
        """
        Get the current economic state for a game.
        
        Args:
            game_id (str): The ID of the game.
            
        Returns:
            dict: A dictionary with the current economic state.
        """
        try:
            # Get the game state
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the current economic state
            current_state = game_state.inflation_state or "stable"
            
            # Get interest rates
            if hasattr(game_state, 'interest_rates') and game_state.interest_rates:
                try:
                    interest_rates = json.loads(game_state.interest_rates)
                except json.JSONDecodeError:
                    interest_rates = {}
            else:
                # Default interest rates if none are set
                interest_rates = {
                    "loan": 0.05,
                    "cd": 0.03,
                    "heloc": 0.06
                }
            
            return {
                "success": True,
                "game_id": game_id,
                "economic_state": current_state,
                "economic_description": ECONOMIC_STATES[current_state]["description"],
                "inflation_rate": game_state.inflation_rate or 0.0,
                "interest_rates": interest_rates,
                "color": ECONOMIC_STATES[current_state]["color"],
                "last_update": game_state.last_economic_update.isoformat() if game_state.last_economic_update else None
            }
            
        except Exception as e:
            logger.error(f"Error getting economic state: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def trigger_market_crash(self, game_id, admin_key=None):
        """
        Trigger a market crash event.
        
        Args:
            game_id (str): The ID of the game.
            admin_key (str, optional): Admin authentication key.
            
        Returns:
            dict: A dictionary with the results of the market crash.
        """
        logger.info(f"Triggering market crash for game {game_id}")
        
        try:
            # Get the game state
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Update economic state to depression
            game_state.inflation_state = "depression"
            game_state.last_economic_update = datetime.utcnow()
            
            # Apply severe property value reduction
            self._update_property_values(game_id, 0.6)  # 40% drop in property values
            
            # Update interest rates for financial instruments
            base_loan_rate = 0.08  # Higher loan rates during crash
            base_cd_rate = 0.01    # Lower CD rates during crash
            base_heloc_rate = 0.09 # Higher HELOC rates during crash
            
            interest_rates = {
                "loan": base_loan_rate,
                "cd": base_cd_rate,
                "heloc": base_heloc_rate
            }
            
            # Store interest rates
            game_state.interest_rates = json.dumps(interest_rates)
            
            # Add to game log
            log_entry = {
                "type": "market_crash",
                "economic_state": "depression",
                "property_value_change": -0.4,  # 40% reduction
                "interest_rates": interest_rates,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    current_log = []
            
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Process effects on loans and CDs
            self._process_loan_interest_changes(game_id, base_loan_rate)
            self._process_cd_interest_changes(game_id, base_cd_rate)
            
            # Commit changes to database
            db.session.commit()
            
            # Emit an event to notify clients
            market_crash_event = {
                "game_id": game_id,
                "event": "market_crash",
                "economic_state": "depression",
                "economic_description": "Market Crash! Severe economic depression has hit the economy.",
                "property_value_change": -0.4,
                "interest_rates": interest_rates,
                "color": "#F44336",  # Red
                "timestamp": datetime.utcnow().isoformat()
            }
            self.socketio.emit('market_crash', market_crash_event, room=game_id)
            
            return {
                "success": True,
                "event": "market_crash",
                "economic_state": "depression",
                "property_value_change": -0.4,
                "interest_rates": interest_rates
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error triggering market crash: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def trigger_economic_boom(self, game_id, admin_key=None):
        """
        Trigger an economic boom event.
        
        Args:
            game_id (str): The ID of the game.
            admin_key (str, optional): Admin authentication key.
            
        Returns:
            dict: A dictionary with the results of the economic boom.
        """
        logger.info(f"Triggering economic boom for game {game_id}")
        
        try:
            # Get the game state
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Update economic state to boom
            game_state.inflation_state = "boom"
            game_state.last_economic_update = datetime.utcnow()
            
            # Apply property value increase
            self._update_property_values(game_id, 1.25)  # 25% increase in property values
            
            # Update interest rates for financial instruments
            base_loan_rate = 0.06  # Higher loan rates during boom
            base_cd_rate = 0.05    # Higher CD rates during boom
            base_heloc_rate = 0.07 # Higher HELOC rates during boom
            
            interest_rates = {
                "loan": base_loan_rate,
                "cd": base_cd_rate,
                "heloc": base_heloc_rate
            }
            
            # Store interest rates
            game_state.interest_rates = json.dumps(interest_rates)
            
            # Add to game log
            log_entry = {
                "type": "economic_boom",
                "economic_state": "boom",
                "property_value_change": 0.25,  # 25% increase
                "interest_rates": interest_rates,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    current_log = []
            else:
                current_log = []
            
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Process effects on loans and CDs
            self._process_loan_interest_changes(game_id, base_loan_rate)
            self._process_cd_interest_changes(game_id, base_cd_rate)
            
            # Commit changes to database
            db.session.commit()
            
            # Emit an event to notify clients
            economic_boom_event = {
                "game_id": game_id,
                "event": "economic_boom",
                "economic_state": "boom",
                "economic_description": "Economic Boom! Prosperity has arrived with rising property values and interest rates.",
                "property_value_change": 0.25,
                "interest_rates": interest_rates,
                "color": "#4CAF50",  # Green
                "timestamp": datetime.utcnow().isoformat()
            }
            self.socketio.emit('economic_boom', economic_boom_event, room=game_id)
            
            return {
                "success": True,
                "event": "economic_boom",
                "economic_state": "boom",
                "property_value_change": 0.25,
                "interest_rates": interest_rates
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error triggering economic boom: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def handle_market_fluctuation_space(self, game_id, player_id):
        """
        Handle when a player lands on a market fluctuation space.
        
        Args:
            game_id (str): The ID of the game.
            player_id (int): The ID of the player.
            
        Returns:
            dict: A dictionary with the results of the market fluctuation.
        """
        try:
            # Get the game state
            game_state = GameState.query.get(game_id)
            if not game_state:
                self.logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player
            player = Player.query.get(player_id)
            if not player:
                self.logger.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the current economic state
            current_state = game_state.inflation_state or "stable"
            
            # Different effects based on economic state
            effects = {
                "boom": {
                    "description": "The economy is booming! Your investments have paid off!",
                    "cash_bonus": 100,
                    "property_value_increase": 0.05  # 5% increase
                },
                "stable": {
                    "description": "The market is stable. Your diversified portfolio earns a modest return.",
                    "cash_bonus": 50,
                    "property_value_increase": 0.02  # 2% increase
                },
                "recession": {
                    "description": "Economic recession is affecting your investments.",
                    "cash_penalty": 50,
                    "property_value_decrease": 0.03  # 3% decrease
                },
                "depression": {
                    "description": "Economic depression has severely impacted your finances!",
                    "cash_penalty": 100,
                    "property_value_decrease": 0.08  # 8% decrease
                }
            }
            
            # Get effects for current state
            state_effects = effects.get(current_state, effects["stable"])
            result = {
                "state": current_state,
                "description": state_effects["description"]
            }
            
            # Apply cash effects
            if "cash_bonus" in state_effects:
                player.money += state_effects["cash_bonus"]
                result["cash_bonus"] = state_effects["cash_bonus"]
            elif "cash_penalty" in state_effects:
                player.money -= state_effects["cash_penalty"]
                result["cash_penalty"] = state_effects["cash_penalty"]
            
            # Apply property value changes
            property_changes = []
            owned_properties = Property.query.filter_by(owner_id=player_id, game_id=game_id).all()
            
            for prop in owned_properties:
                if "property_value_increase" in state_effects:
                    # Increase property value
                    increase_rate = state_effects["property_value_increase"]
                    old_value = prop.current_price
                    new_value = int(old_value * (1 + increase_rate))
                    prop.current_price = new_value
                    
                    property_changes.append({
                        "property_id": prop.id,
                        "property_name": prop.name,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change": new_value - old_value
                    })
                    
                elif "property_value_decrease" in state_effects:
                    # Decrease property value
                    decrease_rate = state_effects["property_value_decrease"]
                    old_value = prop.current_price
                    new_value = int(old_value * (1 - decrease_rate))
                    prop.current_price = new_value
                    
                    property_changes.append({
                        "property_id": prop.id,
                        "property_name": prop.name,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change": new_value - old_value
                    })
            
            # Add property changes to result if any happened
            if property_changes:
                result["property_changes"] = property_changes
                
                # Calculate total property value change
                total_change = sum(p["change"] for p in property_changes)
                result["total_property_value_change"] = total_change
                
                if total_change > 0:
                    result["property_effect"] = "increase"
                else:
                    result["property_effect"] = "decrease"
            
            # Commit changes
            db.session.commit()
            
            # Emit event
            if self.socketio:
                self.socketio.emit('market_fluctuation', {
                    "player_id": player_id,
                    "game_id": game_id,
                    "result": result
                }, room=game_id)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling market fluctuation: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def trigger_economic_event(self, game_id, admin_key=None, specific_event=None):
        """
        Trigger a random economic event that affects the game economy.
        
        Args:
            game_id (str): The ID of the game.
            admin_key (str, optional): Admin authentication key for admin-triggered events.
            specific_event (str, optional): Specific event to trigger (admin only).
            
        Returns:
            dict: A dictionary with the results of the economic event.
        """
        logger.info(f"Triggering economic event for game {game_id}")
        
        try:
            # Get the game state
            game_state = GameState.query.get(game_id)
            if not game_state:
                logger.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the current economic state
            current_state = game_state.inflation_state or "stable"
            
            # Define possible economic events for each economic state
            economic_events = {
                "boom": [
                    {
                        "name": "stock_market_rally",
                        "title": "Stock Market Rally",
                        "description": "The stock market experiences a significant rally! Property values increase and players with investments gain.",
                        "property_value_modifier": 1.1,  # 10% increase
                        "cash_modifier": 1.05,  # 5% increase in cash for all players
                        "bank_interest_modifier": 1.1,  # 10% increase in interest rates
                        "probability": 0.3,
                        "color": "#4CAF50"  # Green
                    },
                    {
                        "name": "tech_bubble",
                        "title": "Tech Bubble Forms",
                        "description": "A tech bubble is forming in the market. High-value properties experience rapid growth.",
                        "property_value_modifier": 1.15,  # 15% increase
                        "high_value_property_modifier": 1.25,  # 25% increase for expensive properties
                        "probability": 0.2,
                        "color": "#2196F3"  # Blue
                    },
                    {
                        "name": "foreign_investment",
                        "title": "Foreign Investment Surge",
                        "description": "Foreign investors pour money into the economy. Bank loans are cheaper.",
                        "loan_interest_modifier": 0.9,  # 10% decrease in loan rates
                        "cash_modifier": 1.1,  # 10% increase in cash for all players
                        "probability": 0.2,
                        "color": "#9C27B0"  # Purple
                    },
                    {
                        "name": "real_estate_boom",
                        "title": "Real Estate Boom",
                        "description": "The real estate market is booming! All properties increase in value significantly.",
                        "property_value_modifier": 1.2,  # 20% increase
                        "probability": 0.3,
                        "color": "#FF9800"  # Orange
                    }
                ],
                "stable": [
                    {
                        "name": "moderate_growth",
                        "title": "Moderate Growth",
                        "description": "The economy shows signs of moderate growth. Small boost to property values.",
                        "property_value_modifier": 1.05,  # 5% increase
                        "probability": 0.4,
                        "color": "#4CAF50"  # Green
                    },
                    {
                        "name": "market_stabilization",
                        "title": "Market Stabilization",
                        "description": "The market stabilizes after recent fluctuations. Interest rates normalize.",
                        "loan_interest_modifier": 1.0,  # Reset to normal
                        "cd_interest_modifier": 1.0,  # Reset to normal
                        "probability": 0.3,
                        "color": "#2196F3"  # Blue
                    },
                    {
                        "name": "consumer_confidence",
                        "title": "Consumer Confidence Rise",
                        "description": "Consumer confidence is rising. Small cash bonus for all players.",
                        "cash_modifier": 1.03,  # 3% increase in cash
                        "probability": 0.3,
                        "color": "#FFEB3B"  # Yellow
                    }
                ],
                "recession": [
                    {
                        "name": "market_correction",
                        "title": "Market Correction",
                        "description": "The market undergoes a correction. Property values decrease slightly.",
                        "property_value_modifier": 0.95,  # 5% decrease
                        "probability": 0.3,
                        "color": "#FF9800"  # Orange
                    },
                    {
                        "name": "credit_crunch",
                        "title": "Credit Crunch",
                        "description": "Banks restrict lending. Interest rates on loans increase.",
                        "loan_interest_modifier": 1.2,  # 20% increase in loan rates
                        "probability": 0.25,
                        "color": "#F44336"  # Red
                    },
                    {
                        "name": "layoffs",
                        "title": "Corporate Layoffs",
                        "description": "Companies announce layoffs. Players lose a small amount of cash.",
                        "cash_modifier": 0.95,  # 5% decrease in cash
                        "probability": 0.25,
                        "color": "#F44336"  # Red
                    },
                    {
                        "name": "stimulus_package",
                        "title": "Government Stimulus",
                        "description": "The government announces a stimulus package. Small boost to player cash.",
                        "cash_modifier": 1.05,  # 5% increase in cash
                        "property_value_modifier": 1.02,  # 2% increase in property values
                        "probability": 0.2,
                        "color": "#4CAF50"  # Green
                    }
                ],
                "depression": [
                    {
                        "name": "bank_failures",
                        "title": "Bank Failures",
                        "description": "Several banks fail! Interest rates skyrocket and cash is tight.",
                        "loan_interest_modifier": 1.5,  # 50% increase in loan rates
                        "cash_modifier": 0.9,  # 10% decrease in cash
                        "probability": 0.3,
                        "color": "#F44336"  # Red
                    },
                    {
                        "name": "property_crash",
                        "title": "Property Market Crash",
                        "description": "The property market crashes! Property values plummet.",
                        "property_value_modifier": 0.7,  # 30% decrease
                        "probability": 0.3,
                        "color": "#F44336"  # Red
                    },
                    {
                        "name": "emergency_measures",
                        "title": "Emergency Economic Measures",
                        "description": "The government implements emergency economic measures. Some stability returns.",
                        "property_value_modifier": 0.85,  # 15% decrease (better than full crash)
                        "loan_interest_modifier": 0.9,  # 10% decrease in loan rates to stimulate economy
                        "probability": 0.2,
                        "color": "#FFC107"  # Amber
                    },
                    {
                        "name": "economic_depression",
                        "title": "Deepening Depression",
                        "description": "The economic depression deepens. All values fall significantly.",
                        "property_value_modifier": 0.6,  # 40% decrease
                        "cash_modifier": 0.8,  # 20% decrease in cash
                        "loan_interest_modifier": 1.3,  # 30% increase in loan rates
                        "probability": 0.2,
                        "color": "#F44336"  # Red
                    }
                ]
            }
            
            # Select the event
            if specific_event and admin_key:
                # Admin is requesting a specific event
                # Flatten all events
                all_events = []
                for state_events in economic_events.values():
                    all_events.extend(state_events)
                
                # Find the requested event
                event = next((e for e in all_events if e["name"] == specific_event), None)
                if not event:
                    logger.error(f"Requested event '{specific_event}' not found")
                    return {"success": False, "error": "Requested event not found"}
            else:
                # Randomly select an event based on the current economic state
                state_events = economic_events.get(current_state, economic_events["stable"])
                
                # Select an event based on probabilities
                total_prob = sum(event["probability"] for event in state_events)
                random_val = random.random() * total_prob
                
                cumulative_prob = 0
                event = state_events[0]  # Default to first event
                for e in state_events:
                    cumulative_prob += e["probability"]
                    if random_val <= cumulative_prob:
                        event = e
                        break
            
            # Apply the event effects
            result = {
                "event_name": event["name"],
                "title": event["title"],
                "description": event["description"],
                "economic_state": current_state,
                "effects": {}
            }
            
            # Update property values if modifier exists
            if "property_value_modifier" in event:
                property_modifier = event["property_value_modifier"]
                self._update_property_values(game_id, property_modifier)
                result["effects"]["property_value_modifier"] = property_modifier
                
                # If there's a specific modifier for high-value properties
                if "high_value_property_modifier" in event:
                    high_value_modifier = event["high_value_property_modifier"]
                    # Get expensive properties (top 25% by price)
                    properties = Property.query.filter_by(game_id=game_id).order_by(Property.price.desc()).all()
                    high_value_count = max(1, len(properties) // 4)  # At least 1 property
                    high_value_properties = properties[:high_value_count]
                    
                    for prop in high_value_properties:
                        # Apply the additional modifier
                        additional_modifier = high_value_modifier / property_modifier
                        prop.price = int(prop.price * additional_modifier)
                    
                    db.session.commit()
                    result["effects"]["high_value_property_modifier"] = high_value_modifier
            
            # Update interest rates if modifiers exist
            interest_rates_updated = False
            if hasattr(game_state, 'interest_rates') and game_state.interest_rates:
                try:
                    current_rates = json.loads(game_state.interest_rates)
                except json.JSONDecodeError:
                    current_rates = {}
            else:
                current_rates = {}
            
            if "loan_interest_modifier" in event:
                loan_modifier = event["loan_interest_modifier"]
                if "loan" in current_rates:
                    current_rates["loan"] *= loan_modifier
                else:
                    current_rates["loan"] = 0.05 * loan_modifier  # Default 5%
                interest_rates_updated = True
                result["effects"]["loan_interest_modifier"] = loan_modifier
                
                # Process effects on active loans
                self._process_loan_interest_changes(game_id, current_rates["loan"])
            
            if "cd_interest_modifier" in event:
                cd_modifier = event["cd_interest_modifier"]
                if "cd" in current_rates:
                    current_rates["cd"] *= cd_modifier
                else:
                    current_rates["cd"] = 0.03 * cd_modifier  # Default 3%
                interest_rates_updated = True
                result["effects"]["cd_interest_modifier"] = cd_modifier
                
                # Process effects on active CDs
                self._process_cd_interest_changes(game_id, current_rates["cd"])
            
            if interest_rates_updated:
                if hasattr(game_state, 'interest_rates'):
                    game_state.interest_rates = json.dumps(current_rates)
                result["effects"]["new_interest_rates"] = current_rates
            
            # Update player cash if modifier exists
            if "cash_modifier" in event:
                cash_modifier = event["cash_modifier"]
                players = Player.query.filter_by(game_id=game_id, is_active=True).all()
                
                for player in players:
                    original_balance = player.balance
                    new_balance = int(original_balance * cash_modifier)
                    player.balance = new_balance
                
                db.session.commit()
                result["effects"]["cash_modifier"] = cash_modifier
            
            # Add to game log
            log_entry = {
                "type": "economic_event",
                "event_name": event["name"],
                "title": event["title"],
                "description": event["description"],
                "effects": result["effects"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if hasattr(game_state, 'game_log') and game_state.game_log:
                try:
                    current_log = json.loads(game_state.game_log)
                except json.JSONDecodeError:
                    current_log = []
            
            current_log.append(log_entry)
            if hasattr(game_state, 'game_log'):
                game_state.game_log = json.dumps(current_log)
            
            # Commit changes to database
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('economic_event', {
                "game_id": game_id,
                "event_name": event["name"],
                "title": event["title"],
                "description": event["description"],
                "economic_state": current_state,
                "effects": result["effects"],
                "color": event["color"],
                "timestamp": datetime.utcnow().isoformat()
            }, room=game_id)
            
            # Trigger bot reactions to the economic event
            try:
                # Get bot controller from app config
                bot_controller = current_app.config.get('bot_controller')
                
                if bot_controller:
                    logger.info(f"Triggering bot reactions to economic event: {event['name']}")
                    
                    # Prepare event data for bots
                    event_data = {
                        "new_state": current_state,
                        "effects": result["effects"],
                        "event_name": event["name"]
                    }
                    
                    # Determine the event type based on the event name or effects
                    if "property_value_modifier" in event and event["property_value_modifier"] > 1:
                        event_type = "market_boom"
                    elif "property_value_modifier" in event and event["property_value_modifier"] < 1:
                        event_type = "market_crash"
                    elif "loan_interest_modifier" in event or "cd_interest_modifier" in event:
                        event_type = "interest_rate_change"
                        if "loan_interest_modifier" in event:
                            event_data["new_rate"] = current_rates.get("loan", 0.05)
                            event_data["old_rate"] = event_data["new_rate"] / event["loan_interest_modifier"]
                    elif "cash_modifier" in event:
                        event_type = "cash_flow_change"
                    else:
                        event_type = "economic_cycle_change"
                    
                    # Call bot controller to handle bot reactions
                    bot_reaction_result = bot_controller.handle_economic_event(game_id, event_type, event_data)
                    
                    if bot_reaction_result.get('success'):
                        logger.info(f"Bots successfully reacted to economic event: {len(bot_reaction_result.get('bot_responses', {}))} bot responses")
                    else:
                        logger.warning(f"Error in bot reactions to economic event: {bot_reaction_result.get('error', 'Unknown error')}")
                else:
                    logger.warning("Bot controller not found in app config, bot reactions to economic event not triggered")
            except Exception as e:
                logger.error(f"Error triggering bot reactions to economic event: {str(e)}", exc_info=True)
                # Continue with the main event even if bot reactions fail
            
            return {
                "success": True,
                "event_name": event["name"],
                "title": event["title"],
                "description": event["description"],
                "economic_state": current_state,
                "effects": result["effects"]
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error triggering economic event: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

def register_economic_events(socketio, app_config):
    """Register economic cycle related socket event handlers"""
    # Get the EconomicCycleController instance from app_config
    economic_controller = app_config.get('economic_controller')
    if not economic_controller:
        logger.error("Economic controller not found in app config during event registration.")
        return
    
    @socketio.on('get_economic_state')
    def handle_get_economic_state(data):
        """Get the current economic state for a game"""
        game_id = data.get('game_id')
        result = economic_controller.get_current_economic_state(game_id)
        if result.get('success'):
            socketio.emit('economic_state', result, room=data.get('sid', request.sid))
        else:
            socketio.emit('economic_error', {'error': result.get('error')}, room=data.get('sid', request.sid))
    
    @socketio.on('trigger_market_crash')
    def handle_trigger_market_crash(data):
        """Trigger a market crash event (admin only)"""
        game_id = data.get('game_id')
        admin_key = data.get('admin_key')
        
        # Verify admin key
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            socketio.emit('economic_error', {'error': 'Unauthorized admin action'}, room=request.sid)
            return
            
        result = economic_controller.trigger_market_crash(game_id, admin_key)
        if result.get('success'):
            socketio.emit('admin_action_success', {'action': 'market_crash', 'message': 'Market crash triggered'}, room=request.sid)
        else:
            socketio.emit('economic_error', {'error': result.get('error')}, room=request.sid)
    
    @socketio.on('trigger_economic_boom')
    def handle_trigger_economic_boom(data):
        """Trigger an economic boom event (admin only)"""
        game_id = data.get('game_id')
        admin_key = data.get('admin_key')
        
        # Verify admin key
        is_admin = admin_key == app_config.get('ADMIN_KEY', 'pinopoly-admin')
        if not is_admin:
            socketio.emit('economic_error', {'error': 'Unauthorized admin action'}, room=request.sid)
            return
            
        result = economic_controller.trigger_economic_boom(game_id, admin_key)
        if result.get('success'):
            socketio.emit('admin_action_success', {'action': 'economic_boom', 'message': 'Economic boom triggered'}, room=request.sid)
        else:
            socketio.emit('economic_error', {'error': result.get('error')}, room=request.sid)
    
    @socketio.on('handle_market_fluctuation')
    def handle_market_fluctuation(data):
        """Handle when a player lands on a market fluctuation space"""
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if not game_id or not player_id:
            socketio.emit('economic_error', {'error': 'Missing required parameters'}, room=request.sid)
            return
            
        result = economic_controller.handle_market_fluctuation_space(game_id, player_id)
        if result.get('success'):
            # The event emitting is already handled in the method
            pass
        else:
            socketio.emit('economic_error', {'error': result.get('error')}, room=request.sid)
    
    @socketio.on('trigger_economic_event')
    def handle_trigger_economic_event(data):
        """Trigger a random economic event that affects the game economy"""
        game_id = data.get('game_id')
        admin_key = data.get('admin_key')
        specific_event = data.get('specific_event')
        
        if not game_id or not admin_key:
            socketio.emit('economic_error', {'error': 'Missing required parameters'}, room=request.sid)
            return
            
        result = economic_controller.trigger_economic_event(game_id, admin_key, specific_event)
        if result.get('success'):
            socketio.emit('admin_action_success', {'action': 'economic_event', 'message': 'Economic event triggered'}, room=request.sid)
        else:
            socketio.emit('economic_error', {'error': result.get('error')}, room=request.sid)
    
    logger.info("Economic cycle event handlers registered.") 