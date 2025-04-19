import pytest
import json
from unittest.mock import patch

class TestSpeedMode:
    """Tests for the Speed game mode"""
    
    def test_speed_mode_initialization(self, app, db, client):
        """Test a game can be initialized with Speed mode"""
        with app.app_context():
            # Create a new game with Speed mode
            response = client.post('/api/games', json={
                'name': 'Test Speed Game',
                'mode': 'speed',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Get game details to verify mode settings
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify Speed mode settings
            assert data['game']['mode'] == 'speed'
            assert data['game']['property_multiplier'] == 0.5  # Properties cost half
            assert data['game']['rent_multiplier'] == 2.0  # Rent is doubled
            assert data['game']['time_limit'] == 30  # 30 minute time limit
    
    def test_speed_mode_property_purchase(self, app, db, client, test_game_speed, test_player):
        """Test property purchase costs in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player_id = test_player.id
            
            # Get player's initial money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            initial_money = data['player']['money']
            
            # Land on an unowned property (Boardwalk)
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player_id}/move', json={
                    'dice_roll': [6, 4]
                })
                assert response.status_code == 200
            
            # Purchase the property
            response = client.post(f'/api/games/{game_id}/players/{player_id}/buy_property', json={
                'property_id': 39
            })
            assert response.status_code == 200
            
            # Verify property ownership
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['property']['owner_id'] == player_id
            
            # Verify money deducted from player
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            final_money = data['player']['money']
            
            # Boardwalk costs $400, but in Speed mode it's half price: $200
            assert final_money == initial_money - 200
    
    def test_speed_mode_pay_rent(self, app, db, client, test_game_speed, test_players):
        """Test rent payment in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            owner = test_players[0]
            player = test_players[1]
            
            # Give property to owner
            with db.session.begin():
                from src.models import Property
                baltic = Property.query.filter_by(game_id=game_id, position=3).first()  # Baltic Avenue
                baltic.owner_id = owner.id
                db.session.commit()
            
            # Get initial money for both players
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_initial_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_initial_money = json.loads(response.data)['player']['money']
            
            # Land on the owned property
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 3,  # Baltic Avenue
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [1, 2]
                })
                assert response.status_code == 200
            
            # Verify rent was paid automatically
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_final_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_final_money = json.loads(response.data)['player']['money']
            
            # Baltic Avenue base rent is $4, but in Speed mode it's doubled: $8
            assert owner_final_money == owner_initial_money + 8
            assert player_final_money == player_initial_money - 8
    
    def test_speed_mode_railroad_rent(self, app, db, client, test_game_speed, test_players):
        """Test railroad rent calculation in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            owner = test_players[0]
            player = test_players[1]
            
            # Give railroads to owner
            with db.session.begin():
                from src.models import Property
                # Reading Railroad (position 5)
                # Pennsylvania Railroad (position 15)
                reading = Property.query.filter_by(game_id=game_id, position=5).first()
                pennsylvania = Property.query.filter_by(game_id=game_id, position=15).first()
                reading.owner_id = owner.id
                pennsylvania.owner_id = owner.id
                db.session.commit()
            
            # Get initial money for both players
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_initial_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_initial_money = json.loads(response.data)['player']['money']
            
            # Land on one of the railroads
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [1, 4]
                })
                assert response.status_code == 200
            
            # Verify correct rent was paid
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_final_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_final_money = json.loads(response.data)['player']['money']
            
            # Railroad rent with 2 railroads owned is $50, doubled in Speed mode: $100
            assert owner_final_money == owner_initial_money + 100
            assert player_final_money == player_initial_money - 100
    
    def test_speed_mode_house_building(self, app, db, client, test_game_speed, test_players):
        """Test house building in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player = test_players[0]
            
            # Give player a complete property group
            with db.session.begin():
                from src.models import Property
                # Mediterranean (position 1) and Baltic (position 3)
                mediterranean = Property.query.filter_by(game_id=game_id, position=1).first()
                baltic = Property.query.filter_by(game_id=game_id, position=3).first()
                mediterranean.owner_id = player.id
                baltic.owner_id = player.id
                db.session.commit()
            
            # Get player's initial money
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            initial_money = json.loads(response.data)['player']['money']
            
            # Build a house on Baltic Avenue
            response = client.post(f'/api/games/{game_id}/players/{player.id}/build_house', json={
                'property_id': 3  # Baltic Avenue
            })
            assert response.status_code == 200
            
            # Verify house was built
            response = client.get(f'/api/games/{game_id}/properties/3')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            assert property_data['property']['houses'] == 1
            
            # Verify money was deducted
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            final_money = json.loads(response.data)['player']['money']
            
            # House on Mediterranean/Baltic costs $50, but in Speed mode it's half price: $25
            assert final_money == initial_money - 25
    
    def test_speed_mode_house_rent(self, app, db, client, test_game_speed, test_players):
        """Test rent calculation with houses in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            owner = test_players[0]
            player = test_players[1]
            
            # Give property with houses to owner
            with db.session.begin():
                from src.models import Property
                # Baltic Avenue (position 3)
                baltic = Property.query.filter_by(game_id=game_id, position=3).first()
                baltic.owner_id = owner.id
                baltic.houses = 3  # 3 houses
                db.session.commit()
            
            # Get initial money for both players
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_initial_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_initial_money = json.loads(response.data)['player']['money']
            
            # Land on the property with houses
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 3,  # Baltic Avenue
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [1, 2]
                })
                assert response.status_code == 200
            
            # Verify correct rent was paid
            response = client.get(f'/api/games/{game_id}/players/{owner.id}')
            assert response.status_code == 200
            owner_final_money = json.loads(response.data)['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_final_money = json.loads(response.data)['player']['money']
            
            # Baltic Avenue rent with 3 houses is $90, doubled in Speed mode: $180
            assert owner_final_money == owner_initial_money + 180
            assert player_final_money == player_initial_money - 180
    
    def test_speed_mode_go_salary(self, app, db, client, test_game_speed, test_player):
        """Test salary received when passing GO in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player_id = test_player.id
            
            # Get player's initial money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            initial_money = json.loads(response.data)['player']['money']
            
            # Simulate passing GO
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': True
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player_id}/move', json={
                    'dice_roll': [2, 3]
                })
                assert response.status_code == 200
            
            # Verify player received GO salary
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            final_money = json.loads(response.data)['player']['money']
            
            # GO salary in Speed mode is doubled: $400
            assert final_money == initial_money + 400
    
    def test_speed_mode_dice_rolling(self, app, db, client, test_game_speed, test_player):
        """Test dice rolling in Speed mode (should use 3 dice)"""
        with app.app_context():
            game_id = test_game_speed.id
            player_id = test_player.id
            
            # Get player's initial position
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            initial_position = json.loads(response.data)['player']['position']
            
            # Roll dice (should use 3 dice in Speed mode)
            with patch('src.game.game_logic.roll_dice') as mock_dice:
                mock_dice.return_value = [2, 3, 4]  # 3 dice total is 9
                
                with patch('src.game.game_logic.determine_landed_position') as mock_position:
                    # Mock the position calculation based on the dice roll
                    mock_position.return_value = {
                        'position': (initial_position + 9) % 40,  # Move 9 spaces
                        'passed_go': False
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player_id}/roll_dice', json={})
                    assert response.status_code == 200
                    
                    data = json.loads(response.data)
                    dice_roll = data['dice_roll']
                    
                    # Verify 3 dice were rolled
                    assert len(dice_roll) == 3
                    assert sum(dice_roll) == 9
    
    def test_speed_mode_time_limit(self, app, db, client, test_game_speed, test_players):
        """Test game ends when time limit is reached in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            
            # Mock a game that has reached its time limit
            with patch('src.game.game_logic.check_time_limit') as mock_time_limit:
                mock_time_limit.return_value = True  # Time limit reached
                
                # Trigger time check (this could be any game action)
                response = client.post(f'/api/games/{game_id}/check_time_limit', json={})
                assert response.status_code == 200
            
            # Check game status - should be completed
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            game_data = json.loads(response.data)
            
            # Game should be completed
            assert game_data['game']['status'] == 'completed'
            
            # Winner should be determined by highest net worth
            winner_id = game_data['game']['winner_id']
            assert winner_id is not None
    
    def test_speed_mode_player_net_worth(self, app, db, client, test_game_speed, test_players):
        """Test player net worth calculation at game end in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set up properties and money for both players
            with db.session.begin():
                from src.models import Property
                
                # Give player1 some properties
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                boardwalk.owner_id = player1.id
                park_place.owner_id = player1.id
                
                # Give player2 money but fewer properties
                player2.money = 2000
                
                # Give player1 houses
                boardwalk.houses = 3
                
                db.session.commit()
            
            # End the game (simulate time limit reached)
            with patch('src.game.game_logic.check_time_limit') as mock_time_limit:
                mock_time_limit.return_value = True  # Time limit reached
                
                # Trigger time check
                response = client.post(f'/api/games/{game_id}/check_time_limit', json={})
                assert response.status_code == 200
            
            # Check game result
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            game_data = json.loads(response.data)
            
            # Game should be completed
            assert game_data['game']['status'] == 'completed'
            
            # Get net worth calculation for both players
            response = client.get(f'/api/games/{game_id}/players/{player1.id}/net_worth')
            assert response.status_code == 200
            player1_net_worth = json.loads(response.data)['net_worth']
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}/net_worth')
            assert response.status_code == 200
            player2_net_worth = json.loads(response.data)['net_worth']
            
            # Verify the winner has the highest net worth
            if player1_net_worth > player2_net_worth:
                assert game_data['game']['winner_id'] == player1.id
            else:
                assert game_data['game']['winner_id'] == player2.id
    
    def test_speed_mode_double_moves(self, app, db, client, test_game_speed, test_player):
        """Test double moves on doubles in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player_id = test_player.id
            
            # Get player's initial position
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            initial_position = json.loads(response.data)['player']['position']
            
            # Roll doubles with 3 dice (first 2 are doubles)
            with patch('src.game.game_logic.roll_dice') as mock_dice:
                mock_dice.return_value = [4, 4, 3]  # First two dice are doubles
                
                with patch('src.game.game_logic.determine_landed_position') as mock_position:
                    # First move: 11 spaces
                    mock_position.return_value = {
                        'position': (initial_position + 11) % 40,
                        'passed_go': False
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player_id}/roll_dice', json={})
                    assert response.status_code == 200
                    
                    # Should get a second move because of doubles
                    data = json.loads(response.data)
                    assert data.get('can_roll_again') is True
                    
                    # Second roll after doubles
                    mock_dice.return_value = [2, 3, 1]  # No doubles this time
                    current_position = mock_position.return_value['position']
                    
                    # Second move: 6 more spaces
                    mock_position.return_value = {
                        'position': (current_position + 6) % 40,
                        'passed_go': False
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player_id}/roll_dice', json={})
                    assert response.status_code == 200
                    
                    # Should not get a third move
                    data = json.loads(response.data)
                    assert data.get('can_roll_again') is not True
    
    def test_speed_mode_turn_time_limit(self, app, db, client, test_game_speed, test_players):
        """Test turn time limit in Speed mode"""
        with app.app_context():
            game_id = test_game_speed.id
            player = test_players[0]
            
            # Start player's turn
            response = client.post(f'/api/games/{game_id}/players/{player.id}/start_turn', json={})
            assert response.status_code == 200
            
            # Check turn info
            response = client.get(f'/api/games/{game_id}/current_turn')
            assert response.status_code == 200
            turn_data = json.loads(response.data)
            
            # Verify turn has a time limit in Speed mode
            assert 'turn_start_time' in turn_data
            assert 'turn_time_limit' in turn_data
            assert turn_data['turn_time_limit'] == 60  # 60 seconds per turn in Speed mode
            
            # Mock turn time expiring
            with patch('src.game.game_logic.check_turn_time_limit') as mock_time_limit:
                mock_time_limit.return_value = True  # Turn time limit reached
                
                # End turn automatically due to time limit
                response = client.post(f'/api/games/{game_id}/check_turn_time_limit', json={})
                assert response.status_code == 200
            
            # Check if turn has moved to next player
            response = client.get(f'/api/games/{game_id}/current_turn')
            assert response.status_code == 200
            new_turn_data = json.loads(response.data)
            
            # Should be a different player's turn now
            assert new_turn_data['current_player_id'] != player.id 