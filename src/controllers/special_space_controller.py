from typing import Dict, List, Optional, Union, Any
import json
import random
import logging
import datetime
from flask_socketio import emit, SocketIO
from sqlalchemy.exc import SQLAlchemyError

from src.models.special_space import Card, SpecialSpace, CardDeck, TaxSpace
from src.models.player import Player
from src.models.game_state import GameState
from src.models.banker import Banker
from src.models.community_fund import CommunityFund
from src.models import db
from src.models.game_settings import GameSettings


class SpecialSpaceController:
    """Controller for managing special spaces and card actions"""
    
    def __init__(self, socketio=None, game_controller=None, economic_controller=None):
        """Initialize special space controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time communication
            game_controller: GameController instance for game state management
            economic_controller: EconomicCycleController instance for economic effects
        """
        self.socketio = socketio
        self.game_controller = game_controller
        self.economic_controller = economic_controller
        
        # Initialize card decks
        self.chance_deck = CardDeck("chance", socketio, None, None)
        self.community_chest_deck = CardDeck("community_chest", socketio, None, None)
        
        # Initialize tax space handler
        self.tax_handler = TaxSpace(socketio, None, None)
    
    def handle_special_space(self, player_id: int, position: int) -> Dict:
        """Handle player landing on a special space
        
        Args:
            player_id: ID of the player who landed on the space
            position: Board position where the player landed
            
        Returns:
            Action result dictionary
        """
        # Get player and special space
        player = Player.query.get(player_id)
        special_space = SpecialSpace.query.filter_by(position=position).first()
        
        if not player or not special_space:
            return {
                "success": False,
                "error": "Player or special space not found"
            }
        
        # Handle based on space type
        space_type = special_space.space_type
        logging.info(f"Player {player_id} landed on {special_space.name} (Type: {space_type}, Position: {position})")
        
        if space_type == "chance":
            return self.handle_chance_card(special_space.game_id, player_id)
            
        elif space_type == "community_chest":
            return self.handle_community_chest(special_space.game_id, player_id)
            
        elif space_type == "tax":
            return self.handle_tax_space(special_space.game_id, player_id, special_space.id)
            
        elif space_type == "go_to_jail":
            return self.handle_go_to_jail(special_space.game_id, player_id)
            
        elif space_type == "free_parking":
            return self.handle_free_parking(special_space.game_id, player_id)
            
        elif space_type == "market_fluctuation":
            return self.handle_market_fluctuation_space(special_space.game_id, player_id)
            
        elif space_type == "go" or space_type == "jail": # Passive spaces
             logging.debug(f"Player {player_id} landed on passive space {space_type}. No action taken.")
             return {
                 "success": True,
                 "action": "passive_space",
                 "message": f"Landed on {special_space.name}"
             }
        else:
            # Unsupported or unhandled space type
            logging.warning(f"Unhandled special space type '{space_type}' at position {position} for player {player_id}")
            return {
                "success": False,
                "error": f"Unhandled special space type: {space_type}"
            }
    
    def handle_chance_card(self, game_id, player_id):
        """
        Handles when a player lands on a Chance space and draws a Chance card.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on Chance.
            
        Returns:
            dict: A dictionary with success status, card information, and effects.
        """
        try:
            logging.info(f"Player {player_id} landed on Chance space in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Draw a chance card
            card = self.chance_deck.draw_card()
            if not card:
                logging.error("Failed to draw chance card")
                return {"success": False, "error": "Failed to draw chance card"}
            
            # Execute the card action
            action_result = self.chance_deck.execute_card_action(card, player_id)
            if not action_result.get("success", False):
                logging.error(f"Failed to execute chance card action: {action_result.get('error')}")
                return action_result
            
            # Extract card information and effects
            card_dict = card.to_dict()
            effects = action_result.get("action_result", {})
            
            # Log the card draw
            message = f"Player {player.username} drew a Chance card: {card_dict['title']}"
            logging.info(message)
            
            # Add to game log
            log_entry = {
                "type": "chance_card",
                "player_id": player_id,
                "card_id": card_dict["id"],
                "card_title": card_dict["title"],
                "message": message,
                "effects": effects,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('chance_card_drawn', {
                'game_id': game_id,
                'player_id': player_id,
                'card': card_dict,
                'effects': effects,
                'message': message
            }, room=game_id)
            
            return {
                "success": True,
                "card": card_dict,
                "effects": effects,
                "message": message
            }
            
        except Exception as e:
            logging.error(f"Error handling Chance card: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def handle_community_chest(self, game_id, player_id):
        """
        Handles when a player lands on a Community Chest space and draws a Community Chest card.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on Community Chest.
            
        Returns:
            dict: A dictionary with success status, card information, and effects.
        """
        try:
            logging.info(f"Player {player_id} landed on Community Chest space in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Draw a community chest card
            card = self.community_chest_deck.draw_card()
            if not card:
                logging.error("Failed to draw community chest card")
                return {"success": False, "error": "Failed to draw community chest card"}
            
            # Execute the card action
            action_result = self.community_chest_deck.execute_card_action(card, player_id)
            if not action_result.get("success", False):
                logging.error(f"Failed to execute community chest card action: {action_result.get('error')}")
                return action_result
            
            # Extract card information and effects
            card_dict = card.to_dict()
            effects = action_result.get("action_result", {})
            
            # Log the card draw
            message = f"Player {player.username} drew a Community Chest card: {card_dict['title']}"
            logging.info(message)
            
            # Add to game log
            log_entry = {
                "type": "community_chest_card",
                "player_id": player_id,
                "card_id": card_dict["id"],
                "card_title": card_dict["title"],
                "message": message,
                "effects": effects,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('community_chest_card_drawn', {
                'game_id': game_id,
                'player_id': player_id,
                'card': card_dict,
                'effects': effects,
                'message': message
            }, room=game_id)
            
            return {
                "success": True,
                "card": card_dict,
                "effects": effects,
                "message": message
            }
            
        except Exception as e:
            logging.error(f"Error handling Community Chest card: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def handle_go_to_jail(self, game_id, player_id):
        """
        Handles sending a player to jail when they land on the Go To Jail space
        or draw a card that sends them to jail.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who is being sent to jail.
            
        Returns:
            dict: A dictionary with the results of the jail action.
        """
        try:
            logging.info(f"Sending player {player_id} to jail in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the jail position from the board configuration
            board_config = self.board_controller.get_board_configuration(game_state.board_id)
            jail_position = None
            
            for space in board_config["spaces"]:
                if space.get("type") == "jail":
                    jail_position = space.get("position")
                    break
                
            if jail_position is None:
                logging.error(f"Jail position not found on board for game {game_id}")
                return {"success": False, "error": "Jail position not found on board"}
            
            # Update player's status and position
            player_data = game_state.get_player_data(player_id)
            if not player_data:
                logging.error(f"Player data for {player_id} not found in game state")
                return {"success": False, "error": "Player data not found in game state"}
            
            # Update the player's status in the game state
            player_data["in_jail"] = True
            player_data["jail_turns"] = 0  # Reset jail turn counter
            player_data["position"] = jail_position
            player_data["position_name"] = "Jail"  # Set position name
            player_data["last_roll"] = None  # Clear last roll
            
            # Set specific actions for the player based on jail rules
            jail_settings = game_state.get_settings().get("jail", {})
            bail_amount = jail_settings.get("bail_amount", 50)
            
            # Set expected actions for the player's next turn
            expected_actions = [
                {
                    "action": "roll_for_doubles",
                    "description": "Roll for doubles to get out of jail"
                },
                {
                    "action": "pay_bail",
                    "amount": bail_amount,
                    "description": f"Pay ${bail_amount} bail to get out of jail"
                }
            ]
            
            # Check if the player has Get Out of Jail Free cards
            get_out_of_jail_cards = player_data.get("get_out_of_jail_cards", 0)
            if get_out_of_jail_cards > 0:
                expected_actions.append({
                    "action": "use_jail_card",
                    "description": "Use a Get Out of Jail Free card"
                })
            
            # Update the player's expected actions
            player_data["expected_actions"] = expected_actions
            
            # Update the game state with the modified player data
            game_state.set_player_data(player_id, player_data)
            
            # Create a message based on the reason
            reason_messages = {
                "landed_on_space": f"Player {player.name} landed on Go To Jail!",
                "card": f"Player {player.name} drew a card sending them to Jail!",
                "rolled_three_doubles": f"Player {player.name} rolled doubles three times in a row and was sent to Jail!"
            }
            
            message = reason_messages.get(reason, f"Player {player.name} was sent to Jail!")
            
            # Add to game log
            game_state.add_game_log({
                "type": "jail_entry",
                "player_id": player_id,
                "reason": reason,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Update the game state
            self.game_controller.update_game_state(game_id, game_state)
            
            # Emit an event to notify clients
            socketio = self.game_controller.socketio
            socketio.emit('player_to_jail', {
                'game_id': game_id,
                'player_id': player_id,
                'reason': reason,
                'jail_position': jail_position,
                'message': message,
                'expected_actions': expected_actions
            }, room=game_id)
            
            return {
                "success": True,
                "jail_position": jail_position,
                "message": message,
                "expected_actions": expected_actions
            }
            
        except Exception as e:
            logging.error(f"Error handling go to jail: {str(e)}")
            return {"success": False, "error": str(e)}

    def release_from_jail(self, player_id: int, reason: str = "paid_fine") -> Dict:
        """Release player from jail
        
        Args:
            player_id: ID of the player to release
            reason: Reason for release (paid_fine, rolled_doubles, used_card)
            
        Returns:
            Action result
        """
        player = Player.query.get(player_id)
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Update player state
        player.in_jail = False
        player.jail_turns = 0
        
        db.session.add(player)
        db.session.commit()
        
        # Emit event
        if self.socketio:
            self.socketio.emit('player_out_of_jail', {
                "player_id": player_id,
                "player_name": player.username,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "action": "released_from_jail",
            "message": "Released from Jail",
            "reason": reason
        }

    def pay_jail_fine(self, player_id: int) -> Dict:
        """Pay fine to get out of jail
        
        Args:
            player_id: ID of the player paying the fine
            
        Returns:
            Action result
        """
        player = Player.query.get(player_id)
        game_state = GameState.query.first()
        
        if not player or not game_state:
            return {
                "success": False,
                "error": "Player or game state not found"
            }
        
        # Check if player is in jail
        if not player.in_jail:
            return {
                "success": False,
                "error": "Player is not in jail"
            }
        
        # Calculate fine amount (usually $50)
        fine_amount = 50
        
        # Check if player can afford the fine
        if player.cash < fine_amount:
            return {
                "success": False,
                "error": "Insufficient funds to pay jail fine",
                "required": fine_amount,
                "available": player.cash
            }
        
        # Process payment
        if self.banker:
            # Use banker to transfer money
            transaction = self.banker.transfer(player_id, "bank", fine_amount, "Jail fine")
            
            # Handle free parking fund if enabled
            if game_state.settings.get("free_parking_collects_fees", False):
                self.community_fund.add_funds(fine_amount, "Jail fine")
            
            # Release player from jail
            release_result = self.release_from_jail(player_id, "paid_fine")
            
            if release_result.get("success"):
                return {
                    "success": True,
                    "action": "paid_jail_fine",
                    "amount": fine_amount,
                    "transaction_id": transaction.id if transaction else None,
                    "message": "Paid fine and got out of jail"
                }
            else:
                return release_result
        else:
            return {
                "success": False,
                "error": "Banker not available to process payment"
            }

    def use_jail_card(self, player_id: int) -> Dict:
        """Use Get Out of Jail Free card
        
        Args:
            player_id: ID of the player using the card
            
        Returns:
            Action result
        """
        player = Player.query.get(player_id)
        
        if not player:
            return {
                "success": False,
                "error": "Player not found"
            }
        
        # Check if player is in jail
        if not player.in_jail:
            return {
                "success": False,
                "error": "Player is not in jail"
            }
        
        # Check if player has a jail card
        from src.models.jail_card import JailCard
        jail_card = JailCard.query.filter_by(player_id=player_id, used=False).first()
        
        if not jail_card:
            return {
                "success": False,
                "error": "No Get Out of Jail Free card available"
            }
        
        # Use the card
        jail_card.use_card()
        db.session.add(jail_card)
        
        # Emit event
        if self.socketio:
            self.socketio.emit('jail_card_used', {
                "player_id": player_id,
                "player_name": player.username,
                "card_id": jail_card.id,
                "card_type": jail_card.card_type,
                "timestamp": datetime.now().isoformat()
            })
        
        # Release player from jail
        release_result = self.release_from_jail(player_id, "used_card")
        
        if release_result.get("success"):
            return {
                "success": True,
                "action": "used_jail_card",
                "card_id": jail_card.id,
                "card_type": jail_card.card_type,
                "message": "Used Get Out of Jail Free card and got out of jail"
            }
        else:
            return release_result
    
    def handle_free_parking(self, game_id, player_id):
        """
        Handles a player landing on a free parking space.
        Based on game rules, the player may collect money from the community fund.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the free parking space.
            
        Returns:
            dict: A dictionary with the results of the free parking action.
        """
        try:
            logging.info(f"Player {player_id} landed on free parking in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Check if the game rules allow collecting money from free parking
            if game_state.rules.get("money_in_free_parking", False):
                community_fund = game_state.community_fund
                player_state["balance"] += community_fund
                
                # Log the transaction
                message = f"Player {player_id} collected ${community_fund} from Free Parking"
                logging.info(message)
                
                # Add to game log
                log_entry = {
                    "type": "free_parking",
                    "player_id": player_id,
                    "amount": community_fund,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Update game log
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                # Reset the community fund
                game_state.community_fund = 0
                
                # Update the game state
                db.session.commit()
                
                # Emit an event to notify clients
                self.socketio.emit('free_parking', {
                    'game_id': game_id,
                    'player_id': player_id,
                    'amount': community_fund
                }, room=game_id)
                
                return {
                    "success": True,
                    "action": "free_parking",
                    "player_id": player_id,
                    "amount": community_fund,
                    "message": message
                }
            else:
                # Free parking does nothing in this rule set
                message = "Free Parking - just taking a break!"
                
                # Add to game log
                log_entry = {
                    "type": "free_parking",
                    "player_id": player_id,
                    "amount": 0,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Update game log
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                # Update the game state
                db.session.commit()
                
                # Emit an event to notify clients
                self.socketio.emit('free_parking', {
                    'game_id': game_id,
                    'player_id': player_id,
                    'amount': 0
                }, room=game_id)
                
                return {
                    "success": True,
                    "action": "free_parking",
                    "player_id": player_id,
                    "amount": 0,
                    "message": message
                }
                
        except Exception as e:
            logging.error(f"Error handling free parking: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def initialize_special_spaces(self) -> Dict:
        """Initialize special spaces on the board
        
        Returns:
            Initialization result
        """
        # Clear existing special spaces
        SpecialSpace.query.delete()
        
        # Define standard special spaces
        spaces = [
            {
                "position": 0,
                "space_type": "go",
                "name": "GO",
                "description": "Collect salary as you pass GO"
            },
            {
                "position": 2,
                "space_type": "community_chest",
                "name": "Community Chest",
                "description": "Draw a Community Chest card"
            },
            {
                "position": 4,
                "space_type": "tax",
                "name": "Income Tax",
                "description": "Pay 10% or $200",
                "action_data": json.dumps({
                    "tax_type": "fixed",
                    "amount": 200,
                    "destination": "community_fund"
                })
            },
            {
                "position": 7,
                "space_type": "chance",
                "name": "Chance",
                "description": "Draw a Chance card"
            },
            {
                "position": 10,
                "space_type": "jail",
                "name": "Jail / Just Visiting",
                "description": "Just visiting if you're not in jail"
            },
            {
                "position": 15,
                "space_type": "market_fluctuation",
                "name": "Market Fluctuation",
                "description": "Economic changes affect your investments",
                "action_data": json.dumps({
                    "type": "market_fluctuation",
                    "description": "Your investments are affected by the current economic state"
                })
            },
            {
                "position": 17,
                "space_type": "community_chest",
                "name": "Community Chest",
                "description": "Draw a Community Chest card"
            },
            {
                "position": 20,
                "space_type": "free_parking",
                "name": "Free Parking",
                "description": "Relax and collect community fund (if enabled)"
            },
            {
                "position": 22,
                "space_type": "chance",
                "name": "Chance",
                "description": "Draw a Chance card"
            },
            {
                "position": 30,
                "space_type": "go_to_jail",
                "name": "Go to Jail",
                "description": "Go directly to Jail, do not pass GO"
            },
            {
                "position": 33,
                "space_type": "community_chest",
                "name": "Community Chest",
                "description": "Draw a Community Chest card"
            },
            {
                "position": 36,
                "space_type": "chance",
                "name": "Chance",
                "description": "Draw a Chance card"
            },
            {
                "position": 38,
                "space_type": "tax",
                "name": "Luxury Tax",
                "description": "Pay luxury tax",
                "action_data": json.dumps({
                    "tax_type": "fixed",
                    "amount": 100,
                    "destination": "community_fund"
                })
            }
        ]
        
        # Create special spaces
        for space_data in spaces:
            space = SpecialSpace(
                position=space_data["position"],
                space_type=space_data["space_type"],
                name=space_data["name"],
                description=space_data["description"],
                action_data=space_data.get("action_data")
            )
            db.session.add(space)
        
        db.session.commit()
        
        return {
            "success": True,
            "spaces_created": len(spaces),
            "message": "Special spaces initialized successfully"
        }
    
    def initialize_cards(self) -> Dict:
        """Initialize cards for Community Chest and Chance
        
        Returns:
            Initialization result
        """
        # Clear existing cards
        Card.query.delete()
        
        # Initialize Community Chest cards
        community_chest_cards = [
            {
                "title": "Bank Error In Your Favor",
                "description": "Collect $200",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 200,
                    "source": "bank",
                    "description": "Bank error in your favor"
                })
            },
            {
                "title": "Doctor's Fee",
                "description": "Pay $50",
                "action_type": "pay",
                "action_data": json.dumps({
                    "amount": 50,
                    "recipient": "community_fund",
                    "description": "Doctor's fee"
                })
            },
            {
                "title": "From Sale of Stock",
                "description": "Collect $50",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 50,
                    "source": "bank",
                    "description": "From sale of stock"
                })
            },
            {
                "title": "Get Out of Jail Free",
                "description": "This card may be kept until needed",
                "action_type": "jail",
                "action_data": json.dumps({
                    "action": "get_out_of_jail"
                })
            },
            {
                "title": "Go to Jail",
                "description": "Go directly to Jail. Do not pass GO, do not collect $200",
                "action_type": "jail",
                "action_data": json.dumps({
                    "action": "go_to_jail"
                })
            },
            {
                "title": "Holiday Fund Matures",
                "description": "Collect $100",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 100,
                    "source": "bank",
                    "description": "Holiday fund matures"
                })
            },
            {
                "title": "Income Tax Refund",
                "description": "Collect $20",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 20,
                    "source": "bank",
                    "description": "Income tax refund"
                })
            },
            {
                "title": "It's Your Birthday",
                "description": "Collect $10 from each player",
                "action_type": "birthday",
                "action_data": json.dumps({
                    "amount": 10,
                    "description": "Birthday celebration"
                })
            },
            {
                "title": "Life Insurance Matures",
                "description": "Collect $100",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 100,
                    "source": "bank",
                    "description": "Life insurance matures"
                })
            },
            {
                "title": "Pay Hospital Fees",
                "description": "Pay $100",
                "action_type": "pay",
                "action_data": json.dumps({
                    "amount": 100,
                    "recipient": "community_fund",
                    "description": "Hospital fees"
                })
            },
            {
                "title": "Pay School Fees",
                "description": "Pay $50",
                "action_type": "pay",
                "action_data": json.dumps({
                    "amount": 50,
                    "recipient": "community_fund",
                    "description": "School fees"
                })
            },
            {
                "title": "Receive Consultancy Fee",
                "description": "Collect $25",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 25,
                    "source": "bank",
                    "description": "Consultancy fee"
                })
            },
            {
                "title": "Property Repairs",
                "description": "Pay $40 per house and $115 per hotel you own",
                "action_type": "repairs",
                "action_data": json.dumps({
                    "cost_per_house": 40,
                    "cost_per_hotel": 115,
                    "description": "Property repairs"
                })
            },
            {
                "title": "You Have Won Second Prize in a Beauty Contest",
                "description": "Collect $10",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 10,
                    "source": "bank",
                    "description": "Beauty contest prize"
                })
            },
            {
                "title": "You Inherit",
                "description": "Collect $100",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 100,
                    "source": "bank",
                    "description": "Inheritance"
                })
            }
        ]
        
        # Initialize Chance cards
        chance_cards = [
            {
                "title": "Advance to Boardwalk",
                "description": "Advance to Boardwalk",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "to_position",
                    "position": 39
                })
            },
            {
                "title": "Advance to Go",
                "description": "Advance to Go, collect $200",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "to_position",
                    "position": 0
                })
            },
            {
                "title": "Advance to Illinois Avenue",
                "description": "Advance to Illinois Avenue. If you pass GO, collect $200",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "to_position",
                    "position": 24
                })
            },
            {
                "title": "Advance to St. Charles Place",
                "description": "Advance to St. Charles Place. If you pass Go, collect $200",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "to_position",
                    "position": 11
                })
            },
            {
                "title": "Advance to Nearest Railroad",
                "description": "Advance to the nearest Railroad. If owned, pay owner twice the rental",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "nearest",
                    "space_type": "railroad"
                })
            },
            {
                "title": "Advance to Nearest Utility",
                "description": "Advance to the nearest Utility. If owned, roll dice and pay owner 10x the amount rolled",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "nearest",
                    "space_type": "utility"
                })
            },
            {
                "title": "Bank Pays You Dividend",
                "description": "Bank pays you dividend of $50",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 50,
                    "source": "bank",
                    "description": "Bank dividend"
                })
            },
            {
                "title": "Get Out of Jail Free",
                "description": "This card may be kept until needed",
                "action_type": "jail",
                "action_data": json.dumps({
                    "action": "get_out_of_jail"
                })
            },
            {
                "title": "Go Back Three Spaces",
                "description": "Go back 3 spaces",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "backward",
                    "spaces": 3
                })
            },
            {
                "title": "Go to Jail",
                "description": "Go directly to Jail. Do not pass GO, do not collect $200",
                "action_type": "jail",
                "action_data": json.dumps({
                    "action": "go_to_jail"
                })
            },
            {
                "title": "Make General Repairs",
                "description": "Make general repairs on all your property. Pay $25 per house and $100 per hotel",
                "action_type": "repairs",
                "action_data": json.dumps({
                    "cost_per_house": 25,
                    "cost_per_hotel": 100,
                    "description": "General repairs"
                })
            },
            {
                "title": "Pay Poor Tax",
                "description": "Pay poor tax of $15",
                "action_type": "pay",
                "action_data": json.dumps({
                    "amount": 15,
                    "recipient": "community_fund",
                    "description": "Poor tax"
                })
            },
            {
                "title": "Advance to Reading Railroad",
                "description": "Take a trip to Reading Railroad. If you pass GO, collect $200",
                "action_type": "move",
                "action_data": json.dumps({
                    "move_type": "to_position",
                    "position": 5
                })
            },
            {
                "title": "Advance to Nearest Blue Property",
                "description": "Advance to the nearest Blue property. If unowned, you may buy it from the Bank",
                "action_type": "advance_to_property",
                "action_data": json.dumps({
                    "property_group": "blue"
                })
            },
            {
                "title": "Elected Chairman of the Board",
                "description": "You have been elected Chairman of the Board. Pay each player $50",
                "action_type": "birthday",
                "action_data": json.dumps({
                    "amount": 50,
                    "description": "Chairman of the Board payment"
                })
            },
            {
                "title": "Building Loan Matures",
                "description": "Your building loan matures. Collect $150",
                "action_type": "collect",
                "action_data": json.dumps({
                    "amount": 150,
                    "source": "bank",
                    "description": "Building loan matures"
                })
            }
        ]
        
        # Create Community Chest cards
        for card_data in community_chest_cards:
            card = Card(
                card_type="community_chest",
                title=card_data["title"],
                description=card_data["description"],
                action_type=card_data["action_type"],
                action_data=card_data["action_data"],
                is_active=True
            )
            db.session.add(card)
        
        # Create Chance cards
        for card_data in chance_cards:
            card = Card(
                card_type="chance",
                title=card_data["title"],
                description=card_data["description"],
                action_type=card_data["action_type"],
                action_data=card_data["action_data"],
                is_active=True
            )
            db.session.add(card)
        
        db.session.commit()
        
        # Initialize card decks
        self.chance_deck = CardDeck("chance", self.socketio, None, None)
        self.community_chest_deck = CardDeck("community_chest", self.socketio, None, None)
        
        return {
            "success": True,
            "community_chest_cards": len(community_chest_cards),
            "chance_cards": len(chance_cards),
            "message": "Cards initialized successfully"
        }
    
    def create_card(self, card_data: Dict) -> Dict:
        """Creates a new card in the database."""
        try:
            card_type = card_data.get('card_type')
            title = card_data.get('title')
            description = card_data.get('description')
            action_type = card_data.get('action_type')
            action_data_dict = card_data.get('action_data')
            is_active = card_data.get('is_active', True)

            if not card_type or not title or not description or not action_type or not action_data_dict:
                return {"success": False, "error": "Missing required card data"}

            card = Card(
                card_type=card_type,
                title=title,
                description=description,
                action_type=action_type,
                action_data=json.dumps(action_data_dict),
                is_active=is_active
            )
            db.session.add(card)
            db.session.commit()
            logging.info(f"Admin created new card: ID {card.id}, Title: {title}")
            return {"success": True, "card": card.to_dict()}
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating card: {e}", exc_info=True)
            return {"success": False, "error": "Failed to create card"}

    def update_card(self, card_id: int, update_data: Dict) -> Dict:
        """Updates an existing card in the database."""
        try:
            card = Card.query.get(card_id)
            if not card:
                return {"success": False, "error": "Card not found"}

            updated_fields = []
            if 'title' in update_data:
                card.title = update_data['title']
                updated_fields.append('title')
            if 'description' in update_data:
                card.description = update_data['description']
                updated_fields.append('description')
            if 'action_type' in update_data:
                card.action_type = update_data['action_type']
                updated_fields.append('action_type')
            if 'action_data' in update_data:
                card.action_data = json.dumps(update_data['action_data'])
                updated_fields.append('action_data')
            if 'is_active' in update_data:
                card.is_active = update_data['is_active']
                updated_fields.append('is_active')
            
            if not updated_fields:
                 return {"success": False, "error": "No valid fields provided for update"}

            db.session.commit()
            logging.info(f"Admin updated card ID {card_id}. Fields: {', '.join(updated_fields)}")
            return {"success": True, "card": card.to_dict()}
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating card {card_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to update card"}

    def delete_card(self, card_id: int) -> Dict:
        """Soft deletes a card by marking it inactive."""
        try:
            card = Card.query.get(card_id)
            if not card:
                return {"success": False, "error": "Card not found"}

            card.is_active = False
            db.session.commit()
            logging.info(f"Admin deleted (marked inactive) card ID {card_id}")
            return {"success": True, "message": "Card marked as inactive"}
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting card {card_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to delete card"}
            
    # Placeholder for create_special_space if needed
    def create_special_space(self, space_data: Dict) -> Dict:
        logging.warning("SpecialSpaceController.create_special_space not fully implemented.")
        # TODO: Implement logic from original route if needed
        return {"success": False, "error": "Not Implemented"}

    def handle_tax_space(self, game_id, player_id, tax_space_id):
        """
        Handles when a player lands on a tax space.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the space.
            tax_space_id (str): The ID of the tax space.
            
        Returns:
            dict: A dictionary with success status and relevant information.
        """
        try:
            logging.info(f"Player {player_id} landed on Tax Space {tax_space_id} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the tax space details
            tax_space = SpecialSpace.query.get(tax_space_id)
            if not tax_space:
                logging.error(f"Tax space {tax_space_id} not found")
                return {"success": False, "error": "Tax space not found"}
            
            # Get tax space configuration
            tax_config = tax_space.config or {}
            tax_type = tax_config.get("tax_type", "income")  # income or luxury
            tax_rate = tax_config.get("tax_rate", 0.10)      # Default 10%
            flat_amount = tax_config.get("flat_amount", 200) # Default $200
            
            # Get player's net worth and current balance
            player_balance = self.finance_controller.get_balance(player_id)
            
            # Calculate tax amount based on tax type
            tax_amount = 0
            if tax_type == "income":
                # Income tax can be either flat amount or percentage of assets
                if tax_config.get("allow_choice", False):
                    # Player chooses between flat amount and percentage
                    # For this implementation, we'll choose the lower amount
                    percentage_amount = int(player_balance * tax_rate)
                    tax_amount = min(flat_amount, percentage_amount)
                else:
                    # Use the configured flat amount
                    tax_amount = flat_amount
            elif tax_type == "luxury":
                # Luxury tax is typically a flat amount
                tax_amount = flat_amount
            
            # Make sure we don't tax more than the player has
            tax_amount = min(tax_amount, player_balance)
            
            # Process the tax payment
            if tax_amount > 0:
                # Remove funds from player
                payment_result = self.finance_controller.remove_funds(player_id, tax_amount)
                
                if not payment_result["success"]:
                    # Handle insufficient funds
                    logging.warning(f"Player {player_id} has insufficient funds to pay ${tax_amount} tax")
                    return {
                        "success": False,
                        "message": f"Insufficient funds to pay ${tax_amount} tax",
                        "trigger_bankruptcy": True,
                        "tax_amount": tax_amount
                    }
                
                # Add to community fund if configured
                add_to_community_fund = game_state.get_settings().get("taxes_to_community_fund", True)
                if add_to_community_fund:
                    current_fund = game_state.get_community_fund()
                    game_state.set_community_fund(current_fund + tax_amount)
                    
                    # Commit the updated game state
                    self.game_controller.update_game_state(game_id, game_state)
                
                # Prepare response message
                tax_name = "Income Tax" if tax_type == "income" else "Luxury Tax"
                message = f"Player {player.name} paid ${tax_amount} in {tax_name}"
                
                # Add game log
                game_state.add_game_log({
                    "type": "tax_payment",
                    "player_id": player_id,
                    "tax_type": tax_type,
                    "amount": tax_amount,
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # Emit an event to notify clients
                socketio = self.game_controller.socketio
                socketio.emit('player_paid_tax', {
                    'game_id': game_id,
                    'player_id': player_id,
                    'tax_type': tax_type,
                    'tax_amount': tax_amount,
                    'add_to_community_fund': add_to_community_fund,
                    'message': message
                }, room=game_id)
                
                return {
                    "success": True,
                    "tax_amount": tax_amount,
                    "message": message
                }
            else:
                message = f"Player {player.name} didn't need to pay tax (amount was $0)"
                logging.info(message)
                
                return {
                    "success": True,
                    "tax_amount": 0,
                    "message": message
                }
                
        except Exception as e:
            logging.error(f"Error handling tax space: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_jail(self, game_id, player_id, reason="landed"):
        """
        Handles when a player is sent to jail or lands on the jail space as a visitor.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on or is sent to jail.
            reason (str): Reason for jail handling - "landed" (just visiting), 
                         "sent" (sent to jail by card, etc.), or "rolled_doubles" (rolled doubles 3 times).
            
        Returns:
            dict: A dictionary with success status and message.
        """
        try:
            logging.info(f"Player {player_id} jail handling in game {game_id}. Reason: {reason}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            message = ""
            
            if reason == "landed":
                # Player is just visiting jail
                message = f"Player {player.username} is visiting jail."
                logging.info(message)
            elif reason in ["sent", "rolled_doubles"]:
                # Player is sent to jail (by card, by rolling 3 doubles, etc.)
                # Update player state to be in jail
                player_state["in_jail"] = True
                player_state["jail_turns"] = 0  # Start counting turns in jail
                
                # Move player to jail position
                jail_position = next((space["position"] for space in game_state.spaces 
                                     if space.get("type") == "jail"), None)
                
                if jail_position is not None:
                    player_state["position"] = jail_position
                    message = f"Player {player.username} was sent to jail."
                    
                    if reason == "rolled_doubles":
                        message = f"Player {player.username} rolled doubles 3 times and was sent to jail."
                else:
                    logging.error(f"Jail space not found in game {game_id}")
                    return {"success": False, "error": "Jail space not found"}
            
            # Add to game log
            log_entry = {
                "type": "jail_event",
                "player_id": player_id,
                "reason": reason,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('jail_event', {
                'game_id': game_id,
                'player_id': player_id,
                'reason': reason,
                'in_jail': player_state.get("in_jail", False),
                'message': message
            }, room=game_id)
            
            return {
                "success": True,
                "in_jail": player_state.get("in_jail", False),
                "message": message
            }
            
        except Exception as e:
            logging.error(f"Error handling jail: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_get_out_of_jail(self, game_id, player_id, method="pay"):
        """
        Handles a player's attempt to get out of jail.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who wants to get out of jail.
            method (str): Method used - "pay" (pay fine), "card" (use Get Out of Jail Free card),
                          or "roll" (try to roll doubles).
            
        Returns:
            dict: A dictionary with success status and message.
        """
        try:
            logging.info(f"Player {player_id} trying to get out of jail in game {game_id} using method: {method}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Check if player is actually in jail
            if not player_state.get("in_jail", False):
                message = f"Player {player.username} is not in jail."
                logging.warning(message)
                return {"success": False, "error": message}
            
            message = ""
            success = False
            
            # Handle different methods of getting out of jail
            if method == "pay":
                # Get jail fine amount from game config
                jail_fine = game_state.config.get("jail_fine", 50)
                
                # Check if player has enough money
                if player_state.get("balance", 0) >= jail_fine:
                    # Deduct fine from player balance
                    player_state["balance"] -= jail_fine
                    
                    # Add to community fund if configured
                    if game_state.config.get("fines_to_community", True):
                        game_state.community_fund += jail_fine
                    
                    # Set player as out of jail
                    player_state["in_jail"] = False
                    player_state["jail_turns"] = 0
                    
                    message = f"Player {player.username} paid ${jail_fine} to get out of jail."
                    success = True
                else:
                    message = f"Player {player.username} does not have enough money to pay the jail fine."
                    return {"success": False, "error": message}
                
            elif method == "card":
                # Check if player has a Get Out of Jail Free card
                jail_free_cards = player_state.get("jail_free_cards", 0)
                
                if jail_free_cards > 0:
                    # Use one card
                    player_state["jail_free_cards"] = jail_free_cards - 1
                    
                    # Set player as out of jail
                    player_state["in_jail"] = False
                    player_state["jail_turns"] = 0
                    
                    message = f"Player {player.username} used a Get Out of Jail Free card."
                    success = True
                else:
                    message = f"Player {player.username} does not have any Get Out of Jail Free cards."
                    return {"success": False, "error": message}
                
            elif method == "roll":
                # Simulate dice roll
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                is_doubles = dice1 == dice2
                
                message = f"Player {player.username} rolled {dice1} and {dice2}."
                
                if is_doubles:
                    # Player rolled doubles and gets out
                    player_state["in_jail"] = False
                    player_state["jail_turns"] = 0
                    
                    message += " Rolled doubles and got out of jail!"
                    success = True
                else:
                    # Increment jail turns
                    jail_turns = player_state.get("jail_turns", 0) + 1
                    player_state["jail_turns"] = jail_turns
                    
                    # Check if player has been in jail for maximum turns
                    max_jail_turns = game_state.config.get("max_jail_turns", 3)
                    
                    if jail_turns >= max_jail_turns:
                        # Player must pay to get out after max turns
                        jail_fine = game_state.config.get("jail_fine", 50)
                        
                        if player_state.get("balance", 0) >= jail_fine:
                            # Deduct fine from player balance
                            player_state["balance"] -= jail_fine
                            
                            # Add to community fund if configured
                            if game_state.config.get("fines_to_community", True):
                                game_state.community_fund += jail_fine
                            
                            # Set player as out of jail
                            player_state["in_jail"] = False
                            player_state["jail_turns"] = 0
                            
                            message += f" After {max_jail_turns} turns, paid ${jail_fine} to get out of jail."
                            success = True
                        else:
                            message += f" Cannot pay the fine of ${jail_fine} after {jail_turns} turns in jail."
                            return {"success": False, "error": message}
                    else:
                        message += f" Failed to roll doubles. Turns in jail: {jail_turns}/{max_jail_turns}."
                        success = False
            
            # Add to game log if successful
            if success:
                log_entry = {
                    "type": "jail_release",
                    "player_id": player_id,
                    "method": method,
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Update game log
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                # Update the game state
                db.session.commit()
                
                # Emit an event to notify clients
                self.socketio.emit('jail_release', {
                    'game_id': game_id,
                    'player_id': player_id,
                    'method': method,
                    'message': message,
                    'balance': player_state.get("balance", 0)
                }, room=game_id)
            
            return {
                "success": success,
                "in_jail": player_state.get("in_jail", False),
                "jail_turns": player_state.get("jail_turns", 0),
                "message": message
            }
            
        except Exception as e:
            logging.error(f"Error handling get out of jail: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_card_space(self, game_id, player_id, space_type):
        """
        Handles a player landing on a card space (Community Chest or Chance).
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the card space.
            space_type (str): Type of card space - "community_chest" or "chance".
            
        Returns:
            dict: A dictionary with success status, card details, and any effects.
        """
        try:
            logging.info(f"Player {player_id} landed on {space_type} space in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Determine which deck to use
            if space_type not in ["community_chest", "chance"]:
                error_msg = f"Invalid card space type: {space_type}"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Get the appropriate card deck
            card_deck = game_state.config.get(f"{space_type}_cards", [])
            if not card_deck:
                error_msg = f"No {space_type} cards configured for this game"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Clone the deck to avoid modifying the config
            deck = card_deck.copy()
            
            # Check if we need to shuffle
            current_deck = game_state.get(f"{space_type}_deck", [])
            if not current_deck:
                # Initialize or reset the deck
                random.shuffle(deck)
                current_deck = deck
                game_state[f"{space_type}_deck"] = current_deck
            
            # Draw the top card
            card = current_deck.pop(0)
            
            # If deck is empty, reshuffle
            if not current_deck:
                random.shuffle(deck)
                game_state[f"{space_type}_deck"] = deck
            else:
                # Update the remaining deck
                game_state[f"{space_type}_deck"] = current_deck
            
            # Process the card effect
            effect_result = self._process_card_effect(game_state, player, player_state, card)
            
            # Add to game log
            log_entry = {
                "type": space_type,
                "player_id": player_id,
                "card": card.get("title", "Unknown Card"),
                "effect": effect_result.get("message", "Unknown effect"),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('card_drawn', {
                'game_id': game_id,
                'player_id': player_id,
                'card_type': space_type,
                'card': card,
                'effect': effect_result
            }, room=game_id)
            
            return {
                "success": True,
                "card_type": space_type,
                "card": card,
                "effect": effect_result
            }
            
        except Exception as e:
            logging.error(f"Error handling card space: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _process_card_effect(self, game_state, player, player_state, card):
        """
        Process the effect of a drawn card.
        
        Args:
            game_state: The current game state.
            player: The player who drew the card.
            player_state: The player's state in the game.
            card: The card that was drawn.
            
        Returns:
            dict: A dictionary with information about the applied effect.
        """
        effect_type = card.get("type", "")
        effect_value = card.get("value", 0)
        message = card.get("description", "No effect")
        
        # Process different effect types
        if effect_type == "collect":
            # Player collects money
            player_state["balance"] += effect_value
            return {"type": "collect", "amount": effect_value, "message": message}
            
        elif effect_type == "pay":
            # Player pays money
            amount_to_pay = min(effect_value, player_state.get("balance", 0))
            player_state["balance"] -= amount_to_pay
            
            # Add to community fund if configured
            if card.get("to_community", False):
                game_state.community_fund += amount_to_pay
            
            return {"type": "pay", "amount": amount_to_pay, "message": message}
            
        elif effect_type == "move":
            # Player moves to a specific position
            target_position = effect_value
            current_position = player_state.get("position", 0)
            
            # Check if passing GO
            if target_position < current_position:
                # Player passed GO, collect salary
                go_salary = game_state.config.get("go_salary", 200)
                player_state["balance"] += go_salary
                pass_go_msg = f" Passed GO and collected ${go_salary}."
                message += pass_go_msg
            
            # Update position
            player_state["position"] = target_position
            
            return {"type": "move", "position": target_position, "message": message}
            
        elif effect_type == "move_relative":
            # Player moves a relative number of spaces
            current_position = player_state.get("position", 0)
            new_position = (current_position + effect_value) % game_state.config.get("board_size", 40)
            
            # Check if passing GO
            if effect_value > 0 and new_position < current_position:
                # Player passed GO, collect salary
                go_salary = game_state.config.get("go_salary", 200)
                player_state["balance"] += go_salary
                pass_go_msg = f" Passed GO and collected ${go_salary}."
                message += pass_go_msg
            
            # Update position
            player_state["position"] = new_position
            
            return {"type": "move_relative", "position": new_position, "message": message}
            
        elif effect_type == "go_to_jail":
            # Send player to jail
            jail_position = game_state.config.get("jail_position", 10)
            player_state["position"] = jail_position
            player_state["in_jail"] = True
            player_state["jail_turns"] = 0
            
            return {"type": "go_to_jail", "position": jail_position, "message": message}
            
        elif effect_type == "jail_free":
            # Add Get Out of Jail Free card
            current_cards = player_state.get("jail_free_cards", 0)
            player_state["jail_free_cards"] = current_cards + 1
            
            return {"type": "jail_free", "cards": player_state["jail_free_cards"], "message": message}
            
        elif effect_type == "repairs":
            # Pay for repairs on properties
            house_fee = card.get("house_fee", 0)
            hotel_fee = card.get("hotel_fee", 0)
            
            total_fee = 0
            
            # Calculate total fee based on improvements
            for property_id, property_data in player_state.get("properties", {}).items():
                improvements = property_data.get("improvements", 0)
                if improvements == 5:  # Hotel
                    total_fee += hotel_fee
                else:  # Houses
                    total_fee += improvements * house_fee
            
            # Limit payment to available balance
            amount_to_pay = min(total_fee, player_state.get("balance", 0))
            player_state["balance"] -= amount_to_pay
            
            # Add to community fund if configured
            if card.get("to_community", False):
                game_state.community_fund += amount_to_pay
            
            return {"type": "repairs", "amount": amount_to_pay, "message": message}
            
        elif effect_type == "pay_each":
            # Pay each player
            amount_per_player = effect_value
            total_to_pay = 0
            
            # Calculate total amount to pay all other players
            for other_player in game_state.players:
                if other_player.get("id") != player_state.get("id") and other_player.get("active", True):
                    total_to_pay += amount_per_player
            
            # Limit payment to available balance
            amount_to_pay = min(total_to_pay, player_state.get("balance", 0))
            player_state["balance"] -= amount_to_pay
            
            # Distribute evenly among other players
            if total_to_pay > 0:
                amount_per_player_actual = amount_to_pay // len([p for p in game_state.players if p.get("id") != player_state.get("id") and p.get("active", True)])
                
                for other_player in game_state.players:
                    if other_player.get("id") != player_state.get("id") and other_player.get("active", True):
                        other_player["balance"] = other_player.get("balance", 0) + amount_per_player_actual
            
            return {"type": "pay_each", "amount": amount_to_pay, "message": message}
            
        # Default no effect
        return {"type": "none", "message": message}

    def handle_utility_space(self, game_id, player_id, utility_id):
        """
        Handles a player landing on a utility space.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the utility space.
            utility_id (str): The ID of the utility space.
            
        Returns:
            dict: A dictionary with the results of the utility space action.
        """
        try:
            logging.info(f"Player {player_id} landed on utility {utility_id} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Get the utility space
            utility_space = next((s for s in game_state.board if s.get("id") == utility_id), None)
            if not utility_space:
                logging.error(f"Utility space {utility_id} not found in game {game_id}")
                return {"success": False, "error": "Utility space not found"}
            
            # Check if the utility is owned
            owner_id = utility_space.get("owner_id")
            if not owner_id:
                # Utility is not owned, nothing to do
                return {
                    "success": True,
                    "action": "none",
                    "message": "Utility is not owned, no action required"
                }
            
            # Check if the player owns the utility
            if owner_id == player_id:
                # Player owns the utility, nothing to do
                return {
                    "success": True,
                    "action": "none",
                    "message": "You own this utility, no action required"
                }
            
            # Get the owner player state
            owner_state = next((p for p in game_state.players if p.get("id") == owner_id), None)
            if not owner_state:
                logging.error(f"Owner {owner_id} state not found in game {game_id}")
                return {"success": False, "error": "Owner state not found"}
            
            # Calculate rent based on dice roll and number of utilities owned
            dice_roll = player_state.get("last_roll", [1, 1])
            dice_total = sum(dice_roll)
            
            # Count utilities owned by the owner
            owner_utilities = 0
            for space in game_state.board:
                if space.get("type") == "utility" and space.get("owner_id") == owner_id:
                    owner_utilities += 1
            
            # Calculate rent multiplier
            # Standard multipliers: 1 utility = 4x dice, 2 utilities = 10x dice
            multiplier = 4
            if owner_utilities >= 2:
                multiplier = 10
            
            # Calculate rent
            rent = dice_total * multiplier
            
            # Check if player has enough money
            player_balance = player_state.get("balance", 0)
            if player_balance < rent:
                # Player doesn't have enough money
                # In a real implementation, this would trigger mortgage/bankruptcy logic
                logging.warning(f"Player {player_id} doesn't have enough money to pay rent for utility {utility_id}")
                
                # For now, pay what they can
                rent = player_balance
            
            # Transfer money
            player_state["balance"] -= rent
            owner_state["balance"] += rent
            
            # Add to game log
            log_entry = {
                "type": "utility_rent",
                "player_id": player_id,
                "owner_id": owner_id,
                "utility_id": utility_id,
                "dice_roll": dice_total,
                "multiplier": multiplier,
                "rent": rent,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('utility_rent', {
                'game_id': game_id,
                'player_id': player_id,
                'owner_id': owner_id,
                'utility_id': utility_id,
                'dice_roll': dice_total,
                'multiplier': multiplier,
                'rent': rent
            }, room=game_id)
            
            return {
                "success": True,
                "action": "rent_paid",
                "player_id": player_id,
                "owner_id": owner_id,
                "utility_id": utility_id,
                "dice_roll": dice_total,
                "multiplier": multiplier,
                "rent": rent,
                "message": f"Paid ${rent} in utility rent to {owner_state.get('name', 'Owner')}"
            }
            
        except Exception as e:
            logging.error(f"Error handling utility space: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_railroad_space(self, game_id, player_id, railroad_id):
        """
        Handles a player landing on a railroad space.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the railroad space.
            railroad_id (str): The ID of the railroad space.
            
        Returns:
            dict: A dictionary with the results of the railroad space action.
        """
        try:
            logging.info(f"Player {player_id} landed on railroad {railroad_id} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Get the railroad space
            railroad_space = next((s for s in game_state.board if s.get("id") == railroad_id), None)
            if not railroad_space:
                logging.error(f"Railroad space {railroad_id} not found in game {game_id}")
                return {"success": False, "error": "Railroad space not found"}
            
            # Check if the railroad is owned
            owner_id = railroad_space.get("owner_id")
            if not owner_id:
                # Railroad is not owned, nothing to do
                return {
                    "success": True,
                    "action": "none",
                    "message": "Railroad is not owned, no action required"
                }
            
            # Check if the player owns the railroad
            if owner_id == player_id:
                # Player owns the railroad, nothing to do
                return {
                    "success": True,
                    "action": "none",
                    "message": "You own this railroad, no action required"
                }
            
            # Get the owner player state
            owner_state = next((p for p in game_state.players if p.get("id") == owner_id), None)
            if not owner_state:
                logging.error(f"Owner {owner_id} state not found in game {game_id}")
                return {"success": False, "error": "Owner state not found"}
            
            # Count railroads owned by the owner
            owner_railroads = 0
            for space in game_state.board:
                if space.get("type") == "railroad" and space.get("owner_id") == owner_id:
                    owner_railroads += 1
            
            # Calculate rent based on number of railroads owned
            # Standard rents: 1 RR = $25, 2 RR = $50, 3 RR = $100, 4 RR = $200
            base_rent = 25
            rent_multiplier = {1: 1, 2: 2, 3: 4, 4: 8}
            rent = base_rent * rent_multiplier.get(owner_railroads, 1)
            
            # Check if player has enough money
            player_balance = player_state.get("balance", 0)
            if player_balance < rent:
                # Player doesn't have enough money
                # In a real implementation, this would trigger mortgage/bankruptcy logic
                logging.warning(f"Player {player_id} doesn't have enough money to pay rent for railroad {railroad_id}")
                
                # For now, pay what they can
                rent = player_balance
            
            # Transfer money
            player_state["balance"] -= rent
            owner_state["balance"] += rent
            
            # Add to game log
            log_entry = {
                "type": "railroad_rent",
                "player_id": player_id,
                "owner_id": owner_id,
                "railroad_id": railroad_id,
                "owner_railroads": owner_railroads,
                "rent": rent,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('railroad_rent', {
                'game_id': game_id,
                'player_id': player_id,
                'owner_id': owner_id,
                'railroad_id': railroad_id,
                'owner_railroads': owner_railroads,
                'rent': rent
            }, room=game_id)
            
            return {
                "success": True,
                "action": "rent_paid",
                "player_id": player_id,
                "owner_id": owner_id,
                "railroad_id": railroad_id,
                "owner_railroads": owner_railroads,
                "rent": rent,
                "message": f"Paid ${rent} in railroad rent to {owner_state.get('name', 'Owner')}"
            }
            
        except Exception as e:
            logging.error(f"Error handling railroad space: {str(e)}")
            return {"success": False, "error": str(e)} 

    def handle_chance_space(self, game_id, player_id):
        """
        Handle when a player lands on a chance space by drawing a chance card
        and executing its effect.
        
        Args:
            game_id (int): The ID of the game
            player_id (int): The ID of the player who landed on the chance space
        
        Returns:
            dict: Result of the action, including success status and card details
        """
        try:
            logging.info(f"Player {player_id} landed on a chance space in game {game_id}")
            
            # Verify game exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Verify player exists
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get player state - using the player directly instead of looking for it in game_state.players
            # The issue was that game_state doesn't have a 'players' attribute
            player_state = {"id": player.id, "position": player.position, "money": player.money}
            
            # Initialize chance cards if needed
            if not hasattr(game_state, 'chance_cards') or not game_state.chance_cards:
                game_state.chance_cards = self._initialize_chance_cards()
                logging.info(f"Initialized chance cards for game {game_id}")
            
            # Draw a card from the deck (taking the first card and moving it to the end)
            if not game_state.chance_cards:
                logging.error(f"No chance cards available in game {game_id}")
                return {"success": False, "error": "No chance cards available"}
            
            card = game_state.chance_cards.pop(0)
            game_state.chance_cards.append(card)  # Put the card at the end of the deck
            
            # Process the card's effect
            result = self._process_chance_card(game_state, player_id, card)
            
            # Add to game log
            log_entry = {
                "type": "chance_card",
                "player_id": player_id,
                "card_text": card.get("text"),
                "card_action": card.get("action"),
                "result": result,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Save the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('chance_card', {
                'game_id': game_id,
                'player_id': player_id,
                'player_name': player.username,
                'card_text': card.get("text"),
                'card_action': card.get("action"),
                'result': result
            }, room=game_id)
            
            return {
                "success": True,
                "card": card,
                "result": result,
                "message": f"Drew chance card: {card.get('text')}"
            }
            
        except Exception as e:
            logging.error(f"Error handling chance space: {str(e)}")
            return {"success": False, "error": str(e)}

    def process_chance_card(self, player_id, game_id):
        """
        Process a chance card when drawn by a player.
        This is a wrapper around handle_chance_space for socket-based actions.
        
        Args:
            player_id (int): The ID of the player drawing the card
            game_id (int): The ID of the game
            
        Returns:
            dict: Result of the action, including success status and card details
        """
        logging.info(f"Processing chance card for player {player_id} in game {game_id}")
        result = self.handle_chance_space(game_id, player_id)
        
        # Update expected actions to end turn after processing card
        if result.get("success"):
            try:
                game_state = GameState.query.get(game_id)
                if game_state:
                    # Set expected action to end turn
                    game_state.expected_actions = [{
                        "player_id": player_id,
                        "action": "end_turn"
                    }]
                    db.session.commit()
                    logging.info(f"Updated expected actions to end_turn for player {player_id}")
            except Exception as e:
                logging.error(f"Error updating expected actions after chance card: {str(e)}")
        
        return result

    def _initialize_chance_cards(self):
        """
        Initialize the deck of chance cards.
        
        Returns:
            list: A shuffled list of chance cards
        """
        cards = [
            {
                "id": 1,
                "text": "Advance to GO. Collect $200.",
                "action": "move_to",
                "position": 0
            },
            {
                "id": 2,
                "text": "Advance to Illinois Avenue. If you pass GO, collect $200.",
                "action": "move_to",
                "position": 24
            },
            {
                "id": 3,
                "text": "Advance to St. Charles Place. If you pass GO, collect $200.",
                "action": "move_to",
                "position": 11
            },
            {
                "id": 4,
                "text": "Advance to the nearest Utility. If owned, pay owner 10 times amount shown on dice.",
                "action": "move_to_nearest",
                "type": "utility"
            },
            {
                "id": 5,
                "text": "Advance to the nearest Railroad. If owned, pay owner twice the rental.",
                "action": "move_to_nearest",
                "type": "railroad"
            },
            {
                "id": 6,
                "text": "Bank pays you a dividend of $50.",
                "action": "collect",
                "amount": 50
            },
            {
                "id": 7,
                "text": "Get Out of Jail Free.",
                "action": "get_out_of_jail"
            },
            {
                "id": 8,
                "text": "Go back 3 spaces.",
                "action": "move_relative",
                "steps": -3
            },
            {
                "id": 9,
                "text": "Go to Jail. Go directly to Jail. Do not pass GO, do not collect $200.",
                "action": "go_to_jail"
            },
            {
                "id": 10,
                "text": "Make general repairs on all your property: Pay $25 per house and $100 per hotel.",
                "action": "pay_per_building",
                "house_cost": 25,
                "hotel_cost": 100
            },
            {
                "id": 11,
                "text": "Pay speeding fine of $15.",
                "action": "pay",
                "amount": 15
            },
            {
                "id": 12,
                "text": "Take a trip to Reading Railroad. If you pass GO, collect $200.",
                "action": "move_to",
                "position": 5
            },
            {
                "id": 13,
                "text": "Take a walk on the Boardwalk. Advance to Boardwalk.",
                "action": "move_to",
                "position": 39
            },
            {
                "id": 14,
                "text": "You have been elected Chairman of the Board. Pay each player $50.",
                "action": "pay_each_player",
                "amount": 50
            },
            {
                "id": 15,
                "text": "Your building loan matures. Collect $150.",
                "action": "collect",
                "amount": 150
            },
            {
                "id": 16,
                "text": "You have won a crossword competition. Collect $100.",
                "action": "collect",
                "amount": 100
            }
        ]
        
        # Shuffle the cards
        random.shuffle(cards)
        return cards

    def _process_chance_card(self, game_state, player_id, card):
        """
        Process the effect of a chance card.
        
        Args:
            game_state (GameState): The current game state
            player_id (int): The ID of the player who drew the card
            card (dict): The card that was drawn
        
        Returns:
            dict: Result of processing the card
        """
        action = card.get("action")
        result = {"action": action}
        
        # Get player state
        player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
        if not player_state:
            logging.error(f"Player state for {player_id} not found in game {game_state.id}")
            return {"error": "Player state not found"}
        
        # Process card action
        if action == "move_to":
            # Move player to a specific position
            old_position = player_state.get("position", 0)
            new_position = card.get("position", 0)
            
            # Check if passing GO
            if new_position < old_position:
                # Player passes GO (except for direct to jail)
                player_state["balance"] += 200
                result["passed_go"] = True
                result["collect_amount"] = 200
            else:
                result["passed_go"] = False
            
            # Update player position
            player_state["position"] = new_position
            result["old_position"] = old_position
            result["new_position"] = new_position
            
        elif action == "move_relative":
            # Move player a relative number of steps
            old_position = player_state.get("position", 0)
            steps = card.get("steps", 0)
            new_position = (old_position + steps) % 40  # Ensure it wraps around the board
            
            # Update player position
            player_state["position"] = new_position
            result["old_position"] = old_position
            result["new_position"] = new_position
            result["steps"] = steps
            
        elif action == "move_to_nearest":
            # Move player to the nearest utility or railroad
            old_position = player_state.get("position", 0)
            type_to_find = card.get("type")
            
            # Find positions based on type
            if type_to_find == "utility":
                utility_positions = [12, 28]  # Positions of utilities on the board
                nearest_position = self._find_nearest_position(old_position, utility_positions)
                new_position = nearest_position
            elif type_to_find == "railroad":
                railroad_positions = [5, 15, 25, 35]  # Positions of railroads on the board
                nearest_position = self._find_nearest_position(old_position, railroad_positions)
                new_position = nearest_position
            else:
                logging.error(f"Unknown move_to_nearest type: {type_to_find}")
                return {"error": f"Unknown move_to_nearest type: {type_to_find}"}
            
            # Check if passing GO
            if new_position < old_position:
                # Player passes GO
                player_state["balance"] += 200
                result["passed_go"] = True
                result["collect_amount"] = 200
            else:
                result["passed_go"] = False
            
            # Update player position
            player_state["position"] = new_position
            result["old_position"] = old_position
            result["new_position"] = new_position
            result["nearest_type"] = type_to_find
            
        elif action == "collect":
            # Player collects money from the bank
            amount = card.get("amount", 0)
            player_state["balance"] += amount
            result["amount"] = amount
            result["new_balance"] = player_state.get("balance")
            
        elif action == "pay":
            # Player pays money to the bank
            amount = card.get("amount", 0)
            player_state["balance"] -= amount
            result["amount"] = amount
            result["new_balance"] = player_state.get("balance")
            
            # Add money to community fund if configured
            if game_state.community_fund_enabled:
                game_state.community_fund += amount
                result["community_fund"] = game_state.community_fund
            
        elif action == "pay_each_player":
            # Player pays money to each other player
            amount = card.get("amount", 0)
            total_paid = 0
            recipients = []
            
            for p in game_state.players:
                if p.get("id") != player_id and p.get("active", True):
                    # Pay to this player
                    p["balance"] += amount
                    total_paid += amount
                    recipients.append({"player_id": p.get("id"), "amount": amount})
            
            # Deduct total from current player
            player_state["balance"] -= total_paid
            result["amount_per_player"] = amount
            result["total_paid"] = total_paid
            result["recipients"] = recipients
            result["new_balance"] = player_state.get("balance")
            
        elif action == "pay_per_building":
            # Player pays based on number of houses and hotels
            house_cost = card.get("house_cost", 0)
            hotel_cost = card.get("hotel_cost", 0)
            
            # Count player's buildings
            houses = 0
            hotels = 0
            for prop in game_state.properties:
                if prop.get("owner_id") == player_id:
                    houses += prop.get("houses", 0)
                    hotels += prop.get("hotels", 0)
            
            # Calculate and apply payment
            total_cost = (houses * house_cost) + (hotels * hotel_cost)
            player_state["balance"] -= total_cost
            
            result["houses"] = houses
            result["hotels"] = hotels
            result["house_cost"] = house_cost
            result["hotel_cost"] = hotel_cost
            result["total_cost"] = total_cost
            result["new_balance"] = player_state.get("balance")
            
            # Add money to community fund if configured
            if game_state.community_fund_enabled:
                game_state.community_fund += total_cost
                result["community_fund"] = game_state.community_fund
            
        elif action == "get_out_of_jail":
            # Player receives a Get Out of Jail Free card
            player_state["jail_cards"] = player_state.get("jail_cards", 0) + 1
            result["jail_cards"] = player_state.get("jail_cards")
            
        elif action == "go_to_jail":
            # Player goes to jail
            player_state["position"] = 10  # Jail position
            player_state["in_jail"] = True
            player_state["jail_turns"] = 0
            
            result["jail_position"] = 10
            
        else:
            logging.error(f"Unknown card action: {action}")
            return {"error": f"Unknown card action: {action}"}
        
        return result

    def _find_nearest_position(self, current_position, position_list):
        """
        Find the nearest position in a list, moving forward around the board.
        
        Args:
            current_position (int): The current position
            position_list (list): List of positions to find the nearest from
        
        Returns:
            int: The nearest position
        """
        # First, try to find the nearest position ahead of the current position
        ahead_positions = [p for p in position_list if p > current_position]
        if ahead_positions:
            return min(ahead_positions)
        
        # If no positions ahead, wrap around to the beginning of the board
        return min(position_list)

    def handle_community_chest_space(self, game_id, player_id):
        """
        Handles a player landing on a community chest space.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the community chest space.
            
        Returns:
            dict: A dictionary with the results of the community chest card action.
        """
        try:
            logging.info(f"Player {player_id} landed on a community chest space in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state - using the player directly instead of looking for it in game_state.players
            # The issue was that game_state doesn't have a 'players' attribute
            player_state = {"id": player.id, "position": player.position, "balance": player.money}
            
            # Check if there are community chest cards available
            community_chest_cards = game_state.community_chest_cards
            if not community_chest_cards or len(community_chest_cards) == 0:
                # Initialize community chest cards if they don't exist
                community_chest_cards = self._initialize_community_chest_cards()
                game_state.community_chest_cards = community_chest_cards
            
            # Draw a card from the deck
            card = community_chest_cards.pop(0)
            
            # Move the card to the bottom of the deck
            community_chest_cards.append(card)
            game_state.community_chest_cards = community_chest_cards
            
            # Process the card effect
            result = self._process_community_chest_card(game_state, player_state, card)
            
            # Add to game log
            log_entry = {
                "type": "community_chest_card",
                "player_id": player_id,
                "card": card,
                "result": result,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Update the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('community_chest_card', {
                'game_id': game_id,
                'player_id': player_id,
                'card': card,
                'result': result
            }, room=game_id)
            
            return {
                "success": True,
                "action": "community_chest_card",
                "player_id": player_id,
                "card": card,
                "result": result,
                "message": card.get("description", "Drew a community chest card")
            }
            
        except Exception as e:
            logging.error(f"Error handling community chest space: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_community_chest_card(self, player_id, game_id):
        """
        Process a community chest card when drawn by a player.
        This is a wrapper around handle_community_chest_space for socket-based actions.
        
        Args:
            player_id (int): The ID of the player drawing the card
            game_id (int): The ID of the game
            
        Returns:
            dict: Result of the action, including success status and card details
        """
        logging.info(f"Processing community chest card for player {player_id} in game {game_id}")
        result = self.handle_community_chest_space(game_id, player_id)
        
        # Update expected actions to end turn after processing card
        if result.get("success"):
            try:
                game_state = GameState.query.get(game_id)
                if game_state:
                    # Set expected action to end turn
                    game_state.expected_actions = [{
                        "player_id": player_id,
                        "action": "end_turn"
                    }]
                    db.session.commit()
                    logging.info(f"Updated expected actions to end_turn for player {player_id}")
            except Exception as e:
                logging.error(f"Error updating expected actions after community chest card: {str(e)}")
        
        return result
    
    def _initialize_community_chest_cards(self):
        """
        Initialize and shuffle the community chest cards deck.
        
        Returns:
            list: A shuffled list of community chest card dictionaries.
        """
        community_chest_cards = [
            {
                "id": "cc_advance_go",
                "description": "Advance to GO. Collect $200.",
                "type": "move",
                "destination": "go",
                "collect_go": True
            },
            {
                "id": "cc_bank_error",
                "description": "Bank error in your favor. Collect $200.",
                "type": "collect",
                "amount": 200
            },
            {
                "id": "cc_doctor_fee",
                "description": "Doctor's fee. Pay $50.",
                "type": "pay",
                "amount": 50
            },
            {
                "id": "cc_stock_sale",
                "description": "From sale of stock you get $50.",
                "type": "collect",
                "amount": 50
            },
            {
                "id": "cc_get_out_of_jail",
                "description": "Get Out of Jail Free. This card may be kept until needed or traded.",
                "type": "get_out_of_jail"
            },
            {
                "id": "cc_go_to_jail",
                "description": "Go to Jail. Go directly to Jail. Do not pass GO. Do not collect $200.",
                "type": "go_to_jail"
            },
            {
                "id": "cc_holiday_fund",
                "description": "Holiday fund matures. Receive $100.",
                "type": "collect",
                "amount": 100
            },
            {
                "id": "cc_income_tax_refund",
                "description": "Income tax refund. Collect $20.",
                "type": "collect",
                "amount": 20
            },
            {
                "id": "cc_birthday",
                "description": "It's your birthday. Collect $10 from each player.",
                "type": "collect_from_each_player",
                "amount": 10
            },
            {
                "id": "cc_life_insurance",
                "description": "Life insurance matures. Collect $100.",
                "type": "collect",
                "amount": 100
            },
            {
                "id": "cc_hospital_fee",
                "description": "Pay hospital fees of $100.",
                "type": "pay",
                "amount": 100
            },
            {
                "id": "cc_school_fee",
                "description": "Pay school fees of $50.",
                "type": "pay",
                "amount": 50
            },
            {
                "id": "cc_consultancy_fee",
                "description": "Receive $25 consultancy fee.",
                "type": "collect",
                "amount": 25
            },
            {
                "id": "cc_street_repairs",
                "description": "You are assessed for street repairs. Pay $40 per house and $115 per hotel.",
                "type": "pay_per_building",
                "house_fee": 40,
                "hotel_fee": 115
            },
            {
                "id": "cc_beauty_contest",
                "description": "You have won second prize in a beauty contest. Collect $10.",
                "type": "collect",
                "amount": 10
            },
            {
                "id": "cc_inheritance",
                "description": "You inherit $100.",
                "type": "collect",
                "amount": 100
            }
        ]
        
        # Shuffle the deck
        random.shuffle(community_chest_cards)
        
        return community_chest_cards
    
    def _process_community_chest_card(self, game_state, player_state, card):
        """
        Process the effects of a community chest card.
        
        Args:
            game_state (GameState): The game state object.
            player_state (dict): The player state dictionary.
            card (dict): The community chest card to process.
            
        Returns:
            dict: A dictionary with the results of processing the card.
        """
        player_id = player_state.get("id")
        card_type = card.get("type")
        result = {"processed": True, "type": card_type}
        
        try:
            if card_type == "collect":
                # Player receives money
                amount = card.get("amount", 0)
                player_state["balance"] += amount
                result["amount"] = amount
                
            elif card_type == "pay":
                # Player pays money
                amount = card.get("amount", 0)
                player_balance = player_state.get("balance", 0)
                
                # Check if player has enough money
                if player_balance < amount:
                    # In a real implementation, this would trigger mortgage/bankruptcy logic
                    # For now, pay what they can
                    amount = player_balance
                    result["partial_payment"] = True
                
                player_state["balance"] -= amount
                
                # Add to community fund if applicable
                if game_state.rules.get("money_in_free_parking", False):
                    game_state.community_fund += amount
                
                result["amount"] = amount
                
            elif card_type == "collect_from_each_player":
                # Player collects money from each other player
                amount = card.get("amount", 0)
                total_collected = 0
                collections = []
                
                for other_player in game_state.players:
                    if other_player.get("id") != player_id and other_player.get("is_active", True):
                        other_player_balance = other_player.get("balance", 0)
                        
                        # Check if other player has enough money
                        payment_amount = min(amount, other_player_balance)
                        
                        if payment_amount > 0:
                            other_player["balance"] -= payment_amount
                            total_collected += payment_amount
                            
                            collections.append({
                                "player_id": other_player.get("id"),
                                "amount": payment_amount,
                                "full_payment": payment_amount == amount
                            })
                
                player_state["balance"] += total_collected
                result["total_collected"] = total_collected
                result["collections"] = collections
                
            elif card_type == "pay_per_building":
                # Player pays per house and hotel
                house_fee = card.get("house_fee", 0)
                hotel_fee = card.get("hotel_fee", 0)
                total_fee = 0
                property_fees = []
                
                # Count houses and hotels for each property
                for space in game_state.board:
                    if space.get("type") == "property" and space.get("owner_id") == player_id:
                        houses = space.get("houses", 0)
                        hotels = space.get("hotels", 0)
                        property_fee = (houses * house_fee) + (hotels * hotel_fee)
                        
                        if property_fee > 0:
                            total_fee += property_fee
                            property_fees.append({
                                "property_id": space.get("id"),
                                "houses": houses,
                                "hotels": hotels,
                                "fee": property_fee
                            })
                
                player_balance = player_state.get("balance", 0)
                
                # Check if player has enough money
                if player_balance < total_fee:
                    # In a real implementation, this would trigger mortgage/bankruptcy logic
                    # For now, pay what they can
                    total_fee = player_balance
                    result["partial_payment"] = True
                
                player_state["balance"] -= total_fee
                
                # Add to community fund if applicable
                if game_state.rules.get("money_in_free_parking", False):
                    game_state.community_fund += total_fee
                
                result["total_fee"] = total_fee
                result["property_fees"] = property_fees
                
            elif card_type == "get_out_of_jail":
                # Player receives get out of jail free card
                player_state["jail_free_cards"] = player_state.get("jail_free_cards", 0) + 1
                
            elif card_type == "go_to_jail":
                # Player goes to jail
                player_state["in_jail"] = True
                player_state["jail_turns"] = 0
                
                # Find the jail space and move player there
                jail_space = next((s for s in game_state.board if s.get("type") == "jail"), None)
                if jail_space:
                    player_state["position"] = jail_space.get("position", 0)
                    result["jail_position"] = player_state["position"]
                
            elif card_type == "move":
                # Movement will be handled by the move controller
                # This just prepares the data for that controller
                result["requires_move"] = True
                result["card_data"] = card
                
            else:
                logging.warning(f"Unknown community chest card type: {card_type}")
                result["processed"] = False
                result["error"] = f"Unknown card type: {card_type}"
                
            return result
            
        except Exception as e:
            logging.error(f"Error processing community chest card: {str(e)}")
            return {"processed": False, "error": str(e)}

    def handle_jail_action(self, game_id, player_id, action):
        """
        Handles a player's action to try to get out of jail.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player in jail.
            action (str): The action to take ('pay', 'use_card', or 'roll').
            
        Returns:
            dict: A dictionary with the results of the jail action.
        """
        try:
            logging.info(f"Player {player_id} attempting to get out of jail with action: {action} in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get the player state
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Check if player is actually in jail
            if not player_state.get("in_jail", False):
                logging.warning(f"Player {player_id} is not in jail but tried to use jail action")
                return {"success": False, "error": "Player is not in jail"}
            
            # Process the action
            result = {"success": True, "action": action, "player_id": player_id}
            
            if action == "pay":
                # Pay the fine to get out of jail
                jail_fine = game_state.rules.get("jail_fine", 50)  # Default to $50
                
                if player_state["balance"] >= jail_fine:
                    player_state["balance"] -= jail_fine
                    player_state["in_jail"] = False
                    
                    # Add to community fund if rule is enabled
                    if game_state.rules.get("money_in_free_parking", False):
                        game_state.community_fund += jail_fine
                    
                    message = f"Player {player.username} paid ${jail_fine} to get out of jail"
                    result["message"] = message
                    result["amount"] = jail_fine
                    
                    # Add to game log
                    log_entry = {
                        "type": "jail_pay",
                        "player_id": player_id,
                        "amount": jail_fine,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    
                    # Update expected actions
                    game_state.expected_actions = [{
                        "player_id": player_id, 
                        "action": "roll_dice"
                    }]
                else:
                    return {
                        "success": False, 
                        "error": f"Insufficient funds to pay the jail fine of ${jail_fine}",
                        "needed": jail_fine,
                        "balance": player_state["balance"]
                    }
                
            elif action == "use_card":
                # Use Get Out of Jail Free card
                jail_cards = player_state.get("jail_cards", 0)
                
                if jail_cards > 0:
                    player_state["jail_cards"] -= 1
                    player_state["in_jail"] = False
                    
                    message = f"Player {player.username} used a Get Out of Jail Free card"
                    result["message"] = message
                    result["remaining_cards"] = player_state["jail_cards"]
                    
                    # Add to game log
                    log_entry = {
                        "type": "jail_card",
                        "player_id": player_id,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    
                    # Update expected actions
                    game_state.expected_actions = [{
                        "player_id": player_id, 
                        "action": "roll_dice"
                    }]
                else:
                    return {"success": False, "error": "No Get Out of Jail Free cards available"}
                
            elif action == "roll":
                # Try to roll doubles
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                is_doubles = dice1 == dice2
                
                player_state["jail_turns"] = player_state.get("jail_turns", 0) + 1
                max_jail_turns = game_state.rules.get("max_jail_turns", 3)
                
                if is_doubles:
                    # Got doubles, get out of jail
                    player_state["in_jail"] = False
                    message = f"Player {player.username} rolled doubles ({dice1}, {dice2}) and got out of jail"
                    
                    # Move player position based on roll
                    player_state["position"] = (player_state["position"] + dice1 + dice2) % len(game_state.board_config)
                    
                    result["message"] = message
                    result["dice"] = [dice1, dice2]
                    result["doubles"] = True
                    result["position"] = player_state["position"]
                    
                    # Add to game log
                    log_entry = {
                        "type": "jail_roll_success",
                        "player_id": player_id,
                        "dice": [dice1, dice2],
                        "position": player_state["position"],
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    
                    # Check what the player landed on and set expected actions accordingly
                    space = next((s for s in game_state.board_config if s.get("position") == player_state["position"]), None)
                    if space:
                        space_type = space.get("type")
                        result["space_type"] = space_type
                        
                        # Set expected actions based on space type
                        if space_type in ["property", "railroad", "utility"]:
                            if space.get("owner_id") is None:
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "buy_property",
                                    "property_id": space.get("id"),
                                    "options": ["buy", "auction"]
                                }]
                            else:
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "end_turn"
                                }]
                        elif space_type == "tax":
                            game_state.expected_actions = [{
                                "player_id": player_id,
                                "action": "pay_tax",
                                "tax_id": space.get("id")
                            }]
                        elif space_type == "chance":
                            game_state.expected_actions = [{
                                "player_id": player_id,
                                "action": "draw_chance"
                            }]
                        elif space_type == "community_chest":
                            game_state.expected_actions = [{
                                "player_id": player_id,
                                "action": "draw_community_chest"
                            }]
                        elif space_type == "go_to_jail":
                            # Send player to jail
                            return self.handle_go_to_jail(game_id, player_id)
                        else:
                            game_state.expected_actions = [{
                                "player_id": player_id,
                                "action": "end_turn"
                            }]
                    
                elif player_state["jail_turns"] >= max_jail_turns:
                    # Max jail turns reached, must pay to get out
                    jail_fine = game_state.rules.get("jail_fine", 50)
                    
                    if player_state["balance"] >= jail_fine:
                        player_state["balance"] -= jail_fine
                        player_state["in_jail"] = False
                        
                        # Add to community fund if rule is enabled
                        if game_state.rules.get("money_in_free_parking", False):
                            game_state.community_fund += jail_fine
                        
                        message = f"Player {player.username} spent {max_jail_turns} turns in jail and was forced to pay ${jail_fine}"
                        
                        # Roll and move player
                        player_state["position"] = (player_state["position"] + dice1 + dice2) % len(game_state.board_config)
                        
                        result["message"] = message
                        result["dice"] = [dice1, dice2]
                        result["forced_pay"] = True
                        result["amount"] = jail_fine
                        result["position"] = player_state["position"]
                        
                        # Add to game log
                        log_entry = {
                            "type": "jail_forced_pay",
                            "player_id": player_id,
                            "amount": jail_fine,
                            "dice": [dice1, dice2],
                            "position": player_state["position"],
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        
                        # Set expected actions based on the space landed on (same logic as above)
                        space = next((s for s in game_state.board_config if s.get("position") == player_state["position"]), None)
                        if space:
                            space_type = space.get("type")
                            result["space_type"] = space_type
                            
                            # Set expected actions based on space type (same logic as above)
                            if space_type in ["property", "railroad", "utility"]:
                                if space.get("owner_id") is None:
                                    game_state.expected_actions = [{
                                        "player_id": player_id,
                                        "action": "buy_property",
                                        "property_id": space.get("id"),
                                        "options": ["buy", "auction"]
                                    }]
                                else:
                                    game_state.expected_actions = [{
                                        "player_id": player_id,
                                        "action": "end_turn"
                                    }]
                            elif space_type == "tax":
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "pay_tax",
                                    "tax_id": space.get("id")
                                }]
                            elif space_type == "chance":
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "draw_chance"
                                }]
                            elif space_type == "community_chest":
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "draw_community_chest"
                                }]
                            elif space_type == "go_to_jail":
                                # Send player to jail
                                return self.handle_go_to_jail(game_id, player_id)
                            else:
                                game_state.expected_actions = [{
                                    "player_id": player_id,
                                    "action": "end_turn"
                                }]
                    else:
                        # Can't pay and at max turns - would trigger bankruptcy process
                        result["success"] = False
                        result["error"] = f"Insufficient funds to pay the mandatory jail fine of ${jail_fine}"
                        result["needs_bankruptcy_check"] = True
                        result["dice"] = [dice1, dice2]
                        result["jail_turns"] = player_state["jail_turns"]
                        result["max_jail_turns"] = max_jail_turns
                        
                        # Add to game log
                        log_entry = {
                            "type": "jail_bankrupt",
                            "player_id": player_id,
                            "needed": jail_fine,
                            "balance": player_state["balance"],
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                else:
                    # Failed to roll doubles and still have turns left
                    message = f"Player {player.username} rolled ({dice1}, {dice2}) and stays in jail. {max_jail_turns - player_state['jail_turns']} attempts remaining"
                    result["message"] = message
                    result["dice"] = [dice1, dice2]
                    result["jail_turns"] = player_state["jail_turns"]
                    result["remaining_turns"] = max_jail_turns - player_state["jail_turns"]
                    
                    # Add to game log
                    log_entry = {
                        "type": "jail_roll_fail",
                        "player_id": player_id,
                        "dice": [dice1, dice2],
                        "jail_turns": player_state["jail_turns"],
                        "remaining_turns": max_jail_turns - player_state["jail_turns"],
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    
                    # Update expected actions
                    game_state.expected_actions = [{
                        "player_id": player_id,
                        "action": "end_turn"
                    }]
            else:
                return {"success": False, "error": f"Invalid jail action: {action}"}
            
            # Update game log
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            # Commit changes to the database
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('jail_action', {
                'game_id': game_id,
                'player_id': player_id,
                'action': action,
                'result': result
            }, room=game_id)
            
            return result
            
        except Exception as e:
            logging.error(f"Error processing jail action: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_free_parking_space(self, game_id, player_id):
        """
        Handle when a player lands on the Free Parking space.
        If the game has community fund enabled, the player collects the money.
        Otherwise, this is just a free resting place.
        
        Args:
            game_id (int): The ID of the game
            player_id (int): The ID of the player who landed on Free Parking
        
        Returns:
            dict: Result of the action, including success status and amount collected
        """
        try:
            logging.info(f"Player {player_id} landed on Free Parking in game {game_id}")
            
            # Verify game exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Verify player exists
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get player state from game
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            result = {
                "success": True,
                "amount": 0,
                "message": "Free Parking - Just visiting!"
            }
            
            # If community fund is enabled, player collects the money
            if game_state.community_fund_enabled and game_state.community_fund > 0:
                amount = game_state.community_fund
                player_state["balance"] += amount
                game_state.community_fund = 0
                
                result["amount"] = amount
                result["new_balance"] = player_state["balance"]
                result["message"] = f"Collected ${amount} from Free Parking!"
                
                # Add to game log
                log_entry = {
                    "type": "free_parking",
                    "player_id": player_id,
                    "amount": amount,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                logging.info(f"Player {player_id} collected ${amount} from Free Parking in game {game_id}")
            else:
                # Add to game log for just visiting
                log_entry = {
                    "type": "free_parking",
                    "player_id": player_id,
                    "amount": 0,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                logging.info(f"Player {player_id} landed on Free Parking (no funds to collect) in game {game_id}")
            
            # Save the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('free_parking', {
                'game_id': game_id,
                'player_id': player_id,
                'player_name': player.username,
                'amount': result["amount"],
                'message': result["message"]
            }, room=game_id)
            
            return result
            
        except Exception as e:
            logging.error(f"Error handling Free Parking space: {str(e)}")
            return {"success": False, "error": str(e)}

    def handle_go_space(self, game_id, player_id):
        """
        Handle when a player lands directly on the GO space.
        The player gets the GO salary, typically doubled if directly landed on GO.
        
        Args:
            game_id (int): The ID of the game
            player_id (int): The ID of the player who landed on GO
        
        Returns:
            dict: Result of the action, including success status and amount collected
        """
        try:
            logging.info(f"Player {player_id} landed directly on GO in game {game_id}")
            
            # Verify game exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Verify player exists
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Get player state from game
            player_state = next((p for p in game_state.players if p.get("id") == player_id), None)
            if not player_state:
                logging.error(f"Player state for {player_id} not found in game {game_id}")
                return {"success": False, "error": "Player state not found"}
            
            # Get game configuration for GO salary
            config = self.get_game_config(game_id)
            base_go_salary = config.get("go_salary", 200)
            
            # Check if the game has a rule for double salary when landing on GO
            direct_go_multiplier = config.get("direct_go_multiplier", 2)
            go_amount = base_go_salary * direct_go_multiplier
            
            # Update player balance
            player_state["balance"] += go_amount
            
            # Add to game log
            log_entry = {
                "type": "go_direct",
                "player_id": player_id,
                "amount": go_amount,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            current_log = json.loads(game_state.game_log) if game_state.game_log else []
            current_log.append(log_entry)
            game_state.game_log = json.dumps(current_log)
            
            logging.info(f"Player {player_id} collected ${go_amount} for landing directly on GO in game {game_id}")
            
            # Save the game state
            db.session.commit()
            
            # Emit an event to notify clients
            self.socketio.emit('go_direct', {
                'game_id': game_id,
                'player_id': player_id,
                'player_name': player.username,
                'amount': go_amount,
                'message': f"Collected ${go_amount} for landing directly on GO!"
            }, room=game_id)
            
            result = {
                "success": True,
                "amount": go_amount,
                "new_balance": player_state["balance"],
                "message": f"Collected ${go_amount} for landing directly on GO!"
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Error handling GO space: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_game_config(self, game_id):
        """
        Get the game configuration from the database or cache.
        
        Args:
            game_id (int): The ID of the game
        
        Returns:
            dict: The game configuration
        """
        try:
            # Get the game settings from the database
            game_settings = GameSettings.query.filter_by(game_id=game_id).first()
            
            if game_settings and game_settings.config:
                config = json.loads(game_settings.config)
            else:
                # Use default settings if not found
                config = {
                    "go_salary": 200,
                    "direct_go_multiplier": 2,
                    "jail_fee": 50,
                    "luxury_tax": 100,
                    "income_tax_flat": 200,
                    "income_tax_percentage": 0.1,
                    "community_fund_enabled": True
                }
                
            return config
            
        except Exception as e:
            logging.error(f"Error getting game config: {str(e)}")
            # Return default config if error occurs
            return {
                "go_salary": 200,
                "direct_go_multiplier": 2,
                "jail_fee": 50,
                "luxury_tax": 100,
                "income_tax_flat": 200,
                "income_tax_percentage": 0.1,
                "community_fund_enabled": True
            }

    def handle_market_fluctuation_space(self, game_id, player_id):
        """
        Handles when a player lands on a market fluctuation space.
        This delegates to the EconomicCycleController to handle the actual effects.
        
        Args:
            game_id (str): The ID of the game.
            player_id (str): The ID of the player who landed on the space.
            
        Returns:
            dict: A dictionary with the results of the market fluctuation.
        """
        try:
            logging.info(f"Player {player_id} landed on market fluctuation space in game {game_id}")
            
            # Get the game state and validate it exists
            game_state = GameState.query.get(game_id)
            if not game_state:
                logging.error(f"Game {game_id} not found")
                return {"success": False, "error": "Game not found"}
            
            # Get the player and validate they exist
            player = Player.query.get(player_id)
            if not player:
                logging.error(f"Player {player_id} not found")
                return {"success": False, "error": "Player not found"}
            
            # Check if we have access to the economic cycle controller
            if not hasattr(self, 'economic_controller') or not self.economic_controller:
                logging.error("Economic cycle controller not available")
                
                # Use a simple fallback behavior since we can't access the economic controller
                message = "Market fluctuation occurred, but economic system is not available."
                
                # Add to game log
                log_entry = {
                    "type": "market_fluctuation",
                    "player_id": player_id,
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Update game log
                current_log = json.loads(game_state.game_log) if game_state.game_log else []
                current_log.append(log_entry)
                game_state.game_log = json.dumps(current_log)
                
                # Update the game state
                db.session.commit()
                
                # Emit a simple notification
                if self.socketio:
                    self.socketio.emit('game_notification', {
                        'game_id': game_id,
                        'player_id': player_id,
                        'message': message
                    }, room=game_id)
                
                return {
                    "success": True,
                    "message": message
                }
            
            # Delegate to the economic cycle controller to handle the market fluctuation
            result = self.economic_controller.handle_market_fluctuation_space(game_id, player_id)
            return result
            
        except Exception as e:
            logging.error(f"Error handling market fluctuation space: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_to_jail(self, player_id):
        """
        Send a player to jail. This is a wrapper around handle_go_to_jail for better naming.
        
        Args:
            player_id (int): The ID of the player to send to jail.
            
        Returns:
            dict: A dictionary with the results of the jail action.
        """
        # Get the player to determine their game_id
        player = Player.query.get(player_id)
        if not player:
            logging.error(f"Player {player_id} not found in send_to_jail")
            return {"success": False, "error": "Player not found"}
            
        # Call the existing handle_go_to_jail method
        return self.handle_go_to_jail(player.game_id, player_id)