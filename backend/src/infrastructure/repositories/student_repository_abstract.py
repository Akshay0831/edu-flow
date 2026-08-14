"""
Abstract Student Repository

This module provides the abstract base class for student repositories.
It defines the common operations that all student repositories should implement.

Author: Edu-Flow Team
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.infrastructure.repositories.base_repository import QueryResult


class StudentRepositoryAbstract(ABC):
    """Abstract base class for student repositories."""
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> QueryResult:
        """List all students with pagination."""
        pass
    
    @abstractmethod
    async def search(self, search_term: str, limit: int = 100, offset: int = 0) -> QueryResult:
        """Search students by name, email, or student ID."""
        pass
    
    @abstractmethod
    async def filter(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> QueryResult:
        """Filter students by criteria."""
        pass