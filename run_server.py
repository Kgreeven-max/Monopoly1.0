import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinopoly_server.log"),
        logging.StreamHandler()
    ]
)

try:
    # Create a simple Flask app just for Socket.IO
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    
    # Configure CORS to allow requests from any origin
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    socketio = SocketIO(app, cors_allowed_origins="*", path="/ws")

    @app.route('/')
    def index():
        return "WebSocket Server Running"
        
    # Add API routes for authentication
    @app.route('/api/auth/display/initialize', methods=['POST', 'OPTIONS'])
    def initialize_display():
        """Initialize display without validation."""
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response
            
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'success': False, 'error': 'Invalid request format.'}), 400

        # No validation needed, always return success
        return jsonify({'success': True, 'message': 'Display initialized.'}), 200

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        return True

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    if __name__ == '__main__':
        print("Starting WebSocket server on port 8080...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
except Exception as e:
    logging.error(f"Error starting server: {str(e)}")
    sys.exit(1) 