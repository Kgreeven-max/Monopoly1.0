import pytest
import uuid
from datetime import datetime, timedelta

class TestPropertyModel:
    """Tests for the Property model class."""
    
    def test_property_creation(self, app, db, test_game):
        """Test that a property can be created and stored correctly"""
        from src.models.property import Property, PropertyType
        
        with app.app_context():
            # Create a test property with a unique name
            name = f"Test Property {uuid.uuid4().hex[:8]}"
            test_property = Property(
                name=name,
                position=5,
                group_name="test_group",
                price=200,
                rent=10
            )
            
            # Set required attributes
            test_property.type = PropertyType.STREET
            test_property.game_id = test_game.id
            
            # Add to database
            db.session.add(test_property)
            db.session.commit()
            
            # Fetch the property from database
            property_from_db = db.session.get(Property, test_property.id)
            
            # Verify the property was created correctly
            assert property_from_db is not None
            assert property_from_db.name == name
            assert property_from_db.price == 200
            assert property_from_db.rent == 10
            assert property_from_db.type == PropertyType.STREET
            assert property_from_db.position == 5
            assert property_from_db.group_name == "test_group"
            assert property_from_db.game_id == test_game.id
    
    def test_property_ownership(self, app, db, test_property, test_player):
        """Test property ownership"""
        with app.app_context():
            # Initially property has no owner
            assert test_property.owner_id is None
            
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Verify property is owned by player
            assert test_property.owner_id == test_player.id
            
            # Check relationship
            db.session.refresh(test_property)
            assert test_property.owner is not None
            assert test_property.owner.id == test_player.id
    
    def test_property_mortgage(self, app, db, test_property, test_player):
        """Test mortgaging and unmortgaging properties"""
        with app.app_context():
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Initially property is not mortgaged
            assert test_property.is_mortgaged is False
            
            # Get player's initial money
            initial_money = test_player.money
            
            # Mortgage property
            mortgage_value = test_property.mortgage_value
            test_property.mortgage()
            db.session.commit()
            
            # Verify property is mortgaged
            assert test_property.is_mortgaged is True
            
            # Unmortgage property
            unmortgage_cost = int(mortgage_value * 1.1)  # Usually 10% interest
            test_property.unmortgage()
            db.session.commit()
            
            # Verify property is unmortgaged
            assert test_property.is_mortgaged is False
    
    def test_property_improvement(self, app, db, test_property, test_player):
        """Test property improvements (houses/hotels)"""
        with app.app_context():
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Initially property has no houses
            assert test_property.houses == 0
            assert test_property.hotel is False
            
            # Add a house
            test_property.houses = 1
            db.session.commit()
            
            # Verify house was added
            assert test_property.houses == 1
            
            # Add more houses to reach hotel
            test_property.houses = 4
            db.session.commit()
            
            # Convert to hotel
            test_property.houses = 0
            test_property.hotel = True
            db.session.commit()
            
            # Verify hotel was added
            assert test_property.houses == 0
            assert test_property.hotel is True
    
    def test_property_rent_calculation(self, app, db, test_game):
        """Test rent calculation for various property scenarios"""
        from src.models.property import Property, PropertyType
        from src.models.player import Player
        
        with app.app_context():
            # Create property owner
            owner = Player(username="owner", pin="1234", money=2000, game_id=test_game.id)
            db.session.add(owner)
            db.session.commit()
            
            # Create properties of different types
            street_property = Property(
                name="Test Street",
                position=1,
                group_name="brown",
                price=60,
                rent=2,
                rent_house_1=10,
                rent_house_2=30,
                rent_house_3=90,
                rent_house_4=160,
                rent_hotel=250,
                game_id=test_game.id
            )
            street_property.type = PropertyType.STREET
            street_property.owner_id = owner.id
            
            railroad_property = Property(
                name="Test Railroad",
                position=5,
                group_name="railroad",
                price=200,
                rent=25,
                game_id=test_game.id
            )
            railroad_property.type = PropertyType.RAILROAD
            railroad_property.owner_id = owner.id
            
            utility_property = Property(
                name="Test Utility",
                position=12,
                group_name="utility",
                price=150,
                rent=0,  # Rent is based on dice roll
                game_id=test_game.id
            )
            utility_property.type = PropertyType.UTILITY
            utility_property.owner_id = owner.id
            
            db.session.add_all([street_property, railroad_property, utility_property])
            db.session.commit()
            
            # Test basic rent
            assert street_property.calculate_rent() == 2
            
            # Test rent with houses
            street_property.houses = 1
            db.session.commit()
            assert street_property.calculate_rent() == 10
            
            street_property.houses = 2
            db.session.commit()
            assert street_property.calculate_rent() == 30
            
            # Test rent with hotel
            street_property.houses = 0
            street_property.hotel = True
            db.session.commit()
            assert street_property.calculate_rent() == 250
            
            # Test railroad rent (depends on how many railroads owner has)
            assert railroad_property.calculate_rent() == 25  # One railroad
            
            # Test utility rent (depends on dice roll)
            # Assuming dice roll of 7
            assert utility_property.calculate_rent(dice_roll=7) == 28  # 7 * 4 for one utility
    
    def test_property_monopoly_rent(self, app, db, test_game):
        """Test rent calculation when owner has a monopoly"""
        from src.models.property import Property, PropertyType
        from src.models.player import Player
        
        with app.app_context():
            # Create property owner
            owner = Player(username="owner", pin="1234", money=2000, game_id=test_game.id)
            db.session.add(owner)
            db.session.commit()
            
            # Create all properties in a color group
            prop1 = Property(
                name="Mediterranean Avenue",
                position=1,
                group_name="brown",
                price=60,
                rent=2,
                game_id=test_game.id
            )
            prop1.type = PropertyType.STREET
            prop1.owner_id = owner.id
            
            prop2 = Property(
                name="Baltic Avenue",
                position=3,
                group_name="brown",
                price=60,
                rent=4,
                game_id=test_game.id
            )
            prop2.type = PropertyType.STREET
            prop2.owner_id = owner.id
            
            db.session.add_all([prop1, prop2])
            db.session.commit()
            
            # Verify monopoly doubles the rent
            assert prop1.calculate_rent() == 4  # Double the normal rent
            assert prop2.calculate_rent() == 8  # Double the normal rent
    
    def test_property_economic_effects(self, app, db, test_property):
        """Test economic effects on property values"""
        with app.app_context():
            # Get initial values
            initial_price = test_property.price
            
            # Apply market crash (reduce value)
            test_property.apply_market_crash(percentage=20)
            db.session.commit()
            
            # Verify price decreased
            assert test_property.current_price < initial_price
            assert test_property.current_price == int(initial_price * 0.8)  # 20% reduction
            
            # Apply economic boom (increase value)
            test_property.apply_economic_boom(percentage=25)
            db.session.commit()
            
            # Verify price increased
            expected_price = int(int(initial_price * 0.8) * 1.25)  # 25% increase on crashed value
            assert test_property.current_price == expected_price
            
            # Restore to original values
            test_property.restore_market_prices()
            db.session.commit()
            
            # Verify original values restored
            assert test_property.current_price == initial_price
    
    def test_property_to_dict(self, app, db, test_property, test_player):
        """Test the to_dict method for API serialization"""
        with app.app_context():
            # Assign property to player
            test_property.owner_id = test_player.id
            db.session.commit()
            
            # Get property dict
            property_dict = test_property.to_dict()
            
            # Verify dict contains expected keys
            assert 'id' in property_dict
            assert 'name' in property_dict
            assert 'type' in property_dict
            assert 'price' in property_dict
            assert 'rent' in property_dict
            assert 'owner_id' in property_dict
            assert 'is_mortgaged' in property_dict
            assert 'houses' in property_dict
            assert 'hotel' in property_dict
            
            # Verify values
            assert property_dict['name'] == test_property.name
            assert property_dict['price'] == test_property.price
            assert property_dict['owner_id'] == test_player.id
            assert property_dict['is_mortgaged'] == test_property.is_mortgaged 