import pytest
import uuid
from datetime import datetime, timedelta

class TestPlayerModel:
    """Tests for the Player model class."""
    
    def test_player_creation(self, app, db):
        """Test that a player can be created and stored correctly"""
        from src.models.player import Player
        
        with app.app_context():
            # Create a test player with a unique name
            username = f"test_player_{uuid.uuid4().hex[:8]}"
            test_player = Player(
                username=username,
                pin="1234",
                money=1500,
                position=0,
                is_admin=False,
                is_bot=False
            )
            
            # Add to database
            db.session.add(test_player)
            db.session.commit()
            
            # Fetch the player from database
            player_from_db = db.session.get(Player, test_player.id)
            
            # Verify the player was created correctly
            assert player_from_db is not None
            assert player_from_db.username == username
            assert player_from_db.money == 1500
            assert player_from_db.position == 0
            assert player_from_db.is_admin is False
            assert player_from_db.is_bot is False
            assert player_from_db.updated_at is not None
    
    def test_player_money_transactions(self, app, db, test_player):
        """Test player money transactions (add, subtract)"""
        from src.models.player import Player
        
        with app.app_context():
            # Get the initial money
            initial_money = test_player.money
            
            # Add money
            test_player.add_money(500)
            db.session.commit()
            
            # Verify money was added
            assert test_player.money == initial_money + 500
            
            # Subtract money
            test_player.subtract_money(200)
            db.session.commit()
            
            # Verify money was subtracted
            assert test_player.money == initial_money + 500 - 200
    
    def test_player_movement(self, app, db, test_player):
        """Test player movement on the board"""
        with app.app_context():
            # Start at position 0
            assert test_player.position == 0
            
            # Move forward 5 spaces
            test_player.move(5)
            db.session.commit()
            
            # Verify position
            assert test_player.position == 5
            
            # Move forward 35 spaces (should wrap around the board)
            test_player.move(35)
            db.session.commit()
            
            # Verify position (board has 40 spaces, so should be at position 0 + 5 + 35 = 40 -> 0)
            assert test_player.position == 0
            
            # Test wrap detection (should return True if we pass Go)
            # Move to position 39
            test_player.position = 39
            db.session.commit()
            
            # Move 5 spaces (should wrap around)
            passes_go = test_player.move(5)
            
            # Verify position and passing Go
            assert test_player.position == 4
            assert passes_go == True
    
    def test_player_jail_status(self, app, db, test_player):
        """Test player jail status and jail turns"""
        with app.app_context():
            # Initially not in jail
            assert test_player.in_jail is False
            assert test_player.jail_turns == 0
            
            # Send to jail
            test_player.send_to_jail()
            db.session.commit()
            
            # Verify in jail
            assert test_player.in_jail is True
            assert test_player.position == 10  # Jail position
            assert test_player.jail_turns == 0
            
            # Increment jail turn
            test_player.increment_jail_turn()
            db.session.commit()
            
            # Verify jail turn incremented
            assert test_player.jail_turns == 1
            
            # Release from jail
            test_player.release_from_jail()
            db.session.commit()
            
            # Verify released from jail
            assert test_player.in_jail is False
            assert test_player.jail_turns == 0
    
    def test_player_property_ownership(self, app, db, test_player, test_property):
        """Test player property ownership"""
        with app.app_context():
            # Initially player has no properties
            assert len(test_player.properties) == 0
            
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Refresh player to get updated properties list
            db.session.refresh(test_player)
            
            # Verify player owns the property
            assert len(test_player.properties) == 1
            assert test_player.properties[0].id == test_property.id
            assert test_player.properties[0].name == test_property.name
    
    def test_player_credit_score(self, app, db, test_player):
        """Test player credit score functionality"""
        with app.app_context():
            # Default credit score should be set
            assert test_player.credit_score is not None
            initial_score = test_player.credit_score
            
            # Test improving credit score
            test_player.improve_credit_score(10)
            db.session.commit()
            
            # Verify credit score improved
            assert test_player.credit_score == initial_score + 10
            
            # Test decreasing credit score
            test_player.decrease_credit_score(20)
            db.session.commit()
            
            # Verify credit score decreased
            assert test_player.credit_score == initial_score + 10 - 20
    
    def test_player_to_dict(self, app, db, test_player, test_property):
        """Test the to_dict method for API serialization"""
        with app.app_context():
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Get player dict
            player_dict = test_player.to_dict()
            
            # Verify dict contains expected keys
            assert 'id' in player_dict
            assert 'username' in player_dict
            assert 'money' in player_dict
            assert 'position' in player_dict
            assert 'in_jail' in player_dict
            assert 'credit_score' in player_dict
            
            # Verify values
            assert player_dict['username'] == test_player.username
            assert player_dict['money'] == test_player.money
            assert player_dict['position'] == test_player.position
    
    def test_player_bankruptcy(self, app, db, test_player, test_property):
        """Test player bankruptcy process"""
        with app.app_context():
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Declare bankruptcy
            test_player.declare_bankruptcy()
            db.session.commit()
            
            # Verify bankruptcy state
            assert test_player.is_bankrupt is True
            assert test_player.money == 0
            
            # Verify property ownership was removed
            db.session.refresh(test_property)
            assert test_property.owner_id is None
    
    def test_player_last_activity(self, app, db, test_player):
        """Test tracking of player last activity"""
        with app.app_context():
            # Update last activity
            original_time = test_player.updated_at
            
            # Wait a small amount to ensure time difference
            time_before_update = datetime.utcnow()
            
            # Update player to trigger updated_at change
            test_player.money += 100
            db.session.commit()
            
            # Verify updated_at time changed
            assert test_player.updated_at > original_time
            assert test_player.updated_at >= time_before_update 