import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.routes.admin.auction_admin_routes import auction_admin_bp


class TestAuctionAdminRoutes:
    """Test cases for the Auction Admin Routes"""

    @pytest.fixture
    def app(self):
        """Create a Flask test app with the auction admin blueprint"""
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(auction_admin_bp, url_prefix='/api/admin/auctions')
        app.config['TESTING'] = True
        
        # Mock the admin_required decorator
        def mock_admin_required(f):
            return f
            
        import src.routes.admin.auction_admin_routes as routes
        routes.admin_required = mock_admin_required
        
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the app"""
        return app.test_client()

    @pytest.fixture
    def mock_auction_controller(self):
        """Create a mock auction controller"""
        mock_controller = MagicMock()
        return mock_controller

    def test_get_auction_analytics(self, app, client, mock_auction_controller):
        """Test the GET /auction/analytics endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.get_auction_analytics.return_value = {
                "success": True,
                "message": "Auction analytics retrieved successfully",
                "data": {
                    "total_auctions": 10,
                    "successful_auctions": 8,
                    "failed_auctions": 2
                }
            }
            
            # Make the request
            response = client.get('/api/admin/auctions/auction/analytics?game_id=game123')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert "data" in data
            assert data["data"]["total_auctions"] == 10
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.get_auction_analytics.assert_called_once_with(
                game_id='game123',
                start_date=None,
                end_date=None
            )

    def test_get_auction_analytics_missing_game_id(self, app, client, mock_auction_controller):
        """Test the GET /auction/analytics endpoint with missing game_id"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Make the request without game_id
            response = client.get('/api/admin/auctions/auction/analytics')
            
            # Verify the response
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] == False
            assert "Missing required parameter: game_id" in data["message"]
            
            # Verify the controller was not called
            mock_auction_controller.get_auction_analytics.assert_not_called()

    def test_get_property_auction_history(self, app, client, mock_auction_controller):
        """Test the GET /auction/property-history/:property_id endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.get_property_auction_history.return_value = {
                "success": True,
                "message": "Property auction history retrieved successfully",
                "property": {
                    "id": 123,
                    "name": "Boardwalk"
                },
                "history": [
                    {
                        "id": "auction1",
                        "starting_price": 100,
                        "final_price": 150,
                        "winner": {
                            "id": "player1",
                            "name": "Player 1"
                        }
                    }
                ]
            }
            
            # Make the request
            response = client.get('/api/admin/auctions/auction/property-history/123')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert "property" in data
            assert "history" in data
            assert data["property"]["id"] == 123
            assert len(data["history"]) == 1
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.get_property_auction_history.assert_called_once_with(
                property_id=123
            )

    def test_get_active_auctions(self, app, client, mock_auction_controller):
        """Test the GET /active-auctions/:game_id endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.get_active_auctions.return_value = {
                "success": True,
                "auctions": [
                    {
                        "id": "auction1",
                        "property_id": 123,
                        "property_name": "Boardwalk",
                        "current_bid": 150
                    }
                ]
            }
            
            # Make the request
            response = client.get('/api/admin/auctions/active-auctions/game123')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "auctions" in data
            assert len(data["auctions"]) == 1
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.get_active_auctions.assert_called_once_with(
                game_id='game123'
            )

    def test_cancel_auction(self, app, client, mock_auction_controller):
        """Test the POST /cancel-auction/:auction_id endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.cancel_auction.return_value = {
                "success": True,
                "message": "Auction cancelled successfully"
            }
            
            # Make the request
            response = client.post('/api/admin/auctions/cancel-auction/auction123?reason=Test%20cancellation')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.cancel_auction.assert_called_once_with(
                auction_id='auction123',
                reason='Test cancellation'
            )

    def test_cleanup_stale_auctions(self, app, client, mock_auction_controller):
        """Test the POST /cleanup-stale-auctions endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.cleanup_stale_auctions.return_value = {
                "success": True,
                "message": "Stale auctions cleaned up successfully",
                "auctions_cleaned": 2
            }
            
            # Make the request
            response = client.post('/api/admin/auctions/cleanup-stale-auctions?hours_old=48')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert "auctions_cleaned" in data
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.cleanup_stale_auctions.assert_called_once_with(
                hours_old=48
            )

    def test_start_sequential_auctions(self, app, client, mock_auction_controller):
        """Test the POST /start-sequential-auctions endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.start_sequential_auctions.return_value = {
                "success": True,
                "message": "Sequential auctions started successfully",
                "first_auction_id": "auction1"
            }
            
            # Prepare request data
            data = {
                "game_id": "game123",
                "property_ids": [123, 124, 125],
                "starting_bids": [100, 150, 200],
                "duration": 180,
                "reason": "Test sequential auctions"
            }
            
            # Make the request
            response = client.post(
                '/api/admin/auctions/start-sequential-auctions',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify the response
            assert response.status_code == 200
            resp_data = json.loads(response.data)
            assert resp_data["success"] == True
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.start_sequential_auctions.assert_called_once_with(
                game_id="game123",
                property_ids=[123, 124, 125],
                starting_bids=[100, 150, 200],
                duration=180,
                reason="Test sequential auctions"
            )

    def test_get_auction_schedule(self, app, client, mock_auction_controller):
        """Test the GET /auction-schedule/:game_id endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.get_auction_schedule.return_value = {
                "success": True,
                "message": "Auction schedule retrieved successfully",
                "schedule": {
                    "sequential_auctions_active": True,
                    "current_auction": {
                        "id": "auction1",
                        "property_id": 123,
                        "property_name": "Boardwalk"
                    },
                    "remaining_properties": [
                        {"id": 124, "name": "Park Place"}
                    ],
                    "completed_auctions": []
                }
            }
            
            # Make the request
            response = client.get('/api/admin/auctions/auction-schedule/game123')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] == True
            assert "schedule" in data
            assert data["schedule"]["sequential_auctions_active"] == True
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.get_auction_schedule.assert_called_once_with(
                game_id='game123'
            )

    def test_process_bot_bid(self, app, client, mock_auction_controller):
        """Test the POST /process-bot-bid endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.process_bot_bid.return_value = {
                "success": True,
                "message": "Bot bid processed successfully",
                "bid_amount": 120
            }
            
            # Prepare request data
            data = {
                "auction_id": "auction123",
                "bot_id": "bot456",
                "strategy": "aggressive"
            }
            
            # Make the request
            response = client.post(
                '/api/admin/auctions/process-bot-bid',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify the response
            assert response.status_code == 200
            resp_data = json.loads(response.data)
            assert resp_data["success"] == True
            assert "bid_amount" in resp_data
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.process_bot_bid.assert_called_once_with(
                auction_id="auction123",
                bot_id="bot456",
                bot_strategy="aggressive"
            )

    def test_batch_end_auctions(self, app, client, mock_auction_controller):
        """Test the POST /batch-end-auctions endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.batch_end_auctions.return_value = {
                "success": True,
                "message": "Batch end auctions completed",
                "results": {
                    "completed": 2,
                    "failed": 0,
                    "not_found": 0
                }
            }
            
            # Prepare request data
            data = {
                "auction_ids": ["auction1", "auction2"],
                "reason": "Test batch end"
            }
            
            # Make the request
            response = client.post(
                '/api/admin/auctions/batch-end-auctions',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify the response
            assert response.status_code == 200
            resp_data = json.loads(response.data)
            assert resp_data["success"] == True
            assert "results" in resp_data
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.batch_end_auctions.assert_called_once_with(
                auction_ids=["auction1", "auction2"],
                reason="Test batch end"
            )
            
    def test_process_multiple_bot_bids(self, app, client, mock_auction_controller):
        """Test the POST /process-multiple-bot-bids endpoint"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Setup mock return value
            mock_auction_controller.process_multiple_bot_bids.return_value = {
                "success": True,
                "message": "2 bot bids successfully processed",
                "bids": [
                    {
                        "bot_id": "bot1",
                        "success": True,
                        "message": "Bid placed successfully",
                        "bid_amount": 120
                    },
                    {
                        "bot_id": "bot2",
                        "success": True,
                        "message": "Bid placed successfully",
                        "bid_amount": 130
                    }
                ]
            }
            
            # Prepare request data
            data = {
                "auction_id": "auction123",
                "bot_ids": ["bot1", "bot2"],
                "strategies": {
                    "bot1": "aggressive",
                    "bot2": "conservative"
                }
            }
            
            # Make the request
            response = client.post(
                '/api/admin/auctions/process-multiple-bot-bids',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify the response
            assert response.status_code == 200
            resp_data = json.loads(response.data)
            assert resp_data["success"] == True
            assert "bids" in resp_data
            assert len(resp_data["bids"]) == 2
            
            # Verify the controller was called with correct parameters
            mock_auction_controller.process_multiple_bot_bids.assert_called_once_with(
                auction_id="auction123",
                bot_ids=["bot1", "bot2"],
                strategies={
                    "bot1": "aggressive",
                    "bot2": "conservative"
                }
            )
            
    def test_process_multiple_bot_bids_missing_auction_id(self, app, client, mock_auction_controller):
        """Test the POST /process-multiple-bot-bids endpoint with missing auction_id"""
        # Mock the auction controller in the app context
        with app.app_context():
            app.auction_controller = mock_auction_controller
            
            # Prepare request data
            data = {
                "bot_ids": ["bot1", "bot2"]
            }
            
            # Make the request
            response = client.post(
                '/api/admin/auctions/process-multiple-bot-bids',
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify the response
            assert response.status_code == 400
            resp_data = json.loads(response.data)
            assert resp_data["success"] == False
            assert "Missing required parameter: auction_id" in resp_data["message"]
            
            # Verify the controller was not called
            mock_auction_controller.process_multiple_bot_bids.assert_not_called()

    def test_export_auction_data(self, client, mock_auction_controller):
        """Test exporting auction data to CSV."""
        # Mock the export_auction_data method
        mock_auction_controller.export_auction_data.return_value = {
            "success": True,
            "message": "Successfully exported 2 auctions.",
            "data": "auction_id,property_id,start_time,end_time,starting_price,final_price\n1,5,2023-10-01 10:00:00,2023-10-01 10:30:00,500,750\n2,8,2023-10-02 11:00:00,2023-10-02 11:45:00,600,900",
            "column_names": ["auction_id", "property_id", "start_time", "end_time", "starting_price", "final_price"],
            "count": 2
        }
        
        # Make a GET request to the endpoint
        response = client.get('/export-auction-data?game_id=1&start_date=2023-10-01&end_date=2023-10-05')
        
        # Check response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert "Successfully exported 2 auctions" in response_data["message"]
        assert "auction_id,property_id" in response_data["data"]
        assert response_data["count"] == 2
        assert "column_names" in response_data
        
        # Verify the controller method was called with correct params
        mock_auction_controller.export_auction_data.assert_called_once_with(
            game_id="1", 
            start_date="2023-10-01", 
            end_date="2023-10-05",
            format="csv"
        )

    def test_export_auction_data_as_download(self, client, mock_auction_controller):
        """Test exporting auction data as a downloadable file."""
        # Mock the export_auction_data method
        mock_auction_controller.export_auction_data.return_value = {
            "success": True,
            "message": "Successfully exported 2 auctions.",
            "data": "auction_id,property_id,start_time,end_time,starting_price,final_price\n1,5,2023-10-01 10:00:00,2023-10-01 10:30:00,500,750\n2,8,2023-10-02 11:00:00,2023-10-02 11:45:00,600,900",
            "column_names": ["auction_id", "property_id", "start_time", "end_time", "starting_price", "final_price"],
            "count": 2
        }
        
        # Make a GET request to the endpoint with download=true
        response = client.get('/export-auction-data?game_id=1&download=true')
        
        # Check response
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'attachment; filename="auction_data_game_1.csv"' in response.headers['Content-Disposition']
        assert b"auction_id,property_id" in response.data
        
        # Verify the controller method was called with correct params
        mock_auction_controller.export_auction_data.assert_called_once_with(
            game_id="1", 
            start_date=None, 
            end_date=None,
            format="csv"
        ) 