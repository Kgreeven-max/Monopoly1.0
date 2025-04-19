import pytest
import json
from unittest.mock import patch

class TestTurnProgression:
    """Tests for game turn progression and flow."""
    
    def test_game_initialization(self, app, db, test_game, test_game_state):
        """Test that a game initializes correctly with turn order"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create multiple players
            players = []
            for i in range(4):
                player = Player(
                    username=f"player{i}",
                    pin="1234",
                    money=1500,
                    position=0,
                    is_bot=False,
                    game_id=test_game.id
                )
                db.session.add(player)
                players.append(player)
            
            db.session.commit()
            
            # Create game controller and initialize game
            game_controller = GameController()
            result = game_controller.initialize_game(test_game_state.game_id)
            
            # Verify game initialized successfully
            assert result['success'] is True
            
            # Verify game state properties
            db.session.refresh(test_game_state)
            assert test_game_state.status == 'Waiting'
            
            # Player order should be set (comma-separated player IDs)
            assert test_game_state.player_order is not None
            
            # Verify player order includes all players
            player_ids = [str(p.id) for p in players]
            player_order = test_game_state.player_order.split(',')
            
            # All players should be in the order, may be in any order due to randomization
            for player_id in player_ids:
                assert player_id in player_order
    
    def test_start_game(self, app, db, test_game, test_game_state, populate_test_game):
        """Test starting a game and setting up the first player's turn"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create multiple players
            players = []
            for i in range(4):
                player = Player(
                    username=f"player{i}",
                    pin="1234",
                    money=1500,
                    position=0,
                    is_bot=False,
                    game_id=test_game.id
                )
                db.session.add(player)
                players.append(player)
            
            db.session.commit()
            
            # Create game controller
            game_controller = GameController()
            
            # Initialize game first
            game_controller.initialize_game(test_game_state.game_id)
            
            # Start the game
            result = game_controller.start_game(test_game_state.game_id)
            
            # Verify game started successfully
            assert result['success'] is True
            
            # Verify game state
            db.session.refresh(test_game_state)
            assert test_game_state.status == 'In Progress'
            
            # Verify there is a current player
            assert test_game_state.current_player_id is not None
            
            # Verify current player is in the player order
            player_order = test_game_state.player_order.split(',')
            assert str(test_game_state.current_player_id) in player_order
            
            # Verify expected action is set appropriately for first turn
            assert test_game_state.expected_action_type == 'roll_dice'
    
    def test_turn_progression(self, app, db, test_game, test_game_state):
        """Test progression through turns with multiple players"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create exactly 3 players
            players = []
            for i in range(3):
                player = Player(
                    username=f"player{i}",
                    pin="1234",
                    money=1500,
                    position=0,
                    is_bot=False,
                    game_id=test_game.id
                )
                db.session.add(player)
                players.append(player)
            
            db.session.commit()
            
            # Create game controller
            game_controller = GameController()
            
            # Initialize and start game
            game_controller.initialize_game(test_game_state.game_id)
            game_controller.start_game(test_game_state.game_id)
            
            # Get the initial order
            db.session.refresh(test_game_state)
            player_order = test_game_state.player_order.split(',')
            assert len(player_order) == 3
            
            # Get the initial player
            initial_player_id = test_game_state.current_player_id
            initial_index = player_order.index(str(initial_player_id))
            
            # Mock dice roll to avoid randomness
            with patch('src.controllers.game_controller.GameController._roll_dice', return_value=(2, 3)):
                # Process turn for first player
                result = game_controller.process_turn(test_game_state.game_id, initial_player_id, 'roll_dice')
                assert result['success'] is True
                
                # After moving, player should be prompted for next action
                db.session.refresh(test_game_state)
                assert test_game_state.expected_action_type in ['end_turn', 'buy_or_auction_prompt']
                
                # End the turn
                result = game_controller.process_turn(test_game_state.game_id, initial_player_id, 'end_turn')
                assert result['success'] is True
                
                # Verify turn moved to next player
                db.session.refresh(test_game_state)
                next_player_id = test_game_state.current_player_id
                
                # Next player should be the next in order
                next_index = (initial_index + 1) % 3
                assert str(next_player_id) == player_order[next_index]
                
                # Verify expected action reset for new player
                assert test_game_state.expected_action_type == 'roll_dice'
    
    def test_passing_go(self, app, db, test_game, test_game_state):
        """Test that a player receives $200 when passing GO"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create a player
            player = Player(
                username="test_player",
                pin="1234",
                money=1500,
                position=38,  # Position right before GO
                is_bot=False,
                game_id=test_game.id
            )
            db.session.add(player)
            db.session.commit()
            
            # Set up the game state with the player's turn
            test_game_state.current_player_id = player.id
            test_game_state.status = 'In Progress'
            test_game_state.player_order = str(player.id)
            test_game_state.expected_action_type = 'roll_dice'
            db.session.commit()
            
            # Create game controller
            game_controller = GameController()
            
            # Mock dice roll to ensure GO is passed (e.g., roll 4)
            with patch('src.controllers.game_controller.GameController._roll_dice', return_value=(1, 3)):
                # Process turn for the player
                initial_money = player.money
                result = game_controller.process_turn(test_game_state.game_id, player.id, 'roll_dice')
                
                # Verify turn was processed successfully
                assert result['success'] is True
                
                # Refresh player data
                db.session.refresh(player)
                
                # Verify player's new position is past GO (should be 2)
                assert player.position == 2
                
                # Verify player received $200 for passing GO
                assert player.money == initial_money + 200
    
    def test_jail_turn_progression(self, app, db, test_game, test_game_state):
        """Test turn progression when a player is in jail"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create 2 players (one in jail, one not)
            player1 = Player(
                username="free_player",
                pin="1234",
                money=1500,
                position=0,
                is_bot=False,
                game_id=test_game.id
            )
            
            player2 = Player(
                username="jailed_player",
                pin="1234",
                money=1500,
                position=10,  # Jail position
                in_jail=True,
                is_bot=False,
                game_id=test_game.id
            )
            
            db.session.add_all([player1, player2])
            db.session.commit()
            
            # Set up the game state with player order
            test_game_state.status = 'In Progress'
            test_game_state.player_order = f"{player1.id},{player2.id}"
            db.session.commit()
            
            # Create game controller
            game_controller = GameController()
            
            # Start with the jailed player's turn
            test_game_state.current_player_id = player2.id
            test_game_state.expected_action_type = 'jail_options'
            db.session.commit()
            
            # Jailed player has several options:
            # 1. Pay $50 to get out
            # 2. Use "get out of jail free" card
            # 3. Try to roll doubles
            
            # Test option 1: Pay to get out
            initial_money = player2.money
            result = game_controller.process_turn(test_game_state.game_id, player2.id, 'pay_bail')
            
            # Verify action was processed
            assert result['success'] is True
            
            # Verify player is no longer in jail and paid $50
            db.session.refresh(player2)
            assert player2.in_jail is False
            assert player2.money == initial_money - 50
            
            # Now player should be able to roll
            db.session.refresh(test_game_state)
            assert test_game_state.expected_action_type == 'roll_dice'
    
    def test_game_end_conditions(self, app, db, test_game, test_game_state):
        """Test conditions that end the game"""
        from src.models.player import Player
        from src.controllers.game_controller import GameController
        
        with app.app_context():
            # Create 3 players
            players = []
            for i in range(3):
                player = Player(
                    username=f"player{i}",
                    pin="1234",
                    money=1500 - (i * 500),  # Different money amounts
                    position=0,
                    is_bot=False,
                    game_id=test_game.id
                )
                db.session.add(player)
                players.append(player)
            
            db.session.commit()
            
            # Set up game state
            test_game_state.status = 'In Progress'
            test_game_state.player_order = ','.join([str(p.id) for p in players])
            test_game_state.current_player_id = players[0].id
            db.session.commit()
            
            # Create game controller
            game_controller = GameController()
            
            # Bankrupt all but one player
            for i in range(1, 3):
                players[i].declare_bankruptcy()
            
            db.session.commit()
            
            # Check game end conditions
            result = game_controller.check_game_end_conditions(test_game_state.game_id)
            
            # Verify game should end with one player remaining
            assert result['game_ended'] is True
            
            # Verify winner is the remaining player
            assert result['winner_id'] == players[0].id
            
            # Verify game state is updated
            db.session.refresh(test_game_state)
            assert test_game_state.status == 'Ended' 