from typing import Dict, List, Optional, Union, Any
import json
import random
from flask_socketio import emit
from datetime import datetime

from src.models.special_space import Card, SpecialSpace, CardDeck, TaxSpace
from src.models.player import Player
from src.models.game_state import GameState
from src.models.banker import Banker
from src.models.community_fund import CommunityFund
from src.models import db


class SpecialSpaceController:
    """Controller for managing special spaces and card actions"""
    
    def __init__(self, socketio, banker, community_fund):
        """Initialize special space controller
        
        Args:
            socketio: Flask-SocketIO instance for real-time communication
            banker: Banker instance for financial transactions
            community_fund: CommunityFund instance for community fund transactions
        """
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
        
        # Initialize card decks
        self.chance_deck = CardDeck("chance", socketio, banker, community_fund)
        self.community_chest_deck = CardDeck("community_chest", socketio, banker, community_fund)
        
        # Initialize tax space handler
        self.tax_handler = TaxSpace(socketio, banker, community_fund)
    
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
        logger.info(f"Player {player_id} landed on {special_space.name} (Type: {space_type}, Position: {position})")
        
        if space_type == "chance":
            return self.process_chance_card(player_id)
            
        elif space_type == "community_chest":
            return self.process_community_chest_card(player_id)
            
        elif space_type == "tax":
            return self.tax_handler.process_tax(player_id, special_space.id)
            
        elif space_type == "go_to_jail":
            return self.send_to_jail(player_id)
            
        elif space_type == "free_parking":
            return self.handle_free_parking(player_id)
            
        elif space_type == "go" or space_type == "jail": # Passive spaces
             logger.debug(f"Player {player_id} landed on passive space {space_type}. No action taken.")
             return {
                 "success": True,
                 "action": "passive_space",
                 "message": f"Landed on {special_space.name}"
             }
        else:
            # Unsupported or unhandled space type
            logger.warning(f"Unhandled special space type '{space_type}' at position {position} for player {player_id}")
            return {
                "success": False,
                "error": f"Unhandled special space type: {space_type}"
            }
    
    def process_chance_card(self, player_id: int) -> Dict:
        """Process a Chance card for a player
        
        Args:
            player_id: ID of the player drawing the card
            
        Returns:
            Card action result
        """
        try:
            card = self.chance_deck.draw_card()
            result = self.chance_deck.execute_card_action(card, player_id)
            
            # Ensure result contains necessary info for logging/UI
            result['card_title'] = card.title
            result['card_description'] = card.description
            
            # Clear expected action state AFTER successful execution
            if result.get("success", False):
                game_state = GameState.query.first() # Re-fetch might be needed if action modified it
                if game_state:
                    game_state.expected_action_type = None
                    game_state.expected_action_details = None
                    db.session.add(game_state)
                    db.session.commit() # Commit the clearing of the expected state
                    logger.info(f"Cleared expected action state for player {player_id} after Chance card.")
                else:
                    logger.error(f"Could not find GameState to clear expected action after Chance card for player {player_id}")

            # Emit event for UI updates
            self.socketio.emit('chance_card_drawn', {
                "player_id": player_id,
                "card": card.to_dict(),
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Chance card for player {player_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing Chance card: {str(e)}"
            }
    
    def process_community_chest_card(self, player_id: int) -> Dict:
        """Process a Community Chest card for a player
        
        Args:
            player_id: ID of the player drawing the card
            
        Returns:
            Card action result
        """
        try:
            card = self.community_chest_deck.draw_card()
            result = self.community_chest_deck.execute_card_action(card, player_id)
            
            # Ensure result contains necessary info for logging/UI
            result['card_title'] = card.title
            result['card_description'] = card.description
            
            # Clear expected action state AFTER successful execution
            if result.get("success", False):
                game_state = GameState.query.first() # Re-fetch might be needed if action modified it
                if game_state:
                    game_state.expected_action_type = None
                    game_state.expected_action_details = None
                    db.session.add(game_state)
                    db.session.commit() # Commit the clearing of the expected state
                    logger.info(f"Cleared expected action state for player {player_id} after Community Chest card.")
                else:
                    logger.error(f"Could not find GameState to clear expected action after CC card for player {player_id}")

            # Emit event for UI updates
            self.socketio.emit('community_chest_card_drawn', {
                "player_id": player_id,
                "card": card.to_dict(),
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Community Chest card for player {player_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing Community Chest card: {str(e)}"
            }
    
    def send_to_jail(self, player_id: int) -> Dict:
        """Send a player to jail
        
        Args:
            player_id: ID of the player to send to jail
            
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
        player.position = 10  # Jail position
        player.in_jail = True
        player.jail_turns = 0 # Start count at 0, increment at start of player's turn while in jail
        db.session.commit()
        logger.info(f"Player {player.username} (ID: {player_id}) sent to jail. Position set to {player.position}, in_jail={player.in_jail}, jail_turns={player.jail_turns}")
        
        # Emit event for UI updates
        self.socketio.emit('player_sent_to_jail', {
            "player_id": player_id,
            "player_name": player.username,
            "jail_position": 10,
            "jail_turns": 0 # Reflect initial state
        })
        
        return {
            "success": True,
            "player_id": player_id,
            "action": "sent_to_jail",
            "jail_position": 10,
            "jail_turns": 0 # Reflect initial state
        }
    
    def handle_free_parking(self, player_id: int) -> Dict:
        """Handle player landing on Free Parking
        
        Args:
            player_id: ID of the player who landed on Free Parking
            
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
        
        # Check if free parking collects fees
        settings = game_state.settings
        collects_fees = settings.get("free_parking_collects_fees", False)
        logger.info(f"Player {player_id} landed on Free Parking. Collect fees enabled: {collects_fees}")
        
        if collects_fees and self.community_fund:
            # Transfer community fund to player
            funds = self.community_fund.funds
            logger.info(f"Community fund balance: ${funds}")
            
            if funds > 0:
                # Transfer funds from community fund to player
                transaction = self.banker.transfer("community_fund", player_id, funds, "Free Parking bonus")
                
                # Emit event for UI updates
                self.socketio.emit('free_parking_bonus', {
                    "player_id": player_id,
                    "player_name": player.username,
                    "amount": funds,
                    "transaction_id": transaction.id if transaction else None
                })
                
                logger.info(f"Awarded ${funds} Free Parking bonus to player {player_id}")
                return {
                    "success": True,
                    "player_id": player_id,
                    "action": "free_parking_bonus",
                    "amount": funds,
                    "transaction_id": transaction.id if transaction else None
                }
            else:
                logger.info("Free Parking bonus not awarded: Community fund is empty.")
            
        # If no funds or feature disabled, just return basic result
        logger.info(f"Player {player_id} rests at Free Parking.")
        return {
            "success": True,
            "player_id": player_id,
            "action": "free_parking",
            "message": "Enjoy your free parking!"
        }
    
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
                "description": "Advance to Illinois Avenue. If you pass Go, collect $200",
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
                "description": "Take a trip to Reading Railroad. If you pass Go, collect $200",
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
        self.chance_deck = CardDeck("chance", self.socketio, self.banker, self.community_fund)
        self.community_chest_deck = CardDeck("community_chest", self.socketio, self.banker, self.community_fund)
        
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
            logger.info(f"Admin created new card: ID {card.id}, Title: {title}")
            return {"success": True, "card": card.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating card: {e}", exc_info=True)
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
            logger.info(f"Admin updated card ID {card_id}. Fields: {', '.join(updated_fields)}")
            return {"success": True, "card": card.to_dict()}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating card {card_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to update card"}

    def delete_card(self, card_id: int) -> Dict:
        """Soft deletes a card by marking it inactive."""
        try:
            card = Card.query.get(card_id)
            if not card:
                return {"success": False, "error": "Card not found"}

            card.is_active = False
            db.session.commit()
            logger.info(f"Admin deleted (marked inactive) card ID {card_id}")
            return {"success": True, "message": "Card marked as inactive"}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting card {card_id}: {e}", exc_info=True)
            return {"success": False, "error": "Failed to delete card"}
            
    # Placeholder for create_special_space if needed
    def create_special_space(self, space_data: Dict) -> Dict:
        logger.warning("SpecialSpaceController.create_special_space not fully implemented.")
        # TODO: Implement logic from original route if needed
        return {"success": False, "error": "Not Implemented"} 