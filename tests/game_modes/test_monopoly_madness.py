import pytest
import json
from unittest.mock import patch, Mock

class TestMonopolyMadnessMode:
    """Tests for the Monopoly Madness game mode"""
    
    def test_madness_mode_initialization(self, app, db, client):
        """Test a game can be initialized with Monopoly Madness mode"""
        with app.app_context():
            # Create a new game with Monopoly Madness mode
            response = client.post('/api/games', json={
                'name': 'Test Madness Game',
                'mode': 'madness',
                'max_players': 4
            })
            
            assert response.status_code == 201
            data = json.loads(response.data)
            game_id = data['game_id']
            
            # Get game details to verify mode settings
            response = client.get(f'/api/games/{game_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify Monopoly Madness mode settings
            assert data['game']['mode'] == 'madness'
            assert data['game']['random_events_enabled'] is True
            assert data['game']['property_effect_cards'] is True
            assert data['game']['disaster_cards'] is True
    
    def test_madness_mode_starting_money(self, app, db, client, test_game_madness, test_players):
        """Test players start with correct amount of money in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player_id = test_players[0].id
            
            # Check player's money
            response = client.get(f'/api/games/{game_id}/players/{player_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Madness mode players start with $2000 (classic amount)
            assert data['player']['money'] == 2000
    
    def test_madness_mode_random_events(self, app, db, client, test_game_madness, test_players):
        """Test random events are triggered in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Patch the random event generator to ensure a specific event
            with patch('src.game.random_events.generate_random_event') as mock_event:
                mock_event.return_value = {
                    'event_type': 'money_bonus',
                    'amount': 500,
                    'message': 'You found $500 on the street!'
                }
                
                # End player's turn (which triggers random event check)
                response = client.post(f'/api/games/{game_id}/players/{player.id}/end_turn', json={})
                assert response.status_code == 200
                
                # Verify player received the bonus
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Starting money + bonus
                assert data['player']['money'] == 2000 + 500
                
                # Verify event was logged in game history
                response = client.get(f'/api/games/{game_id}/history')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Find the random event entry in the history
                found_event = False
                for entry in data['history']:
                    if 'random_event' in entry and 'money_bonus' in entry['random_event']:
                        found_event = True
                        break
                
                assert found_event is True
    
    def test_madness_mode_property_effects(self, app, db, client, test_game_madness, test_players):
        """Test property effect cards in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Set up a property for the player
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                boardwalk.owner_id = player.id
                db.session.commit()
            
            # Patch the property effect generator
            with patch('src.game.property_effects.apply_property_effect') as mock_effect:
                mock_effect.return_value = {
                    'effect_type': 'rent_boost',
                    'property_id': 39,
                    'multiplier': 2,
                    'duration': 3,
                    'message': 'Boardwalk rent is doubled for 3 turns!'
                }
                
                # Draw a property effect card
                response = client.post(f'/api/games/{game_id}/players/{player.id}/draw_property_card', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['effect']['effect_type'] == 'rent_boost'
                assert data['effect']['property_id'] == 39
                
                # Verify property has the effect applied
                response = client.get(f'/api/games/{game_id}/properties/39')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['property']['active_effects'] is not None
                assert 'rent_boost' in str(data['property']['active_effects'])
                assert data['property']['rent_multiplier'] == 2
    
    def test_madness_mode_disaster_cards(self, app, db, client, test_game_madness, test_players):
        """Test disaster cards in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Set up properties
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player.id
                park_place.owner_id = player.id
                boardwalk.houses = 3
                park_place.houses = 2
                
                db.session.commit()
            
            # Patch the disaster effect generator
            with patch('src.game.disasters.apply_disaster') as mock_disaster:
                mock_disaster.return_value = {
                    'disaster_type': 'hurricane',
                    'affected_properties': [37, 39],
                    'damage': 'houses',
                    'message': 'A hurricane damaged houses on your properties!'
                }
                
                # Draw a disaster card
                response = client.post(f'/api/games/{game_id}/players/{player.id}/draw_disaster_card', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['disaster']['disaster_type'] == 'hurricane'
                
                # Verify properties were damaged
                response = client.get(f'/api/games/{game_id}/properties/39')
                assert response.status_code == 200
                boardwalk_data = json.loads(response.data)
                
                response = client.get(f'/api/games/{game_id}/properties/37')
                assert response.status_code == 200
                park_place_data = json.loads(response.data)
                
                # Houses should be damaged (reduced)
                assert boardwalk_data['property']['houses'] < 3
                assert park_place_data['property']['houses'] < 2
    
    def test_madness_mode_property_trading(self, app, db, client, test_game_madness, test_players):
        """Test property trading in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set up properties
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player1.id
                park_place.owner_id = player2.id
                
                db.session.commit()
            
            # Create a trade
            response = client.post(f'/api/games/{game_id}/trades', json={
                'initiator_id': player1.id,
                'recipient_id': player2.id,
                'initiator_properties': [39],
                'recipient_properties': [37],
                'initiator_money': 0,
                'recipient_money': 0
            })
            assert response.status_code == 201
            data = json.loads(response.data)
            trade_id = data['trade_id']
            
            # Apply madness mode twist - random chance of trade modification
            with patch('src.game.trade_effects.apply_madness_trade_effect') as mock_trade:
                mock_trade.return_value = {
                    'effect_type': 'fee',
                    'fee_amount': 200,
                    'message': 'The trading authority charges a 10% fee!'
                }
                
                # Accept the trade which will apply the madness effect
                response = client.post(f'/api/games/{game_id}/trades/{trade_id}/accept', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert 'trade_effect' in data
                assert data['trade_effect']['fee_amount'] == 200
            
            # Verify properties were exchanged
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            boardwalk_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/properties/37')
            assert response.status_code == 200
            park_place_data = json.loads(response.data)
            
            assert boardwalk_data['property']['owner_id'] == player2.id
            assert park_place_data['property']['owner_id'] == player1.id
            
            # Verify the trade fee was applied
            response = client.get(f'/api/games/{game_id}/players/{player1.id}')
            assert response.status_code == 200
            player1_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/players/{player2.id}')
            assert response.status_code == 200
            player2_data = json.loads(response.data)
            
            # Both players should have paid the fee
            assert player1_data['player']['money'] == 2000 - 200
            assert player2_data['player']['money'] == 2000 - 200
    
    def test_madness_mode_bank_error(self, app, db, client, test_game_madness, test_players):
        """Test bank errors in Monopoly Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Patch the random event generator for a bank error
            with patch('src.game.random_events.generate_random_event') as mock_event:
                mock_event.return_value = {
                    'event_type': 'bank_error',
                    'amount': 300,
                    'in_favor': True,
                    'message': 'Bank error in your favor! Collect $300.'
                }
                
                # Pass GO which triggers random event check
                with patch('src.game.game_logic.determine_landed_position') as mock_position:
                    mock_position.return_value = {
                        'position': 0,  # GO
                        'passed_go': True
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                        'dice_roll': [6, 4]
                    })
                    assert response.status_code == 200
                
                # Verify player received the GO money plus bank error
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Starting money + GO money + bank error
                assert data['player']['money'] == 2000 + 200 + 300
    
    def test_madness_mode_property_purchase(self, app, db, client, test_game_madness, test_players):
        """Test property purchase with random price fluctuations in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Have player land on Boardwalk
            with patch('src.game.game_logic.determine_landed_position') as mock_position:
                mock_position.return_value = {
                    'position': 39,  # Boardwalk
                    'passed_go': False
                }
                
                # Patch the property price fluctuation
                with patch('src.game.property_effects.apply_price_fluctuation') as mock_price:
                    mock_price.return_value = {
                        'original_price': 400,
                        'new_price': 350,
                        'message': 'Property is on sale! 12.5% discount!'
                    }
                    
                    response = client.post(f'/api/games/{game_id}/players/{player.id}/move', json={
                        'dice_roll': [6, 4]
                    })
                    assert response.status_code == 200
                
                # Attempt to purchase the property
                response = client.post(f'/api/games/{game_id}/players/{player.id}/purchase', json={})
                assert response.status_code == 200
                
                # Verify property purchased
                response = client.get(f'/api/games/{game_id}/properties/39')
                assert response.status_code == 200
                property_data = json.loads(response.data)
                
                assert property_data['property']['owner_id'] == player.id
                
                # Verify player paid the fluctuated price
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                player_data = json.loads(response.data)
                
                assert player_data['player']['money'] == 2000 - 350
    
    def test_madness_mode_jail_escape(self, app, db, client, test_game_madness, test_players):
        """Test unique jail escape mechanics in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Send player to jail
            with db.session.begin():
                player.position = 10  # Jail position
                player.in_jail = True
                player.jail_turns = 3
                db.session.commit()
            
            # Patch the jail escape chance
            with patch('src.game.jail_mechanics.attempt_jail_escape') as mock_escape:
                mock_escape.return_value = {
                    'success': True,
                    'method': 'bribery',
                    'cost': 100,
                    'message': 'You bribed the guard to let you out!'
                }
                
                # Try to escape jail
                response = client.post(f'/api/games/{game_id}/players/{player.id}/jail_escape', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['escape']['success'] is True
                assert data['escape']['method'] == 'bribery'
                
                # Verify player was released and paid the bribe
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                player_data = json.loads(response.data)
                
                assert player_data['player']['in_jail'] is False
                assert player_data['player']['money'] == 2000 - 100
    
    def test_madness_mode_property_improvements(self, app, db, client, test_game_madness, test_players):
        """Test property improvements with random effects in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Set up monopoly for the player
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player.id
                park_place.owner_id = player.id
                
                db.session.commit()
            
            # Patch the improvement effect
            with patch('src.game.property_effects.apply_improvement_effect') as mock_improve:
                mock_improve.return_value = {
                    'effect_type': 'construction_bonus',
                    'bonus_houses': 1,
                    'message': 'Construction boom! You get an extra house for free!'
                }
                
                # Attempt to improve a property
                response = client.post(f'/api/games/{game_id}/players/{player.id}/build_house', json={
                    'property_id': 39
                })
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert 'improvement_effect' in data
                assert data['improvement_effect']['bonus_houses'] == 1
                
                # Verify property got the bonus house
                response = client.get(f'/api/games/{game_id}/properties/39')
                assert response.status_code == 200
                property_data = json.loads(response.data)
                
                # Should have 2 houses (1 paid for + 1 bonus)
                assert property_data['property']['houses'] == 2
    
    def test_madness_mode_disaster_recovery(self, app, db, client, test_game_madness, test_players):
        """Test disaster recovery mechanics in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Set up properties with damage
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                park_place = Property.query.filter_by(game_id=game_id, position=37).first()
                
                boardwalk.owner_id = player.id
                park_place.owner_id = player.id
                
                # Add disaster effect to properties
                boardwalk.active_effects = {'disaster': 'flood', 'rent_reduction': 0.5}
                park_place.active_effects = {'disaster': 'flood', 'rent_reduction': 0.5}
                
                db.session.commit()
            
            # Attempt disaster recovery
            response = client.post(f'/api/games/{game_id}/players/{player.id}/disaster_recovery', json={
                'property_ids': [37, 39],
                'recovery_type': 'insurance'
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['recovery']['success'] is True
            assert data['recovery']['cost'] > 0
            
            # Verify properties are restored
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            boardwalk_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/properties/37')
            assert response.status_code == 200
            park_place_data = json.loads(response.data)
            
            # Disaster effects should be cleared
            assert 'disaster' not in str(boardwalk_data['property']['active_effects'])
            assert 'disaster' not in str(park_place_data['property']['active_effects'])
    
    def test_madness_mode_win_condition(self, app, db, client, test_game_madness, test_players):
        """Test wild win condition in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            winner = test_players[0]
            
            # Set winning condition for random selection
            with patch('src.game.madness_rules.select_random_win_condition') as mock_win:
                mock_win.return_value = {
                    'condition': 'most_improved_properties',
                    'winner_id': winner.id,
                    'message': 'The game ends by special decree! Player with most improved properties wins!'
                }
                
                # Trigger end game condition
                response = client.post(f'/api/games/{game_id}/check_win_condition', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['game_over'] is True
                assert data['win_condition']['condition'] == 'most_improved_properties'
                assert data['win_condition']['winner_id'] == winner.id
                
                # Verify game is completed
                response = client.get(f'/api/games/{game_id}')
                assert response.status_code == 200
                game_data = json.loads(response.data)
                
                assert game_data['game']['status'] == 'completed'
                assert game_data['game']['winner_id'] == winner.id
    
    def test_madness_mode_money_rain(self, app, db, client, test_game_madness, test_players):
        """Test the 'money rain' special event in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            
            # Record initial money for all players
            initial_money = {}
            for player in test_players:
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                initial_money[player.id] = data['player']['money']
            
            # Trigger money rain event
            with patch('src.game.random_events.trigger_special_event') as mock_event:
                mock_event.return_value = {
                    'event_type': 'money_rain',
                    'amount_per_player': 500,
                    'message': "It's raining money! Everyone gets $500!"
                }
                
                response = client.post(f'/api/games/{game_id}/trigger_special_event', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['event']['event_type'] == 'money_rain'
            
            # Verify all players received money
            for player in test_players:
                response = client.get(f'/api/games/{game_id}/players/{player.id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # Player should have gotten $500
                assert data['player']['money'] == initial_money[player.id] + 500
    
    def test_madness_mode_player_teleport(self, app, db, client, test_game_madness, test_players):
        """Test the teleport mechanic in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player = test_players[0]
            
            # Set initial position
            with db.session.begin():
                player.position = 5
                db.session.commit()
            
            # Trigger teleport random event
            with patch('src.game.random_events.generate_random_event') as mock_event:
                mock_event.return_value = {
                    'event_type': 'teleport',
                    'destination': 24,
                    'message': "You've been teleported to a random location!"
                }
                
                # End turn to trigger random event
                response = client.post(f'/api/games/{game_id}/players/{player.id}/end_turn', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert 'random_event' in data
                assert data['random_event']['event_type'] == 'teleport'
            
            # Verify player was teleported
            response = client.get(f'/api/games/{game_id}/players/{player.id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['player']['position'] == 24
    
    def test_madness_mode_property_swap(self, app, db, client, test_game_madness, test_players):
        """Test the property swap random event in Madness mode"""
        with app.app_context():
            game_id = test_game_madness.id
            player1 = test_players[0]
            player2 = test_players[1]
            
            # Set up properties
            with db.session.begin():
                from src.models import Property
                boardwalk = Property.query.filter_by(game_id=game_id, position=39).first()
                baltic_ave = Property.query.filter_by(game_id=game_id, position=3).first()
                
                boardwalk.owner_id = player1.id
                baltic_ave.owner_id = player2.id
                
                db.session.commit()
            
            # Trigger property swap event
            with patch('src.game.random_events.generate_random_event') as mock_event:
                mock_event.return_value = {
                    'event_type': 'property_swap',
                    'swap_properties': [
                        {'from_player_id': player1.id, 'property_id': 39},
                        {'from_player_id': player2.id, 'property_id': 3}
                    ],
                    'message': 'Properties have been randomly swapped!'
                }
                
                # End turn to trigger random event
                response = client.post(f'/api/games/{game_id}/players/{player1.id}/end_turn', json={})
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert 'random_event' in data
                assert data['random_event']['event_type'] == 'property_swap'
            
            # Verify properties were swapped
            response = client.get(f'/api/games/{game_id}/properties/39')
            assert response.status_code == 200
            boardwalk_data = json.loads(response.data)
            
            response = client.get(f'/api/games/{game_id}/properties/3')
            assert response.status_code == 200
            baltic_data = json.loads(response.data)
            
            assert boardwalk_data['property']['owner_id'] == player2.id
            assert baltic_data['property']['owner_id'] == player1.id 