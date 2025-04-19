from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
properties = [
    {"id": 1, "name": "Mediterranean Avenue", "price": 60, "rent": 2, "group": "brown"},
    {"id": 2, "name": "Baltic Avenue", "price": 60, "rent": 4, "group": "brown"},
    {"id": 3, "name": "Oriental Avenue", "price": 100, "rent": 6, "group": "light_blue"}
]

players = [
    {"id": 1, "name": "Player 1", "cash": 1500, "pin": "1234", "position": 0, "in_jail": False},
    {"id": 2, "name": "Player 2", "cash": 1500, "pin": "5678", "position": 0, "in_jail": False}
]

@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "message": "Simple test server is running"}), 200

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """Get all properties"""
    return jsonify({"success": True, "properties": properties}), 200

@app.route('/api/property/<int:property_id>', methods=['GET'])
def get_property(property_id):
    """Get a specific property by ID"""
    for prop in properties:
        if prop["id"] == property_id:
            return jsonify({"success": True, "property": prop}), 200
    return jsonify({"success": False, "error": "Property not found"}), 404

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players"""
    return jsonify({"success": True, "players": players}), 200

@app.route('/api/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """Get a specific player by ID"""
    for player in players:
        if player["id"] == player_id:
            return jsonify({"success": True, "player": player}), 200
    return jsonify({"success": False, "error": "Player not found"}), 404

@app.route('/api/player/auth', methods=['POST'])
def authenticate_player():
    """Authenticate a player by ID and PIN"""
    data = request.json
    player_id = data.get('player_id')
    pin = data.get('pin')
    
    if not player_id or not pin:
        return jsonify({"success": False, "error": "Player ID and PIN are required"}), 400
    
    for player in players:
        if player["id"] == player_id and player["pin"] == pin:
            return jsonify({"success": True, "player": player}), 200
    
    return jsonify({"success": False, "error": "Invalid player ID or PIN"}), 401

if __name__ == "__main__":
    print("Starting simple test server on port 5000...")
    print("Available endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/properties")
    print("  GET  /api/property/<id>")
    print("  GET  /api/players")
    print("  GET  /api/player/<id>")
    print("  POST /api/player/auth")
    app.run(host='0.0.0.0', port=5000, debug=True) 