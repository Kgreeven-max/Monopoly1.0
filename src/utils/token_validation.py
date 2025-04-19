"""
Token validation utilities for the Pi-nopoly API.
Handles JWT token validation and permission checking.
"""

import time
import jwt
from functools import wraps
from flask import request, jsonify, current_app


def validate_token(required_role=None):
    """
    Decorator to validate JWT tokens for API requests.
    Optionally checks for a specific role.
    
    Args:
        required_role (str, optional): Role required for access (e.g., 'admin', 'user')
    
    Returns:
        Function: The decorated function with token validation
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Get token from Authorization header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            # Get token from query parameters
            if not token and 'token' in request.args:
                token = request.args.get('token')
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            try:
                # Decode token
                secret_key = current_app.config.get('SECRET_KEY', 'pinopoly-development-key')
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                # Check role if required
                if required_role and payload.get('role') != required_role:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add user info to kwargs for the route handler
                kwargs['user_id'] = payload.get('user_id')
                kwargs['role'] = payload.get('role')
                
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            
        return decorated_function
    return decorator


def generate_token(user_id, role='user', expiry=86400):
    """
    Generate a JWT token for a user.
    
    Args:
        user_id (str): User ID
        role (str, optional): User role. Defaults to 'user'.
        expiry (int, optional): Token expiry in seconds. Defaults to 86400 (24 hours).
    
    Returns:
        str: JWT token
    """
    secret_key = current_app.config.get('SECRET_KEY', 'pinopoly-development-key')
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': int(time.time()) + expiry
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256') 