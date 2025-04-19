import pytest
import json
from unittest.mock import patch, Mock

class TestClassicMode:
    """Tests for the Classic game mode"""
    
    def test_classic_mode_initialization(self, app, db, client):
        """Test a game can be initialized with Classic mode"""
        with app.app_context():
            # Create a new game with Classic mode
            response = client.post('/api/games', json={
                'name': 'Test Classic Game',
                'mode': 'classic',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Get game details to verify mode settings
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify Classic mode settings
            assert data['game']['mode'] == 'classic'
            assert data['game']['max_rounds'] is None  # No round limit in classic
            assert data['game']['double_go_money'] is False  # Standard GO money
            assert data['game']['free_parking_bonus'] is False  # No free parking bonus
    
    def test_classic_mode_starting_money(self, app, db, client, test_game_classic, test_players):
        """Test players start with correct amount of money in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player_id = test_players[0].id
            
            # Check player's money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Classic mode players start with standard $1500
            assert data['player']['money'] == 1500
    
    def test_classic_mode_go_money(self, app, db, client, test_game_classic, test_players):
        """Test players receive standard money when passing GO in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Set initial money and position
            with db.session.begin():
                player.money = 1500  # Reset to starting amount
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
            
            # Verify player received standard GO money
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Starting money + standard GO money ($200)
            assert data['player']['money'] == 1500 + 200
    
    def test_classic_mode_no_free_parking_bonus(self, app, db, client, test_game_classic, test_players):
        """Test no free parking bonus in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Set the initial money and position
            with db.session.begin():
                player.money = 1500  # Reset to starting amount
                test_game_classic.free_parking_pot = 0  # No money in pot
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
            
            # Verify player did not receive any bonus
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Money should remain unchanged
            assert data['player']['money'] == 1500
    
    def test_classic_mode_tax_handling(self, app, db, client, test_game_classic, test_players):
        """Test tax payments go to bank in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Reset free parking pot
            with db.session.begin():
                player.money = 1500  # Reset to starting amount
                test_game_classic.free_parking_pot = 0
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
            assert data['player']['money'] == 1500 - 200
            
            # Verify tax went to bank, not free parking
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Free parking pot should remain 0
            assert data['game']['free_parking_pot'] == 0
    
    def test_classic_mode_property_improvements(self, app, db, client, test_game_classic, test_players):
        """Test standard property improvement costs in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Set up monopoly for the player
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player.id
                park_place.owner_id = player.id
                
                # Set initial money
                player.money = 1500
                
                db.session.commit()
            
            # Get standard house price
            standard_house_price = boardwalk.house_price
            
            # Attempt to build house
            response = client.post(f'/api/games/{game_id}/players/{player.id}/build_house', json={
                'property_id': 39
            })
            assert response.status_code == 200
            
            # Verify house was built and correct price was paid
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['houses'] == 1
            
            # Verify player paid full price
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            # Full price with no discount
            assert player_data['player']['money'] == 1500 - standard_house_price
    
    def test_classic_mode_jail_mechanics(self, app, db, client, test_game_classic, test_players):
        """Test standard jail mechanics in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Send player to jail
            with db.session.begin():
                player.position = 10  # Jail position
                player.in_jail = True
                player.jail_turns = 3  # Standard jail turns
                player.money = 1500  # Reset money
                db.session.commit()
            
            # Attempt to pay bail
            response = client.post(f'/api/games/{game_id}/players/{player.id}/pay_bail', json={})
            assert response.status_code == 200
            
            # Verify player was released and paid standard bail
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['player']['in_jail'] is False
            
            # Standard bail is $50
            assert data['player']['money'] == 1500 - 50
    
    def test_classic_mode_jail_dice_roll(self, app, db, client, test_game_classic, test_players):
        """Test jail mechanics with dice roll in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Send player to jail
            with db.session.begin():
                player.position = 10  # Jail position
                player.in_jail = True
                player.jail_turns = 3  # Standard jail turns
                player.money = 1500  # Reset money
                db.session.commit()
            
            # Roll doubles to get out of jail
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 16,  # Some position after Jail
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                    'dice_roll': [3, 3]  # Doubles
                })
                assert response.status_code == 200
            
            # Verify player was released without paying
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['player']['in_jail'] is False
            
            # Money unchanged (no bail paid)
            assert data['player']['money'] == 1500
    
    def test_classic_mode_property_auction(self, app, db, client, test_game_classic, test_players):
        """Test property auction in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set initial money
            with db.session.begin():
                player1.money = 1500
                player2.money = 1500
                db.session.commit()
            
            # Land on an unowned property but decline to buy
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 1,  # Mediterranean Avenue
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player1.id}/move', json={
                    'dice_roll': [1, 0]
                })
                assert response.status_code == 200
            
            # Decline to buy the property
            response = client.post(f'/api/games/{game_id}/players/{player1.id}/decline_purchase', json={
                'property_id': 1
            })
            assert response.status_code == 200
            
            # Verify auction was initiated
            data = json.loads(response.data)
            assert data['auction_initiated'] is True
            auction_id = data['auction_id']
            
            # Player2 bids on the property
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player2.id,
                'amount': 60  # Bid for Mediterranean
            })
            assert response.status_code == 200
            
            # End the auction
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/end', json={})
            assert response.status_code == 200
            
            # Verify player2 won the auction
            response = client.get(f'/api/games/{game_id}/properties/1')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['owner_id'] == player2.id
            
            # Verify player2 paid bid amount
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['money'] == 1500 - 60
    
    def test_classic_mode_mortgage_handling(self, app, db, client, test_game_classic, test_players):
        """Test standard mortgage handling in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Give player a property
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                
                # Reset money to starting amount
                player.money = 1500
                
                db.session.commit()
            
            # Get standard mortgage value
            standard_mortgage_value = boardwalk.mortgage_value
            
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
            
            # Verify player received standard mortgage value
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['money'] == 1500 + standard_mortgage_value
    
    def test_classic_mode_unmortgage_handling(self, app, db, client, test_game_classic, test_players):
        """Test unmortgage handling with interest in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player = test_players[0]
            
            # Give player a mortgaged property
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                boardwalk.is_mortgaged = True
                
                # Give enough money to unmortgage
                player.money = 1500
                
                db.session.commit()
            
            # Get mortgage value to calculate unmortgage cost
            mortgage_value = boardwalk.mortgage_value
            unmortgage_cost = int(mortgage_value * 1.1)  # 10% interest
            
            # Unmortgage the property
            response = client.post(f'/api/games/{game_id}/players/{player.id}/unmortgage_property', json={
                'property_id': 39
            })
            assert response.status_code == 200
            
            # Verify property was unmortgaged
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['is_mortgaged'] is False
            
            # Verify player paid cost with interest
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['money'] == 1500 - unmortgage_cost
    
    def test_classic_mode_rent_calculation(self, app, db, client, test_game_classic, test_players):
        """Test standard rent calculation in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player1 = test_players[0]  # Owner
            player2 = test_players[1]  # Renter
            
            # Give player1 a property and reset money
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player1.id
                
                player1.money = 1500
                player2.money = 1500
                
                db.session.commit()
            
            # Standard rent for Boardwalk
            standard_rent = boardwalk.rent
            
            # Have player2 land on player1's property
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                    'dice_roll': [6, 6]
                })
                assert response.status_code == 200
            
            # Verify player2 paid rent to player1
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            owner_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            renter_data = json.loads(response.data)
            
            # Owner receives rent
            assert owner_data['player']['money'] == 1500 + standard_rent
            # Renter pays rent
            assert renter_data['player']['money'] == 1500 - standard_rent
    
    def test_classic_mode_bankruptcy_auction(self, app, db, client, test_game_classic, test_players):
        """Test bankruptcy with property auctions in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player1 = test_players[0]  # Will go bankrupt
            player2 = test_players[1]  # Creditor
            player3 = test_players[2]  # Will participate in auction
            
            # Set up properties and money situation
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player1.id
                
                player1.money = 100  # Very low on money
                player2.money = 1500
                player3.money = 1500
                
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
            
            # In Classic mode, properties should go to auction
            data = json.loads(response.data)
            assert data['auctions_initiated'] is True
            auction_id = data['auction_ids'][0]  # Auction for Boardwalk
            
            # Player3 bids on the property
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player3.id,
                'amount': 300  # Bid for Boardwalk
            })
            assert response.status_code == 200
            
            # End the auction
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/end', json={})
            assert response.status_code == 200
            
            # Verify player3 won the auction
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            
            assert property_data['property']['owner_id'] == player3.id
            
            # Verify player1 is bankrupt
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            player_data = json.loads(response.data)
            
            assert player_data['player']['status'] == 'bankrupt'
            
            # Verify auction proceeds went to the creditor
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            creditor_data = json.loads(response.data)
            
            # Original money + player1's cash + auction proceeds
            assert creditor_data['player']['money'] == 1500 + 100 + 300
    
    def test_classic_mode_win_condition(self, app, db, client, test_game_classic, test_players):
        """Test win condition in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
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
            assert game_data['game']['end_reason'] == 'last_player_standing'
    
    def test_classic_mode_utility_rent(self, app, db, client, test_game_classic, test_players):
        """Test utility rent calculation in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player1 = test_players[0]  # Owner
            player2 = test_players[1]  # Renter
            
            # Give player1 utilities and reset money
            with db.session.begin():
                from src.models import Property
                electric_company = Property.query.filter_by(game_id=game_id, position=12).first()
                water_works = Property.query.filter_by(game_id=game_id, position=28).first()
                
                electric_company.owner_id = player1.id
                
                player1.money = 1500
                player2.money = 1500
                
                db.session.commit()
            
            # Have player2 land on Electric Company
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 12,  # Electric Company
                    'passed_go': False
                }
                
                dice_roll = [4, 5]  # Total 9
                response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                    'dice_roll': dice_roll
                })
                assert response.status_code == 200
            
            # Verify player2 paid correct utility rent to player1
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            owner_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            renter_data = json.loads(response.data)
            
            # With only one utility, rent is 4x dice roll
            expected_rent = 4 * sum(dice_roll)
            
            # Owner receives rent
            assert owner_data['player']['money'] == 1500 + expected_rent
            # Renter pays rent
            assert renter_data['player']['money'] == 1500 - expected_rent
            
            # Now give player1 the second utility
            with db.session.begin():
                water_works.owner_id = player1.id
                # Reset money
                player1.money = 1500
                player2.money = 1500
                db.session.commit()
            
            # Have player2 land on Water Works
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 28,  # Water Works
                    'passed_go': False
                }
                
                dice_roll = [3, 4]  # Total 7
                response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                    'dice_roll': dice_roll
                })
                assert response.status_code == 200
            
            # Verify player2 paid correct utility rent to player1
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            owner_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            renter_data = json.loads(response.data)
            
            # With both utilities, rent is 10x dice roll
            expected_rent = 10 * sum(dice_roll)
            
            # Owner receives rent
            assert owner_data['player']['money'] == 1500 + expected_rent
            # Renter pays rent
            assert renter_data['player']['money'] == 1500 - expected_rent
    
    def test_classic_mode_railroad_rent(self, app, db, client, test_game_classic, test_players):
        """Test railroad rent calculation in Classic mode"""
        with app.app_context():
            game_id = test_game_classic.id
            player1 = test_players[0]  # Owner
            player2 = test_players[1]  # Renter
            
            # Give player1 one railroad and reset money
            with db.session.begin():
                from src.models import Property
                reading_rr = Property.query.filter_by(game_id=game_id, position=5).first()
                pennsylvania_rr = Property.query.filter_by(game_id=game_id, position=15).first()
                b_and_o_rr = Property.query.filter_by(game_id=game_id, position=25).first()
                short_line_rr = Property.query.filter_by(game_id=game_id, position=35).first()
                
                reading_rr.owner_id = player1.id
                
                player1.money = 1500
                player2.money = 1500
                
                db.session.commit()
            
            # Have player2 land on Reading Railroad
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 5,  # Reading Railroad
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                    'dice_roll': [2, 3]
                })
                assert response.status_code == 200
            
            # Verify player2 paid correct railroad rent to player1
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            owner_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            renter_data = json.loads(response.data)
            
            # With 1 railroad, rent is $25
            expected_rent = 25
            
            # Owner receives rent
            assert owner_data['player']['money'] == 1500 + expected_rent
            # Renter pays rent
            assert renter_data['player']['money'] == 1500 - expected_rent
            
            # Give player1 more railroads and test again
            railroad_counts = [2, 3, 4]
            railroads = [pennsylvania_rr, b_and_o_rr, short_line_rr]
            expected_rents = [50, 100, 200]
            
            for i in range(len(railroad_counts)):
                # Give player an additional railroad
                with db.session.begin():
                    railroads[i].owner_id = player1.id
                    # Reset money
                    player1.money = 1500
                    player2.money = 1500
                    db.session.commit()
                
                # Have player2 land on Reading Railroad again
                with patch('src.game.game_logic.determine_landed_position') as mock_position:
                    mock_position.return_value = {
                        'position': 5,  # Reading Railroad
                        'passed_go': False
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                        'dice_roll': [2, 3]
                    })
                    assert response.status_code == 200
                
                # Verify player2 paid correct railroad rent to player1
                response = client.get(f'/api/games/{game_id}/players/{player1.id}')
                assert response.status_code == 200
                owner_data = json.loads(response.data)
                
                response = client.get(f'/api/games/{game_id}/players/{player2.id}')
                assert response.status_code == 200
                renter_data = json.loads(response.data)
                
                # Owner receives rent
                assert owner_data['player']['money'] == 1500 + expected_rents[i]
                # Renter pays rent
                assert renter_data['player']['money'] == 1500 - expected_rents[i] 