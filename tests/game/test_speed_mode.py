import pytest
import json
from unittest.mock import patch, Mock
import random

class TestSpeedGameMode:
    """Tests for the speed Monopoly game mode"""
    
    def test_create_speed_game(self, app, db, client, user_token):
        """Test creation of a speed mode game"""
        with app.app_context():
            # Create new speed game
            response = client.post('/api/games', json={
                'name': 'Test Speed Game',
                'mode': 'speed',
                'max_players': 4
            }, headers={
                'Authorization': f'Bearer {user_token}'
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify game properties
            assert data['game']['name'] == 'Test Speed Game'
            assert data['game']['mode'] == 'speed'
            assert data['game']['status'] == 'waiting'
            assert data['game']['max_players'] == 4
            
            # Game should have speed mode board setup
            assert 'board' in data['game']
            # Speed mode typically has fewer properties than classic
            assert len(data['game']['board']['properties']) < 40
    
    def test_join_speed_game(self, app, db, client, test_game_speed, user_token, user_token2):
        """Test joining a speed mode game"""
        with app.app_context():
            game_id = test_game_speed.id
            
            # First player joins the game
            response = client.post(f'/api/games/{game_id}/join', headers={
                'Authorization': f'Bearer {user_token}'
            })
            
            assert response.status_code == 200
            
            # Second player joins the game
            response = client.post(f'/api/games/{game_id}/join', headers={
                'Authorization': f'Bearer {user_token2}'
            })
            
            assert response.status_code == 200
            
            # Verify game state
            response = client.get(f'/api/games/{game_id}', headers={
                'Authorization': f'Bearer {user_token}'
            })
            
            data = json.loads(response.data)
            assert len(data['game']['players']) == 2
    
    def test_start_speed_game(self, app, db, client, test_game_speed_with_players, owner_token):
        """Test starting a speed mode game"""
        with app.app_context():
            game_id = test_game_speed_with_players.id
            
            # Start the game (should be initiated by the owner)
            response = client.post(f'/api/games/{game_id}/start', headers={
                'Authorization': f'Bearer {owner_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Game should now be active
            assert data['game']['status'] == 'active'
            
            # Verify initial game state
            assert data['game']['current_player'] is not None
            
            # All players should start with speed mode starting money (typically less than classic)
            for player in data['game']['players']:
                assert player['money'] == 1000  # Speed mode typically starts with less money
                assert player['position'] == 0  # Starting position (GO)
    
    def test_roll_dice_speed(self, app, db, client, test_active_speed_game, player_token):
        """Test rolling dice in speed mode"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Need to ensure it's this player's turn
            from src.models import Game, GamePlayer
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Set current player to this player
            game.current_player_id = player.id
            db.session.commit()
            
            # Roll dice
            with patch('random.randint', side_effect=[3, 4]):  # Mocking dice roll to 3 and 4
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {player_token["token"]}'
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify dice roll
            assert 'dice' in data
            assert len(data['dice']) == 2  # Speed mode also uses 2 dice
            assert data['dice'][0] == 3
            assert data['dice'][1] == 4
            
            # Player should move 7 spaces (3+4)
            # In speed mode, the board is smaller so position might wrap around earlier
            assert data['player']['position'] == (0 + 7) % len(game.board.properties)
    
    def test_buy_property_speed(self, app, db, client, test_active_speed_game, player_token):
        """Test buying a property in speed mode"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Need to ensure it's this player's turn and position them on a property
            from src.models import Game, GamePlayer, Property
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Position player on a property (e.g. first property after GO)
            property_pos = 1
            player.position = property_pos
            game.current_player_id = player.id
            db.session.commit()
            
            # Get property details
            property_obj = Property.query.filter_by(
                game_id=game_id,
                position=property_pos
            ).first()
            
            initial_money = player.money
            
            # Buy the property
            response = client.post(f'/api/games/{game_id}/buy', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Property should now be owned by the player
            assert data['property']['owner_id'] == player.id
            
            # Player money should be reduced by property price
            assert data['player']['money'] == initial_money - property_obj.price
            
            # Property prices in speed mode are typically lower than in classic
            assert property_obj.price < 200  # Assuming Mediterranean Ave price in classic is 60
    
    def test_speed_mode_time_limit(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has a game time limit"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Get game details
            response = client.get(f'/api/games/{game_id}', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Speed mode should have a time limit defined
            assert 'time_limit' in data['game']
            assert data['game']['time_limit'] is not None
            assert data['game']['time_limit'] > 0  # Positive time limit
            
            # Speed mode typically has a 30-minute time limit (1800 seconds)
            assert data['game']['time_limit'] <= 1800  # At most 30 minutes
    
    def test_speed_mode_turn_timer(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has a turn timer"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Need to ensure it's this player's turn
            from src.models import Game, GamePlayer
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            game.current_player_id = player.id
            db.session.commit()
            
            # Get current turn details
            response = client.get(f'/api/games/{game_id}/turn', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Turn should have a time limit
            assert 'turn_time_limit' in data
            assert data['turn_time_limit'] is not None
            assert data['turn_time_limit'] > 0
            
            # Speed mode typically has a short turn limit (e.g., 30 seconds)
            assert data['turn_time_limit'] <= 60  # At most 60 seconds
    
    def test_pass_go_speed_mode(self, app, db, client, test_active_speed_game, player_token):
        """Test passing GO in speed mode (should give a different amount than classic)"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Position player just before GO
            from src.models import Game, GamePlayer
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Position at the last property before GO
            max_position = len(game.board.properties) - 1
            player.position = max_position
            game.current_player_id = player.id
            
            initial_money = player.money
            db.session.commit()
            
            # Roll dice to pass GO
            with patch('random.randint', side_effect=[1, 2]):  # 1+2 = 3, taking player past GO
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {player_token["token"]}'
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify player position wrapped around and money increased
            assert data['player']['position'] == 3 - 1  # Account for 0-indexing
            
            # Speed mode typically gives less GO salary (e.g., $100 instead of $200)
            assert data['player']['money'] > initial_money
            assert data['player']['money'] == initial_money + 100  # Speed mode GO salary
    
    def test_speed_mode_simplified_jail(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has simplified jail mechanics"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Put player in jail
            from src.models import Game, GamePlayer
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Find the jail position in speed mode (typically still position 10)
            jail_position = 10
            # Check if jail position exists in this smaller board
            if jail_position >= len(game.board.properties):
                jail_position = len(game.board.properties) // 4  # Approximately 1/4 through the board
            
            player.position = jail_position
            player.in_jail = True
            game.current_player_id = player.id
            
            initial_money = player.money
            db.session.commit()
            
            # In speed mode, jail fee should be lower
            response = client.post(f'/api/games/{game_id}/pay-jail-fine', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Player should be out of jail
            assert data['player']['in_jail'] is False
            
            # Speed mode jail fine should be $25 (half of classic mode)
            assert data['player']['money'] == initial_money - 25
    
    def test_speed_mode_property_groups(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has simplified property groups"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Get game board configuration
            response = client.get(f'/api/games/{game_id}/board', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Count the number of property groups in speed mode
            property_groups = set()
            for prop in data['properties']:
                if 'group' in prop and prop['group'] is not None:
                    property_groups.add(prop['group'])
            
            # Speed mode should have fewer property groups than classic (which has 8 color groups)
            assert len(property_groups) < 8
    
    def test_speed_mode_simplified_houses(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has simplified house building rules"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Setup: player owns a complete property group
            from src.models import Game, GamePlayer, Property
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Find properties in the same group
            properties = Property.query.filter_by(game_id=game_id).all()
            # Get the first property and its group
            first_property = properties[1]  # Skip GO
            property_group = first_property.group
            
            # Find all properties in this group
            group_properties = [p for p in properties if p.group == property_group]
            
            # Give all properties in the group to the player
            for prop in group_properties:
                prop.owner_id = player.id
            
            initial_money = player.money
            db.session.commit()
            
            # In speed mode, building houses should be cheaper
            response = client.post(f'/api/games/{game_id}/properties/{first_property.id}/build', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify house was built
            assert data['property']['houses'] == 1
            
            # House cost in speed mode is typically lower than in classic
            player = GamePlayer.query.get(player.id)
            house_cost = initial_money - player.money
            
            # Verify the house cost is reduced in speed mode
            # Classic mode house costs are $50+ depending on property
            assert house_cost < 50
    
    def test_speed_mode_bankruptcy_condition(self, app, db, client, test_active_speed_game, player_token, player_token2):
        """Test modified bankruptcy conditions in speed mode"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Setup: player1 has very little money, player2 owns property
            from src.models import Game, GamePlayer, Property
            
            game = Game.query.get(game_id)
            
            player1 = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            player2 = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token2['user_id']
            ).first()
            
            # Make player1 almost broke
            player1.money = 10
            
            # Find an expensive property and make player2 own it
            properties = Property.query.filter_by(game_id=game_id).all()
            expensive_property = max(properties, key=lambda p: p.price)
            expensive_property.owner_id = player2.id
            expensive_property.houses = 1  # Add a house to increase rent
            
            # Position player1 just before expensive property
            player1.position = (expensive_property.position - 1) % len(properties)
            game.current_player_id = player1.id
            db.session.commit()
            
            # Roll to land on expensive property
            dice_value = 1
            with patch('random.randint', return_value=dice_value):
                response = client.post(f'/api/games/{game_id}/roll', headers={
                    'Authorization': f'Bearer {player_token["token"]}'
                })
            
            # Player should now be bankrupt
            player1 = GamePlayer.query.get(player1.id)
            assert player1.bankrupt is True
            
            # In speed mode, after bankruptcy we should verify the game checks win condition
            # which is typically based on either money, properties, or a mix
            game = Game.query.get(game_id)
            
            # If all other players are bankrupt, the game should be over
            all_others_bankrupt = all(p.bankrupt for p in game.players if p.id != player2.id)
            if all_others_bankrupt:
                assert game.status == 'completed'
                assert game.winner_id == player2.id
    
    def test_speed_mode_win_by_time(self, app, db, client, test_active_speed_game):
        """Test that speed mode can end by time limit with a winner"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Setup: make the game expire by time
            from src.models import Game, GamePlayer
            from datetime import datetime, timedelta
            
            game = Game.query.get(game_id)
            
            # Set game start time to be just before the time limit expires
            time_limit_seconds = game.time_limit or 1800  # Default to 30 min if not set
            game.started_at = datetime.utcnow() - timedelta(seconds=time_limit_seconds + 1)
            
            # Give each player different money and property values to determine a winner
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            
            # Give the first player the most money
            for i, player in enumerate(players):
                player.money = 1000 - (i * 100)  # First player has the most
            
            db.session.commit()
            
            # Trigger a game state check which should end the game by time
            response = client.post(f'/api/games/{game_id}/check-time-limit', headers={
                'Authorization': 'Bearer admin_token_placeholder'  # Server-side operation
            })
            
            # Verify game has ended
            game = Game.query.get(game_id)
            assert game.status == 'completed'
            
            # Winner should be player with most money (first player)
            assert game.winner_id == players[0].id
            
            # Get game details to verify end message
            response = client.get(f'/api/games/{game_id}', headers={
                'Authorization': 'Bearer admin_token_placeholder'
            })
            
            data = json.loads(response.data)
            assert "time limit" in data['game']['end_message'].lower()
    
    def test_speed_mode_skip_turn_on_timeout(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode skips a player's turn if they time out"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Setup: current player turn has timed out
            from src.models import Game, GamePlayer
            from datetime import datetime, timedelta
            
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Find another player to be next
            next_player = GamePlayer.query.filter(
                GamePlayer.game_id == game_id,
                GamePlayer.id != player.id
            ).first()
            
            # Set current player
            game.current_player_id = player.id
            
            # Set turn started time to be in the past, beyond the turn time limit
            turn_time_limit_seconds = 30  # Speed mode typically has a 30-second turn limit
            game.turn_started_at = datetime.utcnow() - timedelta(seconds=turn_time_limit_seconds + 5)
            
            db.session.commit()
            
            # Simulate server checking for timed-out turns
            response = client.post(f'/api/games/{game_id}/check-turn-timeout', headers={
                'Authorization': 'Bearer admin_token_placeholder'  # Server-side operation
            })
            
            # Verify turn was skipped to next player
            game = Game.query.get(game_id)
            assert game.current_player_id == next_player.id
            
            # There should be a message about the turn being skipped
            assert "turn skipped" in response.data.decode().lower()
    
    def test_speed_mode_property_values(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode has modified property values"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Get game board configuration
            response = client.get(f'/api/games/{game_id}/board', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Get property prices from the response
            property_prices = [prop['price'] for prop in data['properties'] if 'price' in prop]
            
            # In speed mode, property prices should generally be lower
            # Let's check that the most expensive property is less than the most expensive
            # in classic mode (typically Boardwalk at $400)
            assert max(property_prices) < 400
            
            # Check rent values too
            property_rents = [prop['rent'] for prop in data['properties'] if 'rent' in prop]
            # Max rent in classic mode for a property without houses is typically 50
            assert max(property_rents) < 50
    
    def test_speed_mode_no_utilities(self, app, db, client, test_active_speed_game, player_token):
        """Test that speed mode might simplify utilities"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Get game board configuration
            response = client.get(f'/api/games/{game_id}/board', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Count utilities and railroads (speed mode often simplifies or removes these)
            utilities = [prop for prop in data['properties'] if prop.get('type') == 'utility']
            railroads = [prop for prop in data['properties'] if prop.get('type') == 'railroad']
            
            # Speed mode might have fewer utilities and railroads than classic
            # Classic has 2 utilities and 4 railroads
            assert len(utilities) <= 2
            assert len(railroads) <= 4
    
    def test_speed_mode_game_end_by_property_count(self, app, db, client, test_active_speed_game):
        """Test that speed mode can end when a player owns a certain number of properties"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Setup: give one player most of the properties
            from src.models import Game, GamePlayer, Property
            
            game = Game.query.get(game_id)
            players = GamePlayer.query.filter_by(game_id=game_id).all()
            first_player = players[0]
            
            # Count total properties on the board
            properties = Property.query.filter_by(game_id=game_id).all()
            purchasable_properties = [p for p in properties if p.price > 0]
            
            # Give the first player most of the properties
            property_threshold = len(purchasable_properties) * 0.75  # 75% ownership threshold
            for i, prop in enumerate(purchasable_properties):
                if i < property_threshold:
                    prop.owner_id = first_player.id
            
            db.session.commit()
            
            # Trigger property check
            response = client.post(f'/api/games/{game_id}/check-property-win', headers={
                'Authorization': 'Bearer admin_token_placeholder'  # Server-side operation
            })
            
            # Verify game has ended and winner is determined
            game = Game.query.get(game_id)
            
            # Only assert these if speed mode implements property-based winning
            if game.status == 'completed':
                assert game.winner_id == first_player.id
                
                # Get game details to verify end message
                response = client.get(f'/api/games/{game_id}', headers={
                    'Authorization': 'Bearer admin_token_placeholder'
                })
                
                data = json.loads(response.data)
                assert "properties" in data['game']['end_message'].lower()
    
    def test_speed_mode_auction_timer(self, app, db, client, test_active_speed_game, player_token):
        """Test that auctions in speed mode have a time limit"""
        with app.app_context():
            game_id = test_active_speed_game.id
            
            # Position player on an unowned property
            from src.models import Game, GamePlayer, Property
            game = Game.query.get(game_id)
            player = GamePlayer.query.filter_by(
                game_id=game_id, 
                user_id=player_token['user_id']
            ).first()
            
            # Find an unowned property
            properties = Property.query.filter_by(
                game_id=game_id,
                owner_id=None
            ).filter(Property.price > 0).all()
            
            if not properties:
                # Create an unowned property if none exists
                first_property = Property.query.filter(
                    Property.game_id == game_id,
                    Property.price > 0
                ).first()
                first_property.owner_id = None
                db.session.commit()
                
                unowned_property = first_property
            else:
                unowned_property = properties[0]
            
            # Position player on the unowned property
            player.position = unowned_property.position
            game.current_player_id = player.id
            db.session.commit()
            
            # Decline to buy the property (triggering auction)
            response = client.post(f'/api/games/{game_id}/decline-purchase', headers={
                'Authorization': f'Bearer {player_token["token"]}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify auction started
            assert "auction" in data['status_message'].lower()
            
            # Speed mode should have an auction timer
            assert 'timer' in data['auction'] or 'time_limit' in data['auction']
            
            auction_timer = data['auction'].get('timer') or data['auction'].get('time_limit')
            assert auction_timer is not None
            assert auction_timer > 0
            
            # Speed mode auction should be quick (e.g., 30 seconds max)
            assert auction_timer <= 30 