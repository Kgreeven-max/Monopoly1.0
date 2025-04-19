import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json

from src.controllers.game_controller import GameController
from src.models.game_state import GameState
from src.models.player import Player

class TestGameController(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.socketio = MagicMock()
        self.banker = MagicMock()
        self.event_system = MagicMock()
        
        self.game_controller = GameController(
            socketio=self.socketio,
            banker=self.banker,
            event_system=self.event_system
        )
        
        # Mock other controllers
        self.game_controller.bot_controller = MagicMock()
        self.game_controller.property_controller = MagicMock()
        
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_success(self, mock_session, mock_player, mock_game_state):
        """Test ending a player's turn successfully."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        
        # Mock the current player
        current_player = MagicMock()
        current_player.id = player_id
        current_player.username = "Player 1"
        current_player.is_bot = False
        current_player.in_jail = False
        current_player.is_active = True
        current_player.turn_order = 1
        mock_player.query.get.return_value = current_player
        
        # Mock the next player
        next_player = MagicMock()
        next_player.id = "player789"
        next_player.username = "Player 2"
        next_player.is_bot = False
        next_player.in_jail = False
        next_player.is_active = True
        next_player.turn_order = 2
        
        # Mock players list for finding next player
        mock_players = [current_player, next_player]
        mock_active_players = MagicMock()
        mock_active_players.all.return_value = mock_players
        mock_player.query.filter_by.return_value.order_by.return_value = mock_active_players
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.current_player_id = player_id
        mock_game.num_players = 2
        mock_game.max_laps = 10
        mock_game.current_lap = 5
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify the current player's state was updated
        self.assertEqual(current_player.expected_actions, "[]")
        
        # Verify the game state was updated
        self.assertEqual(mock_game.current_player_id, next_player.id)
        
        # Verify socket emit was called
        self.socketio.emit.assert_called_with(
            'turn_change',
            {
                'game_id': game_id,
                'next_player_id': next_player.id,
                'next_player_name': next_player.username
            },
            room=game_id
        )
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_game_not_found(self, mock_session, mock_player, mock_game_state):
        """Test ending a turn with a non-existent game."""
        # Setup mocks
        game_id = "nonexistent_game"
        player_id = "player456"
        
        # Mock game state - return None to simulate non-existent game
        mock_game_state.query.get.return_value = None
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertFalse(result)
        
        # Verify no socket emit was called
        self.socketio.emit.assert_not_called()
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_player_not_found(self, mock_session, mock_player, mock_game_state):
        """Test ending a turn with a non-existent player."""
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
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertFalse(result)
        
        # Verify no socket emit was called
        self.socketio.emit.assert_not_called()
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_not_current_player(self, mock_session, mock_player, mock_game_state):
        """Test ending a turn with a player who isn't the current player."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        actual_current_player_id = "player789"
        
        # Mock player
        mock_player_obj = MagicMock()
        mock_player_obj.id = player_id
        mock_player.query.get.return_value = mock_player_obj
        
        # Mock game state with different current player
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.current_player_id = actual_current_player_id
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertFalse(result)
        
        # Verify no socket emit was called
        self.socketio.emit.assert_not_called()
        
        # Verify session commit was not called
        mock_session.commit.assert_not_called()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_next_player_in_jail(self, mock_session, mock_player, mock_game_state):
        """Test ending turn when the next player is in jail."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        
        # Mock the current player
        current_player = MagicMock()
        current_player.id = player_id
        current_player.username = "Player 1"
        current_player.is_bot = False
        current_player.in_jail = False
        current_player.is_active = True
        current_player.turn_order = 1
        mock_player.query.get.return_value = current_player
        
        # Mock the next player (in jail)
        next_player = MagicMock()
        next_player.id = "player789"
        next_player.username = "Player 2"
        next_player.is_bot = False
        next_player.in_jail = True
        next_player.is_active = True
        next_player.turn_order = 2
        next_player.expected_actions = "[]"
        
        # Mock players list for finding next player
        mock_players = [current_player, next_player]
        mock_active_players = MagicMock()
        mock_active_players.all.return_value = mock_players
        mock_player.query.filter_by.return_value.order_by.return_value = mock_active_players
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.current_player_id = player_id
        mock_game.num_players = 2
        mock_game.max_laps = 10
        mock_game.current_lap = 5
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify the next player's expected actions were updated for jail
        self.assertIn("pay_bail", next_player.expected_actions)
        self.assertIn("roll_for_doubles", next_player.expected_actions)
        
        # Verify the game state was updated
        self.assertEqual(mock_game.current_player_id, next_player.id)
        
        # Verify socket emit was called
        self.socketio.emit.assert_called_with(
            'player_in_jail_options',
            {
                'game_id': game_id,
                'player_id': next_player.id,
                'player_name': next_player.username,
                'expected_actions': next_player.expected_actions
            },
            room=game_id
        )
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_next_player_is_bot(self, mock_session, mock_player, mock_game_state):
        """Test ending turn when the next player is a bot."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        
        # Mock the current player
        current_player = MagicMock()
        current_player.id = player_id
        current_player.username = "Player 1"
        current_player.is_bot = False
        current_player.in_jail = False
        current_player.is_active = True
        current_player.turn_order = 1
        mock_player.query.get.return_value = current_player
        
        # Mock the next player (a bot)
        next_player = MagicMock()
        next_player.id = "bot789"
        next_player.username = "Bot Player"
        next_player.is_bot = True
        next_player.in_jail = False
        next_player.is_active = True
        next_player.turn_order = 2
        
        # Mock players list for finding next player
        mock_players = [current_player, next_player]
        mock_active_players = MagicMock()
        mock_active_players.all.return_value = mock_players
        mock_player.query.filter_by.return_value.order_by.return_value = mock_active_players
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.current_player_id = player_id
        mock_game.num_players = 2
        mock_game.max_laps = 10
        mock_game.current_lap = 5
        mock_game.game_log = json.dumps([])
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify the game state was updated
        self.assertEqual(mock_game.current_player_id, next_player.id)
        
        # Verify socket emit was called
        self.socketio.emit.assert_called_with(
            'turn_change',
            {
                'game_id': game_id,
                'next_player_id': next_player.id,
                'next_player_name': next_player.username
            },
            room=game_id
        )
        
        # Verify bot controller was triggered
        self.game_controller.bot_controller.take_bot_turn.assert_called_once_with(game_id, next_player.id)
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
    @patch('src.controllers.game_controller.GameState')
    @patch('src.controllers.game_controller.Player')
    @patch('src.controllers.game_controller.db.session')
    def test_internal_end_turn_check_win_condition(self, mock_session, mock_player, mock_game_state):
        """Test ending turn that triggers a win condition."""
        # Setup mocks
        game_id = "game123"
        player_id = "player456"
        
        # Mock the current player - the only active player
        current_player = MagicMock()
        current_player.id = player_id
        current_player.username = "Player 1"
        current_player.is_bot = False
        current_player.in_jail = False
        current_player.is_active = True
        current_player.turn_order = 1
        mock_player.query.get.return_value = current_player
        
        # Mock other players as inactive
        other_player = MagicMock()
        other_player.id = "player789"
        other_player.username = "Player 2"
        other_player.is_bot = False
        other_player.is_active = False
        other_player.turn_order = 2
        
        # Mock players list for finding next player - only one active player
        mock_active_players = MagicMock()
        mock_active_players.all.return_value = [current_player]
        mock_player.query.filter_by.return_value.order_by.return_value = mock_active_players
        
        # For the full player list (including inactive)
        mock_players = [current_player, other_player]
        mock_all_players = MagicMock()
        mock_all_players.all.return_value = mock_players
        # Return different results based on filter criteria
        def mock_filter_side_effect(**kwargs):
            if kwargs.get('is_active', None) is True:
                mock_filter = MagicMock()
                mock_filter.order_by.return_value = mock_active_players
                return mock_filter
            else:
                mock_filter = MagicMock()
                mock_filter.all.return_value = mock_players
                return mock_filter
        mock_player.query.filter_by.side_effect = mock_filter_side_effect
        
        # Mock game state
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game.current_player_id = player_id
        mock_game.num_players = 2
        mock_game.max_laps = 10
        mock_game.current_lap = 5
        mock_game.game_log = json.dumps([])
        mock_game.winner_id = None
        mock_game_state.query.get.return_value = mock_game
        
        # Test the method
        result = self.game_controller._internal_end_turn(game_id, player_id)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify win condition was checked and winner was set
        self.assertEqual(mock_game.winner_id, player_id)
        self.assertEqual(mock_game.status, "completed")
        
        # Verify socket emit was called for game end
        self.socketio.emit.assert_called_with(
            'game_end',
            {
                'game_id': game_id,
                'winner_id': player_id,
                'winner_name': current_player.username,
                'reason': "All other players are bankrupt or have quit"
            },
            room=game_id
        )
        
        # Verify session commit was called
        mock_session.commit.assert_called_once()
    
if __name__ == '__main__':
    unittest.main() 