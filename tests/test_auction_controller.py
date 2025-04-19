import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.controllers.auction_controller import AuctionController
from src.models.auction import Auction
from src.models.game_state import GameState
from src.models.property import Property
from src.models.player import Player

class TestAuctionController:
    """Test cases for the AuctionController class"""

    @pytest.fixture
    def auction_controller(self):
        """Create a mock AuctionController instance"""
        game_controller = MagicMock()
        socketio = MagicMock()
        app_config = {'AUCTION_DURATION': 60}
        return AuctionController(game_controller, socketio, app_config)

    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.GameState')
    @patch('src.controllers.auction_controller.Property')
    @patch('src.controllers.auction_controller.Player')
    def test_get_auction_analytics(self, mock_player, mock_property, mock_game_state, mock_auction, auction_controller):
        """Test the get_auction_analytics method"""
        # Setup mock data
        game_id = "game123"
        mock_game = MagicMock()
        mock_game_state.query.filter_by.return_value.first.return_value = mock_game
        
        # Mock auctions for the game
        auction1 = MagicMock()
        auction1.id = "auction1"
        auction1.property_id = "prop1"
        auction1.starting_price = 100
        auction1.current_bid = 150
        auction1.winner_id = "player1"
        auction1.status = "completed"
        auction1.created_at = datetime.now() - timedelta(days=1)
        auction1.details = json.dumps({"original_owner": "player2"})
        
        auction2 = MagicMock()
        auction2.id = "auction2"
        auction2.property_id = "prop2"
        auction2.starting_price = 200
        auction2.current_bid = 250
        auction2.winner_id = "player2"
        auction2.status = "completed"
        auction2.created_at = datetime.now() - timedelta(hours=12)
        auction2.details = json.dumps({"original_owner": "player1", "emergency": True})
        
        auction3 = MagicMock()
        auction3.id = "auction3"
        auction3.property_id = "prop3"
        auction3.starting_price = 300
        auction3.current_bid = 0
        auction3.winner_id = None
        auction3.status = "cancelled"
        auction3.created_at = datetime.now() - timedelta(hours=2)
        auction3.details = json.dumps({})
        
        mock_auction.query.filter_by.return_value.all.return_value = [auction1, auction2, auction3]
        
        # Mock properties
        prop1 = MagicMock()
        prop1.id = "prop1"
        prop1.name = "Property 1"
        
        prop2 = MagicMock()
        prop2.id = "prop2"
        prop2.name = "Property 2"
        
        prop3 = MagicMock()
        prop3.id = "prop3"
        prop3.name = "Property 3"
        
        # Return specific properties based on ID
        def get_property_by_id(property_id):
            if property_id == "prop1":
                return prop1
            elif property_id == "prop2":
                return prop2
            elif property_id == "prop3":
                return prop3
            return None
        
        mock_property.query.get.side_effect = get_property_by_id
        
        # Mock players
        player1 = MagicMock()
        player1.id = "player1"
        player1.name = "Player 1"
        
        player2 = MagicMock()
        player2.id = "player2"
        player2.name = "Player 2"
        
        # Return specific players based on ID
        def get_player_by_id(player_id):
            if player_id == "player1":
                return player1
            elif player_id == "player2":
                return player2
            return None
        
        mock_player.query.get.side_effect = get_player_by_id
        
        # Execute the method
        result = auction_controller.get_auction_analytics(game_id)
        
        # Verify the result
        assert result["success"] is True
        assert "analytics" in result
        analytics = result["analytics"]
        
        assert analytics["total_auctions"] == 3
        assert analytics["completed_auctions"] == 2
        assert analytics["cancelled_auctions"] == 1
        assert analytics["success_rate"] == 66.67  # 2/3 * 100
        assert analytics["average_price_increase"] == 50.0  # (50 + 50) / 2
        assert len(analytics["top_bidders"]) == 2
        assert len(analytics["property_stats"]) == 3
        assert "emergency_auctions" in analytics
        
    @patch('src.controllers.auction_controller.Auction')
    @patch('src.controllers.auction_controller.Property')
    @patch('src.controllers.auction_controller.Player')
    def test_get_property_auction_history(self, mock_player, mock_property, mock_auction, auction_controller):
        """Test the get_property_auction_history method"""
        # Setup mock data
        property_id = "prop1"
        
        # Mock property
        mock_prop = MagicMock()
        mock_prop.id = property_id
        mock_prop.name = "Boardwalk"
        mock_property.query.get.return_value = mock_prop
        
        # Mock auctions for the property
        auction1 = MagicMock()
        auction1.id = "auction1"
        auction1.starting_price = 100
        auction1.current_bid = 150
        auction1.winner_id = "player1"
        auction1.status = "completed"
        auction1.created_at = datetime.now() - timedelta(days=30)
        auction1.details = json.dumps({"original_owner": "bank"})
        
        auction2 = MagicMock()
        auction2.id = "auction2"
        auction2.starting_price = 150
        auction2.current_bid = 200
        auction2.winner_id = "player2"
        auction2.status = "completed"
        auction2.created_at = datetime.now() - timedelta(days=15)
        auction2.details = json.dumps({"original_owner": "player1", "emergency": True})
        
        mock_auction.query.filter_by.return_value.all.return_value = [auction1, auction2]
        
        # Mock players
        player1 = MagicMock()
        player1.id = "player1"
        player1.name = "Player 1"
        
        player2 = MagicMock()
        player2.id = "player2"
        player2.name = "Player 2"
        
        # Return specific players based on ID
        def get_player_by_id(player_id):
            if player_id == "player1":
                return player1
            elif player_id == "player2":
                return player2
            return None
        
        mock_player.query.get.side_effect = get_player_by_id
        
        # Execute the method
        result = auction_controller.get_property_auction_history(property_id)
        
        # Verify the result
        assert result["success"] is True
        assert "property" in result
        assert result["property"]["id"] == property_id
        assert result["property"]["name"] == "Boardwalk"
        
        assert "history" in result
        history = result["history"]
        assert len(history) == 2
        
        # Check first auction details
        assert history[0]["id"] == "auction1"
        assert history[0]["starting_price"] == 100
        assert history[0]["final_price"] == 150
        assert history[0]["winner"]["id"] == "player1"
        assert history[0]["winner"]["name"] == "Player 1"
        assert history[0]["original_owner"] == "bank"
        assert history[0]["is_emergency"] is False
        
        # Check second auction details
        assert history[1]["id"] == "auction2"
        assert history[1]["starting_price"] == 150
        assert history[1]["final_price"] == 200
        assert history[1]["winner"]["id"] == "player2"
        assert history[1]["winner"]["name"] == "Player 2"
        assert history[1]["original_owner"] == "player1"
        assert history[1]["is_emergency"] is True
        
    @patch('src.controllers.auction_controller.Auction')
    def test_get_property_auction_history_nonexistent_property(self, mock_auction, auction_controller):
        """Test get_property_auction_history with a nonexistent property"""
        property_id = "nonexistent"
        
        # Mock Property.query.get to return None
        auction_controller._get_property = MagicMock(return_value=None)
        
        result = auction_controller.get_property_auction_history(property_id)
        
        assert result["success"] is False
        assert "error" in result
        assert "Property not found" in result["error"] 