# Use Case Template
# Copy this template when creating new use cases

from dataclasses import dataclass
from typing import Any, Optional
from abc import ABC, abstractmethod

@dataclass
class UseCaseRequest:
    """Template for use case request data."""
    # Add request fields here
    pass

@dataclass
class UseCaseResponse:
    """Template for use case response data."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None

class UseCaseTemplate(ABC):
    """Template for use cases (application layer).
    
    Use cases represent application-specific business rules.
    They orchestrate domain entities and services.
    """
    
    def __init__(self, repository, other_dependencies):
        self.repository = repository
        # Initialize other dependencies
    
    @abstractmethod
    def execute(self, request: UseCaseRequest) -> UseCaseResponse:
        """Execute the use case."""
        pass
    
    def _validate_request(self, request: UseCaseRequest) -> None:
        """Validate use case request."""
        # Add validation logic
        pass
    
    def _handle_error(self, error: Exception) -> UseCaseResponse:
        """Handle use case errors."""
        return UseCaseResponse(
            success=False,
            error=str(error)
        )

# Concrete Use Case Template
class ConcreteUseCaseTemplate(UseCaseTemplate):
    """Concrete implementation template."""
    
    def execute(self, request: UseCaseRequest) -> UseCaseResponse:
        try:
            # 1. Validate request
            self._validate_request(request)
            
            # 2. Load required entities
            entity = self.repository.get_by_id(request.entity_id)
            if not entity:
                return UseCaseResponse(
                    success=False,
                    error="Entity not found"
                )
            
            # 3. Execute business logic
            result = entity.business_operation()
            
            # 4. Save changes
            self.repository.save(entity)
            
            # 5. Return success response
            return UseCaseResponse(
                success=True,
                message="Operation completed successfully",
                data=result
            )
            
        except Exception as e:
            return self._handle_error(e)

# Example usage:
# @dataclass
# class MovePlayerRequest:
#     player_id: str
#     spaces: int
#
# class MovePlayerUseCase(UseCaseTemplate):
#     def __init__(self, player_repository, game_repository):
#         self.player_repository = player_repository
#         self.game_repository = game_repository
#     
#     def execute(self, request: MovePlayerRequest) -> UseCaseResponse:
#         # Implementation here
#         pass