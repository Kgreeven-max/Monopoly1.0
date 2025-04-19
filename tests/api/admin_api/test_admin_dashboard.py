import pytest
import json
import uuid

class TestAdminDashboard:
    """Tests for the Admin Dashboard API endpoints."""
    
    def test_admin_login(self, app, client):
        """Test the admin login endpoint"""
        with app.app_context():
            # Test with correct credentials
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': app.config.get('ADMIN_PASSWORD', 'admin')
            })
            
            # Should succeed
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            assert 'token' in data
            
            # Test with incorrect credentials
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'wrongpassword'
            })
            
            # Should fail
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data.get('success') is False
    
    def test_admin_properties_endpoint(self, app, authenticated_client, db, test_game, test_property):
        """Test the admin properties endpoint"""
        with app.app_context():
            # Get all properties
            response = authenticated_client.get('/api/admin/properties')
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            assert 'properties' in data
            
            # Verify our test property is in the response
            found = False
            for prop in data['properties']:
                if prop.get('id') == test_property.id:
                    found = True
                    assert prop.get('name') == test_property.name
                    assert prop.get('price') == test_property.price
                    assert prop.get('rent') == test_property.rent
            
            assert found, "Test property not found in response"
    
    def test_admin_edit_property(self, app, authenticated_client, db, test_property):
        """Test editing a property through the admin API"""
        with app.app_context():
            # Prepare property update
            new_name = f"Updated Property {uuid.uuid4().hex[:8]}"
            new_price = 300
            new_rent = 25
            
            # Update the property
            response = authenticated_client.put(f'/api/admin/properties/{test_property.id}', json={
                'name': new_name,
                'price': new_price,
                'rent': new_rent
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify property was updated in the database
            db.session.refresh(test_property)
            assert test_property.name == new_name
            assert test_property.price == new_price
            assert test_property.rent == new_rent
    
    def test_admin_players_endpoint(self, app, authenticated_client, db, test_game, test_player):
        """Test the admin players endpoint"""
        with app.app_context():
            # Get all players
            response = authenticated_client.get('/api/admin/players')
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            assert 'players' in data
            
            # Verify our test player is in the response
            found = False
            for player in data['players']:
                if player.get('id') == test_player.id:
                    found = True
                    assert player.get('username') == test_player.username
                    assert player.get('money') == test_player.money
                    assert player.get('position') == test_player.position
            
            assert found, "Test player not found in response"
    
    def test_admin_edit_player(self, app, authenticated_client, db, test_player):
        """Test editing a player through the admin API"""
        with app.app_context():
            # Prepare player update
            new_money = 2000
            new_position = 15
            
            # Update the player
            response = authenticated_client.put(f'/api/admin/players/{test_player.id}', json={
                'money': new_money,
                'position': new_position
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify player was updated in the database
            db.session.refresh(test_player)
            assert test_player.money == new_money
            assert test_player.position == new_position
    
    def test_admin_game_state_endpoint(self, app, authenticated_client, db, test_game_state):
        """Test the admin game state endpoint"""
        with app.app_context():
            # Get game state
            response = authenticated_client.get('/api/admin/game-state')
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            assert 'game_state' in data
            
            # Verify game state data
            game_state = data['game_state']
            assert game_state.get('game_id') == test_game_state.game_id
            assert game_state.get('status') == test_game_state.status
    
    def test_admin_update_game_state(self, app, authenticated_client, db, test_game_state):
        """Test updating game state through the admin API"""
        with app.app_context():
            # Prepare game state update
            new_status = 'Paused'
            
            # Update the game state
            response = authenticated_client.put('/api/admin/game-state', json={
                'status': new_status
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify game state was updated in the database
            db.session.refresh(test_game_state)
            assert test_game_state.status == new_status
    
    def test_admin_create_bot(self, app, authenticated_client, db, test_game):
        """Test creating a bot player through the admin API"""
        with app.app_context():
            # Prepare bot creation data
            bot_name = f"Bot_{uuid.uuid4().hex[:8]}"
            bot_type = "aggressive"
            
            # Create the bot
            response = authenticated_client.post('/api/admin/bots', json={
                'username': bot_name,
                'type': bot_type,
                'game_id': test_game.id
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            assert 'bot' in data
            
            # Verify bot properties
            bot = data['bot']
            assert bot.get('username') == bot_name
            assert bot.get('is_bot') is True
            
            # Verify bot was created in the database
            from src.models.player import Player
            bot_in_db = Player.query.filter_by(username=bot_name).first()
            assert bot_in_db is not None
            assert bot_in_db.is_bot is True
            assert bot_in_db.game_id == test_game.id
    
    def test_admin_reset_game(self, app, authenticated_client, db, test_game, test_game_state, test_player):
        """Test resetting a game through the admin API"""
        with app.app_context():
            # First modify some game state to verify reset
            test_player.money = 5000
            test_player.position = 20
            test_game_state.status = 'In Progress'
            db.session.commit()
            
            # Reset the game
            response = authenticated_client.post('/api/admin/reset-game')
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify game was reset
            db.session.refresh(test_game_state)
            db.session.refresh(test_player)
            
            assert test_game_state.status == 'Waiting'
            assert test_player.money == 1500  # Default starting money
            assert test_player.position == 0   # Start position
    
    def test_admin_economic_controls(self, app, authenticated_client, db, test_game_state):
        """Test the economic control endpoints"""
        with app.app_context():
            # Test setting inflation
            response = authenticated_client.post('/api/admin/economy/set-inflation', json={
                'inflation_rate': 1.05
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify inflation was updated
            db.session.refresh(test_game_state)
            assert abs(test_game_state.inflation_factor - 1.05) < 0.001
            
            # Test triggering economic event
            response = authenticated_client.post('/api/admin/economy/trigger-event', json={
                'event_type': 'recession'
            })
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify economic state was updated
            db.session.refresh(test_game_state)
            assert test_game_state.inflation_state == 'recession'
    
    def test_admin_dashboard_statistics(self, app, authenticated_client, db, test_game, test_player, test_property):
        """Test the admin dashboard statistics endpoint"""
        with app.app_context():
            # Assign property to player to create some game data
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Get dashboard statistics
            response = authenticated_client.get('/api/admin/dashboard/stats')
            
            # Verify successful response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('success') is True
            
            # Verify statistics data structure
            stats = data.get('stats', {})
            assert 'player_count' in stats
            assert 'property_ownership' in stats
            assert 'money_distribution' in stats
            
            # Verify our test data is reflected
            assert stats['player_count'] >= 1
            
            # Player should have one property
            found = False
            for player_data in stats['property_ownership']:
                if player_data.get('player_id') == test_player.id:
                    found = True
                    assert player_data.get('property_count') >= 1
            
            assert found, "Test player property ownership not found in statistics" 