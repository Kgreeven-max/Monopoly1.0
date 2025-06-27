# API Router Template
# Copy this template when creating new API routers

from flask import Blueprint, request, jsonify
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from ...application.use_cases import UseCase
from ...domain.exceptions import DomainException

# Create blueprint
router_template = Blueprint('template', __name__, url_prefix='/api/v1/template')

# Request/Response models
class CreateRequestModel(BaseModel):
    """Request model for create endpoint."""
    name: str
    description: Optional[str] = None

class UpdateRequestModel(BaseModel):
    """Request model for update endpoint."""
    name: Optional[str] = None
    description: Optional[str] = None

class ResponseModel(BaseModel):
    """Response model for entity."""
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str

class ErrorResponseModel(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[dict] = None

# Helper functions
def handle_validation_error(error: ValidationError):
    """Handle Pydantic validation errors."""
    return jsonify({
        'error': 'Validation Error',
        'message': 'Invalid request data',
        'details': error.errors()
    }), 400

def handle_domain_error(error: DomainException):
    """Handle domain-specific errors."""
    return jsonify({
        'error': 'Domain Error',
        'message': str(error)
    }), 400

def handle_generic_error(error: Exception):
    """Handle generic errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# Route handlers
@router_template.route('/', methods=['POST'])
def create_entity():
    """Create new entity."""
    try:
        # Parse and validate request
        request_data = CreateRequestModel.parse_obj(request.json)
        
        # Execute use case
        use_case = CreateEntityUseCase()  # Inject dependencies
        result = use_case.execute(request_data)
        
        if not result.success:
            return jsonify({'error': result.error}), 400
        
        # Return success response
        response = ResponseModel.from_dict(result.data)
        return jsonify(response.dict()), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except DomainException as e:
        return handle_domain_error(e)
    except Exception as e:
        return handle_generic_error(e)

@router_template.route('/<entity_id>', methods=['GET'])
def get_entity(entity_id: str):
    """Get entity by ID."""
    try:
        use_case = GetEntityUseCase()  # Inject dependencies
        result = use_case.execute(entity_id)
        
        if not result.success:
            return jsonify({'error': result.error}), 404
        
        response = ResponseModel.from_dict(result.data)
        return jsonify(response.dict()), 200
        
    except DomainException as e:
        return handle_domain_error(e)
    except Exception as e:
        return handle_generic_error(e)

@router_template.route('/', methods=['GET'])
def list_entities():
    """List all entities with optional filtering."""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        filters = {
            key: value for key, value in request.args.items()
            if key not in ['page', 'limit']
        }
        
        use_case = ListEntitiesUseCase()  # Inject dependencies
        result = use_case.execute(page, limit, filters)
        
        if not result.success:
            return jsonify({'error': result.error}), 400
        
        entities = [ResponseModel.from_dict(entity) for entity in result.data['entities']]
        
        return jsonify({
            'entities': [entity.dict() for entity in entities],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': result.data['total'],
                'pages': result.data['pages']
            }
        }), 200
        
    except Exception as e:
        return handle_generic_error(e)

@router_template.route('/<entity_id>', methods=['PUT'])
def update_entity(entity_id: str):
    """Update entity."""
    try:
        request_data = UpdateRequestModel.parse_obj(request.json)
        
        use_case = UpdateEntityUseCase()  # Inject dependencies
        result = use_case.execute(entity_id, request_data)
        
        if not result.success:
            return jsonify({'error': result.error}), 400
        
        response = ResponseModel.from_dict(result.data)
        return jsonify(response.dict()), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except DomainException as e:
        return handle_domain_error(e)
    except Exception as e:
        return handle_generic_error(e)

@router_template.route('/<entity_id>', methods=['DELETE'])
def delete_entity(entity_id: str):
    """Delete entity."""
    try:
        use_case = DeleteEntityUseCase()  # Inject dependencies
        result = use_case.execute(entity_id)
        
        if not result.success:
            return jsonify({'error': result.error}), 400
        
        return '', 204
        
    except DomainException as e:
        return handle_domain_error(e)
    except Exception as e:
        return handle_generic_error(e)

# Register error handlers
@router_template.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@router_template.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method Not Allowed',
        'message': 'The requested method is not allowed for this resource'
    }), 405

# Example usage:
# from .template_router import router_template
# 
# # In main app registration:
# app.register_blueprint(router_template)