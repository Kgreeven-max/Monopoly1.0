import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

class TestAdminDashboard:
    """Tests for the admin dashboard functionality"""
    
    def test_admin_login(self, app, db, client):
        """Test admin login functionality"""
        with app.app_context():
            # Test admin login
            response = client.post('/api/admin/login', json={
                'username': 'admin',
                'password': 'admin_password'  # Assuming this is the admin password in test environment
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify token is returned
            assert 'token' in data
            assert data['token'] is not None
            assert len(data['token']) > 0
            
            # Verify admin role
            assert 'role' in data
            assert data['role'] == 'admin'
    
    def test_admin_dashboard_access(self, app, db, client, admin_token):
        """Test accessing the admin dashboard"""
        with app.app_context():
            # Access admin dashboard
            response = client.get('/api/admin/dashboard', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify dashboard data structure
            assert 'stats' in data
            assert 'games' in data['stats']
            assert 'users' in data['stats']
            assert 'active_games' in data['stats']
    
    def test_list_all_games(self, app, db, client, admin_token, test_game_classic, test_game_speed):
        """Test listing all games in the admin dashboard"""
        with app.app_context():
            # Get all games
            response = client.get('/api/admin/games', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify games list
            assert 'games' in data
            assert len(data['games']) >= 2  # At least our test games should be there
            
            # Verify game details
            game_ids = [game['id'] for game in data['games']]
            assert test_game_classic.id in game_ids
            assert test_game_speed.id in game_ids
    
    def test_view_specific_game(self, app, db, client, admin_token, test_game_classic):
        """Test viewing a specific game as admin"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Get specific game details
            response = client.get(f'/api/admin/games/{game_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify game details
            assert 'game' in data
            assert data['game']['id'] == game_id
            assert data['game']['name'] == test_game_classic.name
            assert data['game']['mode'] == 'classic'
            
            # Admin view should have extra details not available to regular users
            assert 'created_at' in data['game']
            assert 'admin_notes' in data
    
    def test_list_all_users(self, app, db, client, admin_token, test_user, test_user2):
        """Test listing all users in the admin dashboard"""
        with app.app_context():
            # Get all users
            response = client.get('/api/admin/users', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify users list
            assert 'users' in data
            assert len(data['users']) >= 2  # At least our test users should be there
            
            # Verify user details (without exposing sensitive info)
            user_ids = [user['id'] for user in data['users']]
            assert test_user.id in user_ids
            assert test_user2.id in user_ids
            
            # Ensure password is not exposed
            for user in data['users']:
                assert 'password' not in user
    
    def test_view_specific_user(self, app, db, client, admin_token, test_user):
        """Test viewing a specific user as admin"""
        with app.app_context():
            user_id = test_user.id
            
            # Get specific user details
            response = client.get(f'/api/admin/users/{user_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify user details
            assert 'user' in data
            assert data['user']['id'] == user_id
            assert data['user']['username'] == test_user.username
            
            # Admin view should have extra details not available to regular users
            assert 'created_at' in data['user']
            assert 'last_login' in data['user']
            
            # Also should show games played by this user
            assert 'games' in data
    
    def test_create_user(self, app, db, client, admin_token):
        """Test creating a new user as admin"""
        with app.app_context():
            # Create new user
            response = client.post('/api/admin/users', json={
                'username': 'new_test_user',
                'password': 'password123',
                'email': 'newtest@example.com'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify user was created
            assert 'user' in data
            assert data['user']['username'] == 'new_test_user'
            assert data['user']['email'] == 'newtest@example.com'
            
            # Ensure password is not exposed
            assert 'password' not in data['user']
            
            # Verify user exists in database
            from src.models import User
            new_user = User.query.filter_by(username='new_test_user').first()
            assert new_user is not None
    
    def test_edit_user(self, app, db, client, admin_token, test_user):
        """Test editing a user as admin"""
        with app.app_context():
            user_id = test_user.id
            
            # Edit existing user
            response = client.put(f'/api/admin/users/{user_id}', json={
                'email': 'updated_email@example.com',
                'status': 'suspended'  # Admin can suspend users
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify user was updated
            assert 'user' in data
            assert data['user']['email'] == 'updated_email@example.com'
            assert data['user']['status'] == 'suspended'
            
            # Verify changes in database
            from src.models import User
            updated_user = User.query.get(user_id)
            assert updated_user.email == 'updated_email@example.com'
            assert updated_user.status == 'suspended'
    
    def test_delete_user(self, app, db, client, admin_token):
        """Test deleting a user as admin"""
        with app.app_context():
            # First create a user to delete
            from src.models import User
            delete_test_user = User(
                username='delete_test_user',
                email='delete@example.com'
            )
            delete_test_user.set_password('password123')
            db.session.add(delete_test_user)
            db.session.commit()
            
            user_id = delete_test_user.id
            
            # Delete the user
            response = client.delete(f'/api/admin/users/{user_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify deletion success message
            assert 'message' in data
            assert 'successfully deleted' in data['message'].lower()
            
            # Verify user no longer exists in database
            deleted_user = User.query.get(user_id)
            assert deleted_user is None
    
    def test_admin_create_game(self, app, db, client, admin_token):
        """Test creating a game as admin"""
        with app.app_context():
            # Create new game
            response = client.post('/api/admin/games', json={
                'name': 'Admin Created Game',
                'mode': 'classic',
                'max_players': 6,
                'password_protected': True,
                'password': 'game_password'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify game was created
            assert 'game' in data
            assert data['game']['name'] == 'Admin Created Game'
            assert data['game']['mode'] == 'classic'
            assert data['game']['max_players'] == 6
            assert data['game']['password_protected'] is True
            
            # Ensure password is not exposed
            assert 'password' not in data['game']
    
    def test_admin_edit_game(self, app, db, client, admin_token, test_game_classic):
        """Test editing a game as admin"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Edit existing game
            response = client.put(f'/api/admin/games/{game_id}', json={
                'name': 'Updated Game Name',
                'max_players': 8,
                'admin_notes': 'Test notes from admin'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify game was updated
            assert 'game' in data
            assert data['game']['name'] == 'Updated Game Name'
            assert data['game']['max_players'] == 8
            
            # Verify admin notes
            assert 'admin_notes' in data
            assert data['admin_notes'] == 'Test notes from admin'
            
            # Verify changes in database
            from src.models import Game
            updated_game = Game.query.get(game_id)
            assert updated_game.name == 'Updated Game Name'
            assert updated_game.max_players == 8
    
    def test_admin_delete_game(self, app, db, client, admin_token, test_game_classic):
        """Test deleting a game as admin"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Delete the game
            response = client.delete(f'/api/admin/games/{game_id}', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify deletion success message
            assert 'message' in data
            assert 'successfully deleted' in data['message'].lower()
            
            # Verify game no longer exists in database
            from src.models import Game
            deleted_game = Game.query.get(game_id)
            assert deleted_game is None
    
    def test_admin_override_game_status(self, app, db, client, admin_token, test_game_classic):
        """Test admin ability to override game status"""
        with app.app_context():
            game_id = test_game_classic.id
            
            # Override game status
            response = client.post(f'/api/admin/games/{game_id}/override', json={
                'status': 'completed',
                'winner_id': 1,  # Assuming player ID 1 exists
                'admin_notes': 'Game manually completed by admin due to technical issue'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify game status was updated
            assert 'game' in data
            assert data['game']['status'] == 'completed'
            assert data['game']['winner_id'] == 1
            
            # Verify changes in database
            from src.models import Game
            updated_game = Game.query.get(game_id)
            assert updated_game.status == 'completed'
            assert updated_game.winner_id == 1
    
    def test_admin_reset_game(self, app, db, client, admin_token, test_active_classic_game):
        """Test admin ability to reset a game to initial state"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # First ensure game is in progress with some player actions
            from src.models import Game, GamePlayer, Property
            game = Game.query.get(game_id)
            
            # Make sure game is active with some properties owned
            assert game.status == 'active'
            
            # Get a player
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            
            # Make player own a property
            prop = Property.query.filter_by(game_id=game_id).filter(Property.price > 0).first()
            prop.owner_id = player.id
            db.session.commit()
            
            # Now reset the game
            response = client.post(f'/api/admin/games/{game_id}/reset', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify reset message
            assert 'message' in data
            assert 'reset' in data['message'].lower()
            
            # Verify game state reset in database
            game = Game.query.get(game_id)
            assert game.status == 'waiting'  # Reset to waiting for players
            
            # Properties should no longer be owned
            prop = Property.query.get(prop.id)
            assert prop.owner_id is None
            
            # Players should still exist but with reset values
            player = GamePlayer.query.get(player.id)
            assert player.money == 1500  # Reset to starting money
            assert player.position == 0  # Reset to GO position
    
    def test_admin_game_logs(self, app, db, client, admin_token, test_active_classic_game):
        """Test viewing game logs as admin"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Create some game logs
            from src.models import GameLog
            
            # Add test logs
            log1 = GameLog(
                game_id=game_id,
                action='Player joined',
                details='Player 1 joined the game',
                timestamp=datetime.utcnow() - timedelta(minutes=10)
            )
            log2 = GameLog(
                game_id=game_id,
                action='Game started',
                details='Game started with 2 players',
                timestamp=datetime.utcnow() - timedelta(minutes=5)
            )
            db.session.add(log1)
            db.session.add(log2)
            db.session.commit()
            
            # Get game logs
            response = client.get(f'/api/admin/games/{game_id}/logs', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify logs list
            assert 'logs' in data
            assert len(data['logs']) >= 2
            
            # Verify log details
            log_actions = [log['action'] for log in data['logs']]
            assert 'Player joined' in log_actions
            assert 'Game started' in log_actions
    
    def test_admin_system_settings(self, app, db, client, admin_token):
        """Test viewing and updating system settings as admin"""
        with app.app_context():
            # Get current system settings
            response = client.get('/api/admin/settings', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            initial_data = json.loads(response.data)
            
            # Update system settings
            response = client.put('/api/admin/settings', json={
                'maintenance_mode': True,
                'maintenance_message': 'System under maintenance, please check back later',
                'max_games_per_user': 5,
                'default_starting_money': 2000
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            updated_data = json.loads(response.data)
            
            # Verify settings were updated
            assert updated_data['settings']['maintenance_mode'] is True
            assert updated_data['settings']['maintenance_message'] == 'System under maintenance, please check back later'
            assert updated_data['settings']['max_games_per_user'] == 5
            assert updated_data['settings']['default_starting_money'] == 2000
            
            # Verify settings affect game creation
            # Try to create a game while in maintenance mode
            response = client.post('/api/games', json={
                'name': 'Test Game During Maintenance',
                'mode': 'classic',
                'max_players': 4
            }, headers={
                'Authorization': f'Bearer {admin_token}'  # Even admin should see maintenance mode
            })
            
            # Should get maintenance mode response
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'maintenance' in data['message'].lower()
    
    def test_admin_audit_log(self, app, db, client, admin_token):
        """Test viewing admin action audit logs"""
        with app.app_context():
            # Perform an admin action to create a log entry
            client.post('/api/admin/users', json={
                'username': 'audit_test_user',
                'password': 'password123',
                'email': 'audit@example.com'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            # Get admin audit logs
            response = client.get('/api/admin/audit-logs', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify audit logs structure
            assert 'logs' in data
            assert len(data['logs']) > 0
            
            # Find our user creation action
            user_creation_logs = [log for log in data['logs'] 
                                 if 'created user' in log.get('action', '').lower()]
            assert len(user_creation_logs) > 0
            
            # Audit log should have admin details
            last_log = data['logs'][0]
            assert 'admin_id' in last_log
            assert 'timestamp' in last_log
            assert 'action' in last_log
            assert 'ip_address' in last_log
    
    def test_admin_dashboard_statistics(self, app, db, client, admin_token):
        """Test admin dashboard statistics"""
        with app.app_context():
            # Get dashboard statistics
            response = client.get('/api/admin/statistics', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify statistics structure
            assert 'statistics' in data
            stats = data['statistics']
            
            # User statistics
            assert 'users' in stats
            assert 'total' in stats['users']
            assert 'active' in stats['users']
            assert 'new_today' in stats['users']
            
            # Game statistics
            assert 'games' in stats
            assert 'total' in stats['games']
            assert 'active' in stats['games']
            assert 'completed' in stats['games']
            assert 'by_mode' in stats['games']
            
            # System statistics
            assert 'system' in stats
            assert 'uptime' in stats['system']
            assert 'version' in stats['system']
    
    def test_admin_announcement(self, app, db, client, admin_token):
        """Test creating global announcements as admin"""
        with app.app_context():
            # Create announcement
            response = client.post('/api/admin/announcements', json={
                'title': 'Test Announcement',
                'content': 'This is a test announcement for all users',
                'level': 'info',
                'expiry': (datetime.utcnow() + timedelta(days=7)).isoformat()
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            # Verify announcement created
            assert 'announcement' in data
            announcement_id = data['announcement']['id']
            
            # Regular users should see the announcement
            # First logout from admin
            client.post('/api/logout')
            
            # Login as regular user
            from src.models import User
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(username='testuser', email='test@example.com')
                test_user.set_password('password123')
                db.session.add(test_user)
                db.session.commit()
            
            # Get user token
            response = client.post('/api/login', json={
                'username': 'testuser',
                'password': 'password123'
            })
            user_token = json.loads(response.data)['token']
            
            # Get announcements as user
            response = client.get('/api/announcements', headers={
                'Authorization': f'Bearer {user_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify user can see the announcement
            assert 'announcements' in data
            assert len(data['announcements']) > 0
            
            # Find our test announcement
            test_announcements = [a for a in data['announcements'] if a['title'] == 'Test Announcement']
            assert len(test_announcements) > 0
    
    def test_admin_ban_user(self, app, db, client, admin_token, test_user):
        """Test banning a user as admin"""
        with app.app_context():
            user_id = test_user.id
            
            # Ban the user
            response = client.post(f'/api/admin/users/{user_id}/ban', json={
                'reason': 'Test ban reason',
                'duration': 24  # Ban for 24 hours
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify ban message
            assert 'message' in data
            assert 'banned' in data['message'].lower()
            
            # Check that user is now banned
            from src.models import User
            banned_user = User.query.get(user_id)
            assert banned_user.status == 'banned'
            assert banned_user.ban_reason == 'Test ban reason'
            assert banned_user.ban_expires_at is not None  # Should have an expiry time
            
            # User should not be able to login
            response = client.post('/api/login', json={
                'username': test_user.username,
                'password': 'password123'  # Assuming this is the test user password
            })
            
            assert response.status_code == 403
            data = json.loads(response.data)
            assert 'banned' in data['message'].lower()
    
    def test_admin_unban_user(self, app, db, client, admin_token, test_user):
        """Test unbanning a user as admin"""
        with app.app_context():
            user_id = test_user.id
            
            # First ensure user is banned
            from src.models import User
            banned_user = User.query.get(user_id)
            banned_user.status = 'banned'
            banned_user.ban_reason = 'Banned for testing'
            banned_user.ban_expires_at = datetime.utcnow() + timedelta(days=1)
            db.session.commit()
            
            # Now unban the user
            response = client.post(f'/api/admin/users/{user_id}/unban', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify unban message
            assert 'message' in data
            assert 'unbanned' in data['message'].lower()
            
            # Check that user is now active again
            unbanned_user = User.query.get(user_id)
            assert unbanned_user.status == 'active'
            assert unbanned_user.ban_reason is None
            assert unbanned_user.ban_expires_at is None
            
            # User should be able to login now
            response = client.post('/api/login', json={
                'username': test_user.username,
                'password': 'password123'  # Assuming this is the test user password
            })
            
            assert response.status_code == 200
            assert 'token' in json.loads(response.data)
    
    def test_admin_force_game_action(self, app, db, client, admin_token, test_active_classic_game):
        """Test admin ability to force game actions"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Get a player in the game
            from src.models import GamePlayer
            player = GamePlayer.query.filter_by(game_id=game_id).first()
            
            # Force a game action (e.g., give player money)
            response = client.post(f'/api/admin/games/{game_id}/force-action', json={
                'action': 'give_money',
                'player_id': player.id,
                'amount': 500,
                'reason': 'Admin intervention to fix game imbalance'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify action success
            assert 'message' in data
            assert 'successfully' in data['message'].lower()
            
            # Verify player's money was updated
            player = GamePlayer.query.get(player.id)
            assert player.money == 1500 + 500  # Starting money (1500) + amount (500)
    
    def test_admin_force_game_chat(self, app, db, client, admin_token, test_active_classic_game):
        """Test admin ability to send game chat messages"""
        with app.app_context():
            game_id = test_active_classic_game.id
            
            # Send admin message to game chat
            response = client.post(f'/api/admin/games/{game_id}/send-message', json={
                'content': 'This is an important admin message',
                'is_system': True
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify message success
            assert 'message' in data
            assert 'sent' in data['message'].lower()
            
            # Verify message appears in game chat
            response = client.get(f'/api/games/{game_id}/chat', headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            chat_data = json.loads(response.data)
            admin_messages = [msg for msg in chat_data['messages'] 
                             if msg.get('is_system') and 'admin message' in msg.get('content', '')]
            
            assert len(admin_messages) > 0
    
    def test_admin_purge_old_games(self, app, db, client, admin_token):
        """Test admin ability to purge old games"""
        with app.app_context():
            # Create some old games
            from src.models import Game
            
            old_game1 = Game(
                name='Old Game 1',
                mode='classic',
                status='completed',
                created_at=datetime.utcnow() - timedelta(days=90)
            )
            old_game2 = Game(
                name='Old Game 2',
                mode='speed',
                status='completed',
                created_at=datetime.utcnow() - timedelta(days=95)
            )
            db.session.add(old_game1)
            db.session.add(old_game2)
            db.session.commit()
            
            old_game_ids = [old_game1.id, old_game2.id]
            
            # Purge old games (older than 30 days)
            response = client.post('/api/admin/purge-old-games', json={
                'days': 30,
                'status': 'completed'
            }, headers={
                'Authorization': f'Bearer {admin_token}'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify purge message
            assert 'message' in data
            assert 'purged' in data['message'].lower()
            assert 'count' in data
            assert data['count'] >= 2  # At least our two old games
            
            # Verify old games are gone
            for game_id in old_game_ids:
                game = Game.query.get(game_id)
                assert game is None 