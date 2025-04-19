import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json

from src.controllers.economic_cycle_controller import EconomicCycleController, ECONOMIC_STATES
from src.models.game_state import GameState
from src.models.property import Property
from src.models.loan import Loan
from src.models.cd import CD
from src.models.player import Player

class TestEconomicCycleController(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.socketio = MagicMock()
        self.economic_controller = EconomicCycleController(self.socketio)
        
    @patch('src.controllers.economic_cycle_controller.GameState')
    @patch('src.controllers.economic_cycle_controller.Property')
    @patch('src.controllers.economic_cycle_controller.Loan')
    @patch('src.controllers.economic_cycle_controller.CD')
    @patch('src.controllers.economic_cycle_controller.db.session')
    def test_process_economic_cycle(self, mock_session, mock_cd, mock_loan, mock_property, mock_game_state):
        """Test processing an economic cycle update."""
        # Setup mocks
        game_id = "game123"
        current_state = "stable"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.economic_state = current_state
        mock_game.inflation_rate = 0.0
        mock_game.game_log = json.dumps([])
        mock_game.interest_rates = json.dumps({
            "loan": 0.05,
            "cd": 0.03,
            "heloc": 0.06
        })
        mock_game.config = {"property_values_follow_economy": True}
        mock_game_state.query.get.return_value = mock_game
        
        # Mock property query
        mock_props = [MagicMock(), MagicMock()]
        mock_property.query.filter_by.return_value.all.return_value = mock_props
        
        # Mock loan query
        mock_loans = [MagicMock(), MagicMock()]
        mock_loan.query.filter_by.return_value.all.return_value = mock_loans
        
        # Mock CD query
        mock_cds = [MagicMock(), MagicMock()]
        mock_cd.query.filter_by.return_value.all.return_value = mock_cds
        
        # Force the next state to be predictable
        with patch('random.choice', return_value="boom"):
            # Test the method
            result = self.economic_controller.process_economic_cycle(game_id)
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertEqual(result["previous_state"], current_state)
            self.assertEqual(result["new_state"], "boom")
            
            # Verify property values were updated
            self.economic_controller._update_property_values.assert_called_once_with(
                game_id, ECONOMIC_STATES["boom"]["property_value_modifier"]
            )
            
            # Verify loan interest rates were updated
            self.economic_controller._process_loan_interest_changes.assert_called_once()
            
            # Verify CD interest rates were updated
            self.economic_controller._process_cd_interest_changes.assert_called_once()
            
            # Verify game state was updated
            self.assertEqual(mock_game.economic_state, "boom")
            self.assertIsNotNone(mock_game.last_economic_update)
            
            # Verify socketio emit was called
            self.socketio.emit.assert_called_once()
            
            # Verify session commit was called
            mock_session.commit.assert_called_once()
    
    @patch('src.controllers.economic_cycle_controller.GameState')
    @patch('src.controllers.economic_cycle_controller.db.session')
    def test_get_current_economic_state(self, mock_session, mock_game_state):
        """Test getting the current economic state."""
        # Setup mocks
        game_id = "game123"
        current_state = "boom"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.economic_state = current_state
        mock_game.inflation_rate = 0.02
        mock_game.last_economic_update = datetime.utcnow()
        mock_game.interest_rates = json.dumps({
            "loan": 0.06,
            "cd": 0.04,
            "heloc": 0.07
        })
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.economic_controller.get_current_economic_state(game_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["economic_state"], current_state)
        self.assertEqual(result["inflation_rate"], 0.02)
        self.assertEqual(result["economic_description"], ECONOMIC_STATES[current_state]["description"])
        self.assertEqual(result["color"], ECONOMIC_STATES[current_state]["color"])
        self.assertIsNotNone(result["last_update"])
    
    @patch('src.controllers.economic_cycle_controller.GameState')
    @patch('src.controllers.economic_cycle_controller.db.session')
    def test_trigger_market_crash(self, mock_session, mock_game_state):
        """Test triggering a market crash event."""
        # Setup mocks
        game_id = "game123"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.economic_state = "stable"
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Mock _update_property_values and _process methods
        self.economic_controller._update_property_values = MagicMock()
        self.economic_controller._process_loan_interest_changes = MagicMock()
        self.economic_controller._process_cd_interest_changes = MagicMock()
        
        # Test the method
        result = self.economic_controller.trigger_market_crash(game_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["event"], "market_crash")
        self.assertEqual(result["economic_state"], "depression")
        self.assertEqual(result["property_value_change"], -0.4)
        
        # Verify economic state was updated
        self.assertEqual(mock_game.economic_state, "depression")
        
        # Verify _update_property_values was called with correct parameter
        self.economic_controller._update_property_values.assert_called_once_with(game_id, 0.6)
        
        # Verify interest rate processing methods were called
        self.economic_controller._process_loan_interest_changes.assert_called_once()
        self.economic_controller._process_cd_interest_changes.assert_called_once()
        
        # Verify socketio emit was called
        self.socketio.emit.assert_called_once()
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()

    @patch('src.controllers.economic_cycle_controller.GameState')
    @patch('src.controllers.economic_cycle_controller.Property')
    @patch('src.controllers.economic_cycle_controller.Player')
    @patch('src.controllers.economic_cycle_controller.db.session')
    def test_handle_market_fluctuation_space(self, mock_session, mock_player, mock_property, mock_game_state):
        """Test handling a player landing on a market fluctuation space."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        current_state = "boom"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.economic_state = current_state
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.username = "Test Player"
        mock_player_obj.balance = 1000
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock owned properties
        mock_prop1 = MagicMock()
        mock_prop1.id = "prop1"
        mock_prop1.name = "Boardwalk"
        mock_prop1.price = 400
        
        mock_prop2 = MagicMock()
        mock_prop2.id = "prop2"
        mock_prop2.name = "Park Place"
        mock_prop2.price = 350
        
        mock_property.query.filter_by.return_value.all.return_value = [mock_prop1, mock_prop2]
        
        # Test the method
        result = self.economic_controller.handle_market_fluctuation_space(game_id, player_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["economic_state"], current_state)
        
        # In boom state, player should get a cash bonus
        self.assertEqual(result["effects"]["cash_effect"], "bonus")
        self.assertEqual(result["effects"]["cash_change"], 100)
        
        # Properties should increase in value
        self.assertEqual(len(result["effects"]["property_changes"]), 2)
        self.assertEqual(result["effects"]["property_effect"], "increase")
        
        # Verify game log was updated
        self.assertIn("market_fluctuation", json.loads(mock_game.game_log)[0]["type"])
        
        # Verify player balance was updated
        self.assertEqual(mock_player_obj.balance, 1100)  # 1000 + 100 bonus
        
        # Verify socketio emit was called
        self.socketio.emit.assert_called_once_with('market_fluctuation', {
            'game_id': game_id,
            'player_id': player_id,
            'player_name': mock_player_obj.username,
            'economic_state': current_state,
            'effects': result["effects"],
            'color': ECONOMIC_STATES[current_state]["color"]
        }, room=game_id)
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
    @patch('src.controllers.economic_cycle_controller.GameState')
    @patch('src.controllers.economic_cycle_controller.Property')
    @patch('src.controllers.economic_cycle_controller.Player')
    @patch('src.controllers.economic_cycle_controller.db.session')
    def test_handle_market_fluctuation_space_recession(self, mock_session, mock_player, mock_property, mock_game_state):
        """Test handling a player landing on a market fluctuation space during recession."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        current_state = "recession"
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.economic_state = current_state
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player_obj.username = "Test Player"
        mock_player_obj.balance = 1000
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock owned properties
        mock_prop1 = MagicMock()
        mock_prop1.id = "prop1"
        mock_prop1.name = "Boardwalk"
        mock_prop1.price = 400
        
        mock_property.query.filter_by.return_value.all.return_value = [mock_prop1]
        
        # Test the method
        result = self.economic_controller.handle_market_fluctuation_space(game_id, player_id)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["economic_state"], current_state)
        
        # In recession state, player should get a cash penalty
        self.assertEqual(result["effects"]["cash_effect"], "penalty")
        self.assertEqual(result["effects"]["cash_change"], -50)
        
        # Properties should decrease in value
        self.assertEqual(len(result["effects"]["property_changes"]), 1)
        self.assertEqual(result["effects"]["property_effect"], "decrease")
        
        # Verify player balance was updated
        self.assertEqual(mock_player_obj.balance, 950)  # 1000 - 50 penalty
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main() 