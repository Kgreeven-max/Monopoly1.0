from datetime import datetime
import random
import json
from typing import Dict, List, Optional, Tuple, Union
import logging

from src.models import db
from src.models.game_state import GameState
from src.models.property import Property
from src.models.player import Player
from src.models.community_fund import CommunityFund


class Card(db.Model):
    """Model for Community Chest and Chance cards"""
    id = db.Column(db.Integer, primary_key=True)
    card_type = db.Column(db.String(20), nullable=False)  # 'chance' or 'community_chest'
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # 'move', 'pay', 'collect', 'jail', etc.
    action_data = db.Column(db.Text, nullable=False)  # JSON data for specific action
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Card {self.id}: {self.title}>"

    def to_dict(self) -> Dict:
        """Convert card to dictionary"""
        return {
            "id": self.id,
            "card_type": self.card_type,
            "title": self.title,
            "description": self.description,
            "action_type": self.action_type,
            "action_data": json.loads(self.action_data),
            "is_active": self.is_active,
            "image_url": self.image_url
        }


class SpecialSpace(db.Model):
    """Model for special spaces on the game board"""
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False, unique=True)
    space_type = db.Column(db.String(50), nullable=False)  # 'chance', 'community_chest', 'tax', 'go', 'jail', etc.
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    action_data = db.Column(db.Text, nullable=True)  # JSON data for specific action
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<SpecialSpace {self.id}: {self.name} at position {self.position}>"

    def to_dict(self) -> Dict:
        """Convert special space to dictionary"""
        result = {
            "id": self.id,
            "position": self.position,
            "space_type": self.space_type,
            "name": self.name,
            "description": self.description,
        }
        
        if self.action_data:
            result["action_data"] = json.loads(self.action_data)
            
        return result


class CardDeck:
    """Represents a deck of Chance or Community Chest cards."""
    def __init__(self, card_type: str, socketio, banker, community_fund):
        self.card_type = card_type
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
        self.cards: List[Card] = []
        self.discard_pile: List[Card] = []
        # Remove immediate initialization
        # self._initialize_deck()
        self.logger = logging.getLogger(f"CardDeck_{card_type}")
        self.logger.info(f"{card_type.capitalize()} CardDeck initialized.")

    def _initialize_deck(self):
        """Load cards from the database and shuffle them."""
        self.logger.info(f"Loading and shuffling {self.card_type} deck from database.")
        try:
            # This query needs the app context
            self.cards = Card.query.filter_by(card_type=self.card_type, is_active=True).all()
            if not self.cards:
                 self.logger.warning(f"No active cards found for deck type '{self.card_type}' in the database.")
                 # TODO: Maybe load default cards if none found?
            self.discard_pile = []
            random.shuffle(self.cards)
            self.logger.info(f"Deck initialized with {len(self.cards)} cards.")
        except Exception as e:
             self.logger.error(f"Error initializing card deck from database: {e}", exc_info=True)
             # Keep self.cards empty or raise?
             self.cards = [] 

    def draw_card(self) -> Optional[Card]:
        """Draw a card from the deck, reshuffling discard pile if necessary."""
        # Lazy load deck if not already initialized
        if not self.cards and not self.discard_pile: 
             # Check both, because if only discard pile has cards, we reshuffle below
             self._initialize_deck()
             # If initialization failed or found no cards, return None
             if not self.cards: 
                 self.logger.error(f"Cannot draw card: {self.card_type} deck is empty and could not be initialized.")
                 return None

        if not self.cards:
            self.logger.info(f"Deck empty, reshuffling discard pile ({len(self.discard_pile)} cards) into deck.")
            self.cards = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.cards)
            # If still no cards after reshuffle (shouldn't happen if discard pile had cards), return None
            if not self.cards:
                 self.logger.error(f"Cannot draw card: Deck empty even after reshuffling discard pile.")
                 return None

        drawn_card = self.cards.pop(0)
        self.logger.debug(f"Drew card: {drawn_card.description[:50]}... (Type: {self.card_type})")
        return drawn_card
    
    def execute_card_action(self, card: Card, player_id: int) -> Dict:
        """Execute the action associated with a card
        
        Args:
            card: The card to execute
            player_id: ID of the player who drew the card
            
        Returns:
            Dictionary with action results
        """
        player = Player.query.get(player_id)
        game_state = GameState.query.first()
        
        if not player or not game_state:
            return {
                "success": False,
                "error": "Player or game state not found"
            }
        
        # Parse action data
        action_data = json.loads(card.action_data)
        result = {
            "success": True,
            "card": card.to_dict(),
            "player_id": player_id,
            "player_name": player.username,
            "action_type": card.action_type,
            "action_result": {}
        }
        
        # Execute action based on action_type
        if card.action_type == "move":
            result["action_result"] = self._handle_move_action(player, action_data)
        
        elif card.action_type == "pay":
            result["action_result"] = self._handle_pay_action(player, action_data)
        
        elif card.action_type == "collect":
            result["action_result"] = self._handle_collect_action(player, action_data)
        
        elif card.action_type == "jail":
            result["action_result"] = self._handle_jail_action(player, action_data)
        
        elif card.action_type == "repairs":
            result["action_result"] = self._handle_repairs_action(player, action_data)
        
        elif card.action_type == "birthday":
            result["action_result"] = self._handle_birthday_action(player, action_data)
        
        elif card.action_type == "advance_to_property":
            result["action_result"] = self._handle_advance_to_property_action(player, action_data)
        
        # Broadcast card drawn event
        if self.socketio:
            self.socketio.emit('card_drawn', result)
        
        return result
    
    def _handle_move_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle move actions
        
        Args:
            player: Player who drew the card
            action_data: Dictionary with action details
            
        Returns:
            Dictionary with action results
        """
        move_type = action_data.get("move_type")
        
        if move_type == "forward":
            spaces = action_data.get("spaces", 0)
            new_position = (player.position + spaces) % 40
            player.position = new_position
            db.session.commit()
            return {
                "move_type": "forward",
                "spaces": spaces,
                "new_position": new_position
            }
            
        elif move_type == "backward":
            spaces = action_data.get("spaces", 0)
            new_position = (player.position - spaces) % 40
            player.position = new_position
            db.session.commit()
            return {
                "move_type": "backward",
                "spaces": spaces,
                "new_position": new_position
            }
            
        elif move_type == "to_position":
            position = action_data.get("position", 0)
            # Check if passing Go
            if position < player.position:
                # Player passed Go
                if self.banker:
                    game_state = GameState.query.first()
                    go_salary = game_state.settings.get("go_salary", 200)
                    self.banker.transfer("bank", player.id, go_salary, "Passed Go")
                
            player.position = position
            db.session.commit()
            return {
                "move_type": "to_position",
                "position": position
            }
            
        elif move_type == "nearest":
            space_type = action_data.get("space_type")
            if space_type == "railroad":
                return self._move_to_nearest_railroad(player)
            elif space_type == "utility":
                return self._move_to_nearest_utility(player)
            
        return {"error": "Invalid move type"}
    
    def _handle_pay_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle payment actions"""
        if not self.banker:
            return {"error": "Banker not available"}
        
        amount = action_data.get("amount", 0)
        recipient = action_data.get("recipient", "bank")
        description = action_data.get("description", "Card payment")
        
        if recipient == "community_fund" and self.community_fund:
            transaction = self.banker.transfer(player.id, "community_fund", amount, description)
            return {
                "amount": amount,
                "recipient": "community_fund",
                "transaction_id": transaction.id if transaction else None
            }
        else:
            transaction = self.banker.transfer(player.id, recipient, amount, description)
            return {
                "amount": amount,
                "recipient": recipient,
                "transaction_id": transaction.id if transaction else None
            }
    
    def _handle_collect_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle collection actions"""
        if not self.banker:
            return {"error": "Banker not available"}
        
        amount = action_data.get("amount", 0)
        source = action_data.get("source", "bank")
        description = action_data.get("description", "Card collection")
        
        if source == "community_fund" and self.community_fund:
            if self.community_fund.funds >= amount:
                transaction = self.banker.transfer("community_fund", player.id, amount, description)
                return {
                    "amount": amount,
                    "source": "community_fund",
                    "transaction_id": transaction.id if transaction else None
                }
            else:
                # Not enough funds, collect from bank instead
                transaction = self.banker.transfer("bank", player.id, amount, description)
                return {
                    "amount": amount,
                    "source": "bank",
                    "transaction_id": transaction.id if transaction else None
                }
        else:
            transaction = self.banker.transfer(source, player.id, amount, description)
            return {
                "amount": amount,
                "source": source,
                "transaction_id": transaction.id if transaction else None
            }
    
    def _handle_jail_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle jail actions"""
        action = action_data.get("action")
        
        if action == "go_to_jail":
            player.position = 10  # Jail position
            player.in_jail = True
            player.jail_turns = 3
            db.session.commit()
            return {
                "action": "go_to_jail",
                "jail_position": 10,
                "jail_turns": 3
            }
            
        elif action == "get_out_of_jail":
            player.jail_cards += 1
            db.session.commit()
            return {
                "action": "get_out_of_jail",
                "jail_cards": player.jail_cards
            }
            
        return {"error": "Invalid jail action"}
    
    def _handle_repairs_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle repair actions"""
        if not self.banker:
            return {"error": "Banker not available"}
        
        cost_per_house = action_data.get("cost_per_house", 0)
        cost_per_hotel = action_data.get("cost_per_hotel", 0)
        description = action_data.get("description", "Repairs payment")
        
        # Get player properties and count houses/hotels
        properties = Property.query.filter_by(owner_id=player.id).all()
        house_count = 0
        hotel_count = 0
        
        for prop in properties:
            development_level = prop.get_development_level()
            if development_level == 4:  # Advanced Development (Hotel equivalent)
                hotel_count += 1
            elif 1 <= development_level <= 3:  # Basic to Intermediate Development (House equivalent)
                house_count += development_level
        
        total_cost = (house_count * cost_per_house) + (hotel_count * cost_per_hotel)
        
        if total_cost > 0:
            transaction = self.banker.transfer(player.id, "bank", total_cost, description)
            return {
                "houses": house_count,
                "hotels": hotel_count,
                "cost_per_house": cost_per_house,
                "cost_per_hotel": cost_per_hotel,
                "total_cost": total_cost,
                "transaction_id": transaction.id if transaction else None
            }
        
        return {
            "houses": house_count,
            "hotels": hotel_count,
            "cost_per_house": cost_per_house,
            "cost_per_hotel": cost_per_hotel,
            "total_cost": 0
        }
    
    def _handle_birthday_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle birthday actions (collect from each player)"""
        if not self.banker:
            return {"error": "Banker not available"}
        
        amount_per_player = action_data.get("amount", 0)
        description = action_data.get("description", "Birthday celebration")
        
        # Get all other active players
        players = Player.query.filter(Player.id != player.id, Player.in_game == True).all()
        total_collected = 0
        player_payments = []
        
        for other_player in players:
            # Transfer from other player to the birthday player
            actual_amount = min(amount_per_player, other_player.cash)
            if actual_amount > 0:
                transaction = self.banker.transfer(other_player.id, player.id, actual_amount, description)
                total_collected += actual_amount
                player_payments.append({
                    "player_id": other_player.id,
                    "player_name": other_player.username,
                    "amount": actual_amount,
                    "transaction_id": transaction.id if transaction else None
                })
        
        return {
            "amount_per_player": amount_per_player,
            "total_collected": total_collected,
            "player_count": len(players),
            "player_payments": player_payments
        }
    
    def _handle_advance_to_property_action(self, player: Player, action_data: Dict) -> Dict:
        """Handle advance to property actions"""
        property_group = action_data.get("property_group")
        properties = Property.query.filter_by(group=property_group).all()
        
        if not properties:
            return {"error": "No properties found in group"}
        
        # Sort properties by position
        properties.sort(key=lambda p: p.position)
        
        # Find the next property in the group based on player position
        next_property = None
        for prop in properties:
            if prop.position > player.position:
                next_property = prop
                break
        
        # If no property ahead, wrap around to the first one
        if not next_property and properties:
            next_property = properties[0]
            # Player passes Go
            if self.banker:
                game_state = GameState.query.first()
                go_salary = game_state.settings.get("go_salary", 200)
                self.banker.transfer("bank", player.id, go_salary, "Passed Go")
        
        if next_property:
            player.position = next_property.position
            db.session.commit()
            return {
                "property_group": property_group,
                "property_id": next_property.id,
                "property_name": next_property.name,
                "new_position": next_property.position
            }
        
        return {"error": "Could not advance to property"}
    
    def _move_to_nearest_railroad(self, player: Player) -> Dict:
        """Move player to the nearest railroad"""
        # Railroad positions: 5, 15, 25, 35
        railroad_positions = [5, 15, 25, 35]
        player_pos = player.position
        
        # Find the nearest railroad ahead of the player
        nearest_railroad = None
        for pos in railroad_positions:
            if pos > player_pos:
                nearest_railroad = pos
                break
        
        # If no railroad ahead, wrap around to the first one
        if nearest_railroad is None:
            nearest_railroad = railroad_positions[0]
            # Player passes Go
            if self.banker:
                game_state = GameState.query.first()
                go_salary = game_state.settings.get("go_salary", 200)
                self.banker.transfer("bank", player.id, go_salary, "Passed Go")
        
        player.position = nearest_railroad
        db.session.commit()
        
        # Get the railroad property
        railroad_property = Property.query.filter_by(position=nearest_railroad).first()
        
        return {
            "move_type": "nearest",
            "space_type": "railroad",
            "new_position": nearest_railroad,
            "property_id": railroad_property.id if railroad_property else None,
            "property_name": railroad_property.name if railroad_property else "Railroad"
        }
    
    def _move_to_nearest_utility(self, player: Player) -> Dict:
        """Move player to the nearest utility"""
        # Utility positions: 12, 28
        utility_positions = [12, 28]
        player_pos = player.position
        
        # Find the nearest utility ahead of the player
        nearest_utility = None
        for pos in utility_positions:
            if pos > player_pos:
                nearest_utility = pos
                break
        
        # If no utility ahead, wrap around to the first one
        if nearest_utility is None:
            nearest_utility = utility_positions[0]
            # Player passes Go
            if self.banker:
                game_state = GameState.query.first()
                go_salary = game_state.settings.get("go_salary", 200)
                self.banker.transfer("bank", player.id, go_salary, "Passed Go")
        
        player.position = nearest_utility
        db.session.commit()
        
        # Get the utility property
        utility_property = Property.query.filter_by(position=nearest_utility).first()
        
        return {
            "move_type": "nearest",
            "space_type": "utility",
            "new_position": nearest_utility,
            "property_id": utility_property.id if utility_property else None,
            "property_name": utility_property.name if utility_property else "Utility"
        }


class TaxSpace:
    """Class to handle tax space operations"""
    
    def __init__(self, socketio=None, banker=None, community_fund=None):
        """Initialize tax space handler
        
        Args:
            socketio: SocketIO instance for broadcasting events
            banker: Banker instance for financial transactions
            community_fund: CommunityFund instance for community fund transactions
        """
        self.socketio = socketio
        self.banker = banker
        self.community_fund = community_fund
    
    def process_tax(self, player_id: int, space_id: int) -> Dict:
        """Process tax payment when player lands on a tax space
        
        Args:
            player_id: ID of the player who landed on the tax space
            space_id: ID of the tax space
            
        Returns:
            Dictionary with tax results
        """
        player = Player.query.get(player_id)
        tax_space = SpecialSpace.query.get(space_id)
        game_state = GameState.query.first()
        
        if not player or not tax_space or not game_state:
            return {
                "success": False,
                "error": "Player, tax space, or game state not found"
            }
        
        # Parse tax data
        tax_data = json.loads(tax_space.action_data) if tax_space.action_data else {}
        
        # Calculate tax amount
        tax_amount = self._calculate_tax_amount(player, tax_data, game_state)
        
        # Process tax payment
        if self.banker:
            destination = tax_data.get("destination", "community_fund")
            description = f"Tax payment: {tax_space.name}"
            
            if destination == "community_fund" and self.community_fund:
                transaction = self.banker.transfer(player.id, "community_fund", tax_amount, description)
            else:
                transaction = self.banker.transfer(player.id, "bank", tax_amount, description)
            
            result = {
                "success": True,
                "player_id": player.id,
                "player_name": player.username,
                "tax_space_id": tax_space.id,
                "tax_space_name": tax_space.name,
                "tax_amount": tax_amount,
                "transaction_id": transaction.id if transaction else None,
                "destination": destination
            }
            
            # Broadcast tax payment
            if self.socketio:
                self.socketio.emit('tax_paid', result)
            
            return result
        
        return {
            "success": False,
            "error": "Banker not available"
        }
    
    def _calculate_tax_amount(self, player: Player, tax_data: Dict, game_state: GameState) -> int:
        """Calculate tax amount based on tax type and economic conditions
        
        Args:
            player: Player who landed on the tax space
            tax_data: Dictionary with tax configuration
            game_state: Current game state
            
        Returns:
            Tax amount as integer
        """
        tax_type = tax_data.get("tax_type", "fixed")
        
        if tax_type == "fixed":
            # Fixed amount tax
            base_amount = tax_data.get("amount", 200)
            
            # Apply economic phase multiplier
            economic_phase = game_state.inflation_state
            phase_multipliers = {
                "recession": 0.8,  # Lower taxes during recession
                "normal": 1.0,
                "growth": 1.1,
                "boom": 1.2   # Higher taxes during boom
            }
            
            # Default to 1.0 if phase not found
            phase_multiplier = phase_multipliers.get(economic_phase, 1.0)
            
            return int(base_amount * phase_multiplier)
            
        elif tax_type == "percentage":
            # Percentage of player's net worth
            percentage = tax_data.get("percentage", 10)
            
            # Calculate player's net worth
            net_worth = player.cash
            
            # Add property values
            properties = Property.query.filter_by(owner_id=player.id).all()
            for prop in properties:
                if not prop.is_mortgaged:
                    net_worth += prop.current_price
            
            # Apply percentage
            return int((percentage / 100) * net_worth)
            
        else:
            # Default to fixed 200
            return 200 