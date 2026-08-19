"""
Excel Integration API Endpoints

This module provides REST API endpoints for Excel operations:
- Import operations with validation and processing
- Export operations with multiple format support
- Template management
- Job management and monitoring
- File download and validation

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid

from core.dependencies import get_current_user, get_current_active_admin
from core.exceptions import ValidationError, NotFoundError, DatabaseError
from core.response_handler import ResponseFormatter
from core.database_abstraction import DatabaseInterface
from src.services.excel_integration_service import ExcelIntegrationService
from models.excel_integration import (
    ExcelImport, ExcelExport, ExcelTemplate, ExcelJob,
    ExcelImportStatus, ExcelExportStatus, ExcelTemplateType,
    ExcelValidationError, ExcelProcessingLog
)

router = APIRouter(prefix="/excel", tags=["excel_integration"])
excel_service = ExcelIntegrationService()


# region: Import Operations

@router.post("/imports", response_model=Dict[str, Any])
async def upload_excel_file(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    user_id: str = Depends(get_current_user),
    template_id: Optional[str] = Form(None),
    description: Optional[str] = Form(""),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Upload an Excel file for import processing
    
    Args:
        file: Excel file to upload (xlsx, xls, csv)
        import_type: Type of import (students, courses, feedback, marks, attendance, teachers)
        user_id: Current user ID (from authentication)
        template_id: Optional template ID for validation
        description: Optional description of the import
    
    Returns:
        ExcelImport: Import record with initial status
    """
    try:
        # Import configuration
        import_config = {
            'description': description,
            'process_errors': True,
            'validation_level': 'strict'
        }
        
        # Process file upload
        excel_import = await excel_service.upload_excel_file(
            file=file,
            import_type=import_type,
            user_id=user_id,
            template_id=template_id,
            import_config=import_config
        )
        
        return ResponseFormatter.success(
            data=excel_import.__dict__,
            message="Excel file uploaded successfully",
            code="EXCEL_UPLOAD_SUCCESS"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/imports/{import_id}", response_model=Dict[str, Any])
async def get_import_status(
    import_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the status of an import operation
    
    Args:
        import_id: Import ID to check
        user_id: Current user ID (from authentication)
    
    Returns:
        Import operation status and progress
    """
    try:
        status = await excel_service.get_import_status(import_id)
        
        return ResponseFormatter.success(
            data=status,
            message="Import status retrieved successfully",
            code="IMPORT_STATUS_RETRIEVED"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.post("/imports/{import_id}/start", response_model=Dict[str, Any])
async def start_import_process(
    import_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start the import process for a validated file
    
    Args:
        import_id: Import ID to start processing
        user_id: Current user ID (from authentication)
    
    Returns:
        Updated import record
    """
    try:
        excel_import = await excel_service.start_import_process(import_id)
        
        return ResponseFormatter.success(
            data=excel_import.__dict__,
            message="Import process started successfully",
            code="IMPORT_STARTED"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.post("/imports/{import_id}/cancel", response_model=Dict[str, Any])
async def cancel_import_process(
    import_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel an ongoing import process
    
    Args:
        import_id: Import ID to cancel
        user_id: Current user ID (from authentication)
    
    Returns:
        Updated import record
    """
    try:
        excel_import = await excel_service.cancel_import_process(import_id, user_id)
        
        return ResponseFormatter.success(
            data=excel_import.__dict__,
            message="Import process cancelled successfully",
            code="IMPORT_CANCELLED"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/imports/{import_id}/errors", response_model=Dict[str, Any])
async def get_import_errors(
    import_id: str,
    user_id: str = Depends(get_current_user),
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Get validation errors for an import
    
    Args:
        import_id: Import ID to check errors for
        user_id: Current user ID (from authentication)
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Paginated list of validation errors
    """
    try:
        # Get validation errors from database
        errors = await excel_service.find_many('excel_validation_errors', {
            'import_id': import_id
        }, page=page, page_size=page_size, sort=[('row_number', 1)])
        
        total_count = await excel_service.count('excel_validation_errors', {'import_id': import_id})
        
        return ResponseFormatter.paginated(
            data=errors,
            total=total_count,
            page=page,
            page_size=page_size,
            message="Validation errors retrieved successfully",
            code="VALIDATION_ERRORS_RETRIEVED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


# region: Export Operations

@router.post("/exports", response_model=Dict[str, Any])
async def create_export_job(
    export_type: str,
    query_config: Dict[str, Any],
    format_type: str = "xlsx",
    user_id: str = Depends(get_current_user),
    template_id: Optional[str] = None,
    description: Optional[str] = ""
) -> Dict[str, Any]:
    """
    Create an export job
    
    Args:
        export_type: Type of export (students, courses, feedback, etc.)
        query_config: Configuration for data query
        format_type: Export format (xlsx, xls, csv)
        user_id: Current user ID (from authentication)
        template_id: Optional template ID for formatting
        description: Optional description of the export
    
    Returns:
        ExcelExport: Export job record
    """
    try:
        # Export configuration
        export_config = {
            'description': description,
            'include_headers': True,
            'auto_filter': True,
            'freeze_headers': True
        }
        
        # Create export job
        excel_export = await excel_service.create_export_job(
            export_type=export_type,
            query_config=query_config,
            user_id=user_id,
            format_type=format_type,
            template_id=template_id,
            export_config=export_config
        )
        
        return ResponseFormatter.success(
            data=excel_export.__dict__,
            message="Export job created successfully",
            code="EXPORT_CREATED"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/exports/{export_id}", response_model=Dict[str, Any])
async def get_export_status(
    export_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the status of an export operation
    
    Args:
        export_id: Export ID to check
        user_id: Current user ID (from authentication)
    
    Returns:
        Export operation status and progress
    """
    try:
        status = await excel_service.get_export_status(export_id)
        
        return ResponseFormatter.success(
            data=status,
            message="Export status retrieved successfully",
            code="EXPORT_STATUS_RETRIEVED"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/exports/{export_id}/download")
async def download_export_file(
    export_id: str,
    user_id: str = Depends(get_current_user)
) -> FileResponse:
    """
    Download an exported Excel file
    
    Args:
        export_id: Export ID to download
        user_id: Current user ID (from authentication)
    
    Returns:
        FileResponse with the exported Excel file
    """
    try:
        # Get file information
        file_info = await excel_service.download_export_file(export_id, user_id)
        
        # Check if file exists
        if not os.path.exists(file_info['file_path']):
            raise NotFoundError("Export file not found")
        
        return FileResponse(
            path=file_info['file_path'],
            filename=file_info['file_name'],
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


# region: Template Management

@router.post("/templates", response_model=Dict[str, Any])
async def create_excel_template(
    template_name: str,
    template_type: str,
    template_file: UploadFile = File(...),
    description: Optional[str] = "",
    field_mapping: Optional[Dict[str, str]] = None,
    validation_rules: Optional[Dict[str, Any]] = None,
    required_fields: Optional[List[str]] = None,
    is_active: bool = True,
    is_default: bool = False,
    user_id: str = Depends(get_current_active_admin)
) -> Dict[str, Any]:
    """
    Create an Excel template
    
    Args:
        template_name: Name of the template
        template_type: Type of template
        template_file: Excel template file
        description: Optional description
        field_mapping: Field mapping configuration
        validation_rules: Validation rules configuration
        required_fields: List of required fields
        is_active: Whether template is active
        is_default: Whether template is default
        user_id: Current user ID (from authentication - admin required)
    
    Returns:
        ExcelTemplate: Created template record
    """
    try:
        # Template configuration
        config = {
            'version': '1.0',
            'is_active': is_active,
            'is_default': is_default,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_file_types': ['.xlsx', '.xls', '.csv'],
            'max_records': 10000,
            'target_system': 'edu_flow',
            'target_module': None
        }
        
        # Create template
        template = await excel_service.create_excel_template(
            template_name=template_name,
            template_type=template_type,
            template_file=template_file,
            description=description,
            field_mapping=field_mapping,
            validation_rules=validation_rules,
            required_fields=required_fields,
            config=config
        )
        
        return ResponseFormatter.success(
            data=template.__dict__,
            message="Excel template created successfully",
            code="TEMPLATE_CREATED"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/templates", response_model=Dict[str, Any])
async def get_templates(
    template_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Excel templates
    
    Args:
        template_type: Optional template type filter
        page: Page number for pagination
        page_size: Number of items per page
        user_id: Current user ID (from authentication)
    
    Returns:
        Paginated list of Excel templates
    """
    try:
        # Build query
        query = {}
        if template_type:
            query['template_type'] = template_type
        
        # Get templates
        templates = await excel_service.find_many('excel_templates', query, page=page, page_size=page_size)
        total_count = await excel_service.count('excel_templates', query)
        
        return ResponseFormatter.paginated(
            data=templates,
            total=total_count,
            page=page,
            page_size=page_size,
            message="Templates retrieved successfully",
            code="TEMPLATES_RETRIEVED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific Excel template
    
    Args:
        template_id: Template ID to retrieve
        user_id: Current user ID (from authentication)
    
    Returns:
        ExcelTemplate: Template record
    """
    try:
        template = await excel_service.get_template(template_id)
        
        if not template:
            raise NotFoundError("Template not found")
        
        return ResponseFormatter.success(
            data=template.__dict__,
            message="Template retrieved successfully",
            code="TEMPLATE_RETRIEVED"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/templates/default/{template_type}", response_model=Dict[str, Any])
async def get_default_template(
    template_type: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get default template for a specific type
    
    Args:
        template_type: Template type to get default for
        user_id: Current user ID (from authentication)
    
    Returns:
        ExcelTemplate: Default template record
    """
    try:
        template = await excel_service.get_default_template(template_type)
        
        if not template:
            raise NotFoundError("No default template found for this type")
        
        return ResponseFormatter.success(
            data=template.__dict__,
            message="Default template retrieved successfully",
            code="DEFAULT_TEMPLATE_RETRIEVED"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.get("/templates/download/{template_id}")
async def download_template_file(
    template_id: str,
    user_id: str = Depends(get_current_user)
) -> FileResponse:
    """
    Download template file
    
    Args:
        template_id: Template ID to download
        user_id: Current user ID (from authentication)
    
    Returns:
        FileResponse with the template Excel file
    """
    try:
        # Get template
        template = await excel_service.get_template(template_id)
        
        if not template:
            raise NotFoundError("Template not found")
        
        # Check if template file exists
        if not os.path.exists(template.template_file_path):
            raise NotFoundError("Template file not found")
        
        return FileResponse(
            path=template.template_file_path,
            filename=f"{template.name}.xlsx",
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.post("/templates/{template_id}/validate", response_model=Dict[str, Any])
async def validate_template_file(
    template_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate a file against a template
    
    Args:
        template_id: Template ID to validate against
        file: Excel file to validate
        user_id: Current user ID (from authentication)
    
    Returns:
        Validation results
    """
    try:
        # Get template
        template = await excel_service.get_template(template_id)
        
        if not template:
            raise NotFoundError("Template not found")
        
        # Validate file against template
        validation_result = await excel_service.validate_file_against_template(
            file=file,
            template=template
        )
        
        return ResponseFormatter.success(
            data=validation_result,
            message="Template validation completed",
            code="TEMPLATE_VALIDATION_COMPLETED"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=ResponseFormatter.error(message=str(e), code="NOT_FOUND"))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


# region: Job Management

@router.get("/jobs", response_model=Dict[str, Any])
async def get_jobs(
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Get Excel jobs
    
    Args:
        job_type: Optional job type filter
        status: Optional status filter
        user_id: Current user ID (from authentication)
        page: Page number for pagination
        page_size: Number of items per page
    
    Returns:
        Paginated list of Excel jobs
    """
    try:
        # Build query
        query = {}
        if job_type:
            query['job_type'] = job_type
        if status:
            query['status'] = status
        
        # Get jobs
        jobs = await excel_service.find_many('excel_jobs', query, page=page, page_size=page_size)
        total_count = await excel_service.count('excel_jobs', query)
        
        return ResponseFormatter.paginated(
            data=jobs,
            total=total_count,
            page=page,
            page_size=page_size,
            message="Jobs retrieved successfully",
            code="JOBS_RETRIEVED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.post("/jobs/process", response_model=Dict[str, Any])
async def process_excel_jobs(
    limit: int = 10,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process pending Excel jobs
    
    Args:
        limit: Maximum number of jobs to process
        user_id: Current user ID (from authentication)
    
    Returns:
        List of processed jobs
    """
    try:
        processed_jobs = await excel_service.process_excel_jobs(limit=limit)
        
        return ResponseFormatter.success(
            data=[job.__dict__ for job in processed_jobs],
            message="Excel jobs processed successfully",
            code="JOBS_PROCESSED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


# region: Configuration Management

@router.get("/config", response_model=Dict[str, Any])
async def get_excel_config(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get Excel integration configuration
    
    Args:
        user_id: Current user ID (from authentication)
    
    Returns:
        Excel configuration settings
    """
    try:
        config = await excel_service.get_excel_config()
        
        return ResponseFormatter.success(
            data=config,
            message="Excel configuration retrieved successfully",
            code="CONFIG_RETRIEVED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


@router.post("/config", response_model=Dict[str, Any])
async def update_excel_config(
    config: Dict[str, Any],
    user_id: str = Depends(get_current_active_admin)
) -> Dict[str, Any]:
    """
    Update Excel integration configuration
    
    Args:
        config: Configuration settings to update
        user_id: Current user ID (from authentication - admin required)
    
    Returns:
        Updated configuration
    """
    try:
        updated_config = await excel_service.update_excel_config(config, user_id)
        
        return ResponseFormatter.success(
            data=updated_config,
            message="Excel configuration updated successfully",
            code="CONFIG_UPDATED"
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=ResponseFormatter.error(message=str(e), code="VALIDATION_ERROR"))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))


# region: Health Check

@router.get("/health", response_model=Dict[str, Any])
async def check_excel_health(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Check Excel integration system health
    
    Args:
        user_id: Current user ID (from authentication)
    
    Returns:
        System health status
    """
    try:
        # Check system components
        health_status = {
            'status': 'healthy',
            'components': {
                'file_storage': True,
                'database': True,
                'validation': True,
                'processing': True,
                'exports': True,
                'templates': True
            },
            'metrics': {
                'pending_jobs': 0,
                'active_imports': 0,
                'active_exports': 0,
                'template_count': 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get actual metrics
        pending_jobs = await excel_service.count('excel_jobs', {'status': 'pending'})
        active_imports = await excel_service.count('excel_imports', {'status': 'processing'})
        active_exports = await excel_service.count('excel_exports', {'status': 'processing'})
        template_count = await excel_service.count('excel_templates', {'is_active': True})
        
        health_status['metrics'] = {
            'pending_jobs': pending_jobs,
            'active_imports': active_imports,
            'active_exports': active_exports,
            'template_count': template_count
        }
        
        return ResponseFormatter.success(
            data=health_status,
            message="Excel system health check completed",
            code="HEALTH_CHECK_COMPLETED"
        )
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message=str(e), code="DATABASE_ERROR"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=ResponseFormatter.error(message="Internal server error", code="INTERNAL_ERROR"))