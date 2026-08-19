"""
Base Model for Database Operations

This module provides the base model class for all database entities.
It includes common fields, validation methods, and database operations.

Author: Edu-Flow Team
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)

# Create base class for SQLAlchemy models
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class for all database entities.
    
    Provides common fields and methods for all database models.
    """
    __abstract__ = True
    
    # Common fields for all entities
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize the base model with provided data."""
        super().__init__()
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.is_active = kwargs.get('is_active', True)
        
        # Set specific attributes, skip properties
        for key, value in kwargs.items():
            if hasattr(self, key) and not isinstance(getattr(type(self), key, None), property):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name, None)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs) -> None:
        """
        Update the model with new data.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def validate(self) -> bool:
        """
        Validate the model data.
        
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Common validations
            if not hasattr(self, 'id') or not self.id:
                raise ValidationError("ID is required")
            
            if not hasattr(self, 'created_at') or not self.created_at:
                raise ValidationError("Created at timestamp is required")
            
            if not hasattr(self, 'updated_at') or not self.updated_at:
                raise ValidationError("Updated at timestamp is required")
            
            # Validate timestamp order
            if self.updated_at < self.created_at:
                raise ValidationError("Updated timestamp cannot be before created timestamp")
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error for {self.__class__.__name__}: {str(e)}")
            raise ValidationError(f"Validation error: {str(e)}")
    
    def soft_delete(self) -> None:
        """
        Mark the model as inactive (soft delete).
        """
        self.is_active = False
        self.updated_at = datetime.now()
        logger.info(f"Soft deleted {self.__class__.__name__} with id: {self.id}")
    
    def restore(self) -> None:
        """
        Restore a soft-deleted model.
        """
        self.is_active = True
        self.updated_at = datetime.now()
        logger.info(f"Restored {self.__class__.__name__} with id: {self.id}")
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            BaseModel instance
        """
        return cls(**data)
    
    @classmethod
    def create_from_dicts(cls, data_list: list) -> list:
        """
        Create multiple model instances from a list of dictionaries.
        
        Args:
            data_list: List of dictionaries containing model data
            
        Returns:
            List of BaseModel instances
        """
        return [cls.create_from_dict(data) for data in data_list]
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id='{self.id}')>"