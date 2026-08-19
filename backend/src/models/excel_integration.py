"""
Excel Integration Models for Edu-Flow

This module defines the data models for Excel integration:
- ExcelImport: Track import operations
- ExcelExport: Track export operations
- ExcelTemplate: Excel templates for data formatting
- ExcelJob: Background processing jobs for Excel operations

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON, Numeric
from sqlalchemy.orm import relationship
import uuid

from infrastructure.models.base_model import Base

class ExcelOperationType(Enum):
    """Excel operation types"""
    IMPORT = "import"
    EXPORT = "export"
    TEMPLATE = "template"

class ExcelStatus(Enum):
    """Excel processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExcelImportStatus(Enum):
    """Excel import status"""
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    PARTIAL = "partial"

class ExcelExportStatus(Enum):
    """Excel export status"""
    GENERATING = "generating"
    GENERATED = "generated"
    READY = "ready"
    DOWNLOADING = "downloading"
    EXPIRED = "expired"

class ExcelTemplateType(Enum):
    """Excel template types"""
    STUDENT_REGISTRATION = "student_registration"
    COURSE_UPLOAD = "course_upload"
    FEEDBACK_COLLECTION = "feedback_collection"
    MARKS_ENTRY = "marks_entry"
    ATTENDANCE_UPLOAD = "attendance_upload"
    TEACHER_ALLOCATION = "teacher_allocation"
    CLASS_SCHEDULE = "class_schedule"
    REPORT_TEMPLATE = "report_template"

class ExcelImport(Base):
    """Excel import operation tracking"""
    
    __tablename__ = "excel_imports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    file_type = Column(String, nullable=False)  # .xlsx, .xls, .csv
    
    # Import configuration
    import_type = Column(String, nullable=False)  # feedback, students, courses, marks, etc.
    template_id = Column(String, nullable=True)  # Optional template ID
    
    # Processing status
    status = Column(String, default="uploaded", nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    record_count = Column(Integer, default=0, nullable=True)
    success_count = Column(Integer, default=0, nullable=True)
    error_count = Column(Integer, default=0, nullable=True)
    
    # Error handling
    error_details = Column(JSON, nullable=True)  # Error information
    validation_errors = Column(JSON, nullable=True)  # Validation errors
    processing_errors = Column(JSON, nullable=True)  # Processing errors
    
    # User information
    uploaded_by = Column(String, nullable=False)
    processed_by = Column(String, nullable=True)
    
    # Timing
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Additional configuration
    import_config = Column(JSON, nullable=True)  # Import-specific configuration
    validation_config = Column(JSON, nullable=True)  # Validation rules
    mapping_config = Column(JSON, nullable=True)  # Field mappings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ExcelExport(Base):
    """Excel export operation tracking"""
    
    __tablename__ = "excel_exports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Export configuration
    export_type = Column(String, nullable=False)  # feedback, students, courses, marks, etc.
    format_type = Column(String, default="xlsx", nullable=False)  # xlsx, xls, csv
    template_id = Column(String, nullable=True)  # Optional template ID
    
    # Query configuration
    query_config = Column(JSON, nullable=False)  # Query parameters and filters
    data_config = Column(JSON, nullable=True)  # Data selection configuration
    
    # File information
    file_path = Column(String, nullable=True)  # Generated file path
    file_size = Column(Integer, nullable=True)  # File size in bytes
    download_url = Column(String, nullable=True)  # Download URL
    file_name = Column(String, nullable=True)  # Final file name
    
    # Processing status
    status = Column(String, default="generating", nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    record_count = Column(Integer, default=0, nullable=True)
    
    # User information
    requested_by = Column(String, nullable=False)
    generated_by = Column(String, nullable=True)
    
    # Timing
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Expiration time
    
    # Additional configuration
    export_config = Column(JSON, nullable=True)  # Export-specific configuration
    format_config = Column(JSON, nullable=True)  # Format configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ExcelTemplate(Base):
    """Excel templates for data formatting"""
    
    __tablename__ = "excel_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template_code = Column(String, unique=True, nullable=False)
    
    # Template configuration
    template_type = Column(String, nullable=False)
    template_version = Column(String, default="1.0", nullable=False)
    
    # Template content
    template_file_path = Column(String, nullable=False)
    template_content = Column(JSON, nullable=True)  # Template structure and formatting
    
    # Data configuration
    field_mapping = Column(JSON, nullable=True)  # Column to field mappings
    validation_rules = Column(JSON, nullable=True)  # Field validation rules
    required_fields = Column(JSON, nullable=True)  # Required field list
    data_types = Column(JSON, nullable=True)  # Field data types
    
    # Display configuration
    display_name = Column(String, nullable=True)
    description_template = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    sample_data = Column(JSON, nullable=True)  # Sample data for reference
    
    # Usage configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Configuration
    max_file_size = Column(Integer, nullable=True)  # Maximum file size in bytes
    allowed_file_types = Column(JSON, nullable=True)  # Allowed file extensions
    max_records = Column(Integer, nullable=True)  # Maximum records per file
    
    # Target system
    target_system = Column(String, default="edu_flow", nullable=False)
    target_module = Column(String, nullable=True)  # Which module uses this template
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ExcelJob(Base):
    """Background processing jobs for Excel operations"""
    
    __tablename__ = "excel_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_name = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # import, export, bulk_operation
    
    # Job configuration
    job_config = Column(JSON, nullable=False)  # Job-specific configuration
    priority = Column(Integer, default=0, nullable=False)  # Job priority
    retry_count = Column(Integer, default=0, nullable=False)  # Retry counter
    
    # Processing status
    status = Column(String, default="pending", nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # File information
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # User information
    requested_by = Column(String, nullable=False)
    processed_by = Column(String, nullable=True)
    
    # Timing
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)  # Estimated completion time
    
    # Additional metadata
    log_file_path = Column(String, nullable=True)
    result_file_path = Column(String, nullable=True)
    
    # Dependencies
    depends_on = Column(JSON, nullable=True)  # Job dependencies
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ExcelValidationError(Base):
    """Excel validation error records"""
    
    __tablename__ = "excel_validation_errors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    import_id = Column(String, nullable=False)
    row_number = Column(Integer, nullable=False)
    column_name = Column(String, nullable=True)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON, nullable=True)
    
    # Error severity
    severity = Column(String, default="error", nullable=False)  # error, warning, info
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class ExcelProcessingLog(Base):
    """Excel processing logs"""
    
    __tablename__ = "excel_processing_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String, nullable=False)
    operation_type = Column(String, nullable=False)
    
    # Log information
    level = Column(String, nullable=False)  # info, warning, error, debug
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Performance metrics
    execution_time = Column(Float, nullable=True)  # Execution time in seconds
    
    # Context
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    # File information
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ExcelConfiguration(Base):
    """Excel system configuration"""
    
    __tablename__ = "excel_configurations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration metadata
    category = Column(String, nullable=False)  # general, import, export, templates, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System configuration
    
    # Validation
    validation_rules = Column(JSON, nullable=True)  # Value validation rules
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)