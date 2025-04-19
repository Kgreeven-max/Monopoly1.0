import pytest
import json
from unittest.mock import patch, Mock

class TestQuickPlayMode:
    """Tests for the Quick Play game mode"""
    
    def test_quick_play_initialization(self, app, db, client):
        """Test a game can be initialized with Quick Play mode"""
        with app.app_context():
            # Create a new game with Quick Play mode
            response = client.post('/api/games', json={
                'name': 'Test Quick Play Game',
                'mode': 'quick_play',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Get game details to verify mode settings
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify Quick Play mode settings
            assert data['game']['mode'] == 'quick_play'
            assert data['game']['max_rounds'] == 20  # Limited rounds in quick play
            assert data['game']['double_go_money'] is True  # Double GO money
            assert data['game']['free_parking_bonus'] is True  # Free parking bonus enabled
    
    def test_quick_play_starting_money(self, app, db, client, test_game_quick_play, test_players):
        """Test players start with correct amount of money in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player_id = test_players[0].id
            
            # Check player's money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Quick Play mode players start with higher amount ($2500)
            assert data['player']['money'] == 2500
    
    def test_quick_play_double_go_money(self, app, db, client, test_game_quick_play, test_players):
        """Test players receive double money when passing GO in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Set initial money and position
            with db.session.begin():
                player.money = 2500  # Reset to starting amount
                player.position = 39  # Boardwalk (just before GO)
                db.session.commit()
            
            # Move player past GO
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': True
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [3, 3]
                })
                assert response.status_code == 200
            
            # Verify player received double GO money
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Starting money + double GO money (2 * $200)
            assert data['player']['money'] == 2500 + (2 * 200)
    
    def test_quick_play_free_parking_bonus(self, app, db, client, test_game_quick_play, test_players):
        """Test free parking bonus in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Set the free parking pot and player position
            with db.session.begin():
                player.money = 2500  # Reset to starting amount
                test_game_quick_play.free_parking_pot = 500  # Set money in pot
                db.session.commit()
            
            # Land player on Free Parking
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 20,  # Free Parking
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [5, 5]
                })
                assert response.status_code == 200
            
            # Verify player received the free parking bonus
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Money should increase by pot amount
            assert data['player']['money'] == 2500 + 500
            
            # Verify pot is reset to 0
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            game_data = json.loads(response.data)
            
            assert game_data['game']['free_parking_pot'] == 0
    
    def test_quick_play_tax_to_free_parking(self, app, db, client, test_game_quick_play, test_players):
        """Test tax payments go to free parking pot in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Reset free parking pot
            with db.session.begin():
                player.money = 2500  # Reset to starting amount
                test_game_quick_play.free_parking_pot = 0
                db.session.commit()
            
            # Land player on Income Tax
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 4,  # Income Tax
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [2, 2]
                })
                assert response.status_code == 200
            
            # Verify player paid tax
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Player should pay income tax of $200
            assert data['player']['money'] == 2500 - 200
            
            # Verify tax went to free parking pot
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Free parking pot should have the tax amount
            assert data['game']['free_parking_pot'] == 200
    
    def test_quick_play_round_tracking(self, app, db, client, test_game_quick_play, test_players):
        """Test rounds are tracked correctly in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Get initial round count
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            initial_round = data['game']['current_round']
            
            # Move last player past GO to increment round
            with db.session.begin():
                # Set as last player in turn order
                test_game_quick_play.current_player_index = len(test_players) - 1
                # Position just before GO
                player.position = 39
                db.session.commit()
            
            # Move player past GO
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': True
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [3, 3]
                })
                assert response.status_code == 200
            
            # Verify round was incremented
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['game']['current_round'] == initial_round + 1
    
    def test_quick_play_max_rounds_ending(self, app, db, client, test_game_quick_play, test_players):
        """Test game ends after max rounds in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Set game to last round
            with db.session.begin():
                test_game_quick_play.current_round = test_game_quick_play.max_rounds - 1
                # Set as last player in turn order
                test_game_quick_play.current_player_index = len(test_players) - 1
                # Position just before GO
                player.position = 39
                db.session.commit()
            
            # Move player past GO to trigger round increment
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': True
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [3, 3]
                })
                assert response.status_code == 200
            
            # Check game state - should end after max rounds
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['game']['status'] == 'completed'
            assert data['game']['end_reason'] == 'max_rounds_reached'
    
    def test_quick_play_property_improvements(self, app, db, client, test_game_quick_play, test_players):
        """Test property improvements are cheaper in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Set up monopoly for the player
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player.id
                park_place.owner_id = player.id
                
                # Set initial money
                player.money = 2500
                
                db.session.commit()
            
            # Get standard house price
            standard_house_price = boardwalk.house_price
            discounted_price = int(standard_house_price * 0.75)  # 25% discount
            
            # Attempt to build house
            response = client.post(f'/api/games/{game_id}/players/{player.id}/build_house', json={
                'property_id': 39
            })
            assert response.status_code == 200
            
            # Verify house was built and discounted price was paid
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['houses'] == 1
            
            # Verify player paid discounted price
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            # Should pay discounted price in quick play
            assert player_data['player']['money'] == 2500 - discounted_price
    
    def test_quick_play_jail_mechanics(self, app, db, client, test_game_quick_play, test_players):
        """Test jail mechanics are different in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Send player to jail
            with db.session.begin():
                player.position = 10  # Jail position
                player.in_jail = True
                player.jail_turns = 2  # Reduced jail turns in quick play
                player.money = 2500  # Reset money
                db.session.commit()
            
            # Attempt to pay bail
            response = client.post(f'/api/games/{game_id}/players/{player.id}/pay_bail', json={})
            assert response.status_code == 200
            
            # Verify player was released and paid reduced bail
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['player']['in_jail'] is False
            
            # Reduced bail in quick play is $25 (half of standard)
            assert data['player']['money'] == 2500 - 25
    
    def test_quick_play_mortgage_bonus(self, app, db, client, test_game_quick_play, test_players):
        """Test mortgage payouts are higher in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Give player a property
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                
                # Reset money to starting amount
                player.money = 2500
                
                db.session.commit()
            
            # Get standard mortgage value and calculate quick play bonus
            standard_mortgage_value = boardwalk.mortgage_value
            boosted_mortgage_value = int(standard_mortgage_value * 1.2)  # 20% more
            
            # Mortgage the property
            response = client.post(f'/api/games/{game_id}/players/{player.id}/mortgage_property', json={
                'property_id': 39
            })
            assert response.status_code == 200
            
            # Verify property was mortgaged
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['is_mortgaged'] is True
            
            # Verify player received boosted mortgage value
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['money'] == 2500 + boosted_mortgage_value
    
    def test_quick_play_property_trading_bonus(self, app, db, client, test_game_quick_play, test_players):
        """Test trading bonus in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Give properties to players
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player1.id
                park_place.owner_id = player2.id
                
                # Reset money
                player1.money = 2500
                player2.money = 2500
                
                db.session.commit()
            
            # Create a trade with a bonus
            trade_bonus = 100  # Quick play mode might give bonus for trading
            response = client.post(f'/api/games/{game_id}/trades', json={
                'proposer_id': player1.id,
                'recipient_id': player2.id,
                'proposer_properties': [39],  # Boardwalk
                'recipient_properties': [37],  # Park Place
                'proposer_money': 0,
                'recipient_money': 0
            })
            assert response.status_code == 201
            data = json.loads(response.data)
            trade_id = data['trade_id']
            
            # Accept the trade
            response = client.post(f'/api/games/{game_id}/trades/{trade_id}/accept', json={})
            assert response.status_code == 200
            
            # Verify properties were exchanged
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            boardwalk_data = json.loads(response.data)
            assert boardwalk_data['property']['owner_id'] == player2.id
            
            response = client.get(f'/api/games/{game_id}/properties/37')
            assert response.status_code == 200
            park_place_data = json.loads(response.data)
            assert park_place_data['property']['owner_id'] == player1.id
            
            # Verify trading bonus if it exists in quick play mode
            if trade_bonus > 0:
                response = client.get(f'/api/games/{game_id}/players/{player1.id}')
                assert response.status_code == 200
                player1_data = json.loads(response.data)
                
                response = client.get(f'/api/games/{game_id}/players/{player2.id}')
                assert response.status_code == 200
                player2_data = json.loads(response.data)
                
                # Both players should receive trading bonus
                assert player1_data['player']['money'] == 2500 + trade_bonus
                assert player2_data['player']['money'] == 2500 + trade_bonus
    
    def test_quick_play_bankruptcy_handling(self, app, db, client, test_game_quick_play, test_players):
        """Test bankruptcy handling in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player1 = test_players[0]  # Will go bankrupt
            player2 = test_players[1]  # Creditor
            
            # Set up properties and money situation
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player1.id
                
                player1.money = 100  # Very low on money
                player2.money = 2500
                
                db.session.commit()
            
            # Create a debt situation that will lead to bankruptcy
            response = client.post(f'/api/games/{game_id}/debts', json={
                'debtor_id': player1.id,
                'creditor_id': player2.id,
                'amount': 500  # More than player1 has
            })
            assert response.status_code == 201
            data = json.loads(response.data)
            debt_id = data['debt_id']
            
            # Declare bankruptcy
            response = client.post(f'/api/games/{game_id}/players/{player1.id}/declare_bankruptcy', json={
                'debt_id': debt_id
            })
            assert response.status_code == 200
            
            # In Quick Play mode, properties might transfer directly to creditor
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            # Verify property transferred to creditor
            assert property_data['property']['owner_id'] == player2.id
            
            # Verify player1 is bankrupt
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['status'] == 'bankrupt'
    
    def test_quick_play_win_condition(self, app, db, client, test_game_quick_play, test_players):
        """Test win condition when all players but one are bankrupt"""
        with app.app_context():
            game_id = test_game_quick_play.id
            for i in range(len(test_players) - 1):
                # Mark all but one player as bankrupt
                with db.session.begin():
                    test_players[i].status = 'bankrupt'
                    db.session.commit()
            
            # Check win condition
            response = client.post(f'/api/games/{game_id}/check_win_condition', json={})
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Game should be over with one winner
            assert data['game_over'] is True
            assert data['winner_id'] == test_players[-1].id
            
            # Verify game state
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            game_data = json.loads(response.data)
            
            assert game_data['game']['status'] == 'completed'
            assert game_data['game']['winner_id'] == test_players[-1].id
    
    def test_quick_play_net_worth_tracking(self, app, db, client, test_game_quick_play, test_players):
        """Test net worth tracking in Quick Play mode"""
        with app.app_context():
            game_id = test_game_quick_play.id
            player = test_players[0]
            
            # Give player properties
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                boardwalk.houses = 1  # Add one house
                
                player.money = 2500
                
                db.session.commit()
            
            # Calculate expected net worth
            property_value = boardwalk.price
            house_value = boardwalk.house_price / 2  # Houses are worth half their cost
            expected_net_worth = 2500 + property_value + house_value
            
            # Check player net worth
            response = client.get(f'/api/games/{game_id}/players/{player.id}/net_worth')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify net worth calculation includes cash and property values
            assert abs(data['net_worth'] - expected_net_worth) < 1  # Allow for minor rounding differences 