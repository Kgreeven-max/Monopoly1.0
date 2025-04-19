import pytest
import json
import os
import logging
import time
import uuid
from flask import Flask, g, session
from flask_socketio import SocketIO, emit
from sqlalchemy import text
from unittest.mock import MagicMock, patch

# Setup test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture
def app():
    """Create a test Flask app with testing configuration"""
    # Import the Flask app instance from the main app.py file
    import sys
    import os
    # Add the project root to sys.path to allow proper imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import app as flask_app
    
    # Set testing configuration
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost'
    
    # Use an in-memory SQLite database for testing
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Return the app
    return flask_app

@pytest.fixture
def client(app):
    """Get a test client for the app"""
    return app.test_client()

@pytest.fixture
def socketio_client(app):
    """Get a test socketio client for the app"""
    from app import socketio
    return socketio.test_client(app)

@pytest.fixture
def db(app):
    """Get the database object and set up test database"""
    from src.models import db
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Run migrations
        try:
            from src.migrations.add_updated_at_column import run_migration
            run_migration()
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
        
        yield db
        
        # Clean up
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_game(app, db):
    """Create a test game for use in tests"""
    from src.models.game import Game
    
    with app.app_context():
        test_game = Game()  # No parameters needed for basic initialization
        db.session.add(test_game)
        db.session.commit()
        
        return test_game

@pytest.fixture
def test_player(app, db, test_game):
    """Create a test player for use in tests"""
    from src.models.player import Player
    
    with app.app_context():
        test_player = Player(
            username=f"test_player_{uuid.uuid4().hex[:8]}",
            pin="1234",
            money=1500,
            position=0,
            is_admin=False,
            is_bot=False,
            game_id=test_game.id if test_game else None
        )
        
        db.session.add(test_player)
        db.session.commit()
        
        return test_player

@pytest.fixture
def admin_player(app, db, test_game):
    """Create an admin player for testing admin functionality"""
    from src.models.player import Player
    
    with app.app_context():
        admin = Player(
            username="admin",
            pin="admin",
            money=10000,
            position=0,
            is_admin=True,
            is_bot=False,
            game_id=test_game.id if test_game else None
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return admin

@pytest.fixture
def test_property(app, db, test_game):
    """Create a test property for use in tests"""
    from src.models.property import Property, PropertyType
    
    with app.app_context():
        test_property = Property(
            name=f"Test Property {uuid.uuid4().hex[:8]}",
            position=5,
            group_name="test_group",
            price=200,
            rent=10
        )
        
        # Set required attributes
        test_property.type = PropertyType.STREET
        test_property.game_id = test_game.id
        
        db.session.add(test_property)
        db.session.commit()
        
        return test_property

@pytest.fixture
def test_game_state(app, db):
    """Create a test game state for use in tests"""
    from src.models.game_state import GameState
    
    with app.app_context():
        game_id = str(uuid.uuid4())
        test_game_state = GameState(game_id=game_id)
        
        db.session.add(test_game_state)
        db.session.commit()
        
        return test_game_state

@pytest.fixture
def mock_admin_auth(monkeypatch):
    """Mock admin authentication for admin routes testing"""
    from flask import g, session
    
    def mock_admin_required(f):
        def decorated(*args, **kwargs):
            # This simulates having admin auth
            g.is_admin = True
            g.admin_authenticated = True
            session['is_admin'] = True
            return f(*args, **kwargs)
        return decorated
    
    monkeypatch.setattr('src.routes.decorators.admin_required', mock_admin_required)
    
    # Also directly patch the underlying auth check function if it exists
    try:
        monkeypatch.setattr('src.controllers.auth_controller.is_admin', lambda *args, **kwargs: True)
    except (ImportError, AttributeError):
        pass
    
    return mock_admin_required

@pytest.fixture
def authenticated_client(client, app, admin_player):
    """Get a test client with admin authentication already set up"""
    with client.session_transaction() as sess:
        sess['is_admin'] = True
        sess['admin_authenticated'] = True
        sess['user_id'] = admin_player.id
    
    client.environ_base['HTTP_X_ADMIN_KEY'] = 'admin_test_key'
    return client

@pytest.fixture
def populate_test_game(app, db, test_game, test_player, test_property):
    """Populate a test game with standard Monopoly data"""
    from src.models.property import Property, PropertyType
    
    with app.app_context():
        # Add some standard properties
        properties = [
            # Brown group
            {"name": "Mediterranean Avenue", "position": 1, "group_name": "brown", "price": 60, "rent": 2, "type": PropertyType.STREET},
            {"name": "Baltic Avenue", "position": 3, "group_name": "brown", "price": 60, "rent": 4, "type": PropertyType.STREET},
            
            # Light blue group
            {"name": "Oriental Avenue", "position": 6, "group_name": "light_blue", "price": 100, "rent": 6, "type": PropertyType.STREET},
            {"name": "Vermont Avenue", "position": 8, "group_name": "light_blue", "price": 100, "rent": 6, "type": PropertyType.STREET},
            {"name": "Connecticut Avenue", "position": 9, "group_name": "light_blue", "price": 120, "rent": 8, "type": PropertyType.STREET},
            
            # Railroads
            {"name": "Reading Railroad", "position": 5, "group_name": "railroad", "price": 200, "rent": 25, "type": PropertyType.RAILROAD},
            {"name": "Pennsylvania Railroad", "position": 15, "group_name": "railroad", "price": 200, "rent": 25, "type": PropertyType.RAILROAD},
            
            # Utilities
            {"name": "Electric Company", "position": 12, "group_name": "utility", "price": 150, "rent": 0, "type": PropertyType.UTILITY},
            {"name": "Water Works", "position": 28, "group_name": "utility", "price": 150, "rent": 0, "type": PropertyType.UTILITY},
        ]
        
        for prop_data in properties:
            prop = Property(
                name=prop_data["name"],
                position=prop_data["position"],
                group_name=prop_data["group_name"],
                price=prop_data["price"],
                rent=prop_data["rent"]
            )
            prop.type = prop_data["type"]
            prop.game_id = test_game.id
            db.session.add(prop)
        
        db.session.commit()
        
        return test_game 