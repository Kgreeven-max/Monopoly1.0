# Repository Template
# Copy this template when creating new repositories

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Entity
from ..value_objects import EntityId

class RepositoryTemplate(ABC):
    """Template for repository interfaces.
    
    Repositories provide data access abstraction for domain entities.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[Entity]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Entity]:
        """Get all entities."""
        pass
    
    @abstractmethod
    def find_by_criteria(self, **criteria) -> List[Entity]:
        """Find entities by criteria."""
        pass
    
    @abstractmethod
    def save(self, entity: Entity) -> None:
        """Save entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: EntityId) -> None:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    def exists(self, entity_id: EntityId) -> bool:
        """Check if entity exists."""
        pass

# SQLAlchemy Implementation Template
from sqlalchemy.orm import Session
from ...infrastructure.database.models import SQLModel

class SQLAlchemyRepositoryTemplate(RepositoryTemplate):
    """SQLAlchemy implementation template."""
    
    def __init__(self, session: Session, model_class: type):
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, entity_id: EntityId) -> Optional[Entity]:
        model = self.session.query(self.model_class).filter_by(id=str(entity_id)).first()
        return self._to_domain_entity(model) if model else None
    
    def get_all(self) -> List[Entity]:
        models = self.session.query(self.model_class).all()
        return [self._to_domain_entity(model) for model in models]
    
    def find_by_criteria(self, **criteria) -> List[Entity]:
        query = self.session.query(self.model_class)
        for key, value in criteria.items():
            query = query.filter(getattr(self.model_class, key) == value)
        models = query.all()
        return [self._to_domain_entity(model) for model in models]
    
    def save(self, entity: Entity) -> None:
        model = self._to_database_model(entity)
        self.session.merge(model)
        self.session.commit()
    
    def delete(self, entity_id: EntityId) -> None:
        self.session.query(self.model_class).filter_by(id=str(entity_id)).delete()
        self.session.commit()
    
    def exists(self, entity_id: EntityId) -> bool:
        return self.session.query(self.model_class).filter_by(id=str(entity_id)).first() is not None
    
    def _to_domain_entity(self, model: SQLModel) -> Entity:
        """Convert database model to domain entity."""
        # Implement conversion logic
        pass
    
    def _to_database_model(self, entity: Entity) -> SQLModel:
        """Convert domain entity to database model."""
        # Implement conversion logic
        pass

# Example usage:
# class PlayerRepository(RepositoryTemplate):
#     def get_by_game_id(self, game_id: GameId) -> List[Player]:
#         pass
#
# class SQLAlchemyPlayerRepository(SQLAlchemyRepositoryTemplate, PlayerRepository):
#     def __init__(self, session: Session):
#         super().__init__(session, PlayerModel)