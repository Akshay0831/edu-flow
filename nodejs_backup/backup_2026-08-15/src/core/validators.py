"""Centralized validation system for common patterns."""

import re
from typing import List, Optional, Dict, Any
from pydantic import field_validator, EmailStr
from datetime import datetime, date


class CommonValidators:
    """Common validation utilities."""
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        if not v:
            raise ValueError('Email is required')
        # Simple regex email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        # Remove all non-digit characters except + at the start
        phone = re.sub(r'[^+\d]', '', v)
        
        # Basic validation: starts with + followed by digits, total length 10-15
        if not re.match(r'^\+[1-9]\d{1,14}$', phone):
            raise ValueError('Invalid phone number format')
        return phone
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if not v:
            raise ValueError('Password is required')
        
        password_min_length = 8
        password_require_uppercase = True
        password_require_lowercase = True
        password_require_number = True
        password_require_special = True
        
        if len(v) < password_min_length:
            raise ValueError(f'Password must be at least {password_min_length} characters')
        
        if password_require_uppercase and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if password_require_lowercase and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if password_require_number and not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format and ensure it's not in the future."""
        if isinstance(v, str):
            try:
                v = datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        
        if isinstance(v, date) and v > date.today():
            raise ValueError('Date cannot be in the future')
        
        return v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v:
            return v
        
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name format."""
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        # Remove extra whitespace
        v = ' '.join(v.strip().split())
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[a-zA-Z\s\'-]+$', v):
            raise ValueError('Name contains invalid characters')
        
        return v