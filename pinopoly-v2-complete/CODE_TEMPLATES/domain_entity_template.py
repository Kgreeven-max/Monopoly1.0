# Domain Entity Template
# Copy this template when creating new domain entities

from dataclasses import dataclass
from typing import List, Optional
from ..events import DomainEvent
from ..value_objects import EntityId

@dataclass
class EntityTemplate:
    """Template for domain entities.
    
    Domain entities represent core business concepts and contain:
    - Identity (unique ID)
    - Business logic methods
    - State validation
    - Domain event generation
    """
    
    id: EntityId
    # Add other attributes here
    _events: List[DomainEvent] = None
    
    def __post_init__(self):
        if self._events is None:
            self._events = []
    
    def business_operation(self) -> DomainEvent:
        """Template for business operations.
        
        Returns:
            Domain event representing what happened
        """
        # 1. Validate business rules
        self._validate_business_rules()
        
        # 2. Perform the operation
        # ... business logic here ...
        
        # 3. Create domain event
        event = DomainEvent(
            entity_id=self.id,
            event_type="operation_performed",
            data={}
        )
        
        # 4. Add event to entity
        self._events.append(event)
        
        return event
    
    def _validate_business_rules(self):
        """Validate business rules before operations."""
        # Add validation logic here
        pass
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events for this entity."""
        return self._events.copy()
    
    def clear_events(self):
        """Clear domain events after processing."""
        self._events.clear()

# Example usage:
# class Player(EntityTemplate):
#     name: str
#     money: Money
#     position: Position
#     
#     def move(self, spaces: int) -> PlayerMoved:
#         # Implementation here
#         pass