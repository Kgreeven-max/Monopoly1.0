import functools
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta

def create_token(user_id, is_admin=False, expires_in_hours=24):
    """Create a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    secret = current_app.config.get('JWT_SECRET', 'dev_secret')
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def validate_token(token):
    """Validate a JWT token"""
    try:
        secret = current_app.config.get('JWT_SECRET', 'dev_secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def admin_required(f):
    """Decorator to require admin authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        payload = validate_token(token)
        
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        if not payload.get('is_admin', False):
            return jsonify({'success': False, 'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def login_required(f):
    """Decorator to require user authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        payload = validate_token(token)
        
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Add user_id to request for convenience
        request.user_id = payload.get('user_id')
        
        return f(*args, **kwargs)
    
    return decorated 