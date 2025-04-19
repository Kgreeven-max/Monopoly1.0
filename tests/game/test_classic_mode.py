import pytest
import json
from unittest.mock import patch, Mock
import random

class TestClassicGameMode:
    """Tests for the classic mode of the Monopoly game"""
    
    def test_create_classic_game(self, app, db, client):
        """Test creating a classic mode game"""
        with app.app_context():
            response = client.post('/api/games', json={
                'name': 'Test Classic Game',
                'mode': 'classic',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify game properties
            assert 'game' in data
            assert data['game']['name'] == 'Test Classic Game'
            assert data['game']['mode'] == 'classic'
            assert data['game']['status'] == 'waiting'
            assert data['game']['max_players'] == 4
            
            # Verify game exists in database
            from src.models import Game
            game = Game.query.filter_by(name='Test Classic Game').first()
            assert game is not None
            assert game.mode == 'classic'
    
    def test_join_classic_game(self, app, db, client, test_game_classic, test_user_token):
        """Test joining a classic mode game"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Join the game
            response = client.post(f'/api/games/{game_id}/join', headers={
                'Authorization': f'Bearer {test_user_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify join success
            assert 'message' in data
            assert 'joined' in data['message'].lower()
            
            # Verify player count
            response = client.get(f'/api/games/{game_id}')
            data = json.loads(response.data)
            
            assert 'players' in data
            assert len(data['players']) == 1  # Our test user
    
    def test_start_classic_game(self, app, db, client, test_game_classic_with_players, admin_token):
        """Test starting a classic mode game"""
        with app.app_context():
            game_id = test_game_classic_with_players.id
            
            # Start the game
            response = client.post(f'/api/games/{game_id}/start', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify game started
            assert 'message' in data
            assert 'started' in data['message'].lower()
            
            # Check game status
            from src.models import Game
            game = Game.query.get(game_id)
            assert game.status == 'active'
            
            # Verify initial game state
            response = client.get(f'/api/games/{game_id}')
            data = json.loads(response.data)
            
            for player in data['players']:
                assert player['money'] == 1500  # Starting money in classic mode
                assert player['position'] == 0   # Starting at GO
    
    def test_roll_dice_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test rolling dice in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Roll dice
            with patch('random.randint', side_effect=[4, 3]):  # Mock dice roll to 4 and 3
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Verify dice roll
                assert 'dice' in data
                assert len(data['dice']) == 2
                assert data['dice'][0] == 4
                assert data['dice'][1] == 3
                assert data['total'] == 7
                
                # Verify player moved
                assert 'player' in data
                assert data['player']['position'] == 7  # Started at 0, moved 7 spaces
    
    def test_buy_property_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test buying property in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # First, move player to a property (e.g., Mediterranean Avenue)
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            initial_money = player.money
            player.position = 1  # Mediterranean Avenue
            db.session.commit()
            
            # Get property details
            response = client.get(f'/api/games/{game_id}/properties/1')
            property_data = json.loads(response.data)
            property_price = property_data['property']['price']
            
            # Buy the property
            response = client.post(f'/api/games/{game_id}/buy', headers={
                'Authorization': f'Bearer {test_player_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify purchase
            assert 'message' in data
            assert 'purchased' in data['message'].lower()
            
            # Verify player money decreased
            player = GamePlayer.query.get(player.id)
            assert player.money == initial_money - property_price
            
            # Verify property ownership
            response = client.get(f'/api/games/{game_id}/properties/1')
            data = json.loads(response.data)
            
            assert data['property']['owner_id'] == player.id
    
    def test_property_rent_classic(self, app, db, client, test_active_classic_game_with_properties):
        """Test rent payment in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_properties.id
            
            # Get players
            from src.models import GamePlayer, Property
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            player1 = players[0]  # Property owner
            player2 = players[1]  # Player who will land on property
            
            # Ensure player1 owns a property (e.g., Mediterranean Avenue)
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()
            property1.owner_id = player1.id
            
            # Record initial money
            player1_initial_money = player1.money
            player2_initial_money = player2.money
            
            # Move player2 to the property
            player2.position = 1  # Mediterranean Avenue
            db.session.commit()
            
            # Get token for player2
            # Note: In a real test, you would need to generate a token for player2
            test_player2_token = "player2_token"  # This would be generated
            
            # Roll dice (staying on the same space for testing)
            with patch('random.randint', return_value=0):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player2_token}'
                })
                
                assert response.status_code == 200
                
                # Verify rent was paid
                player1 = GamePlayer.query.get(player1.id)
                player2 = GamePlayer.query.get(player2.id)
                
                rent_amount = property1.rent
                assert player1.money == player1_initial_money + rent_amount
                assert player2.money == player2_initial_money - rent_amount
    
    def test_passing_go_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test passing GO and collecting salary in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to position 39 (Boardwalk)
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 39
            initial_money = player.money
            db.session.commit()
            
            # Roll dice to pass GO
            with patch('random.randint', side_effect=[2, 1]):  # Total of 3, moving from 39 to position 2
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player received GO salary
                player = GamePlayer.query.get(player.id)
                assert player.position == 2  # Moved past GO to position 2
                assert player.money == initial_money + 200  # Classic GO salary is $200
    
    def test_jail_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test jail mechanics in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to "Go to Jail" space
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 30  # "Go to Jail" space
            db.session.commit()
            
            # Roll dice
            response = client.post(f'/api/games/{game_id}/roll', headers={
                'Authorization': f'Bearer {test_player_token}'
            })
            
            assert response.status_code == 200
            
            # Verify player is in jail
            player = GamePlayer.query.get(player.id)
            assert player.position == 10  # Jail position
            assert player.in_jail is True
            
            # Try to get out with a double
            with patch('random.randint', side_effect=[6, 6]):  # Double 6
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player got out of jail
                player = GamePlayer.query.get(player.id)
                assert player.in_jail is False
                assert player.position == 22  # Moved 12 spaces from jail
    
    def test_pay_jail_fine_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test paying jail fine in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Put player in jail
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 10  # Jail position
            player.in_jail = True
            initial_money = player.money
            db.session.commit()
            
            # Pay to get out of jail
            response = client.post(f'/api/games/{game_id}/jail/pay', headers={
                'Authorization': f'Bearer {test_player_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify player is out of jail
            assert 'message' in data
            assert 'paid' in data['message'].lower()
            
            player = GamePlayer.query.get(player.id)
            assert player.in_jail is False
            assert player.money == initial_money - 50  # Classic jail fine is $50
    
    def test_house_building_classic(self, app, db, client, test_active_classic_game_with_color_group):
        """Test building houses in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_color_group.id
            
            # Get player who owns a complete color group
            from src.models import GamePlayer, Property
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            
            # Find a property in the owned color group (e.g., purple)
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            property3 = Property.query.filter_by(game_id=game_id, position=3).first()  # Baltic Avenue
            
            # Ensure player owns both properties
            property1.owner_id = player.id
            property3.owner_id = player.id
            initial_money = player.money
            db.session.commit()
            
            # Get token for player
            # Note: In a real test, you would need the player's token
            test_owner_token = "owner_token"  # This would be generated
            
            # Build house on Mediterranean Avenue
            response = client.post(f'/api/games/{game_id}/properties/1/house', headers={
                'Authorization': f'Bearer {test_owner_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify house was built
            assert 'message' in data
            assert 'built' in data['message'].lower()
            
            # Verify property has a house
            property1 = Property.query.get(property1.id)
            assert property1.houses == 1
            
            # Verify player's money decreased by house cost
            player = GamePlayer.query.get(player.id)
            assert player.money == initial_money - property1.house_cost
    
    def test_hotel_building_classic(self, app, db, client, test_active_classic_game_with_color_group):
        """Test building a hotel in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_color_group.id
            
            # Get player who owns a complete color group
            from src.models import GamePlayer, Property
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            
            # Find a property in the owned color group (e.g., purple)
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            
            # Set player as owner with 4 houses already
            property1.owner_id = player.id
            property1.houses = 4
            initial_money = player.money
            db.session.commit()
            
            # Get token for player
            # Note: In a real test, you would need the player's token
            test_owner_token = "owner_token"  # This would be generated
            
            # Build hotel on Mediterranean Avenue (replaces 4 houses)
            response = client.post(f'/api/games/{game_id}/properties/1/hotel', headers={
                'Authorization': f'Bearer {test_owner_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify hotel was built
            assert 'message' in data
            assert 'hotel' in data['message'].lower()
            
            # Verify property has a hotel
            property1 = Property.query.get(property1.id)
            assert property1.hotels == 1
            assert property1.houses == 0  # Houses are replaced by hotel
            
            # Verify player's money decreased by hotel cost
            player = GamePlayer.query.get(player.id)
            assert player.money == initial_money - property1.house_cost  # Hotel costs same as one more house
    
    def test_mortgage_property_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test mortgaging a property in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # First, give player a property
            from src.models import GamePlayer, Property
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            
            property1.owner_id = player.id
            initial_money = player.money
            db.session.commit()
            
            # Mortgage the property
            response = client.post(f'/api/games/{game_id}/properties/1/mortgage', headers={
                'Authorization': f'Bearer {test_player_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify mortgage
            assert 'message' in data
            assert 'mortgaged' in data['message'].lower()
            
            # Verify property is mortgaged
            property1 = Property.query.get(property1.id)
            assert property1.is_mortgaged is True
            
            # Verify player received mortgage value
            player = GamePlayer.query.get(player.id)
            assert player.money == initial_money + (property1.price // 2)  # Mortgage value is half of price
    
    def test_lift_mortgage_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test lifting a mortgage in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # First, give player a mortgaged property
            from src.models import GamePlayer, Property
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            
            property1.owner_id = player.id
            property1.is_mortgaged = True
            mortgage_value = property1.price // 2
            mortgage_interest = mortgage_value // 10  # 10% interest
            
            # Give player enough money to lift mortgage
            player.money = 1000
            initial_money = player.money
            db.session.commit()
            
            # Lift the mortgage
            response = client.post(f'/api/games/{game_id}/properties/1/unmortgage', headers={
                'Authorization': f'Bearer {test_player_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify mortgage lifted
            assert 'message' in data
            assert 'unmortgaged' in data['message'].lower()
            
            # Verify property is no longer mortgaged
            property1 = Property.query.get(property1.id)
            assert property1.is_mortgaged is False
            
            # Verify player paid mortgage value plus 10% interest
            player = GamePlayer.query.get(player.id)
            assert player.money == initial_money - (mortgage_value + mortgage_interest)
    
    def test_trading_classic(self, app, db, client, test_active_classic_game_with_players):
        """Test trading between players in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_players.id
            
            # Get two players
            from src.models import GamePlayer, Property
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            player1 = players[0]
            player2 = players[1]
            
            # Give player1 a property to trade
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            property1.owner_id = player1.id
            
            # Give player2 a property to trade
            property3 = Property.query.filter_by(game_id=game_id, position=3).first()  # Baltic Avenue
            property3.owner_id = player2.id
            
            # Record initial money
            player1_initial_money = player1.money
            player2_initial_money = player2.money
            db.session.commit()
            
            # Get token for player1
            # Note: In a real test, you would need the player's token
            test_player1_token = "player1_token"  # This would be generated
            
            # Create a trade offer
            response = client.post(f'/api/games/{game_id}/trade', json={
                'to_player_id': player2.id,
                'offer_properties': [1],  # Offering Mediterranean Avenue
                'offer_money': 100,
                'request_properties': [3],  # Requesting Baltic Avenue
                'request_money': 0
            }, headers={
                'Authorization': f'Bearer {test_player1_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify trade offer was created
            assert 'trade' in data
            trade_id = data['trade']['id']
            
            # Get token for player2
            # Note: In a real test, you would need the player's token
            test_player2_token = "player2_token"  # This would be generated
            
            # Accept the trade offer
            response = client.post(f'/api/games/{game_id}/trade/{trade_id}/accept', headers={
                'Authorization': f'Bearer {test_player2_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify trade was completed
            assert 'message' in data
            assert 'completed' in data['message'].lower()
            
            # Verify property ownership changed
            property1 = Property.query.get(property1.id)
            property3 = Property.query.get(property3.id)
            
            assert property1.owner_id == player2.id
            assert property3.owner_id == player1.id
            
            # Verify money was exchanged
            player1 = GamePlayer.query.get(player1.id)
            player2 = GamePlayer.query.get(player2.id)
            
            assert player1.money == player1_initial_money - 100
            assert player2.money == player2_initial_money + 100
    
    def test_bankruptcy_classic(self, app, db, client, test_active_classic_game_with_players):
        """Test bankruptcy in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_players.id
            
            # Get two players
            from src.models import GamePlayer, Property, Game
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            player1 = players[0]  # Will go bankrupt
            player2 = players[1]  # Will receive assets
            
            # Give player1 a property
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()  # Mediterranean Avenue
            property1.owner_id = player1.id
            
            # Set player1's money to a very low amount
            player1.money = 10
            db.session.commit()
            
            # Get token for player1
            # Note: In a real test, you would need the player's token
            test_player1_token = "player1_token"  # This would be generated
            
            # Move player1 to an expensive rent property owned by player2
            expensive_property = Property.query.filter_by(game_id=game_id, position=39).first()  # Boardwalk
            expensive_property.owner_id = player2.id
            expensive_property.houses = 4  # High rent with 4 houses
            player1.position = 39  # Boardwalk
            db.session.commit()
            
            # Roll dice (staying on the same space for testing)
            with patch('random.randint', return_value=0):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player1_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player1 went bankrupt
                player1 = GamePlayer.query.get(player1.id)
                assert player1.status == 'bankrupt'
                
                # Verify player1's property was transferred to player2
                property1 = Property.query.get(property1.id)
                assert property1.owner_id == player2.id
                
                # If only two players, game should be over with player2 as winner
                game = Game.query.get(game_id)
                active_players = GamePlayer.query.filter_by(game_id=game_id, status='active').count()
                
                if active_players == 1:
                    assert game.status == 'completed'
                    assert game.winner_id == player2.id
    
    def test_chance_card_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test chance card in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to Chance space
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 7  # First Chance space
            initial_money = player.money
            initial_position = player.position
            db.session.commit()
            
            # Mock a chance card (e.g., "Advance to GO")
            with patch('random.choice', return_value={'type': 'move_to', 'position': 0, 'text': 'Advance to GO. Collect $200.'}):
                # Roll dice (staying on the same space for testing)
                with patch('random.randint', return_value=0):
                    response = client.post(f'/api/games/{game_id}/roll', headers={
                        'Authorization': f'Bearer {test_player_token}'
                    })
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    
                    # Verify chance card was drawn
                    assert 'card' in data
                    assert 'Advance to GO' in data['card']['text']
                    
                    # Verify player moved to GO
                    player = GamePlayer.query.get(player.id)
                    assert player.position == 0  # GO position
                    
                    # Verify player collected $200
                    assert player.money == initial_money + 200
    
    def test_community_chest_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test community chest card in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to Community Chest space
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 2  # First Community Chest space
            initial_money = player.money
            db.session.commit()
            
            # Mock a community chest card (e.g., "Bank error in your favor")
            with patch('random.choice', return_value={'type': 'collect', 'amount': 200, 'text': 'Bank error in your favor. Collect $200.'}):
                # Roll dice (staying on the same space for testing)
                with patch('random.randint', return_value=0):
                    response = client.post(f'/api/games/{game_id}/roll', headers={
                        'Authorization': f'Bearer {test_player_token}'
                    })
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    
                    # Verify community chest card was drawn
                    assert 'card' in data
                    assert 'Bank error in your favor' in data['card']['text']
                    
                    # Verify player received money
                    player = GamePlayer.query.get(player.id)
                    assert player.money == initial_money + 200
    
    def test_income_tax_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test income tax space in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to Income Tax space
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 4  # Income Tax space
            player.money = 2000  # Set money to a known amount
            db.session.commit()
            
            # Roll dice (staying on the same space for testing)
            with patch('random.randint', return_value=0):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player paid income tax
                player = GamePlayer.query.get(player.id)
                assert player.money == 1800  # $2000 - 10% ($200)
    
    def test_luxury_tax_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test luxury tax space in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to Luxury Tax space
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 38  # Luxury Tax space
            player.money = 2000  # Set money to a known amount
            db.session.commit()
            
            # Roll dice (staying on the same space for testing)
            with patch('random.randint', return_value=0):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player paid luxury tax
                player = GamePlayer.query.get(player.id)
                assert player.money == 1900  # $2000 - $100 (luxury tax)
    
    def test_free_parking_classic(self, app, db, client, test_active_classic_game, test_player_token):
        """Test free parking space in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Move player to Free Parking space
            from src.models import GamePlayer, Game
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            player.position = 20  # Free Parking space
            initial_money = player.money
            
            # Set free parking pot
            game = Game.query.get(game_id)
            game.free_parking_pot = 500
            db.session.commit()
            
            # Roll dice (staying on the same space for testing)
            with patch('random.randint', return_value=0):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {test_player_token}'
                })
                
                assert response.status_code == 200
                
                # Verify player collected free parking pot
                player = GamePlayer.query.get(player.id)
                assert player.money == initial_money + 500
                
                # Verify pot is reset
                game = Game.query.get(game_id)
                assert game.free_parking_pot == 0
    
    def test_auction_property_classic(self, app, db, client, test_active_classic_game_with_players):
        """Test property auction in classic mode"""
        with app.app_context():
            game_id = test_active_classic_game_with_players.id
            
            # Get players
            from src.models import GamePlayer, Property
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            player1 = players[0]
            player2 = players[1]
            
            # Move player1 to a property
            player1.position = 1  # Mediterranean Avenue
            property1 = Property.query.filter_by(game_id=game_id, position=1).first()
            initial_money1 = player1.money
            initial_money2 = player2.money
            db.session.commit()
            
            # Get token for player1
            # Note: In a real test, you would need the player's token
            test_player1_token = "player1_token"  # This would be generated
            
            # Decline to buy property, triggering auction
            response = client.post(f'/api/games/{game_id}/decline-purchase', headers={
                'Authorization': f'Bearer {test_player1_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify auction started
            assert 'auction' in data
            auction_id = data['auction']['id']
            
            # Get token for player2
            # Note: In a real test, you would need the player's token
            test_player2_token = "player2_token"  # This would be generated
            
            # Player2 bids on the property
            response = client.post(f'/api/games/{game_id}/auction/{auction_id}/bid', json={
                'amount': 60  # Slightly higher than base price
            }, headers={
                'Authorization': f'Bearer {test_player2_token}'
            })
            
            assert response.status_code == 200
            
            # Player1 passes on bidding
            response = client.post(f'/api/games/{game_id}/auction/{auction_id}/pass', headers={
                'Authorization': f'Bearer {test_player1_token}'
            })
            
            assert response.status_code == 200
            
            # Auction should end with player2 winning
            from src.models import Auction
            auction = Auction.query.get(auction_id)
            assert auction.status == 'completed'
            
            # Verify property ownership and money
            property1 = Property.query.get(property1.id)
            assert property1.owner_id == player2.id
            
            player1 = GamePlayer.query.get(player1.id)
            player2 = GamePlayer.query.get(player2.id)
            
            assert player1.money == initial_money1  # No change
            assert player2.money == initial_money2 - 60  # Paid bid amount 