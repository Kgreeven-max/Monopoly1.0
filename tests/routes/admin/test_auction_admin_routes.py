import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, json
import io

from src.routes.admin.auction_admin_routes import auction_admin_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(auction_admin_bp, url_prefix='/admin')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('src.routes.admin.auction_admin_routes.admin_required')
@patch('src.routes.admin.auction_admin_routes.AuctionController')
def test_get_auction_analytics(mock_auction_controller, mock_admin_required, client):
    # Setup mock decorator
    mock_admin_required.return_value = lambda x: x
    
    # Setup mock controller
    mock_controller_instance = MagicMock()
    mock_auction_controller.return_value = mock_controller_instance
    mock_controller_instance.get_auction_analytics.return_value = {
        "success": True,
        "message": "Analytics retrieved successfully",
        "data": {
            "total_auctions": 10,
            "successful_auctions": 8,
            "average_price_increase": 15.5
        }
    }
    
    # Make request
    response = client.get('/admin/auction/analytics?game_id=123')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] == True
    assert "total_auctions" in data["data"]
    
    # Verify controller called with correct parameters
    mock_controller_instance.get_auction_analytics.assert_called_once_with("123", None, None)

@patch('src.routes.admin.auction_admin_routes.admin_required')
@patch('src.routes.admin.auction_admin_routes.AuctionController')
def test_get_property_auction_history(mock_auction_controller, mock_admin_required, client):
    # Setup mock decorator
    mock_admin_required.return_value = lambda x: x
    
    # Setup mock controller
    mock_controller_instance = MagicMock()
    mock_auction_controller.return_value = mock_controller_instance
    mock_controller_instance.get_property_auction_history.return_value = {
        "success": True,
        "message": "Property auction history retrieved",
        "data": {
            "property_id": 5,
            "property_name": "Boardwalk",
            "auctions": [
                {"date": "2023-05-01", "winning_bid": 500},
                {"date": "2023-06-15", "winning_bid": 650}
            ]
        }
    }
    
    # Make request
    response = client.get('/admin/auction/property-history/5')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] == True
    assert data["data"]["property_id"] == 5
    assert len(data["data"]["auctions"]) == 2
    
    # Verify controller called with correct parameters
    mock_controller_instance.get_property_auction_history.assert_called_once_with(5)

@patch('src.routes.admin.auction_admin_routes.admin_required')
@patch('src.routes.admin.auction_admin_routes.AuctionController')
def test_export_auction_data_json_format(mock_auction_controller, mock_admin_required, client):
    # Setup mock decorator
    mock_admin_required.return_value = lambda x: x
    
    # Setup mock controller
    mock_controller_instance = MagicMock()
    mock_auction_controller.return_value = mock_controller_instance
    csv_content = "id,game_id,property_id,start_time,end_time,starting_price,winning_bid\n1,123,5,2023-05-01,2023-05-01,200,500\n2,123,7,2023-06-15,2023-06-15,300,650\n"
    mock_controller_instance.export_auction_data.return_value = {
        "success": True,
        "message": "Auction data exported successfully",
        "data": csv_content
    }
    
    # Make request for JSON response
    response = client.get('/admin/export-auction-data?game_id=123')
    
    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] == True
    assert data["data"] == csv_content
    
    # Verify controller called with correct parameters
    mock_controller_instance.export_auction_data.assert_called_once_with("123", None, None)

@patch('src.routes.admin.auction_admin_routes.admin_required')
@patch('src.routes.admin.auction_admin_routes.AuctionController')
def test_export_auction_data_download_format(mock_auction_controller, mock_admin_required, client):
    # Setup mock decorator
    mock_admin_required.return_value = lambda x: x
    
    # Setup mock controller
    mock_controller_instance = MagicMock()
    mock_auction_controller.return_value = mock_controller_instance
    csv_content = "id,game_id,property_id,start_time,end_time,starting_price,winning_bid\n1,123,5,2023-05-01,2023-05-01,200,500\n2,123,7,2023-06-15,2023-06-15,300,650\n"
    mock_controller_instance.export_auction_data.return_value = {
        "success": True,
        "message": "Auction data exported successfully",
        "data": csv_content
    }
    
    # Make request for file download
    response = client.get('/admin/export-auction-data?game_id=123&download=true')
    
    # Check response
    assert response.status_code == 200
    assert response.data.decode('utf-8') == csv_content
    assert response.headers['Content-Type'] == 'text/csv'
    assert 'auction_data_game_123.csv' in response.headers['Content-Disposition']
    
    # Verify controller called with correct parameters
    mock_controller_instance.export_auction_data.assert_called_once_with("123", None, None)

@patch('src.routes.admin.auction_admin_routes.admin_required')
@patch('src.routes.admin.auction_admin_routes.AuctionController')
def test_export_auction_data_error_handling(mock_auction_controller, mock_admin_required, client):
    # Setup mock decorator
    mock_admin_required.return_value = lambda x: x
    
    # Setup mock controller to return an error
    mock_controller_instance = MagicMock()
    mock_auction_controller.return_value = mock_controller_instance
    mock_controller_instance.export_auction_data.return_value = {
        "success": False,
        "message": "Invalid date format",
        "data": None
    }
    
    # Make request with invalid parameters
    response = client.get('/admin/export-auction-data?start_date=invalid-date')
    
    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] == False
    assert data["message"] == "Invalid date format"
    
    # Verify controller called with correct parameters
    mock_controller_instance.export_auction_data.assert_called_once_with(None, "invalid-date", None) 