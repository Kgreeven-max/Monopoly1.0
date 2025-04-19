import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

class TestAdminDashboard:
    """Tests for admin dashboard functionality"""
    
    def test_admin_login(self, app, db, client):
        """Test administrator login functionality"""
        with app.app_context():
            # Create admin user
            from src.models import User
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("adminpassword")
            db.session.add(admin)
            db.session.commit()
            
            # Test login
            response = client.post('/api/auth/login', json={
                'username': 'admin',
                'password': 'adminpassword'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify admin flag is included in response
            assert data['user']['is_admin'] is True
            assert 'token' in data  # Should return authentication token
    
    def test_admin_access_dashboard(self, app, db, client, admin_token):
        """Test admin dashboard access with valid credentials"""
        with app.app_context():
            # Access admin dashboard
            response = client.get('/api/admin/dashboard', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify dashboard contains expected components
            assert 'active_games' in data
            assert 'registered_users' in data
            assert 'total_games_played' in data
            assert 'system_status' in data
    
    def test_non_admin_access_denied(self, app, db, client, user_token):
        """Test non-admin users cannot access admin dashboard"""
        with app.app_context():
            # Attempt to access admin dashboard with regular user token
            response = client.get('/api/admin/dashboard', headers={
                'Authorization': f'Bearer {user_token}'
            })
            
            # Should be forbidden
            assert response.status_code == 403
    
    def test_admin_view_all_games(self, app, db, client, admin_token, test_games):
        """Test admin can view all games in the system"""
        with app.app_context():
            # Get all games
            response = client.get('/api/admin/games', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify all test games are returned
            assert len(data['games']) == len(test_games)
            
            # Check if response contains essential game data
            for game in data['games']:
                assert 'id' in game
                assert 'name' in game
                assert 'mode' in game
                assert 'status' in game
                assert 'created_at' in game
    
    def test_admin_view_all_users(self, app, db, client, admin_token, test_users):
        """Test admin can view all registered users"""
        with app.app_context():
            # Get all users
            response = client.get('/api/admin/users', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify all test users are returned plus admin
            assert len(data['users']) >= len(test_users)
            
            # Check if response contains essential user data
            for user in data['users']:
                assert 'id' in user
                assert 'username' in user
                assert 'email' in user
                assert 'is_admin' in user
                assert 'created_at' in user
                
                # Password should not be included
                assert 'password' not in user
    
    def test_admin_game_details(self, app, db, client, admin_token, test_game_classic):
        """Test admin can view detailed game information"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Get detailed game info
            response = client.get(f'/api/admin/games/{game_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify detailed game data
            assert data['game']['id'] == game_id
            assert 'name' in data['game']
            assert 'players' in data['game']
            assert 'properties' in data['game']
            assert 'transactions' in data['game']
            assert 'created_at' in data['game']
            assert 'updated_at' in data['game']
    
    def test_admin_terminate_game(self, app, db, client, admin_token, test_game_classic):
        """Test admin can forcefully terminate a game"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Terminate game
            response = client.post(f'/api/admin/games/{game_id}/terminate', json={
                'reason': 'Administrative action'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            
            # Verify game was terminated
            from src.models import Game
            game = Game.query.get(game_id)
            assert game.status == 'terminated'
            assert game.end_reason == 'admin_terminated'
    
    def test_admin_modify_user(self, app, db, client, admin_token, test_users):
        """Test admin can modify user account settings"""
        with app.app_context():
            user_id = test_users[0].id
            
            # Update user details
            response = client.put(f'/api/admin/users/{user_id}', json={
                'email': 'updated@example.com',
                'is_admin': False,
                'is_active': True
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            
            # Verify changes applied
            from src.models import User
            user = User.query.get(user_id)
            assert user.email == 'updated@example.com'
            assert user.is_admin is False
            assert user.is_active is True
    
    def test_admin_system_stats(self, app, db, client, admin_token):
        """Test admin can view system statistics"""
        with app.app_context():
            # Get system stats
            response = client.get('/api/admin/stats', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify stats fields
            assert 'user_count' in data
            assert 'game_count' in data
            assert 'active_games' in data
            assert 'games_by_mode' in data
            assert 'registrations_by_date' in data
            assert 'games_by_date' in data
    
    def test_admin_create_user(self, app, db, client, admin_token):
        """Test admin can create new user accounts"""
        with app.app_context():
            # Create a new user
            response = client.post('/api/admin/users', json={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'newuserpassword',
                'is_admin': False
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify user was created
            assert 'user_id' in data
            
            # Check user in database
            from src.models import User
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.is_admin is False
            
            # Password should be hashed
            assert user.check_password('newuserpassword') is True
    
    def test_admin_delete_user(self, app, db, client, admin_token, test_users):
        """Test admin can delete user accounts"""
        with app.app_context():
            user_id = test_users[-1].id  # Use last test user
            
            # Delete user
            response = client.delete(f'/api/admin/users/{user_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            
            # Verify user is deleted or deactivated
            from src.models import User
            user = User.query.get(user_id)
            
            # Depending on implementation, user might be hard deleted or just marked inactive
            if user is not None:
                assert user.is_active is False
            else:
                assert User.query.filter_by(id=user_id).first() is None
    
    def test_admin_game_logs(self, app, db, client, admin_token, test_game_classic):
        """Test admin can view game logs"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Create some game logs
            from src.models import GameLog
            logs = [
                GameLog(game_id=game_id, action="start_game", details="Game started"),
                GameLog(game_id=game_id, action="player_move", details="Player 1 moved to Boardwalk"),
                GameLog(game_id=game_id, action="property_purchase", details="Player 1 purchased Boardwalk")
            ]
            db.session.add_all(logs)
            db.session.commit()
            
            # Get game logs
            response = client.get(f'/api/admin/games/{game_id}/logs', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify logs are returned
            assert len(data['logs']) >= 3
            
            # Check log structure
            for log in data['logs']:
                assert 'id' in log
                assert 'game_id' in log
                assert 'action' in log
                assert 'details' in log
                assert 'created_at' in log
    
    def test_admin_system_configuration(self, app, db, client, admin_token):
        """Test admin can update system configuration"""
        with app.app_context():
            # Update system configuration
            response = client.put('/api/admin/config', json={
                'user_registration_enabled': True,
                'max_games_per_user': 5,
                'maintenance_mode': False,
                'system_announcement': "Welcome to the game!"
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            
            # Verify configuration was updated
            response = client.get('/api/admin/config', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['config']['user_registration_enabled'] is True
            assert data['config']['max_games_per_user'] == 5
            assert data['config']['maintenance_mode'] is False
            assert data['config']['system_announcement'] == "Welcome to the game!"
    
    def test_admin_game_analytics(self, app, db, client, admin_token, test_games):
        """Test admin can view game analytics"""
        with app.app_context():
            # Get game analytics
            response = client.get('/api/admin/analytics/games', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify analytics data structure
            assert 'average_game_duration' in data
            assert 'games_by_mode' in data
            assert 'completion_rate' in data
            assert 'popular_properties' in data
    
    def test_admin_user_analytics(self, app, db, client, admin_token, test_users):
        """Test admin can view user analytics"""
        with app.app_context():
            # Get user analytics
            response = client.get('/api/admin/analytics/users', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify analytics data structure
            assert 'active_users' in data
            assert 'user_growth' in data
            assert 'top_players' in data
            assert 'login_frequency' in data
    
    def test_admin_daily_report(self, app, db, client, admin_token):
        """Test admin can generate daily activity reports"""
        with app.app_context():
            # Generate report for today
            today = datetime.now().strftime('%Y-%m-%d')
            response = client.get(f'/api/admin/reports/daily/{today}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify report structure
            assert 'date' in data
            assert 'new_users' in data
            assert 'new_games' in data
            assert 'active_games' in data
            assert 'completed_games' in data
    
    def test_admin_export_data(self, app, db, client, admin_token):
        """Test admin can export system data"""
        with app.app_context():
            # Request data export
            response = client.get('/api/admin/export/games', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            assert response.mimetype == 'application/json'
            
            data = json.loads(response.data)
            assert 'games' in data
            
            # Test user export
            response = client.get('/api/admin/export/users', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            assert response.mimetype == 'application/json'
            
            data = json.loads(response.data)
            assert 'users' in data
            
            # Ensure sensitive data is excluded
            for user in data['users']:
                assert 'password' not in user 