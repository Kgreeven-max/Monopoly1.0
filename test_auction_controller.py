import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json

from src.controllers.auction_controller import AuctionController
from src.models.game_state import GameState
from src.models.player import Player
from src.models.property import Property
from src.models.auction import Auction

class TestAuctionController(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.db_session = MagicMock()
        self.banker = MagicMock()
        self.event_system = MagicMock()
        self.socketio = MagicMock()
        self.auction_controller = AuctionController(
            db_session=self.db_session,
            banker=self.banker,
            event_system=self.event_system,
            socketio=self.socketio
        )
        
    @patch('src.controllers.auction_controller.Property')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.db.session')
    def test_start_auction_logic(self, mock_session, mock_auction, mock_player, mock_game_state, mock_property):
        """Test starting an auction."""
        # Setup mocks
        game_id = "game123"
        property_id = "prop456"
        
        # Mock property
        mock_prop = MagicMock()
        mock_prop.id = property_id
        mock_prop.name = "Boardwalk"
        mock_prop.price = 400
        mock_prop.game_id = game_id
        mock_property_query = MagicMock()
        mock_property_query.filter_by.return_value.first.return_value = mock_prop
        mock_property.query = mock_property_query
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Mock players
        mock_players = [MagicMock(), MagicMock()]
        mock_player_query = MagicMock()
        mock_player_query.filter_by.return_value.all.return_value = mock_players
        mock_player.query = mock_player_query
        
        # Mock auction
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = "auction789"
        mock_auction_instance.property_id = property_id
        mock_auction_instance.game_id = game_id
        mock_auction_instance.starting_bid = 200  # 50% of $400
        mock_auction.return_value = mock_auction_instance
        
        # Test the method
        result = self.auction_controller._start_auction_logic(property_id, game_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["auction_id"], "auction789")
        self.assertEqual(result["property_id"], property_id)
        self.assertEqual(result["starting_bid"], 200)
        
        # Verify session add and commit was called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()
        
        # Verify socket emit was called
        self.socketio.emit.assert_called_once_with(
            'auction_started', 
            {
                'game_id': game_id,
                'auction_id': "auction789",
                'property_id': property_id,
                'property_name': mock_prop.name,
                'starting_bid': 200,
                'auction_duration': 120
            }, 
            room=game_id
        )
    
    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.db.session')
    def test_place_bid_logic(self, mock_session, mock_player, mock_game_state, mock_auction):
        """Test placing a bid."""
        # Setup mocks
        auction_id = "auction123"
        player_id = "player456"
        bid_amount = 150
        
        # Mock auction
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = auction_id
        mock_auction_instance.game_id = "game789"
        mock_auction_instance.property_id = "prop123"
        mock_auction_instance.status = "active"
        mock_auction_instance.current_bid = 100
        mock_auction_instance.starting_bid = 50
        mock_auction_instance.current_winner_id = "player999"
        mock_auction.query.get.return_value = mock_auction_instance
        
        # Mock player
        mock_player_instance = MagicMock()
        mock_player_instance.id = player_id
        mock_player_instance.name = "Test Player"
        mock_player_instance.balance = 500
        mock_player_instance.is_active = True
        mock_player.query.get.return_value = mock_player_instance
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = "game789"
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Assertions
        self.assertTrue(result["success"])
        
        # Verify auction was updated
        self.assertEqual(mock_auction_instance.current_bid, bid_amount)
        self.assertEqual(mock_auction_instance.current_winner_id, player_id)
        
        # Verify session commit was called
        mock_session.commit.assert_called()

    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.db.session')
    def test_place_bid_logic_validates_status(self, mock_session, mock_player, mock_game_state, mock_auction):
        """Test bid validation for auction status."""
        # Setup mocks
        auction_id = "auction123"
        player_id = "player456"
        bid_amount = 150
        
        # Mock auction with closed status
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = auction_id
        mock_auction_instance.status = "closed"
        mock_auction.query.get.return_value = mock_auction_instance
        
        # Test the method
        result = self.auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Auction is not active")
        
        # Verify auction was not updated
        mock_auction_instance.current_bid = 100  # Original value
        mock_auction_instance.current_winner_id = "player999"  # Original value
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()

    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.db.session')
    def test_place_bid_logic_validates_player_active(self, mock_session, mock_player, mock_game_state, mock_auction):
        """Test bid validation for player active status."""
        # Setup mocks
        auction_id = "auction123"
        player_id = "player456"
        bid_amount = 150
        
        # Mock auction
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = auction_id
        mock_auction_instance.game_id = "game789"
        mock_auction_instance.status = "active"
        mock_auction.query.get.return_value = mock_auction_instance
        
        # Mock player as inactive
        mock_player_instance = MagicMock()
        mock_player_instance.id = player_id
        mock_player_instance.is_active = False
        mock_player.query.get.return_value = mock_player_instance
        
        # Test the method
        result = self.auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Player is not active in the game")
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()

    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.db.session')
    def test_place_bid_logic_validates_bid_amount(self, mock_session, mock_player, mock_game_state, mock_auction):
        """Test bid validation for minimum bid amount."""
        # Setup mocks
        auction_id = "auction123"
        player_id = "player456"
        bid_amount = 90  # Less than current bid of 100
        
        # Mock auction
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = auction_id
        mock_auction_instance.game_id = "game789"
        mock_auction_instance.status = "active"
        mock_auction_instance.current_bid = 100
        mock_auction_instance.min_increment = 10
        mock_auction.query.get.return_value = mock_auction_instance
        
        # Mock player
        mock_player_instance = MagicMock()
        mock_player_instance.id = player_id
        mock_player_instance.is_active = True
        mock_player_instance.balance = 500
        mock_player.query.get.return_value = mock_player_instance
        
        # Test the method
        result = self.auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Bid must be at least 110")
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()

    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Player')
    @patch('src.controllers.auction_controller.db.session')
    def test_place_bid_logic_validates_funds(self, mock_session, mock_player, mock_game_state, mock_auction):
        """Test bid validation for sufficient funds."""
        # Setup mocks
        auction_id = "auction123"
        player_id = "player456"
        bid_amount = 600  # More than player balance of 500
        
        # Mock auction
        mock_auction_instance = MagicMock()
        mock_auction_instance.id = auction_id
        mock_auction_instance.game_id = "game789"
        mock_auction_instance.status = "active"
        mock_auction_instance.current_bid = 100
        mock_auction.query.get.return_value = mock_auction_instance
        
        # Mock player with insufficient funds
        mock_player_instance = MagicMock()
        mock_player_instance.id = player_id
        mock_player_instance.is_active = True
        mock_player_instance.balance = 500
        mock_player.query.get.return_value = mock_player_instance
        
        # Test the method
        result = self.auction_controller._place_bid_logic(auction_id, player_id, bid_amount)
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Insufficient funds to place bid")
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main() 