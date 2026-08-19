"""
Excel Integration Service for Edu-Flow

This module provides comprehensive Excel integration functionality:
- Import operations with validation and error handling
- Export operations with multiple format support
- Template management and validation
- Background job processing
- Bulk data operations
- Performance monitoring

Author: Edu-Flow Team
"""

import asyncio
import os
import io
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
from fastapi import UploadFile
from sqlalchemy.orm import Session
import logging
import uuid
from pathlib import Path
import aiofiles
import zipfile
from concurrent.futures import ThreadPoolExecutor

from core.exceptions import ValidationError, NotFoundError, DatabaseError
from core.database_abstraction import DatabaseInterface
from core.cache_abstraction import CacheManager
from core.logging import get_logger
from core.service_container import get_service_container
from models.excel_integration import (
    ExcelImport, ExcelExport, ExcelTemplate, ExcelJob, 
    ExcelValidationError, ExcelProcessingLog, ExcelConfiguration,
    ExcelStatus, ExcelImportStatus, ExcelExportStatus, 
    ExcelTemplateType, ExcelOperationType
)
from src.services.base_service import BaseService

logger = get_logger(__name__)


class ExcelIntegrationService(BaseService):
    """Excel Integration Service for handling Excel operations"""
    
    def __init__(self, service_name: str = "excel_integration_service"):
        super().__init__(service_name)
        self._supported_formats = ['.xlsx', '.xls', '.csv']
        self._max_file_size = 100 * 1024 * 1024  # 100MB
        self._max_records_per_file = 50000
        self._allowed_file_types = ['.xlsx', '.xls', '.csv']
        
        # Initialize paths
        self._upload_path = Path("uploads/excel")
        self._export_path = Path("exports/excel")
        self._template_path = Path("templates/excel")
        
        # Create directories
        self._upload_path.mkdir(parents=True, exist_ok=True)
        self._export_path.mkdir(parents=True, exist_ok=True)
        self._template_path.mkdir(parents=True, exist_ok=True)
        
        # Template mappings
        self._template_mappings = {
            ExcelTemplateType.STUDENT_REGISTRATION: {
                'required_fields': ['student_id', 'full_name', 'email', 'phone'],
                'field_mapping': {
                    'Student ID': 'student_id',
                    'Full Name': 'full_name',
                    'Email': 'email',
                    'Phone': 'phone',
                    'Department': 'department',
                    'Program': 'program',
                    'Year': 'year'
                }
            },
            ExcelTemplateType.COURSE_UPLOAD: {
                'required_fields': ['course_id', 'course_name', 'department'],
                'field_mapping': {
                    'Course Code': 'course_id',
                    'Course Name': 'course_name',
                    'Department': 'department',
                    'Credits': 'credits',
                    'Description': 'description'
                }
            },
            ExcelTemplateType.FEEDBACK_COLLECTION: {
                'required_fields': ['course_id', 'feedback_type'],
                'field_mapping': {
                    'Course ID': 'course_id',
                    'Feedback Type': 'feedback_type',
                    'Rating': 'rating',
                    'Comments': 'comments'
                }
            },
            ExcelTemplateType.MARKS_ENTRY: {
                'required_fields': ['student_id', 'course_id', 'marks'],
                'field_mapping': {
                    'Student ID': 'student_id',
                    'Course ID': 'course_id',
                    'Marks': 'marks',
                    'Grade': 'grade',
                    'Exam Type': 'exam_type'
                }
            },
            ExcelTemplateType.ATTENDANCE_UPLOAD: {
                'required_fields': ['student_id', 'date', 'status'],
                'field_mapping': {
                    'Student ID': 'student_id',
                    'Date': 'date',
                    'Status': 'status',
                    'Course ID': 'course_id'
                }
            },
            ExcelTemplateType.TEACHER_ALLOCATION: {
                'required_fields': ['teacher_id', 'course_id', 'semester'],
                'field_mapping': {
                    'Teacher ID': 'teacher_id',
                    'Course ID': 'course_id',
                    'Semester': 'semester',
                    'Role': 'role'
                }
            }
        }
        
        # Validation rules
        self._validation_rules = {
            'email': self._validate_email,
            'phone': self._validate_phone,
            'student_id': self._validate_student_id,
            'course_id': self._validate_course_id,
            'marks': self._validate_marks,
            'rating': self._validate_rating
        }
    
    # region: Import Operations
    
    async def upload_excel_file(
        self,
        file: UploadFile,
        import_type: str,
        user_id: str,
        template_id: Optional[str] = None,
        import_config: Optional[Dict[str, Any]] = None
    ) -> ExcelImport:
        """Upload and validate Excel file for import"""
        try:
            # Validate file
            await self._validate_uploaded_file(file)
            
            # Generate file path
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            file_path = self._upload_path / f"{file_id}{file_extension}"
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create import record
            excel_import = ExcelImport(
                name=file.filename,
                description=import_config.get('description', '') if import_config else '',
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=len(content),
                file_type=file_extension,
                import_type=import_type,
                template_id=template_id,
                status=ExcelImportStatus.UPLOADED.value,
                uploaded_by=user_id,
                uploaded_at=datetime.utcnow(),
                import_config=import_config or {}
            )
            
            # Save to database
            await self.insert_one('excel_imports', excel_import.__dict__)
            
            # Start validation job
            await self._start_validation_job(excel_import.id)
            
            logger.info(f"Excel file uploaded: {file.filename} ({file_id})")
            return excel_import
            
        except Exception as e:
            logger.error(f"Error uploading Excel file: {str(e)}")
            raise DatabaseError(f"Failed to upload Excel file: {str(e)}")
    
    async def get_import_status(self, import_id: str) -> Dict[str, Any]:
        """Get import operation status"""
        try:
            excel_import = await self.find_one('excel_imports', {'id': import_id})
            if not excel_import:
                raise NotFoundError(f"Excel import not found: {import_id}")
            
            return {
                'id': excel_import['id'],
                'name': excel_import['name'],
                'status': excel_import['status'],
                'progress_percentage': excel_import['progress_percentage'],
                'record_count': excel_import['record_count'],
                'success_count': excel_import['success_count'],
                'error_count': excel_import['error_count'],
                'uploaded_at': excel_import['uploaded_at'],
                'processing_started_at': excel_import['processing_started_at'],
                'processing_completed_at': excel_import['processing_completed_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting import status: {str(e)}")
            raise DatabaseError(f"Failed to get import status: {str(e)}")
    
    async def start_import_process(self, import_id: str) -> ExcelImport:
        """Start the import process for a validated file"""
        try:
            # Get import record
            excel_import = await self.find_one('excel_imports', {'id': import_id})
            if not excel_import:
                raise NotFoundError(f"Excel import not found: {import_id}")
            
            # Check status
            if excel_import['status'] not in [ExcelImportStatus.VALIDATED.value]:
                raise ValidationError(f"Cannot start import: invalid status {excel_import['status']}")
            
            # Update status to processing
            await self.update_one('excel_imports', {'id': import_id}, {
                'status': ExcelImportStatus.PROCESSING.value,
                'processing_started_at': datetime.utcnow(),
                'progress_percentage': 0
            })
            
            # Create processing job
            job = ExcelJob(
                job_name=f"Excel Import {import_id}",
                job_type="import",
                job_config={
                    'import_id': import_id,
                    'import_type': excel_import['import_type'],
                    'template_id': excel_import['template_id']
                },
                priority=1,
                requested_by=excel_import['uploaded_by']
            )
            
            await self.insert_one('excel_jobs', job.__dict__)
            
            logger.info(f"Import process started: {import_id}")
            return ExcelImport(**excel_import)
            
        except Exception as e:
            logger.error(f"Error starting import process: {str(e)}")
            raise DatabaseError(f"Failed to start import process: {str(e)}")
    
    async def cancel_import_process(self, import_id: str, user_id: str) -> ExcelImport:
        """Cancel an ongoing import process"""
        try:
            excel_import = await self.find_one('excel_imports', {'id': import_id})
            if not excel_import:
                raise NotFoundError(f"Excel import not found: {import_id}")
            
            # Check if can be cancelled
            if excel_import['status'] not in [ExcelImportStatus.VALIDATING.value, ExcelImportStatus.PROCESSING.value]:
                raise ValidationError(f"Cannot cancel import: invalid status {excel_import['status']}")
            
            # Update status
            await self.update_one('excel_imports', {'id': import_id}, {
                'status': ExcelImportStatus.CANCELLED.value,
                'processing_completed_at': datetime.utcnow()
            })
            
            # Cancel associated job
            await self.update_one('excel_jobs', {
                'job_config': {'$contains': {'import_id': import_id}}
            }, {
                'status': 'cancelled'
            })
            
            logger.info(f"Import process cancelled: {import_id}")
            return ExcelImport(**excel_import)
            
        except Exception as e:
            logger.error(f"Error cancelling import process: {str(e)}")
            raise DatabaseError(f"Failed to cancel import process: {str(e)}")
    
    # region: Export Operations
    
    async def create_export_job(
        self,
        export_type: str,
        query_config: Dict[str, Any],
        user_id: str,
        format_type: str = 'xlsx',
        template_id: Optional[str] = None,
        export_config: Optional[Dict[str, Any]] = None
    ) -> ExcelExport:
        """Create an export job"""
        try:
            # Validate configuration
            if not query_config:
                raise ValidationError("Query configuration is required")
            
            if format_type not in ['xlsx', 'xls', 'csv']:
                raise ValidationError("Unsupported export format")
            
            # Create export record
            export_name = f"{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            excel_export = ExcelExport(
                name=export_name,
                description=export_config.get('description', '') if export_config else '',
                export_type=export_type,
                format_type=format_type,
                template_id=template_id,
                query_config=query_config,
                export_config=export_config or {},
                status=ExcelExportStatus.GENERATING.value,
                requested_by=user_id,
                requested_at=datetime.utcnow()
            )
            
            # Save to database
            await self.insert_one('excel_exports', excel_export.__dict__)
            
            # Create export job
            job = ExcelJob(
                job_name=f"Excel Export {excel_export.id}",
                job_type="export",
                job_config={
                    'export_id': excel_export.id,
                    'export_type': export_type,
                    'query_config': query_config,
                    'format_type': format_type,
                    'template_id': template_id
                },
                priority=2,
                requested_by=user_id
            )
            
            await self.insert_one('excel_jobs', job.__dict__)
            
            logger.info(f"Export job created: {excel_export.id}")
            return excel_export
            
        except Exception as e:
            logger.error(f"Error creating export job: {str(e)}")
            raise DatabaseError(f"Failed to create export job: {str(e)}")
    
    async def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """Get export operation status"""
        try:
            excel_export = await self.find_one('excel_exports', {'id': export_id})
            if not excel_export:
                raise NotFoundError(f"Excel export not found: {export_id}")
            
            return {
                'id': excel_export['id'],
                'name': excel_export['name'],
                'status': excel_export['status'],
                'progress_percentage': excel_export['progress_percentage'],
                'record_count': excel_export['record_count'],
                'requested_at': excel_export['requested_at'],
                'generated_at': excel_export['generated_at'],
                'download_url': excel_export.get('download_url'),
                'expires_at': excel_export.get('expires_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting export status: {str(e)}")
            raise DatabaseError(f"Failed to get export status: {str(e)}")
    
    async def download_export_file(self, export_id: str, user_id: str) -> Dict[str, Any]:
        """Download generated export file"""
        try:
            excel_export = await self.find_one('excel_exports', {'id': export_id})
            if not excel_export:
                raise NotFoundError(f"Excel export not found: {export_id}")
            
            # Check permissions
            if excel_export['requested_by'] != user_id and not await self._has_admin_privileges(user_id):
                raise ValidationError("Permission denied")
            
            # Check status
            if excel_export['status'] not in [ExcelExportStatus.READY.value, ExcelExportStatus.GENERATED.value]:
                raise ValidationError(f"Export not ready: {excel_export['status']}")
            
            # Check expiration
            if excel_export.get('expires_at') and datetime.utcnow() > datetime.fromisoformat(excel_export['expires_at']):
                raise ValidationError("Export file has expired")
            
            # Update download status
            await self.update_one('excel_exports', {'id': export_id}, {
                'status': ExcelExportStatus.DOWNLOADING.value
            })
            
            # Return file information
            return {
                'file_path': excel_export['file_path'],
                'file_name': excel_export.get('file_name', f"{excel_export.name}.{excel_export['format_type']}"),
                'file_size': excel_export['file_size'],
                'download_url': excel_export['download_url']
            }
            
        except Exception as e:
            logger.error(f"Error downloading export file: {str(e)}")
            raise DatabaseError(f"Failed to download export file: {str(e)}")
    
    # region: Template Management
    
    async def create_excel_template(
        self,
        template_name: str,
        template_type: str,
        template_file: UploadFile,
        description: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        required_fields: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ExcelTemplate:
        """Create Excel template"""
        try:
            # Validate template type
            if not ExcelTemplateType(template_type):
                raise ValidationError(f"Invalid template type: {template_type}")
            
            # Save template file
            template_id = str(uuid.uuid4())
            template_extension = Path(template_file.filename).suffix
            template_path = self._template_path / f"{template_id}{template_extension}"
            
            async with aiofiles.open(template_path, 'wb') as f:
                content = await template_file.read()
                await f.write(content)
            
            # Create template record
            template = ExcelTemplate(
                name=template_name,
                description=description or '',
                template_code=f"TEMPLATE_{template_id}",
                template_type=template_type,
                template_version=config.get('version', '1.0') if config else '1.0',
                template_file_path=str(template_path),
                field_mapping=field_mapping or {},
                validation_rules=validation_rules or {},
                required_fields=required_fields or [],
                max_file_size=config.get('max_file_size') if config else None,
                allowed_file_types=config.get('allowed_file_types') if config else self._allowed_file_types,
                max_records=config.get('max_records') if config else self._max_records_per_file,
                target_system=config.get('target_system', 'edu_flow') if config else 'edu_flow',
                target_module=config.get('target_module') if config else None,
                is_active=config.get('is_active', True) if config else True,
                is_default=config.get('is_default', False) if config else False
            )
            
            # Save to database
            await self.insert_one('excel_templates', template.__dict__)
            
            logger.info(f"Excel template created: {template_name} ({template_id})")
            return template
            
        except Exception as e:
            logger.error(f"Error creating Excel template: {str(e)}")
            raise DatabaseError(f"Failed to create Excel template: {str(e)}")
    
    async def get_template(self, template_id: str) -> Optional[ExcelTemplate]:
        """Get Excel template by ID"""
        try:
            template_data = await self.find_one('excel_templates', {'id': template_id})
            if not template_data:
                return None
            
            return ExcelTemplate(**template_data)
            
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            raise DatabaseError(f"Failed to get template: {str(e)}")
    
    async def get_templates_by_type(self, template_type: str) -> List[ExcelTemplate]:
        """Get templates by type"""
        try:
            template_data = await self.find_many('excel_templates', {'template_type': template_type})
            return [ExcelTemplate(**data) for data in template_data]
            
        except Exception as e:
            logger.error(f"Error getting templates by type: {str(e)}")
            raise DatabaseError(f"Failed to get templates by type: {str(e)}")
    
    async def get_default_template(self, template_type: str) -> Optional[ExcelTemplate]:
        """Get default template for a type"""
        try:
            template_data = await self.find_one('excel_templates', {
                'template_type': template_type,
                'is_default': True
            })
            
            if template_data:
                return ExcelTemplate(**template_data)
            
            # Get first available template if no default
            templates = await self.get_templates_by_type(template_type)
            return templates[0] if templates else None
            
        except Exception as e:
            logger.error(f"Error getting default template: {str(e)}")
            raise DatabaseError(f"Failed to get default template: {str(e)}")
    
    # region: Background Processing
    
    async def process_excel_jobs(self, limit: int = 10) -> List[ExcelJob]:
        """Process pending Excel jobs"""
        try:
            # Get pending jobs
            job_data = await self.find_many('excel_jobs', {
                'status': 'pending'
            }, limit=limit, sort=[('priority', 1), ('requested_at', 1)])
            
            if not job_data:
                return []
            
            # Process jobs
            processed_jobs = []
            for job_data_dict in job_data:
                job = ExcelJob(**job_data_dict)
                try:
                    await self._process_job(job)
                    processed_jobs.append(job)
                except Exception as e:
                    logger.error(f"Error processing job {job.id}: {str(e)}")
                    await self._mark_job_failed(job, str(e))
            
            return processed_jobs
            
        except Exception as e:
            logger.error(f"Error processing Excel jobs: {str(e)}")
            raise DatabaseError(f"Failed to process Excel jobs: {str(e)}")
    
    async def _process_job(self, job: ExcelJob) -> None:
        """Process a single Excel job"""
        try:
            # Update job status
            await self.update_one('excel_jobs', {'id': job.id}, {
                'status': 'processing',
                'started_at': datetime.utcnow()
            })
            
            # Process based on job type
            if job.job_type == 'import':
                await self._process_import_job(job)
            elif job.job_type == 'export':
                await self._process_export_job(job)
            elif job.job_type == 'bulk_operation':
                await self._process_bulk_operation_job(job)
            
            # Mark as completed
            await self.update_one('excel_jobs', {'id': job.id}, {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'progress_percentage': 100
            })
            
        except Exception as e:
            await self._mark_job_failed(job, str(e))
            raise
    
    async def _process_import_job(self, job: ExcelJob) -> None:
        """Process an import job"""
        try:
            import_id = job.job_config['import_id']
            excel_import = await self.find_one('excel_imports', {'id': import_id})
            
            if not excel_import:
                raise NotFoundError(f"Import not found: {import_id}")
            
            # Parse Excel file
            df = await self._parse_excel_file(excel_import['file_path'])
            
            # Validate data
            validation_result = await self._validate_excel_data(
                df, 
                excel_import['import_type'],
                excel_import.get('template_id')
            )
            
            # Update import status
            await self.update_one('excel_imports', {'id': import_id}, {
                'status': 'validated',
                'validation_errors': validation_result['errors'],
                'progress_percentage': 50
            })
            
            # Process records
            if not validation_result['has_errors'] or excel_import['import_config'].get('process_errors', True):
                await self._process_excel_records(df, excel_import)
                
                # Update final status
                await self.update_one('excel_imports', {'id': import_id}, {
                    'status': 'processed',
                    'processing_completed_at': datetime.utcnow(),
                    'progress_percentage': 100
                })
            
        except Exception as e:
            raise DatabaseError(f"Failed to process import job: {str(e)}")
    
    async def _process_export_job(self, job: ExcelJob) -> None:
        """Process an export job"""
        try:
            export_id = job.job_config['export_id']
            excel_export = await self.find_one('excel_exports', {'id': export_id})
            
            if not excel_export:
                raise NotFoundError(f"Export not found: {export_id}")
            
            # Get data based on query config
            data = await self._get_export_data(excel_export['query_config'])
            
            # Create Excel file
            file_path = await self._create_excel_file(
                data, 
                excel_export['format_type'],
                excel_export.get('template_id')
            )
            
            # Update export record
            await self.update_one('excel_exports', {'id': export_id}, {
                'status': 'generated',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'file_name': f"{excel_export.name}.{excel_export['format_type']}",
                'download_url': f"/api/v1/excel/exports/{export_id}/download",
                'generated_at': datetime.utcnow(),
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'progress_percentage': 100
            })
            
        except Exception as e:
            raise DatabaseError(f"Failed to process export job: {str(e)}")
    
    # region: Data Processing Methods
    
    async def _validate_uploaded_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file type
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self._supported_formats:
            raise ValidationError(f"Unsupported file format: {file_extension}")
        
        # Check file size
        file_size = len(await file.read())
        file.file.seek(0)  # Reset file pointer
        
        if file_size > self._max_file_size:
            raise ValidationError(f"File too large: {file_size} bytes")
        
        # Check filename
        if not file.filename or len(file.filename.strip()) == 0:
            raise ValidationError("Invalid filename")
    
    async def _parse_excel_file(self, file_path: str) -> pd.DataFrame:
        """Parse Excel file to DataFrame"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            return df
            
        except Exception as e:
            raise DatabaseError(f"Failed to parse Excel file: {str(e)}")
    
    async def _validate_excel_data(
        self, 
        df: pd.DataFrame, 
        import_type: str, 
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate Excel data against rules"""
        try:
            validation_result = {
                'errors': [],
                'warnings': [],
                'has_errors': False,
                'has_warnings': False,
                'valid_records': 0,
                'invalid_records': 0
            }
            
            # Get template configuration
            template_config = None
            if template_id:
                template = await self.get_template(template_id)
                if template:
                    template_config = {
                        'field_mapping': template.field_mapping,
                        'validation_rules': template.validation_rules,
                        'required_fields': template.required_fields
                    }
            
            # Get default template configuration
            if not template_config:
                template_type = self._get_template_type_for_import_type(import_type)
                if template_type:
                    default_template = await self.get_default_template(template_type.value)
                    if default_template:
                        template_config = {
                            'field_mapping': default_template.field_mapping,
                            'validation_rules': default_template.validation_rules,
                            'required_fields': default_template.required_fields
                        }
            
            # Perform validation
            for index, row in df.iterrows():
                row_errors = []
                row_warnings = []
                
                # Check required fields
                if template_config and template_config['required_fields']:
                    for field in template_config['required_fields']:
                        if field not in row or pd.isna(row[field]):
                            row_errors.append({
                                'type': 'missing_required_field',
                                'field': field,
                                'message': f'Required field {field} is missing'
                            })
                
                # Validate each field
                for column_name, value in row.items():
                    if pd.isna(value):
                        continue
                    
                    # Check field mapping
                    field_key = template_config['field_mapping'].get(column_name, column_name) if template_config else column_name
                    
                    # Apply validation rules
                    validation_func = self._validation_rules.get(field_key)
                    if validation_func:
                        try:
                            validation_func(value)
                        except ValidationError as e:
                            row_errors.append({
                                'type': 'validation_error',
                                'field': field_key,
                                'message': str(e)
                            })
                
                # Record errors
                if row_errors:
                    for error in row_errors:
                        validation_result['errors'].append({
                            'row_number': index + 2,  # +1 for header, +1 for 1-based index
                            'error_type': error['type'],
                            'column_name': error['field'],
                            'error_message': error['message'],
                            'severity': 'error'
                        })
                    validation_result['invalid_records'] += 1
                else:
                    validation_result['valid_records'] += 1
            
            # Check for warnings
            if validation_result['warnings']:
                validation_result['has_warnings'] = True
            
            # Check for errors
            if validation_result['errors']:
                validation_result['has_errors'] = True
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Excel data: {str(e)}")
            raise DatabaseError(f"Failed to validate Excel data: {str(e)}")
    
    async def _process_excel_records(self, df: pd.DataFrame, excel_import: Dict[str, Any]) -> None:
        """Process validated Excel records"""
        try:
            import_type = excel_import['import_type']
            
            # Get service container
            service_container = get_service_container()
            
            # Process based on import type
            if import_type == 'students':
                await self._process_student_records(df, service_container)
            elif import_type == 'courses':
                await self._process_course_records(df, service_container)
            elif import_type == 'feedback':
                await self._process_feedback_records(df, service_container)
            elif import_type == 'marks':
                await self._process_marks_records(df, service_container)
            elif import_type == 'attendance':
                await self._process_attendance_records(df, service_container)
            elif import_type == 'teachers':
                await self._process_teacher_records(df, service_container)
            else:
                raise ValidationError(f"Unsupported import type: {import_type}")
            
            # Update success count
            await self.update_one('excel_imports', {'id': excel_import['id']}, {
                'success_count': df.shape[0],
                'progress_percentage': 90
            })
            
        except Exception as e:
            logger.error(f"Error processing Excel records: {str(e)}")
            raise DatabaseError(f"Failed to process Excel records: {str(e)}")
    
    async def _get_export_data(self, query_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get data for export based on query configuration"""
        try:
            # Get service container
            service_container = get_service_container()
            
            # Extract export type
            export_type = query_config.get('type', '')
            
            # Get data based on type
            if export_type == 'students':
                student_service = service_container.get_student_service()
                students = await student_service.get_students()
                return [student.__dict__ for student in students]
            elif export_type == 'courses':
                course_service = service_container.get_course_service()
                courses = await course_service.get_courses()
                return [course.__dict__ for course in courses]
            elif export_type == 'feedback':
                feedback_service = service_container.get_feedback_service()
                feedback = await feedback_service.get_feedback()
                return [f.__dict__ for f in feedback]
            elif export_type == 'teachers':
                teacher_service = service_container.get_teacher_service()
                teachers = await teacher_service.get_teachers()
                return [teacher.__dict__ for teacher in teachers]
            else:
                # Default: query based on filters
                # This would be implemented based on specific requirements
                return []
            
        except Exception as e:
            logger.error(f"Error getting export data: {str(e)}")
            raise DatabaseError(f"Failed to get export data: {str(e)}")
    
    async def _create_excel_file(
        self, 
        data: List[Dict[str, Any]], 
        format_type: str, 
        template_id: Optional[str] = None
    ) -> str:
        """Create Excel file from data"""
        try:
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Apply template formatting if provided
            if template_id:
                template = await self.get_template(template_id)
                if template and template.template_content:
                    # Apply template formatting
                    pass
            
            # Generate file path
            export_id = str(uuid.uuid4())
            file_extension = f".{format_type}"
            file_path = self._export_path / f"export_{export_id}{file_extension}"
            
            # Save file
            if format_type == 'csv':
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error creating Excel file: {str(e)}")
            raise DatabaseError(f"Failed to create Excel file: {str(e)}")
    
    # region: Record Processing Methods
    
    async def _process_student_records(self, df: pd.DataFrame, service_container) -> None:
        """Process student records"""
        student_service = service_container.get_student_service()
        
        for index, row in df.iterrows():
            try:
                await student_service.create_student(
                    student_id=row.get('student_id', ''),
                    full_name=row.get('full_name', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    department=row.get('department', ''),
                    program=row.get('program', ''),
                    year=row.get('year', 1)
                )
            except Exception as e:
                logger.warning(f"Failed to process student record {index}: {str(e)}")
    
    async def _process_course_records(self, df: pd.DataFrame, service_container) -> None:
        """Process course records"""
        course_service = service_container.get_course_service()
        
        for index, row in df.iterrows():
            try:
                await course_service.create_course(
                    course_id=row.get('course_id', ''),
                    course_name=row.get('course_name', ''),
                    department=row.get('department', ''),
                    credits=row.get('credits', 3),
                    description=row.get('description', '')
                )
            except Exception as e:
                logger.warning(f"Failed to process course record {index}: {str(e)}")
    
    async def _process_feedback_records(self, df: pd.DataFrame, service_container) -> None:
        """Process feedback records"""
        feedback_service = service_container.get_feedback_service()
        
        for index, row in df.iterrows():
            try:
                await feedback_service.create_feedback(
                    student_id=row.get('student_id', ''),
                    course_id=row.get('course_id', ''),
                    feedback_data={
                        'feedback_type': row.get('feedback_type', 'overall'),
                        'rating': row.get('rating', 0),
                        'comments': row.get('comments', '')
                    },
                    teacher_id=row.get('teacher_id', '')
                )
            except Exception as e:
                logger.warning(f"Failed to process feedback record {index}: {str(e)}")
    
    async def _process_marks_records(self, df: pd.DataFrame, service_container) -> None:
        """Process marks records"""
        # This would integrate with the marks service
        marks_service = service_container.get_marks_service() if hasattr(service_container, 'get_marks_service') else None
        
        if not marks_service:
            raise ValidationError("Marks service not available")
        
        for index, row in df.iterrows():
            try:
                await marks_service.create_mark(
                    student_id=row.get('student_id', ''),
                    course_id=row.get('course_id', ''),
                    marks=row.get('marks', 0),
                    grade=row.get('grade', ''),
                    exam_type=row.get('exam_type', 'midterm')
                )
            except Exception as e:
                logger.warning(f"Failed to process marks record {index}: {str(e)}")
    
    async def _process_attendance_records(self, df: pd.DataFrame, service_container) -> None:
        """Process attendance records"""
        # This would integrate with the attendance service
        attendance_service = service_container.get_attendance_service() if hasattr(service_container, 'get_attendance_service') else None
        
        if not attendance_service:
            raise ValidationError("Attendance service not available")
        
        for index, row in df.iterrows():
            try:
                await attendance_service.create_attendance(
                    student_id=row.get('student_id', ''),
                    course_id=row.get('course_id', ''),
                    date=row.get('date', ''),
                    status=row.get('status', 'present')
                )
            except Exception as e:
                logger.warning(f"Failed to process attendance record {index}: {str(e)}")
    
    async def _process_teacher_records(self, df: pd.DataFrame, service_container) -> None:
        """Process teacher records"""
        # This would integrate with the teacher service
        teacher_service = service_container.get_teacher_service() if hasattr(service_container, 'get_teacher_service') else None
        
        if not teacher_service:
            raise ValidationError("Teacher service not available")
        
        for index, row in df.iterrows():
            try:
                await teacher_service.create_teacher(
                    teacher_id=row.get('teacher_id', ''),
                    full_name=row.get('full_name', ''),
                    email=row.get('email', ''),
                    department=row.get('department', ''),
                    specialization=row.get('specialization', '')
                )
            except Exception as e:
                logger.warning(f"Failed to process teacher record {index}: {str(e)}")
    
    # region: Helper Methods
    
    async def _start_validation_job(self, import_id: str) -> None:
        """Start a validation job for an import"""
        try:
            job = ExcelJob(
                job_name=f"Excel Validation {import_id}",
                job_type="validation",
                job_config={
                    'import_id': import_id,
                    'operation': 'validate'
                },
                priority=3,
                requested_by="system"
            )
            
            await self.insert_one('excel_jobs', job.__dict__)
            
        except Exception as e:
            logger.error(f"Error starting validation job: {str(e)}")
            raise DatabaseError(f"Failed to start validation job: {str(e)}")
    
    async def _mark_job_failed(self, job: ExcelJob, error_message: str) -> None:
        """Mark a job as failed"""
        try:
            await self.update_one('excel_jobs', {'id': job.id}, {
                'status': 'failed',
                'error_message': error_message,
                'completed_at': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error marking job failed: {str(e)}")
    
    async def _has_admin_privileges(self, user_id: str) -> bool:
        """Check if user has admin privileges"""
        # This would check user permissions
        return False  # Placeholder
    
    def _get_template_type_for_import_type(self, import_type: str) -> Optional[ExcelTemplateType]:
        """Get template type for import type"""
        mapping = {
            'students': ExcelTemplateType.STUDENT_REGISTRATION,
            'courses': ExcelTemplateType.COURSE_UPLOAD,
            'feedback': ExcelTemplateType.FEEDBACK_COLLECTION,
            'marks': ExcelTemplateType.MARKS_ENTRY,
            'attendance': ExcelTemplateType.ATTENDANCE_UPLOAD,
            'teachers': ExcelTemplateType.TEACHER_ALLOCATION
        }
        return mapping.get(import_type)
    
    # region: Validation Methods
    
    def _validate_email(self, email: str) -> None:
        """Validate email address"""
        if not email:
            return
        
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError(f"Invalid email format: {email}")
    
    def _validate_phone(self, phone: str) -> None:
        """Validate phone number"""
        if not phone:
            return
        
        # Basic phone validation - can be enhanced
        if len(phone.strip()) < 10:
            raise ValidationError(f"Invalid phone number: {phone}")
    
    def _validate_student_id(self, student_id: str) -> None:
        """Validate student ID"""
        if not student_id:
            raise ValidationError("Student ID is required")
        
        if len(student_id.strip()) < 3:
            raise ValidationError("Student ID must be at least 3 characters")
    
    def _validate_course_id(self, course_id: str) -> None:
        """Validate course ID"""
        if not course_id:
            raise ValidationError("Course ID is required")
        
        if len(course_id.strip()) < 3:
            raise ValidationError("Course ID must be at least 3 characters")
    
    def _validate_marks(self, marks: Any) -> None:
        """Validate marks"""
        if marks is None:
            raise ValidationError("Marks cannot be null")
        
        try:
            marks_float = float(marks)
            if marks_float < 0 or marks_float > 100:
                raise ValidationError("Marks must be between 0 and 100")
        except (ValueError, TypeError):
            raise ValidationError("Marks must be a valid number")
    
    def _validate_rating(self, rating: Any) -> None:
        """Validate rating"""
        if rating is None:
            raise ValidationError("Rating cannot be null")
        
        try:
            rating_float = float(rating)
            if rating_float < 0 or rating_float > 5:
                raise ValidationError("Rating must be between 0 and 5")
        except (ValueError, TypeError):
            raise ValidationError("Rating must be a valid number")