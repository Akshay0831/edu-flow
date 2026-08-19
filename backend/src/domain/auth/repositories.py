"""
Authentication repositories

This module contains repository interfaces and implementations for authentication:
- UserRepository: Interface for user data access
- TokenRepository: Interface for token data access

Author: Edu-Flow Team
"""

from typing import Optional, List
from abc import ABC, abstractmethod

from .entities import User, UserRole


class UserRepository(ABC):
    """Abstract repository interface for user data access"""
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create new user"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination"""
        pass
    
    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        pass


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository for testing"""
    
    def __init__(self):
        self.users = {}
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def get_by_role(self, role: UserRole) -> List[User]:
        return [user for user in self.users.values() if user.role == role]
    
    async def create(self, user: User) -> User:
        if user.id in self.users:
            raise ValueError("User already exists")
        self.users[user.id] = user
        return user
    
    async def update(self, user: User) -> User:
        if user.id not in self.users:
            raise ValueError("User not found")
        self.users[user.id] = user
        return user
    
    async def delete(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        users = list(self.users.values())
        return users[offset:offset + limit]
    
    async def count_by_role(self, role: UserRole) -> int:
        return len([user for user in self.users.values() if user.role == role])


class TokenRepository(ABC):
    """Abstract repository interface for token data access"""
    
    @abstractmethod
    async def get_by_id(self, token_id: str) -> Optional[dict]:
        """Get token by ID"""
        pass
    
    @abstractmethod
    async def create(self, token_data: dict) -> dict:
        """Create new token"""
        pass
    
    @abstractmethod
    async def revoke(self, token_id: str) -> bool:
        """Revoke token"""
        pass
    
    @abstractmethod
    async def is_revoked(self, token_id: str) -> bool:
        """Check if token is revoked"""
        pass
    
    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        pass