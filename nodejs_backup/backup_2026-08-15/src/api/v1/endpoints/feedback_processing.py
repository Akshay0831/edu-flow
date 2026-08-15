"""
Feedback Processing API Endpoints

This module provides REST API endpoints for feedback processing:
- Feedback collection and management
- Automated analysis and response management
- Report generation and analytics
- Campaign management
- Excel integration for bulk operations

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import io
import json

from src.api.deps import get_db, get_current_user, get_service_container
from src.services.feedback_service import FeedbackService
from src.core.response_handler import ResponseFormatter
from src.core.exceptions import ValidationError, NotFoundError
from src.models.feedback import FeedbackStatus, FeedbackResponseStatus
from src.core.service_container import ServiceContainer

router = APIRouter(prefix="/feedback", tags=["Feedback Processing"])

# region: Basic CRUD Endpoints
@router.post("/submit", response_model=Dict[str, Any])
async def submit_feedback(
    feedback_data: Dict[str, Any],
    anonymous: bool = False,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """
    Submit student feedback
    
    **Required:**
    - student_id: Student ID (can be provided via user context)
    - course_id: Course ID
    - feedback_type: Type of feedback (course_content, teaching_method, assessment, infrastructure, administration, overall)
    
    **Optional:**
    - teacher_id: Teacher ID
    - rating: Rating (0-5)
    - overall_rating: Overall rating (0-5)
    - comments: Free text feedback
    - strengths: What was good
    - improvements: Suggestions for improvement
    - scale: Rating scale (five_point, ten_point, likert_scale)
    - ratings: Multiple rating aspects
    """
    
    # Extract student_id from current_user if not provided
    if "student_id" not in feedback_data:
        feedback_data["student_id"] = current_user.get("user_id")
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        feedback = await feedback_service.create_feedback(
            student_id=feedback_data["student_id"],
            course_id=feedback_data["course_id"],
            feedback_data=feedback_data,
            teacher_id=feedback_data.get("teacher_id"),
            anonymous=anonymous,
            semester=feedback_data.get("semester"),
            academic_year=feedback_data.get("academic_year")
        )
        
        return ResponseFormatter.success(
            data=feedback.__dict__,
            message="Feedback submitted successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/{feedback_id}", response_model=Dict[str, Any])
async def get_feedback(
    feedback_id: str = Path(..., description="Feedback ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get specific feedback by ID"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        feedback = await feedback_service.get_feedback_by_id(feedback_id)
        
        if not feedback:
            raise NotFoundError(f"Feedback not found: {feedback_id}")
        
        return ResponseFormatter.success(
            data=feedback.__dict__,
            message="Feedback retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feedback: {str(e)}")

@router.get("/", response_model=Dict[str, Any])
async def get_feedback_list(
    student_id: Optional[str] = Query(None, description="Student ID filter"),
    course_id: Optional[str] = Query(None, description="Course ID filter"),
    teacher_id: Optional[str] = Query(None, description="Teacher ID filter"),
    semester: Optional[str] = Query(None, description="Semester filter"),
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    feedback_type: Optional[str] = Query(None, description="Feedback type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    min_rating: Optional[float] = Query(None, description="Minimum rating filter"),
    max_rating: Optional[float] = Query(None, description="Maximum rating filter"),
    limit: int = Query(100, description="Maximum number of results"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get feedback list with optional filters"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        feedback_list = await feedback_service.get_feedback(
            student_id=student_id,
            course_id=course_id,
            teacher_id=teacher_id,
            semester=semester,
            academic_year=academic_year,
            feedback_type=feedback_type,
            status=status,
            min_rating=min_rating,
            max_rating=max_rating,
            limit=limit
        )
        
        return ResponseFormatter.success(
            data=[feedback.__dict__ for feedback in feedback_list],
            message=f"Found {len(feedback_list)} feedback records"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving feedback: {str(e)}")

@router.put("/{feedback_id}", response_model=Dict[str, Any])
async def update_feedback(
    feedback_id: str = Path(..., description="Feedback ID"),
    updates: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Update feedback (for partial corrections or status changes)"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        feedback = await feedback_service.update_feedback(feedback_id, updates)
        
        return ResponseFormatter.success(
            data=feedback.__dict__,
            message="Feedback updated successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")

# region: Analysis and Response Management
@router.post("/{feedback_id}/analyze", response_model=Dict[str, Any])
async def analyze_feedback(
    feedback_id: str = Path(..., description="Feedback ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Manually trigger feedback analysis"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        feedback = await feedback_service.get_feedback_by_id(feedback_id)
        
        if not feedback:
            raise NotFoundError(f"Feedback not found: {feedback_id}")
        
        # Run analysis
        await feedback_service._analyze_feedback(feedback_id)
        await feedback_service._generate_response_suggestion(feedback_id)
        await feedback_service._calculate_priority_score(feedback_id)
        
        # Update feedback
        feedback = await feedback_service.get_feedback_by_id(feedback_id)
        
        return ResponseFormatter.success(
            data=feedback.__dict__,
            message="Feedback analyzed successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing feedback: {str(e)}")

@router.post("/{feedback_id}/response", response_model=Dict[str, Any])
async def create_response(
    feedback_id: str = Path(..., description="Feedback ID"),
    response_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Create teacher response to feedback"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        response = await feedback_service.create_response(
            feedback_id=feedback_id,
            teacher_id=current_user.get("user_id"),
            response_data=response_data,
            course_id=response_data.get("course_id")
        )
        
        return ResponseFormatter.success(
            data=response.__dict__,
            message="Feedback response created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating response: {str(e)}")

@router.put("/responses/{response_id}/approve", response_model=Dict[str, Any])
async def approve_response(
    response_id: str = Path(..., description="Response ID"),
    approval_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Approve feedback response"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        response = await feedback_service.approve_response(
            response_id=response_id,
            approver_id=current_user.get("user_id"),
            approval_comments=approval_data.get("approval_comments")
        )
        
        return ResponseFormatter.success(
            data=response.__dict__,
            message="Response approved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving response: {str(e)}")

# region: Report Generation
@router.post("/reports/generate", response_model=Dict[str, Any])
async def generate_feedback_report(
    report_config: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Generate comprehensive feedback report"""
    
    required_fields = ["report_type", "generated_by"]
    for field in required_fields:
        if field not in report_config:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        report = await feedback_service.generate_feedback_report(
            report_config=report_config,
            academic_year=report_config.get("academic_year"),
            semester=report_config.get("semester"),
            course_id=report_config.get("course_id"),
            teacher_id=report_config.get("teacher_id")
        )
        
        return ResponseFormatter.success(
            data=report.__dict__,
            message="Feedback report generated successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_feedback_report(
    report_id: str = Path(..., description="Report ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get generated feedback report"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        from src.models.feedback import FeedbackReport
        report = db.query(FeedbackReport).filter(
            FeedbackReport.id == report_id
        ).first()
        
        if not report:
            raise NotFoundError(f"Report not found: {report_id}")
        
        return ResponseFormatter.success(
            data=report.__dict__,
            message="Feedback report retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

@router.get("/reports/download/{report_id}")
async def download_feedback_report(
    report_id: str = Path(..., description="Report ID"),
    format: str = Query("html", description="Download format (html, pdf, json)"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> FileResponse:
    """Download feedback report in specified format"""
    
    try:
        from src.models.feedback import FeedbackReport
        report = db.query(FeedbackReport).filter(
            FeedbackReport.id == report_id
        ).first()
        
        if not report:
            raise NotFoundError(f"Report not found: {report_id}")
        
        # Placeholder for actual file generation
        filename = f"feedback_report_{report_id}.{format}"
        file_path = f"/tmp/{filename}"  # Placeholder path
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type={"html": "text/html", "pdf": "application/pdf", "json": "application/json"}[format]
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

# region: Campaign Management
@router.post("/campaigns", response_model=Dict[str, Any])
async def create_feedback_campaign(
    campaign_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Create feedback collection campaign"""
    
    required_fields = ["name", "description", "academic_year", "semester", "start_date", "end_date", "campaign_config"]
    for field in required_fields:
        if field not in campaign_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Convert date strings to datetime objects
    start_date = datetime.fromisoformat(campaign_data["start_date"])
    end_date = datetime.fromisoformat(campaign_data["end_date"])
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        campaign = await feedback_service.create_campaign(
            name=campaign_data["name"],
            description=campaign_data["description"],
            academic_year=campaign_data["academic_year"],
            semester=campaign_data["semester"],
            start_date=start_date,
            end_date=end_date,
            campaign_config=campaign_data["campaign_config"]
        )
        
        return ResponseFormatter.success(
            data=campaign.__dict__,
            message="Feedback campaign created successfully",
            status_code=201
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating campaign: {str(e)}")

@router.get("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def get_feedback_campaign(
    campaign_id: str = Path(..., description="Campaign ID"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get feedback campaign details"""
    
    try:
        from src.models.feedback import FeedbackCampaign
        campaign = db.query(FeedbackCampaign).filter(
            FeedbackCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise NotFoundError(f"Campaign not found: {campaign_id}")
        
        return ResponseFormatter.success(
            data=campaign.__dict__,
            message="Feedback campaign retrieved successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving campaign: {str(e)}")

@router.get("/campaigns/{campaign_id}/responses", response_model=Dict[str, Any])
async def get_campaign_responses(
    campaign_id: str = Path(..., description="Campaign ID"),
    limit: int = Query(100, description="Maximum number of responses"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get responses for a specific campaign"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        responses = await feedback_service.get_campaign_responses(campaign_id, limit)
        
        return ResponseFormatter.success(
            data=[response.__dict__ for response in responses],
            message=f"Found {len(responses)} responses for campaign"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving campaign responses: {str(e)}")

@router.post("/campaigns/{campaign_id}/report", response_model=Dict[str, Any])
async def generate_campaign_report(
    campaign_id: str = Path(..., description="Campaign ID"),
    report_config: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Generate campaign-specific report"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        report_data = await feedback_service.generate_campaign_report(
            campaign_id=campaign_id,
            include_responses=report_config.get("include_responses", False),
            include_anonymized=report_config.get("include_anonymized", True)
        )
        
        return ResponseFormatter.success(
            data=report_data,
            message="Campaign report generated successfully"
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating campaign report: {str(e)}")

# region: Analytics and Statistics
@router.get("/analytics/course/{course_id}", response_model=Dict[str, Any])
async def get_course_feedback_analytics(
    course_id: str = Path(..., description="Course ID"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get feedback analytics for a course"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        # Get feedback data
        feedback_list = await feedback_service.get_feedback(
            course_id=course_id,
            academic_year=academic_year,
            semester=semester
        )
        
        # Calculate analytics
        analytics = {
            "course_id": course_id,
            "academic_year": academic_year or datetime.now().year,
            "semester": semester or "current",
            "total_feedback": len(feedback_list),
            "average_rating": sum(f.rating for f in feedback_list if f.rating is not None) / len([f for f in feedback_list if f.rating is not None]) or 0,
            "rating_distribution": _get_rating_distribution(feedback_list),
            "sentiment_distribution": _get_sentiment_distribution(feedback_list),
            "feedback_type_distribution": _get_feedback_type_distribution(feedback_list),
            "response_rate": len([f for f in feedback_list if f.responses]) / len(feedback_list) * 100 if feedback_list else 0,
            "average_response_time": _calculate_average_response_time(feedback_list)
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="Course feedback analytics generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@router.get("/analytics/teacher/{teacher_id}", response_model=Dict[str, Any])
async def get_teacher_feedback_analytics(
    teacher_id: str = Path(..., description="Teacher ID"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get feedback analytics for a teacher"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        # Get feedback data
        feedback_list = await feedback_service.get_feedback(
            teacher_id=teacher_id,
            academic_year=academic_year,
            semester=semester
        )
        
        # Calculate analytics
        analytics = {
            "teacher_id": teacher_id,
            "academic_year": academic_year or datetime.now().year,
            "semester": semester or "current",
            "total_feedback": len(feedback_list),
            "average_rating": sum(f.rating for f in feedback_list if f.rating is not None) / len([f for f in feedback_list if f.rating is not None]) or 0,
            "rating_distribution": _get_rating_distribution(feedback_list),
            "sentiment_distribution": _get_sentiment_distribution(feedback_list),
            "feedback_type_distribution": _get_feedback_type_distribution(feedback_list),
            "response_rate": len([f for f in feedback_list if f.responses]) / len(feedback_list) * 100 if feedback_list else 0,
            "improvement_areas": _identify_improvement_areas(feedback_list)
        }
        
        return ResponseFormatter.success(
            data=analytics,
            message="Teacher feedback analytics generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@router.get("/analytics/trends", response_model=Dict[str, Any])
async def get_feedback_trends(
    academic_year: Optional[str] = Query(None, description="Academic year"),
    semester: Optional[str] = Query(None, description="Semester"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Get feedback trends over time"""
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        # Get feedback data
        feedback_list = await feedback_service.get_feedback(
            academic_year=academic_year,
            semester=semester
        )
        
        # Calculate trends
        trends = {
            "academic_year": academic_year or datetime.now().year,
            "semester": semester or "current",
            "feedback_volume_trend": _calculate_feedback_volume_trend(feedback_list),
            "rating_trend": _calculate_rating_trend(feedback_list),
            "sentiment_trend": _calculate_sentiment_trend(feedback_list),
            "response_rate_trend": _calculate_response_rate_trend(feedback_list),
            "common_issues": _identify_common_issues(feedback_list)
        }
        
        return ResponseFormatter.success(
            data=trends,
            message="Feedback trends generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trends: {str(e)}")

# region: Excel Integration
@router.post("/upload", response_model=Dict[str, Any])
async def upload_feedback_excel(
    file: UploadFile = File(..., description="Excel file with feedback data"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Upload and process feedback from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        # Read Excel file (placeholder - implement actual Excel processing)
        excel_data = await _process_excel_file(file)
        
        # Process feedback data
        processed_count = 0
        errors = []
        
        for feedback_record in excel_data:
            try:
                await feedback_service.create_feedback(
                    student_id=feedback_record["student_id"],
                    course_id=feedback_record["course_id"],
                    feedback_data=feedback_record,
                    teacher_id=feedback_record.get("teacher_id"),
                    semester=feedback_record.get("semester"),
                    academic_year=feedback_record.get("academic_year")
                )
                processed_count += 1
            except Exception as e:
                errors.append({
                    "record": feedback_record,
                    "error": str(e)
                })
        
        result = {
            "processed_count": processed_count,
            "error_count": len(errors),
            "errors": errors,
            "message": f"Successfully processed {processed_count} feedback records"
        }
        
        return ResponseFormatter.success(
            data=result,
            message="Excel file processed successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@router.get("/export", response_model=Dict[str, Any])
async def export_feedback_data(
    export_config_json: str = Query(..., description="Export configuration as JSON string"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service_container: ServiceContainer = Depends(get_service_container)
) -> JSONResponse:
    """Export feedback data to Excel"""
    
    try:
        import json
        export_config = json.loads(export_config_json)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in export_config: {str(e)}"
        )
    
    required_fields = ["format", "filters"]
    for field in required_fields:
        if field not in export_config:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    feedback_service = service_container.get_feedback_service()
    
    try:
        # Get filtered feedback data
        feedback_list = await feedback_service.get_feedback(
            academic_year=export_config.get("filters", {}).get("academic_year"),
            semester=export_config.get("filters", {}).get("semester"),
            course_id=export_config.get("filters", {}).get("course_id"),
            teacher_id=export_config.get("filters", {}).get("teacher_id")
        )
        
        # Generate export file (placeholder)
        export_filename = f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        export_url = f"/downloads/{export_filename}"
        
        result = {
            "export_filename": export_filename,
            "export_url": export_url,
            "format": export_config["format"],
            "record_count": len(feedback_list),
            "filters": export_config.get("filters", {}),
            "message": f"Exported {len(feedback_list)} feedback records"
        }
        
        return ResponseFormatter.success(
            data=result,
            message="Feedback data exported successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

# region: Helper Methods
def _get_rating_distribution(feedback_list: List) -> Dict[str, int]:
    """Get distribution of ratings"""
    distribution = {
        "5": 0, "4": 0, "3": 0, "2": 0, "1": 0,
        "no_rating": 0
    }
    
    for feedback in feedback_list:
        if feedback.rating is not None:
            rating_key = str(int(feedback.rating))
            if rating_key in distribution:
                distribution[rating_key] += 1
            else:
                distribution["no_rating"] += 1
        else:
            distribution["no_rating"] += 1
    
    return distribution

def _get_sentiment_distribution(feedback_list: List) -> Dict[str, int]:
    """Get distribution of sentiments"""
    distribution = {
        "very_positive": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "very_negative": 0,
        "no_sentiment": 0
    }
    
    for feedback in feedback_list:
        sentiment = feedback.sentiment_category
        if sentiment:
            if sentiment in distribution:
                distribution[sentiment] += 1
            else:
                distribution["no_sentiment"] += 1
        else:
            distribution["no_sentiment"] += 1
    
    return distribution

def _get_feedback_type_distribution(feedback_list: List) -> Dict[str, int]:
    """Get distribution of feedback types"""
    distribution = {}
    
    for feedback in feedback_list:
        feedback_type = feedback.feedback_type
        distribution[feedback_type] = distribution.get(feedback_type, 0) + 1
    
    return distribution

def _calculate_average_response_time(feedback_list: List) -> float:
    """Calculate average response time in days"""
    response_times = []
    
    for feedback in feedback_list:
        if feedback.responses:
            for response in feedback.responses:
                if response.response_date:
                    response_time = (response.response_date - feedback.submission_date).days
                    response_times.append(response_time)
    
    return sum(response_times) / len(response_times) if response_times else 0.0

def _identify_improvement_areas(feedback_list: List) -> List[str]:
    """Identify areas needing improvement based on feedback"""
    improvement_areas = []
    
    for feedback in feedback_list:
        if feedback.rating is not None and feedback.rating < 3.0:
            improvement_areas.append(feedback.feedback_type)
    
    return list(set(improvement_areas))  # Remove duplicates

def _calculate_feedback_volume_trend(feedback_list: List) -> str:
    """Calculate feedback volume trend"""
    if len(feedback_list) < 10:
        return "insufficient_data"
    elif len(feedback_list) > 50:
        return "high_volume"
    elif len(feedback_list) > 25:
        return "medium_volume"
    else:
        return "low_volume"

def _calculate_rating_trend(feedback_list: List) -> str:
    """Calculate rating trend"""
    if not feedback_list:
        return "no_data"
    
    ratings = [f.rating for f in feedback_list if f.rating is not None]
    if not ratings:
        return "no_ratings"
    
    avg_rating = sum(ratings) / len(ratings)
    
    if avg_rating >= 4.0:
        return "high_satisfaction"
    elif avg_rating >= 3.0:
        return "moderate_satisfaction"
    else:
        return "low_satisfaction"

def _calculate_sentiment_trend(feedback_list: List) -> str:
    """Calculate sentiment trend"""
    if not feedback_list:
        return "no_data"
    
    positive_sentiments = [f for f in feedback_list if f.sentiment_category in ["positive", "very_positive"]]
    negative_sentiments = [f for f in feedback_list if f.sentiment_category in ["negative", "very_negative"]]
    
    total = len(feedback_list)
    if total == 0:
        return "no_data"
    
    positive_ratio = len(positive_sentiments) / total
    negative_ratio = len(negative_sentiments) / total
    
    if positive_ratio > negative_ratio:
        return "improving"
    elif negative_ratio > positive_ratio:
        return "declining"
    else:
        return "stable"

def _calculate_response_rate_trend(feedback_list: List) -> str:
    """Calculate response rate trend"""
    if not feedback_list:
        return "no_data"
    
    responded_feedback = [f for f in feedback_list if f.responses]
    response_rate = len(responded_feedback) / len(feedback_list)
    
    if response_rate >= 0.8:
        return "high_response_rate"
    elif response_rate >= 0.5:
        return "medium_response_rate"
    else:
        return "low_response_rate"

def _identify_common_issues(feedback_list: List) -> List[str]:
    """Identify common issues from feedback"""
    issues = []
    
    for feedback in feedback_list:
        if feedback.rating is not None and feedback.rating < 3.0:
            issues.append(feedback.feedback_type)
    
    issue_counts = {}
    for issue in issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    # Return most common issues
    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    return [issue for issue, count in sorted_issues[:3]]

async def _process_excel_file(file: UploadFile) -> List[Dict[str, Any]]:
    """Process Excel file and extract feedback data (placeholder)"""
    # This would implement actual Excel processing
    # For now, return empty list
    return []