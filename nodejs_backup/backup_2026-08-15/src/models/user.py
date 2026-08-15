"""
User models for Edu-Flow Backend

This module contains Pydantic models for user entities:
- Admin, Teacher, Student roles
- User authentication and profiles
- User management schemas

Author: Edu-Flow Team
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(True, description="User account status")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, max_length=128, description="User password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "teacher@eduflow.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "teacher",
                "password": "securepassword123",
                "is_active": True
            }
        }
    }


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User account status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "is_active": True
            }
        }
    }


class UserInDB(UserBase):
    """User database schema with ID"""
    id: str = Field(..., description="User unique identifier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "60c72b2f9b1d8e001f8e4c3a",
                "email": "teacher@eduflow.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "teacher",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    )


class User(UserInDB):
    """User response schema"""
    password: Optional[str] = Field(None, description="Password (hidden in response)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60c72b2f9b1d8e001f8e4c3a",
                "email": "teacher@eduflow.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "teacher",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    }


class TeacherProfile(BaseModel):
    """Teacher-specific profile schema"""
    employee_id: str = Field(..., description="Employee ID")
    department_id: Optional[str] = Field(None, description="Department ID")
    subjects: List[str] = Field(default_factory=list, description="Subjects taught")
    qualifications: List[str] = Field(default_factory=list, description="Qualifications")
    experience_years: int = Field(0, ge=0, description="Years of experience")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "employee_id": "EMP001",
                "department_id": "DEPT001",
                "subjects": ["Mathematics", "Physics"],
                "qualifications": ["M.Sc. Mathematics", "B.Ed."],
                "experience_years": 5
            }
        }
    }


class StudentProfile(BaseModel):
    """Student-specific profile schema"""
    student_id: str = Field(..., description="Student ID")
    department_id: Optional[str] = Field(None, description="Department ID")
    enrolled_courses: List[str] = Field(default_factory=list, description="Enrolled courses")
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Grade Point Average")
    year_of_study: int = Field(1, ge=1, le=5, description="Current year of study")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "student_id": "STU001",
                "department_id": "DEPT001",
                "enrolled_courses": ["CS101", "MATH201"],
                "gpa": 3.8,
                "year_of_study": 2
            }
        }
    }


class AdminProfile(BaseModel):
    """Admin-specific profile schema"""
    admin_id: str = Field(..., description="Administrator ID")
    department: Optional[str] = Field(None, description="Department assigned")
    permissions: List[str] = Field(default_factory=list, description="Admin permissions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "admin_id": "ADM001",
                "department": "IT Department",
                "permissions": ["user_management", "course_management", "report_generation"]
            }
        }
    }