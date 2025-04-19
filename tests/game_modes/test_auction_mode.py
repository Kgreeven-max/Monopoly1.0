import pytest
import json
from unittest.mock import patch

class TestAuctionMode:
    """Tests for the Auction game mode"""
    
    def test_auction_mode_initialization(self, app, db, client):
        """Test a game can be initialized with Auction mode"""
        with app.app_context():
            # Create a new game with Auction mode
            response = client.post('/api/games', json={
                'name': 'Test Auction Game',
                'mode': 'auction',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Get game details to verify mode settings
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify Auction mode settings
            assert data['game']['mode'] == 'auction'
            assert data['game']['all_properties_auction'] is True
            assert data['game']['auction_starting_money'] == 3000
    
    def test_auction_mode_property_handling(self, app, db, client, test_game_auction, test_player):
        """Test all properties go to auction instead of being landed on"""
        with app.app_context():
            game_id = test_game_auction.id
            player_id = test_player.id
            
            # Land on a property square
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 1,  # Mediterranean Avenue
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player_id}/move', json={
                    'dice_roll': [1, 0]
                })
                assert response.status_code == 200
            
            # In auction mode, landing on a property doesn't trigger purchase option
            # but instead the property should already be in the auction queue
            
            # Check if Mediterranean Avenue is still unowned
            response = client.get(f'/api/games/{game_id}/properties/1')
            data = json.loads(response.data)
            assert data['property']['owner_id'] is None
            
            # Get game state to see if auction is active or scheduled
            response = client.get(f'/api/games/{game_id}/status')
            data = json.loads(response.data)
            
            # Either an auction is active or property is in the auction queue
            assert ('auction' in data and data['auction'] is not None) or \
                   ('auction_queue' in data and len(data['auction_queue']) > 0)
    
    def test_auction_mode_start_auctions(self, app, db, client):
        """Test that all properties are put up for auction at game start"""
        with app.app_context():
            # Create a new auction game
            response = client.post('/api/games', json={
                'name': 'Auction Start Test',
                'mode': 'auction',
                'max_players': 3
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Add players to the game
            for i in range(3):
                response = client.post(f'/api/games/{game_id}/players', json={
                    'name': f'Player {i+1}'
                })
                assert response.status_code == 201
            
            # Start the game
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Check game status - auctions should be scheduled
            response = client.get(f'/api/games/{game_id}/status')
            data = json.loads(response.data)
            
            # There should be auctions scheduled for all properties
            assert 'auction_queue' in data
            # The auction queue should have many properties
            assert len(data['auction_queue']) > 20  # There are 28 properties in Monopoly
    
    def test_auction_mode_bid_on_property(self, app, db, client, test_game_auction, test_players):
        """Test bidding on properties in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Trigger or find an active auction
            # First check if there's an active auction
            response = client.get(f'/api/games/{game_id}/status')
            data = json.loads(response.data)
            
            if 'auction' not in data or data['auction'] is None:
                # Start a new auction
                response = client.post(f'/api/games/{game_id}/start_auction', json={
                    'property_id': 1  # Mediterranean Avenue
                })
                assert response.status_code == 200
            
            # Get the current auction status
            response = client.get(f'/api/games/{game_id}/auction')
            assert response.status_code == 200
            auction_data = json.loads(response.data)
            property_id = auction_data['auction']['property_id']
            
            # Player 1 places a bid
            response = client.post(f'/api/games/{game_id}/players/{player1.id}/bid', json={
                'amount': 100
            })
            assert response.status_code == 200
            
            # Player 2 places a higher bid
            response = client.post(f'/api/games/{game_id}/players/{player2.id}/bid', json={
                'amount': 150
            })
            assert response.status_code == 200
            
            # Check auction status - Player 2 should be the highest bidder
            response = client.get(f'/api/games/{game_id}/auction')
            assert response.status_code == 200
            auction_data = json.loads(response.data)
            assert auction_data['auction']['highest_bidder_id'] == player2.id
            assert auction_data['auction']['highest_bid'] == 150
            
            # End the auction (simulating all other players passing)
            for player in test_players:
                if player.id != player2.id:  # All players except highest bidder
                    response = client.post(f'/api/games/{game_id}/players/{player.id}/pass_bid', json={})
                    assert response.status_code == 200
            
            # Verify property ownership after auction ends
            response = client.get(f'/api/games/{game_id}/properties/{property_id}')
            property_data = json.loads(response.data)
            assert property_data['property']['owner_id'] == player2.id
    
    def test_auction_mode_starting_money(self, app, db, client, test_game_auction, test_players):
        """Test players start with correct amount of money in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player_id = test_players[0].id
            
            # Check player's money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Auction mode players start with $3000
            assert data['player']['money'] == 3000
    
    def test_auction_mode_house_auctions(self, app, db, client, test_game_auction, test_players):
        """Test houses are also auctioned in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player = test_players[0]
            
            # Give player a property group (Mocking property ownership directly in DB)
            with db.session.begin():
                # Get Baltic Avenue (ID 3) and Mediterranean Avenue (ID 1)
                from src.models import Property
                baltic = Property.query.filter_by(game_id=game_id, position=3).first()
                mediterranean = Property.query.filter_by(game_id=game_id, position=1).first()
                
                # Set owner for both properties to complete the property group
                baltic.owner_id = player.id
                mediterranean.owner_id = player.id
                db.session.commit()
            
            # Request to build a house in auction mode
            response = client.post(f'/api/games/{game_id}/players/{player.id}/request_house', json={
                'property_id': 3  # Baltic Avenue
            })
            assert response.status_code == 200
            
            # Check if house auction was created
            response = client.get(f'/api/games/{game_id}/house_auctions')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify house auction exists for Baltic Avenue
            house_auctions = data['house_auctions']
            assert any(auction['property_id'] == 3 for auction in house_auctions)
    
    def test_auction_mode_go_salary(self, app, db, client, test_game_auction, test_player):
        """Test players receive correct salary for passing GO in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player_id = test_player.id
            
            # Get initial player money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            initial_money = data['player']['money']
            
            # Simulate player passing GO
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                # Mock landing on position 5 (coming from position 39, passing GO)
                mock_position.return_value = {
                    'position': 5,
                    'passed_go': True
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player_id}/move', json={
                    'dice_roll': [2, 3]
                })
                assert response.status_code == 200
            
            # Get updated player money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            final_money = data['player']['money']
            
            # Auction mode gives $300 for passing GO (more than classic)
            assert final_money == initial_money + 300
    
    def test_auction_mode_victory_conditions(self, app, db, client, test_game_auction, test_players):
        """Test Auction mode victory conditions (most valuable assets after all properties sold)"""
        with app.app_context():
            game_id = test_game_auction.id
            players = test_players
            
            # Set up game state where all properties have been auctioned
            with db.session.begin():
                from src.models import Property, Game
                
                # Mark all auctions as complete
                game = Game.query.filter_by(id=game_id).first()
                game.all_auctions_complete = True
                
                # Give player 1 more valuable properties
                properties = Property.query.filter_by(game_id=game_id).all()
                
                # First half to player 1 (including most expensive)
                for i, prop in enumerate(properties):
                    if i < len(properties) // 2:
                        prop.owner_id = players[0].id
                    else:
                        prop.owner_id = players[1].id
                
                db.session.commit()
            
            # Trigger end game check
            response = client.post(f'/api/games/{game_id}/check_end_conditions', json={})
            assert response.status_code == 200
            
            # Check game status - should be ended with winner
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Game should be over
            assert data['game']['status'] == 'completed'
            
            # Player with most valuable assets should win (player 1)
            assert data['game']['winner_id'] == players[0].id
    
    def test_auction_mode_timed_auctions(self, app, db, client, test_game_auction, test_players):
        """Test auctions have time limits in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player = test_players[0]
            
            # Start an auction
            response = client.post(f'/api/games/{game_id}/start_auction', json={
                'property_id': 1  # Mediterranean Avenue
            })
            assert response.status_code == 200
            
            # Check auction details
            response = client.get(f'/api/games/{game_id}/auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify auction has a time limit
            assert 'time_remaining' in data['auction']
            assert data['auction']['time_remaining'] > 0
            assert 'end_time' in data['auction']  # Should have an end timestamp
    
    def test_auction_mode_asset_valuation(self, app, db, client, test_game_auction, test_players):
        """Test player assets are properly valued for victory conditions"""
        with app.app_context():
            game_id = test_game_auction.id
            player = test_players[0]
            
            # Give player some properties
            with db.session.begin():
                from src.models import Property
                
                # Give player Boardwalk (most expensive property)
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                
                # Add some houses to increase value
                boardwalk.houses = 3
                
                db.session.commit()
            
            # Get player asset valuation
            response = client.get(f'/api/games/{game_id}/players/{player.id}/assets')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify asset values are calculated
            assert 'total_value' in data
            assert data['total_value'] > 0
            
            # Value should include:
            # - Property value (Boardwalk = $400)
            # - Building value (3 houses on Boardwalk = 3 * $200 = $600)
            # - Cash on hand
            expected_min_value = 400 + 600 + player.money
            assert data['total_value'] >= expected_min_value

    def test_auction_mode_property_distribution(self, app, db, client, test_game_auction):
        """Test all properties are auctioned at game start in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            
            # Start the game
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Get game status
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify the game is in auction state
            assert data['game']['status'] == 'auction'
            
            # Check pending auctions
            response = client.get(f'/api/games/{game_id}/auctions')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should have 28 properties in auction queue (all purchasable properties)
            assert len(data['pending_auctions']) == 28
    
    def test_auction_mode_property_bidding(self, app, db, client, test_game_auction, test_players):
        """Test bidding on property auctions"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Start the game and trigger property auctions
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Get the current auction
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            auction_id = data['auction']['id']
            property_id = data['auction']['property_id']
            
            # Player 1 places bid
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player1.id,
                'amount': 100
            })
            assert response.status_code == 200
            
            # Player 2 places higher bid
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player2.id,
                'amount': 150
            })
            assert response.status_code == 200
            
            # Player 1 passes
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/pass', json={
                'player_id': player1.id
            })
            assert response.status_code == 200
            
            # Get auction result
            response = client.get(f'/api/games/{game_id}/auctions/{auction_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Player 2 should be winning the auction
            assert data['auction']['current_highest_bid'] == 150
            assert data['auction']['current_highest_bidder_id'] == player2.id
            
            # Auction should be closing since player 1 passed
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/finalize', json={})
            assert response.status_code == 200
            
            # Verify property ownership
            response = client.get(f'/api/games/{game_id}/properties/{property_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Property should now be owned by player 2
            assert data['property']['owner_id'] == player2.id
            
            # Check player 2's money after winning the auction
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Player should have paid the bid amount
            assert data['player']['money'] == 3000 - 150
    
    def test_auction_mode_all_players_pass(self, app, db, client, test_game_auction, test_players):
        """Test what happens when all players pass on an auction"""
        with app.app_context():
            game_id = test_game_auction.id
            
            # Start the game and trigger property auctions
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Get the current auction
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            auction_id = data['auction']['id']
            property_id = data['auction']['property_id']
            
            # All players pass
            for player in test_players:
                response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/pass', json={
                    'player_id': player.id
                })
                assert response.status_code == 200
            
            # Finalize the auction
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/finalize', json={})
            assert response.status_code == 200
            
            # Verify property status
            response = client.get(f'/api/games/{game_id}/properties/{property_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Property should still be unowned
            assert data['property']['owner_id'] is None
            
            # The game should move to the next auction
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            new_auction_data = json.loads(response.data)
            
            # Ensure we've moved to a different auction
            assert new_auction_data['auction']['id'] != auction_id
    
    def test_auction_mode_bidding_restrictions(self, app, db, client, test_game_auction, test_players):
        """Test bidding restrictions in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            
            # Modify player's money
            with db.session.begin():
                player1.money = 200
                db.session.commit()
            
            # Start the game and trigger property auctions
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Get the current auction
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            auction_id = data['auction']['id']
            
            # Player tries to bid more than they have
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player1.id,
                'amount': 300  # More than the player's 200
            })
            
            # Bid should be rejected
            assert response.status_code == 400
            
            # Player makes a valid bid
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player1.id,
                'amount': 150  # Less than player's 200
            })
            assert response.status_code == 200
            
            # Another player makes a too small bid
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': test_players[1].id,
                'amount': 140  # Less than current highest bid
            })
            assert response.status_code == 400
    
    def test_auction_mode_game_completion(self, app, db, client, test_game_auction, test_players):
        """Test game completion after all auctions are finished"""
        with app.app_context():
            game_id = test_game_auction.id
            
            # Start the game and trigger property auctions
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Fast-forward through all auctions
            for _ in range(28):  # 28 properties to auction
                # Get the current auction
                response = client.get(f'/api/games/{game_id}/current_auction')
                if response.status_code != 200:
                    break  # No more auctions
                    
                data = json.loads(response.data)
                auction_id = data['auction']['id']
                
                # Player 1 bids
                response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                    'player_id': test_players[0].id,
                    'amount': 100
                })
                
                # Other players pass
                for player in test_players[1:]:
                    response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/pass', json={
                        'player_id': player.id
                    })
                
                # Finalize the auction
                response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/finalize', json={})
            
            # Check game status
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Game should switch to active status after auctions
            assert data['game']['status'] == 'active'
            
            # First player should now own many properties
            response = client.get(f'/api/games/{game_id}/players/{test_players[0].id}/properties')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should own a substantial number of properties
            assert len(data['properties']) > 20
    
    def test_auction_mode_post_auction_gameplay(self, app, db, client, test_game_auction, test_players):
        """Test gameplay after initial auctions are completed"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set game to active state after auctions
            with db.session.begin():
                test_game_auction.status = 'active'
                
                # Distribute some properties
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                boardwalk.owner_id = player1.id
                park_place.owner_id = player1.id
                
                # Give players their starting money
                player1.money = 3000 - 1000  # Spent 1000 on properties
                player2.money = 3000
                
                db.session.commit()
            
            # Player 2 lands on Boardwalk
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player2.id}/move', json={
                    'dice_roll': [6, 4]
                })
                assert response.status_code == 200
            
            # Verify rent was paid
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            player1_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            player2_data = json.loads(response.data)
            
            # Player 1 should have received Boardwalk rent
            assert player1_data['player']['money'] > 2000
            # Player 2 should have paid Boardwalk rent
            assert player2_data['player']['money'] < 3000
    
    def test_auction_mode_secondary_auctions(self, app, db, client, test_game_auction, test_players):
        """Test secondary auctions when a player declines to buy a property"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set game to active state after initial auctions
            with db.session.begin():
                test_game_auction.status = 'active'
                player1.money = 3000
                player2.money = 3000
                db.session.commit()
            
            # Player 1 lands on an unowned property (Boardwalk)
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{player1.id}/move', json={
                    'dice_roll': [6, 4]
                })
                assert response.status_code == 200
            
            # Player declines to purchase
            response = client.post(f'/api/games/{game_id}/players/{player1.id}/decline_purchase', json={})
            assert response.status_code == 200
            
            # Verify a secondary auction was created
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Ensure it's an auction for Boardwalk
            assert data['auction']['property_id'] == 39
            
            # Player 2 bids
            auction_id = data['auction']['id']
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player2.id,
                'amount': 350
            })
            assert response.status_code == 200
            
            # Player 1 passes
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/pass', json={
                'player_id': player1.id
            })
            assert response.status_code == 200
            
            # Finalize the auction
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/finalize', json={})
            assert response.status_code == 200
            
            # Verify property ownership
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Property should be owned by player 2
            assert data['property']['owner_id'] == player2.id
            
            # Verify player 2's money was deducted
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['player']['money'] == 3000 - 350
    
    def test_auction_mode_trading(self, app, db, client, test_game_auction, test_players):
        """Test property trading in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set up properties
            with db.session.begin():
                test_game_auction.status = 'active'
                
                from src.models import Property
                # Give player1 Boardwalk
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player1.id
                
                # Give player2 Park Place
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                park_place.owner_id = player2.id
                
                db.session.commit()
            
            # Player 1 offers trade
            response = client.post(f'/api/games/{game_id}/trades', json={
                'initiator_id': player1.id,
                'recipient_id': player2.id,
                'initiator_properties': [39],
                'recipient_properties': [37],
                'initiator_money': 200,
                'recipient_money': 0
            })
            assert response.status_code == 201
            data = json.loads(response.data)
            trade_id = data['trade_id']
            
            # Player 2 accepts trade
            response = client.post(f'/api/games/{game_id}/trades/{trade_id}/accept', json={})
            assert response.status_code == 200
            
            # Verify property ownership changed
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['property']['owner_id'] == player2.id
            
            response = client.get(f'/api/games/{game_id}/properties/37')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['property']['owner_id'] == player1.id
            
            # Verify money was exchanged
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            player1_money = data['player']['money']
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            player2_money = data['player']['money']
            
            # Player 1 should have 200 less, Player 2 should have 200 more
            assert player2_money - player1_money == 400  # 200 + 200 difference
    
    def test_auction_mode_bankruptcy(self, app, db, client, test_game_auction, test_players):
        """Test bankruptcy handling in Auction mode"""
        with app.app_context():
            game_id = test_game_auction.id
            debtor = test_players[0]
            creditor = test_players[1]
            
            # Set up bankruptcy scenario
            with db.session.begin():
                test_game_auction.status = 'active'
                
                # Give creditor a high-rent property
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = creditor.id
                boardwalk.houses = 4
                
                # Give debtor low money
                debtor.money = 50
                
                db.session.commit()
            
            # Debtor lands on high-rent property
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk with hotels
                    'passed_go': False
                }
                
                response = client.post(f'/api/games/{game_id}/players/{debtor.id}/move', json={
                    'dice_roll': [6, 4]
                })
                assert response.status_code == 200
            
            # Verify bankruptcy occurred
            response = client.get(f'/api/games/{game_id}/players/{debtor.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['player']['status'] == 'bankrupt'
            
            # Check if creditor received the debtor's assets
            response = client.get(f'/api/games/{game_id}/players/{creditor.id}')
            assert response.status_code == 200
            creditor_data = json.loads(response.data)
            
            # Creditor should have received debtor's money
            assert creditor_data['player']['money'] > 3000
    
    def test_auction_mode_max_bid_rule(self, app, db, client, test_game_auction, test_players):
        """Test the max bid rule in Auction mode (can't bid more than property value)"""
        with app.app_context():
            game_id = test_game_auction.id
            player1 = test_players[0]
            
            # Start the game and trigger property auctions
            response = client.post(f'/api/games/{game_id}/start', json={})
            assert response.status_code == 200
            
            # Get the current auction
            response = client.get(f'/api/games/{game_id}/current_auction')
            assert response.status_code == 200
            data = json.loads(response.data)
            auction_id = data['auction']['id']
            property_id = data['auction']['property_id']
            
            # Get property details
            response = client.get(f'/api/games/{game_id}/properties/{property_id}')
            assert response.status_code == 200
            property_data = json.loads(response.data)
            property_value = property_data['property']['price']
            
            # Attempt to bid more than the property value
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player1.id,
                'amount': property_value * 2  # More than property value
            })
            
            # Should be rejected
            assert response.status_code == 400
            
            # Make a valid bid at exactly the property value
            response = client.post(f'/api/games/{game_id}/auctions/{auction_id}/bid', json={
                'player_id': player1.id,
                'amount': property_value
            })
            assert response.status_code == 200
    
    def test_auction_mode_win_condition(self, app, db, client, test_game_auction, test_players):
        """Test win condition in Auction mode (last player not bankrupt)"""
        with app.app_context():
            game_id = test_game_auction.id
            winner = test_players[0]
            
            # Bankrupt all players except one
            with db.session.begin():
                test_game_auction.status = 'active'
                
                for player in test_players[1:]:
                    player.status = 'bankrupt'
                
                db.session.commit()
            
            # Check game status
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Game should be completed with the last player as winner
            assert data['game']['status'] == 'completed'
            assert data['game']['winner_id'] == winner.id 