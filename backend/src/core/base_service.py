"""Base Service Pattern for all business logic operations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import asyncio
from core.exceptions import NotFoundError, ValidationError, ForbiddenError
from core.base_repository import BaseRepository


class BaseService(ABC):
    """Abstract base service providing common business operations."""
    
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        
    @abstractmethod
    async def create(self, data: Dict) -> Dict:
        """Create a new entity.
        
        Args:
            data: The data to create
            
        Returns:
            The created entity
            
        Raises:
            ValidationError: If data validation fails
        """
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Optional[Dict]:
        """Get an entity by ID.
        
        Args:
            id: The ID of the entity to retrieve
            
        Returns:
            The entity data or None if not found
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict) -> Dict:
        """Update an entity by ID.
        
        Args:
            id: The ID of the entity to update
            data: The data to update
            
        Returns:
            The updated entity
            
        Raises:
            NotFoundError: If entity not found
            ValidationError: If data validation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID.
        
        Args:
            id: The ID of the entity to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If entity not found
        """
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """List entities with pagination and filtering.
        
        Args:
            skip: Number of entities to skip (for pagination)
            limit: Maximum number of entities to return
            filters: Optional filters to apply
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Dict = None) -> int:
        """Count entities with optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            The number of matching entities
        """
        pass
    
    async def exists(self, id: str) -> bool:
        """Check if an entity exists by ID.
        
        Args:
            id: The ID to check
            
        Returns:
            True if the entity exists, False otherwise
        """
        return await self.repository.exists(id)
    
    async def validate_data(self, data: Dict, required_fields: List[str] = None) -> bool:
        """Validate data against required fields.
        
        Args:
            data: The data to validate
            required_fields: List of required field names
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationError: If validation fails
        """
        if required_fields:
            for field in required_fields:
                if field not in data or data[field] is None:
                    raise ValidationError(f"Required field '{field}' is missing")
        return True
    
    async def sanitize_data(self, data: Dict) -> Dict:
        """Sanitize data by removing sensitive fields.
        
        Args:
            data: The data to sanitize
            
        Returns:
            Sanitized data
        """
        # Remove sensitive fields like passwords, tokens, etc.
        sensitive_fields = ['password', 'token', 'secret', 'key']
        sanitized = data.copy()
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***' if isinstance(sanitized[field], str) else None
        return sanitized
    
    async def audit_log(self, action: str, entity_id: str, user_id: str, changes: Dict = None):
        """Log audit trail for entity operations.
        
        Args:
            action: The action performed (create, update, delete)
            entity_id: The ID of the entity being modified
            user_id: The ID of the user performing the action
            changes: The changes made (for update actions)
        """
        audit_data = {
            'action': action,
            'entity_id': entity_id,
            'entity_type': self.__class__.__name__.replace('Service', ''),
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'changes': changes or {}
        }
        # This would be implemented in the audit service
        # await self.audit_service.create(audit_data)