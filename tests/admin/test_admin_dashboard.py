import pytest
import json
from unittest.mock import patch

class TestAdminDashboard:
    """Tests for the admin dashboard functionality"""
    
    def test_admin_login(self, app, client):
        """Test admin login functionality"""
        with app.app_context():
            # Test successful admin login
            response = client.post('/admin/login', json={
                'username': 'admin',
                'password': 'adminpassword'  # assuming this is configured in the app
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'token' in data
            
            # Test failed admin login with incorrect password
            response = client.post('/admin/login', json={
                'username': 'admin',
                'password': 'wrongpassword'
            })
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid credentials' in data['message']
    
    def test_admin_auth_required(self, app, client):
        """Test that admin endpoints require authentication"""
        with app.app_context():
            # Test accessing a protected endpoint without authentication
            response = client.get('/admin/games')
            assert response.status_code == 401
            
            # Test accessing a protected endpoint with invalid token
            response = client.get('/admin/games', headers={
                'Authorization': 'Bearer invalid_token'
            })
            assert response.status_code == 401
    
    def test_admin_games_list(self, app, client, test_game):
        """Test admin games list functionality"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting list of all games
                response = client.get('/admin/games', headers={
                    'Authorization': 'Bearer mock_token'
                })
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'games' in data
                assert isinstance(data['games'], list)
                
                # Verify the test game is in the list
                game_ids = [g['id'] for g in data['games']]
                assert test_game.id in game_ids
    
    def test_admin_game_details(self, app, client, test_game):
        """Test getting detailed game information"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting details for a specific game
                response = client.get(f'/admin/games/{test_game.id}', headers={
                    'Authorization': 'Bearer mock_token'
                })
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['game']['id'] == test_game.id
                
                # Test getting details for a non-existent game
                response = client.get('/admin/games/999999', headers={
                    'Authorization': 'Bearer mock_token'
                })
                assert response.status_code == 404
    
    def test_admin_create_game(self, app, client):
        """Test admin ability to create a new game"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test creating a new game
                response = client.post('/admin/games', 
                    json={
                        'name': 'Admin Created Game',
                        'mode': 'classic',
                        'max_players': 4
                    },
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'game_id' in data
                
                # Test creating a game with invalid data
                response = client.post('/admin/games', 
                    json={
                        'name': '',  # Empty name should fail validation
                        'mode': 'invalid_mode',
                        'max_players': 0
                    },
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 400
                data = json.loads(response.data)
                assert data['success'] is False
    
    def test_admin_delete_game(self, app, client, db, test_game):
        """Test admin ability to delete a game"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test deleting a game
                response = client.delete(f'/admin/games/{test_game.id}', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                
                # Verify game has been deleted
                response = client.get(f'/admin/games/{test_game.id}', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 404
    
    def test_admin_update_game(self, app, client, db, test_game):
        """Test admin ability to update game settings"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test updating game settings
                response = client.put(f'/admin/games/{test_game.id}', 
                    json={
                        'name': 'Updated Game Name',
                        'status': 'Paused',
                        'mode': 'speed'
                    },
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                
                # Verify game has been updated
                response = client.get(f'/admin/games/{test_game.id}', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['game']['name'] == 'Updated Game Name'
                assert data['game']['status'] == 'Paused'
                assert data['game']['mode'] == 'speed'
    
    def test_admin_player_management(self, app, client, db, test_game, test_player):
        """Test admin ability to manage players in a game"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting players for a game
                response = client.get(f'/admin/games/{test_game.id}/players', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'players' in data
                
                # Verify test player is in the list
                player_ids = [p['id'] for p in data['players']]
                assert test_player.id in player_ids
                
                # Test removing a player from a game
                response = client.delete(f'/admin/games/{test_game.id}/players/{test_player.id}', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                
                # Verify player has been removed
                response = client.get(f'/admin/games/{test_game.id}/players', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                data = json.loads(response.data)
                player_ids = [p['id'] for p in data['players']]
                assert test_player.id not in player_ids
    
    def test_admin_dashboard_stats(self, app, client):
        """Test admin dashboard statistics functionality"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting dashboard statistics
                response = client.get('/admin/dashboard/stats', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Verify required statistics exist
                assert 'active_games' in data
                assert 'total_games' in data
                assert 'active_players' in data
                assert 'total_players' in data
    
    def test_admin_system_settings(self, app, client):
        """Test admin ability to view and update system settings"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting system settings
                response = client.get('/admin/settings', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'settings' in data
                
                # Test updating system settings
                response = client.put('/admin/settings', 
                    json={
                        'max_concurrent_games': 10,
                        'allow_public_game_creation': True,
                        'default_player_starting_money': 2000
                    },
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                
                # Verify settings were updated
                response = client.get('/admin/settings', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                data = json.loads(response.data)
                assert data['settings']['max_concurrent_games'] == 10
                assert data['settings']['allow_public_game_creation'] is True
                assert data['settings']['default_player_starting_money'] == 2000
    
    def test_admin_game_logs(self, app, client, test_game):
        """Test admin ability to view game logs"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test getting game logs
                response = client.get(f'/admin/games/{test_game.id}/logs', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'logs' in data
                assert isinstance(data['logs'], list)
    
    def test_admin_audit_trail(self, app, client):
        """Test admin audit trail functionality"""
        with app.app_context():
            # Mock the auth verification to bypass login
            with patch('src.routes.admin_routes.verify_admin_token', return_value=True):
                # Test accessing audit trail
                response = client.get('/admin/audit-trail', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'audit_entries' in data
                assert isinstance(data['audit_entries'], list)
                
                # Test filtering audit trail by action type
                response = client.get('/admin/audit-trail?action=login', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # All entries should be of type 'login'
                if data['audit_entries']:
                    assert all(entry['action'] == 'login' for entry in data['audit_entries'])
                
                # Test filtering by date range
                response = client.get('/admin/audit-trail?start_date=2023-01-01&end_date=2023-12-31', 
                    headers={'Authorization': 'Bearer mock_token'}
                )
                assert response.status_code == 200 