import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json

from src.controllers.special_space_controller import SpecialSpaceController
from src.models.game_state import GameState
from src.models.player import Player
from src.models.special_space import SpecialSpace, Card, CardDeck, TaxSpace

class TestSpecialSpaceController(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.socketio = MagicMock()
        self.game_controller = MagicMock()
        self.economic_controller = MagicMock()
        self.finance_controller = MagicMock()
        
        self.special_space_controller = SpecialSpaceController(
            socketio=self.socketio,
            game_controller=self.game_controller,
            economic_controller=self.economic_controller
        )
        
        # Mock the finance controller for the special space controller
        self.special_space_controller.finance_controller = self.finance_controller
        
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    @patch('src.controllers.special_space_controller.SpecialSpace')
    @patch('src.controllers.special_space_controller.db.session')
    def test_handle_tax_space_income_tax(self, mock_session, mock_special_space, mock_player, mock_game_state):
        """Test handling a player landing on an income tax space."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        tax_space_id = "tax789"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.get_settings = MagicMock(return_value={"taxes_to_community_fund": True})
        mock_game.get_community_fund = MagicMock(return_value=500)
        mock_game.set_community_fund = MagicMock()
        mock_game.add_game_log = MagicMock()
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.name = "Test Player"
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock tax space
        mock_tax_space = MagicMock()
        mock_tax_space.id = tax_space_id
        mock_tax_space.config = {
            "tax_type": "income",
            "tax_rate": 0.1,
            "flat_amount": 200
        }
        mock_special_space.query.get.return_value = mock_tax_space
        
        # Mock finance controller
        self.finance_controller.get_balance = MagicMock(return_value=1000)
        self.finance_controller.remove_funds = MagicMock(return_value={"success": True})
        
        # Test the method
        result = self.special_space_controller.handle_tax_space(game_id, player_id, tax_space_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["tax_amount"], 200)  # Flat amount for income tax
        self.assertIn("paid $200 in Income Tax", result["message"])
        
        # Verify player funds were deducted
        self.finance_controller.remove_funds.assert_called_once_with(player_id, 200)
        
        # Verify community fund was updated
        mock_game.set_community_fund.assert_called_once_with(700)  # 500 + 200
        
        # Verify game log was updated
        mock_game.add_game_log.assert_called_once()
        
        # Verify socketio emit was called
        self.socketio.emit.assert_called_once()
        
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    @patch('src.controllers.special_space_controller.SpecialSpace')
    @patch('src.controllers.special_space_controller.db.session')
    def test_handle_tax_space_luxury_tax(self, mock_session, mock_special_space, mock_player, mock_game_state):
        """Test handling a player landing on a luxury tax space."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        tax_space_id = "tax789"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.get_settings = MagicMock(return_value={"taxes_to_community_fund": True})
        mock_game.get_community_fund = MagicMock(return_value=500)
        mock_game.set_community_fund = MagicMock()
        mock_game.add_game_log = MagicMock()
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.name = "Test Player"
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock tax space
        mock_tax_space = MagicMock()
        mock_tax_space.id = tax_space_id
        mock_tax_space.config = {
            "tax_type": "luxury",
            "flat_amount": 100
        }
        mock_special_space.query.get.return_value = mock_tax_space
        
        # Mock finance controller
        self.finance_controller.get_balance = MagicMock(return_value=1000)
        self.finance_controller.remove_funds = MagicMock(return_value={"success": True})
        
        # Test the method
        result = self.special_space_controller.handle_tax_space(game_id, player_id, tax_space_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["tax_amount"], 100)  # Flat amount for luxury tax
        self.assertIn("paid $100 in Luxury Tax", result["message"])
        
        # Verify player funds were deducted
        self.finance_controller.remove_funds.assert_called_once_with(player_id, 100)
        
        # Verify community fund was updated
        mock_game.set_community_fund.assert_called_once_with(600)  # 500 + 100
        
        # Verify game log was updated
        mock_game.add_game_log.assert_called_once()
        
        # Verify socketio emit was called
        self.socketio.emit.assert_called_once()
    
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    @patch('src.controllers.special_space_controller.SpecialSpace')
    @patch('src.controllers.special_space_controller.db.session')
    def test_handle_tax_space_insufficient_funds(self, mock_session, mock_special_space, mock_player, mock_game_state):
        """Test handling a player with insufficient funds landing on a tax space."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        tax_space_id = "tax789"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.get_settings = MagicMock(return_value={"taxes_to_community_fund": True})
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.name = "Test Player"
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock tax space
        mock_tax_space = MagicMock()
        mock_tax_space.id = tax_space_id
        mock_tax_space.config = {
            "tax_type": "income",
            "flat_amount": 200
        }
        mock_special_space.query.get.return_value = mock_tax_space
        
        # Mock finance controller - insufficient funds
        self.finance_controller.get_balance = MagicMock(return_value=150)
        self.finance_controller.remove_funds = MagicMock(return_value={"success": False})
        
        # Test the method
        result = self.special_space_controller.handle_tax_space(game_id, player_id, tax_space_id)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertTrue(result["trigger_bankruptcy"])
        self.assertEqual(result["tax_amount"], 150)  # Limited to player's balance
        
        # Verify funds removal attempt
        self.finance_controller.remove_funds.assert_called_once_with(player_id, 150)
        
        # Verify no community fund update
        mock_game.set_community_fund.assert_not_called()
    
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    @patch('src.controllers.special_space_controller.Card')
    @patch('src.controllers.special_space_controller.db.session')
    def test_handle_community_chest_space(self, mock_session, mock_card, mock_player, mock_game_state):
        """Test handling a player landing on a community chest space."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.username = "Test Player"
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock community chest cards
        mock_cards = [
            MagicMock(
                id="card1",
                card_type="community_chest", 
                title="Bank Error In Your Favor",
                description="Collect $200",
                action_type="collect",
                action_data=json.dumps({
                    "amount": 200,
                    "source": "bank",
                    "description": "Bank error in your favor"
                }),
                to_dict=MagicMock(return_value={
                    "id": "card1",
                    "title": "Bank Error In Your Favor",
                    "description": "Collect $200",
                    "action_type": "collect"
                })
            )
        ]
        mock_card.query.filter_by.return_value.all.return_value = mock_cards
        
        # Mock the card deck
        self.special_space_controller._initialize_community_chest_cards = MagicMock(return_value=mock_cards)
        self.special_space_controller._process_community_chest_card = MagicMock(return_value={
            "action_type": "collect",
            "amount": 200,
            "success": True,
            "message": "Collected $200 from the bank"
        })
        
        # Test the method
        result = self.special_space_controller.handle_community_chest_space(game_id, player_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["card"]["title"], "Bank Error In Your Favor")
        self.assertEqual(result["effects"]["amount"], 200)
        
        # Verify card initialization was called when needed
        self.special_space_controller._initialize_community_chest_cards.assert_called_once()
        
        # Verify card processing was called
        self.special_space_controller._process_community_chest_card.assert_called_once()
        
        # Verify socketio emit was called
        self.socketio.emit.assert_called_once_with(
            'community_chest_card_drawn',
            {
                'game_id': game_id,
                'player_id': player_id,
                'card': mock_cards[0].to_dict(),
                'effects': {
                    "action_type": "collect",
                    "amount": 200,
                    "success": True,
                    "message": "Collected $200 from the bank"
                },
                'message': f"Player {mock_player_obj.username} drew a Community Chest card: {mock_cards[0].to_dict()['title']}"
            },
            room=game_id
        )
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    def test_handle_community_chest_space_no_game(self, mock_player, mock_game_state):
        """Test handling a community chest space with invalid game ID."""
        # Setup mocks
        game_id = "nonexistent_game"
        player_id = "player456"
        
        # Mock game state - return None to simulate non-existent game
        mock_game_state.query.get.return_value = None
        
        # Test the method
        result = self.special_space_controller.handle_community_chest_space(game_id, player_id)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Game not found")
        
        # Verify no socket emit was called
        self.socketio.emit.assert_not_called()
    
    @patch('src.controllers.special_space_controller.GameState')
    @patch('src.controllers.special_space_controller.Player')
    def test_handle_community_chest_space_no_player(self, mock_player, mock_game_state):
        """Test handling a community chest space with invalid player ID."""
        # Setup mocks
        game_id = "game123"
        player_id = "nonexistent_player"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player - return None to simulate non-existent player
        mock_player.query.get.return_value = None
        
        # Test the method
        result = self.special_space_controller.handle_community_chest_space(game_id, player_id)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Player not found")
        
        # Verify no socket emit was called
        self.socketio.emit.assert_not_called()

    def test_process_community_chest_card_collect(self):
        """Test processing a community chest card with 'collect' action."""
        # Mock player state
        player_state = {
            "id": "player123",
            "balance": 500
        }
        
        # Mock card
        card = {
            "id": "card1",
            "action_type": "collect",
            "amount": 100,
            "source": "bank"
        }
        
        # Mock game state
        game_state = MagicMock()
        
        # Test the method
        result = self.special_space_controller._process_community_chest_card(game_state, player_state, card)
        
        # Assertions
        self.assertEqual(result["action_type"], "collect")
        self.assertEqual(result["amount"], 100)
        self.assertEqual(player_state["balance"], 600)  # 500 + 100
    
    def test_process_community_chest_card_pay(self):
        """Test processing a community chest card with 'pay' action."""
        # Mock player state
        player_state = {
            "id": "player123",
            "balance": 500
        }
        
        # Mock card
        card = {
            "id": "card1",
            "action_type": "pay",
            "amount": 50,
            "recipient": "community_fund"
        }
        
        # Mock game state
        game_state = MagicMock()
        game_state.get_community_fund = MagicMock(return_value=200)
        game_state.set_community_fund = MagicMock()
        
        # Test the method
        result = self.special_space_controller._process_community_chest_card(game_state, player_state, card)
        
        # Assertions
        self.assertEqual(result["action_type"], "pay")
        self.assertEqual(result["amount"], 50)
        self.assertEqual(player_state["balance"], 450)  # 500 - 50
        
        # Verify community fund was updated
        game_state.set_community_fund.assert_called_once_with(250)  # 200 + 50
    
    def test_process_community_chest_card_collect_from_each_player(self):
        """Test processing a community chest card with 'collect_from_each_player' action."""
        # Mock player state
        player_state = {
            "id": "player123",
            "balance": 500
        }
        
        # Mock card
        card = {
            "id": "card1",
            "action_type": "collect_from_each_player",
            "amount": 10
        }
        
        # Mock other players in game state
        other_players = [
            {"id": "player2", "balance": 300},
            {"id": "player3", "balance": 400},
            {"id": "player4", "balance": 200}
        ]
        
        # Mock game state
        game_state = MagicMock()
        game_state.get_players = MagicMock(return_value=[player_state] + other_players)
        
        # Test the method
        result = self.special_space_controller._process_community_chest_card(game_state, player_state, card)
        
        # Assertions
        self.assertEqual(result["action_type"], "collect_from_each_player")
        self.assertEqual(result["amount"], 30)  # 10 from each of 3 other players
        self.assertEqual(player_state["balance"], 530)  # 500 + 30
        
        # Verify other players' balances were reduced
        self.assertEqual(other_players[0]["balance"], 290)  # 300 - 10
        self.assertEqual(other_players[1]["balance"], 390)  # 400 - 10
        self.assertEqual(other_players[2]["balance"], 190)  # 200 - 10

if __name__ == '__main__':
    unittest.main() 