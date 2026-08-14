"""
Mark Management Service

This module provides business logic for mark management:
- Mark creation and management
- Grade calculation and analysis
- Mark validation and verification
- Mark reporting and analytics
- Bulk operations
- Grade conversion and scaling

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4
import statistics

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.base_service import BaseService
from src.infrastructure.repositories.mark_repository import MarkRepository
from src.models.mark_model import MarkCreate, MarkUpdate, MarkResponse, MarkStats, GradeDistribution

logger = get_logger(__name__)


class MarkService(BaseService):
    """Mark management service with comprehensive functionality."""
    
    def __init__(self, mark_repository: MarkRepository):
        super().__init__()
        self.mark_repository = mark_repository
        self._cache = {}
    
    async def initialize(self) -> None:
        """Initialize the mark service."""
        try:
            await super().initialize()
            logger.info("Mark service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mark service: {str(e)}")
            raise
    
    async def dispose(self) -> None:
        """Dispose the mark service."""
        try:
            await super().dispose()
            self._cache.clear()
            logger.info("Mark service disposed successfully")
        except Exception as e:
            logger.error(f"Failed to dispose mark service: {str(e)}")
            raise
    
    # Core Business Operations
    
    async def create_mark(self, mark_data: Dict[str, Any]) -> MarkResponse:
        """Create a new mark with business logic validation."""
        try:
            # Validate mark data
            await self._validate_mark_creation(mark_data)
            
            # Check if mark already exists
            existing_mark = await self.mark_repository.get_by_student_assessment(
                mark_data['student_id'], 
                mark_data['assessment_id']
            )
            if existing_mark:
                raise ConflictError(f"Mark for student {mark_data['student_id']} in assessment {mark_data['assessment_id']} already exists")
            
            # Create mark
            mark = await self.mark_repository.create(**mark_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Update student grade if needed
            await self._update_student_grade(mark_data['student_id'])
            
            return mark
            
        except Exception as e:
            logger.error(f"Failed to create mark: {str(e)}")
            raise
    
    async def update_mark(self, mark_id: str, mark_data: Dict[str, Any]) -> Optional[MarkResponse]:
        """Update an existing mark with business logic."""
        try:
            # Validate mark exists
            mark = await self.mark_repository.get_by_id(mark_id)
            if not mark:
                raise NotFoundError(f"Mark not found with ID: {mark_id}")
            
            # Validate update data
            await self._validate_mark_update(mark_data)
            
            # Update mark
            updated_mark = await self.mark_repository.update(mark_id, **mark_data)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Update student grade if needed
            await self._update_student_grade(mark.student_id)
            
            return updated_mark
            
        except Exception as e:
            logger.error(f"Failed to update mark {mark_id}: {str(e)}")
            raise
    
    async def get_mark(self, mark_id: str) -> Optional[MarkResponse]:
        """Get a mark by ID with caching."""
        try:
            # Check cache first
            if mark_id in self._cache:
                return self._cache[mark_id]
            
            # Get mark from repository
            mark = await self.mark_repository.get_by_id(mark_id)
            
            if mark:
                # Cache the result
                self._cache[mark_id] = mark
            
            return mark
            
        except Exception as e:
            logger.error(f"Failed to get mark {mark_id}: {str(e)}")
            raise
    
    async def delete_mark(self, mark_id: str) -> bool:
        """Delete a mark with business logic."""
        try:
            # Validate mark exists
            mark = await self.mark_repository.get_by_id(mark_id)
            if not mark:
                raise NotFoundError(f"Mark not found with ID: {mark_id}")
            
            # Delete mark
            result = await self.mark_repository.delete(mark_id)
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Update student grade if needed
            await self._update_student_grade(mark.student_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete mark {mark_id}: {str(e)}")
            raise
    
    # Search and Filtering
    
    async def search_marks(self, search_term: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Search for marks by student name, assessment name, or mark."""
        try:
            marks = await self.mark_repository.search_marks(
                search_term=search_term,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to search marks: {str(e)}")
            raise
    
    async def get_marks_by_student(self, student_id: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get all marks for a student."""
        try:
            marks = await self.mark_repository.get_by_student(
                student_id=student_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for student {student_id}: {str(e)}")
            raise
    
    async def get_marks_by_assessment(self, assessment_id: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get all marks for an assessment."""
        try:
            marks = await self.mark_repository.get_by_assessment(
                assessment_id=assessment_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for assessment {assessment_id}: {str(e)}")
            raise
    
    async def get_marks_by_course(self, course_id: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get all marks for a course."""
        try:
            marks = await self.mark_repository.get_by_course(
                course_id=course_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for course {course_id}: {str(e)}")
            raise
    
    async def get_marks_by_class(self, class_id: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get all marks for a class."""
        try:
            marks = await self.mark_repository.get_by_class(
                class_id=class_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for class {class_id}: {str(e)}")
            raise
    
    async def get_marks_by_teacher(self, teacher_id: str, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get all marks graded by a teacher."""
        try:
            marks = await self.mark_repository.get_by_teacher(
                teacher_id=teacher_id,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for teacher {teacher_id}: {str(e)}")
            raise
    
    async def get_marks_by_date_range(self, start_date: date, end_date: date, skip: int = 0, limit: int = 100) -> List[MarkResponse]:
        """Get marks within a date range."""
        try:
            marks = await self.mark_repository.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                skip=skip,
                limit=limit
            )
            
            # Cache results
            for mark in marks:
                self._cache[mark.id] = mark
            
            return marks
            
        except Exception as e:
            logger.error(f"Failed to get marks for date range: {str(e)}")
            raise
    
    # Grade Management
    
    async def calculate_final_grade(self, student_id: str, course_id: str) -> Optional[Dict[str, Any]]:
        """Calculate final grade for a student in a course."""
        try:
            # Get all marks for student in course
            marks = await self.get_marks_by_course(course_id, 0, 1000)
            student_marks = [m for m in marks if m.student_id == student_id]
            
            if not student_marks:
                return None
            
            # Calculate weighted average
            weighted_sum = 0
            total_weight = 0
            
            for mark in student_marks:
                weight = mark.weight or 0
                mark_value = mark.mark_value or 0
                weighted_sum += mark_value * weight
                total_weight += weight
            
            if total_weight == 0:
                return None
            
            final_mark = weighted_sum / total_weight
            
            # Convert to letter grade
            letter_grade = self._convert_to_letter_grade(final_mark)
            
            return {
                "student_id": student_id,
                "course_id": course_id,
                "final_mark": round(final_mark, 2),
                "letter_grade": letter_grade,
                "grade_point": self._calculate_grade_point(letter_grade),
                "calculated_at": datetime.utcnow().isoformat(),
                "components": [
                    {
                        "assessment_id": mark.assessment_id,
                        "assessment_name": mark.assessment_name,
                        "mark_value": mark.mark_value,
                        "weight": mark.weight,
                        "contributed_value": round(mark.mark_value * (mark.weight or 0), 2)
                    }
                    for mark in student_marks
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate final grade for student {student_id} in course {course_id}: {str(e)}")
            raise
    
    async def bulk_grade_upload(self, grade_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload grades with validation."""
        results = {
            "success": [],
            "failed": [],
            "summary": {
                "total": len(grade_data),
                "success": 0,
                "failed": 0
            }
        }
        
        for grade in grade_data:
            try:
                # Validate grade data
                await self._validate_bulk_grade(grade)
                
                # Create mark
                mark = await self.create_mark(grade)
                
                # Update student grade
                await self._update_student_grade(grade['student_id'])
                
                results["success"].append({
                    "student_id": grade["student_id"],
                    "assessment_id": grade["assessment_id"],
                    "mark_id": mark.id,
                    "status": "created"
                })
                results["summary"]["success"] += 1
                
            except Exception as e:
                results["failed"].append({
                    "student_id": grade.get("student_id"),
                    "assessment_id": grade.get("assessment_id"),
                    "error": str(e),
                    "status": "failed"
                })
                results["summary"]["failed"] += 1
        
        return results
    
    async def grade_adjustment(self, mark_id: str, adjustment_data: Dict[str, Any]) -> bool:
        """Apply grade adjustment with validation."""
        try:
            # Validate mark exists
            mark = await self.mark_repository.get_by_id(mark_id)
            if not mark:
                raise NotFoundError(f"Mark not found with ID: {mark_id}")
            
            # Validate adjustment data
            await self._validate_grade_adjustment(adjustment_data)
            
            # Apply adjustment
            adjusted_mark = await self.mark_repository.grade_adjustment(
                mark_id=mark_id,
                **adjustment_data
            )
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Update student grade
            await self._update_student_grade(mark.student_id)
            
            return adjusted_mark is not None
            
        except Exception as e:
            logger.error(f"Failed to adjust grade for mark {mark_id}: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_student_grade_stats(self, student_id: str, course_id: str = None) -> MarkStats:
        """Get comprehensive grade statistics for a student."""
        try:
            marks = await self.get_marks_by_student(student_id, 0, 1000)
            
            if course_id:
                course_marks = [m for m in marks if m.course_id == course_id]
                marks = course_marks
            
            if not marks:
                raise NotFoundError(f"No marks found for student {student_id}")
            
            # Calculate statistics
            mark_values = [m.mark_value for m in marks if m.mark_value is not None]
            
            if not mark_values:
                raise NotFoundError(f"No valid mark values found for student {student_id}")
            
            stats = MarkStats(
                student_id=student_id,
                total_marks=len(marks),
                average_grade=round(statistics.mean(mark_values), 2),
                highest_grade=max(mark_values),
                lowest_grade=min(mark_values),
                median_grade=round(statistics.median(mark_values), 2),
                standard_deviation=round(statistics.stdev(mark_values), 2) if len(mark_values) > 1 else 0,
                grade_distribution=self._calculate_grade_distribution(mark_values),
                last_grade_date=max(m.created_at for m in marks),
                total_assessments=len(set(m.assessment_id for m in marks))
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get student grade stats for {student_id}: {str(e)}")
            raise
    
    async def get_assessment_grade_stats(self, assessment_id: str) -> MarkStats:
        """Get comprehensive grade statistics for an assessment."""
        try:
            marks = await self.get_marks_by_assessment(assessment_id, 0, 1000)
            
            if not marks:
                raise NotFoundError(f"No marks found for assessment {assessment_id}")
            
            # Calculate statistics
            mark_values = [m.mark_value for m in marks if m.mark_value is not None]
            
            if not mark_values:
                raise NotFoundError(f"No valid mark values found for assessment {assessment_id}")
            
            stats = MarkStats(
                assessment_id=assessment_id,
                total_marks=len(marks),
                average_grade=round(statistics.mean(mark_values), 2),
                highest_grade=max(mark_values),
                lowest_grade=min(mark_values),
                median_grade=round(statistics.median(mark_values), 2),
                standard_deviation=round(statistics.stdev(mark_values), 2) if len(mark_values) > 1 else 0,
                grade_distribution=self._calculate_grade_distribution(mark_values),
                last_grade_date=max(m.created_at for m in marks),
                total_assessments=1  # Single assessment
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get assessment grade stats for {assessment_id}: {str(e)}")
            raise
    
    async def get_course_grade_stats(self, course_id: str) -> MarkStats:
        """Get comprehensive grade statistics for a course."""
        try:
            marks = await self.get_marks_by_course(course_id, 0, 1000)
            
            if not marks:
                raise NotFoundError(f"No marks found for course {course_id}")
            
            # Group by student
            student_marks = {}
            for mark in marks:
                if mark.student_id not in student_marks:
                    student_marks[mark.student_id] = []
                student_marks[mark.student_id].append(mark)
            
            # Calculate final grades for each student
            student_finals = []
            for student_id, student_mark_list in student_marks.items():
                if student_mark_list:
                    final_grade = await self.calculate_final_grade(student_id, course_id)
                    if final_grade:
                        student_finals.append(final_grade['final_mark'])
            
            if not student_finals:
                raise NotFoundError(f"No valid final grades found for course {course_id}")
            
            stats = MarkStats(
                course_id=course_id,
                total_marks=len(marks),
                average_grade=round(statistics.mean(student_finals), 2),
                highest_grade=max(student_finals),
                lowest_grade=min(student_finals),
                median_grade=round(statistics.median(student_finals), 2),
                standard_deviation=round(statistics.stdev(student_finals), 2) if len(student_finals) > 1 else 0,
                grade_distribution=self._calculate_grade_distribution(student_finals),
                last_grade_date=max(m.created_at for m in marks),
                total_assessments=len(set(m.assessment_id for m in marks))
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get course grade stats for {course_id}: {str(e)}")
            raise
    
    async def get_grade_distribution(self, course_id: str = None, class_id: str = None, 
                                  assessment_id: str = None, start_date: date = None, 
                                  end_date: date = None) -> GradeDistribution:
        """Get grade distribution for specified criteria."""
        try:
            marks = []
            
            if course_id:
                marks = await self.get_marks_by_course(course_id, 0, 1000)
            elif class_id:
                marks = await self.get_marks_by_class(class_id, 0, 1000)
            elif assessment_id:
                marks = await self.get_marks_by_assessment(assessment_id, 0, 1000)
            else:
                marks = await self.get_marks_by_date_range(start_date, end_date, 0, 1000)
            
            if not marks:
                raise NotFoundError("No marks found for specified criteria")
            
            # Convert to letter grades
            letter_grades = [self._convert_to_letter_grade(m.mark_value) for m in marks if m.mark_value is not None]
            
            # Calculate distribution
            distribution = self._calculate_grade_distribution(letter_grades)
            
            # Calculate statistics
            mark_values = [m.mark_value for m in marks if m.mark_value is not None]
            
            grade_dist = GradeDistribution(
                total_marks=len(marks),
                grade_distribution=distribution,
                average_grade=round(statistics.mean(mark_values), 2) if mark_values else 0,
                highest_grade=max(mark_values) if mark_values else 0,
                lowest_grade=min(mark_values) if mark_values else 0,
                pass_count=len([m for m in marks if self._is_passing_grade(m.mark_value)]),
                fail_count=len([m for m in marks if not self._is_passing_grade(m.mark_value)]),
                pass_rate=round(len([m for m in marks if self._is_passing_grade(m.mark_value)]) / len(marks) * 100, 2) if marks else 0,
                calculated_at=datetime.utcnow().isoformat()
            )
            
            return grade_dist
            
        except Exception as e:
            logger.error(f"Failed to get grade distribution: {str(e)}")
            raise
    
    # Grade Validation and Verification
    
    async def validate_marks_for_course(self, course_id: str) -> Dict[str, Any]:
        """Validate all marks for a course."""
        try:
            marks = await self.get_marks_by_course(course_id, 0, 1000)
            
            validation_result = {
                "total_marks": len(marks),
                "valid_marks": 0,
                "invalid_marks": 0,
                "issues": [],
                "valid": True
            }
            
            for mark in marks:
                issues = self._validate_mark_value(mark)
                if not issues:
                    validation_result["valid_marks"] += 1
                else:
                    validation_result["invalid_marks"] += 1
                    validation_result["issues"].extend(issues)
                    validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate marks for course {course_id}: {str(e)}")
            raise
    
    async def audit_grade_changes(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Audit grade changes within a date range."""
        try:
            return await self.mark_repository.audit_grade_changes(start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to audit grade changes: {str(e)}")
            raise
    
    # Grade Conversion and Scaling
    
    async def scale_grades(self, scale_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scale marks based on specified criteria."""
        try:
            course_id = scale_data.get('course_id')
            scaling_factor = scale_data.get('scaling_factor', 1.0)
            max_mark = scale_data.get('max_mark', 100)
            
            # Get marks
            marks = await self.get_marks_by_course(course_id, 0, 1000)
            
            if not marks:
                raise NotFoundError(f"No marks found for course {course_id}")
            
            scaling_results = {
                "original_marks": [],
                "scaled_marks": [],
                "scale_factor": scaling_factor,
                "max_mark": max_mark,
                "summary": {
                    "total_marks": len(marks),
                    "average_before": 0,
                    "average_after": 0,
                    "highest_before": 0,
                    "highest_after": 0,
                    "lowest_before": 0,
                    "lowest_after": 0
                }
            }
            
            total_before = 0
            total_after = 0
            highest_before = 0
            highest_after = 0
            lowest_before = 100
            lowest_after = 100
            
            for mark in marks:
                original_mark = mark.mark_value
                scaled_mark = min(original_mark * scaling_factor, max_mark)
                
                scaling_results["original_marks"].append({
                    "student_id": mark.student_id,
                    "assessment_id": mark.assessment_id,
                    "original_mark": original_mark
                })
                
                scaling_results["scaled_marks"].append({
                    "student_id": mark.student_id,
                    "assessment_id": mark.assessment_id,
                    "scaled_mark": round(scaled_mark, 2)
                })
                
                # Update summary
                total_before += original_mark
                total_after += scaled_mark
                highest_before = max(highest_before, original_mark)
                highest_after = max(highest_after, scaled_mark)
                lowest_before = min(lowest_before, original_mark)
                lowest_after = min(lowest_after, scaled_mark)
            
            scaling_results["summary"] = {
                "total_marks": len(marks),
                "average_before": round(total_before / len(marks), 2),
                "average_after": round(total_after / len(marks), 2),
                "highest_before": highest_before,
                "highest_after": highest_after,
                "lowest_before": lowest_before,
                "lowest_after": lowest_after
            }
            
            return scaling_results
            
        except Exception as e:
            logger.error(f"Failed to scale grades: {str(e)}")
            raise
    
    async def curve_grades(self, curve_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply grade curve based on specified method."""
        try:
            course_id = curve_data.get('course_id')
            curve_method = curve_data.get('method', 'linear')
            
            # Get marks
            marks = await self.get_marks_by_course(course_id, 0, 1000)
            
            if not marks:
                raise NotFoundError(f"No marks found for course {course_id}")
            
            mark_values = [m.mark_value for m in marks if m.mark_value is not None]
            
            if not mark_values:
                raise NotFoundError(f"No valid mark values found for course {course_id}")
            
            # Apply curve
            if curve_method == 'linear':
                curve_results = self._apply_linear_curve(mark_values)
            elif curve_method == 'bell':
                curve_results = self._apply_bell_curve(mark_values)
            elif curve_method == 'fixed':
                curve_results = self._apply_fixed_curve(mark_values)
            else:
                raise ValidationError(f"Unknown curve method: {curve_method}")
            
            return curve_results
            
        except Exception as e:
            logger.error(f"Failed to curve grades: {str(e)}")
            raise
    
    # Batch Operations
    
    async def batch_update_marks(self, updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Update multiple marks."""
        results = {}
        
        for update in updates:
            mark_id = update['mark_id']
            try:
                result = await self.update_mark(mark_id, update)
                results[mark_id] = result is not None
            except Exception as e:
                logger.error(f"Failed to update mark {mark_id}: {str(e)}")
                results[mark_id] = False
        
        return results
    
    async def batch_delete_marks(self, mark_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple marks."""
        results = {}
        
        for mark_id in mark_ids:
            try:
                result = await self.delete_mark(mark_id)
                results[mark_id] = result
            except Exception as e:
                logger.error(f"Failed to delete mark {mark_id}: {str(e)}")
                results[mark_id] = False
        
        return results
    
    # Helper Methods
    
    async def _validate_mark_creation(self, data: Dict[str, Any]) -> None:
        """Validate mark creation data."""
        required_fields = ['student_id', 'assessment_id', 'mark_value', 'graded_by', 'graded_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate mark value
        await self._validate_mark_value(data)
        
        # Validate grade exists
        from src.infrastructure.repositories.teacher_repository import TeacherRepository
        teacher_repo = TeacherRepository()
        grader = await teacher_repo.get_by_id(data['graded_by'])
        if not grader:
            raise NotFoundError(f"Teacher not found with ID: {data['graded_by']}")
        
        # Validate student exists
        from src.infrastructure.repositories.student_repository import StudentRepository
        student_repo = StudentRepository()
        student = await student_repo.get_by_id(data['student_id'])
        if not student:
            raise NotFoundError(f"Student not found with ID: {data['student_id']}")
        
        # Validate assessment exists
        from src.infrastructure.repositories.assessment_repository import AssessmentRepository
        assessment_repo = AssessmentRepository()
        assessment = await assessment_repo.get_by_id(data['assessment_id'])
        if not assessment:
            raise NotFoundError(f"Assessment not found with ID: {data['assessment_id']}")
    
    async def _validate_mark_update(self, data: Dict[str, Any]) -> None:
        """Validate mark update data."""
        allowed_fields = ['mark_value', 'comment', 'status', 'weight']
        
        for field in data.keys():
            if field not in allowed_fields:
                raise ValidationError(f"Cannot update field: {field}")
        
        # Validate mark value if provided
        if 'mark_value' in data and data['mark_value'] is not None:
            await self._validate_mark_value(data)
        
        # Validate weight if provided
        if 'weight' in data and data['weight']:
            if not (0 <= data['weight'] <= 1):
                raise ValidationError("Weight must be between 0 and 1")
    
    async def _validate_bulk_grade(self, data: Dict[str, Any]) -> None:
        """Validate bulk grade data."""
        required_fields = ['student_id', 'assessment_id', 'mark_value']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate mark value
        await self._validate_mark_value(data)
    
    async def _validate_grade_adjustment(self, data: Dict[str, Any]) -> None:
        """Validate grade adjustment data."""
        required_fields = ['adjustment_type', 'adjustment_value']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate adjustment type
        valid_types = ['addition', 'subtraction', 'percentage', 'curve']
        if data['adjustment_type'] not in valid_types:
            raise ValidationError(f"Invalid adjustment type: {data['adjustment_type']}")
        
        # Validate adjustment value
        if isinstance(data['adjustment_value'], (int, float)):
            if data['adjustment_type'] in ['addition', 'subtraction'] and not (-100 <= data['adjustment_value'] <= 100):
                raise ValidationError("Adjustment value must be between -100 and 100")
            elif data['adjustment_type'] == 'percentage' and not (-100 <= data['adjustment_value'] <= 100):
                raise ValidationError("Percentage adjustment must be between -100 and 100")
        else:
            raise ValidationError("Adjustment value must be a number")
    
    def _validate_mark_value(self, mark_data: Dict[str, Any]) -> List[str]:
        """Validate mark value and return any issues."""
        issues = []
        
        if 'mark_value' not in mark_data or mark_data['mark_value'] is None:
            return ["Mark value is required"]
        
        mark_value = mark_data['mark_value']
        
        if not isinstance(mark_value, (int, float)):
            issues.append("Mark value must be a number")
        else:
            if mark_value < 0:
                issues.append("Mark value cannot be negative")
            elif mark_value > 100:
                issues.append("Mark value cannot exceed 100")
        
        return issues
    
    def _convert_to_letter_grade(self, mark_value: float) -> str:
        """Convert numeric mark to letter grade."""
        if mark_value >= 90:
            return 'A+'
        elif mark_value >= 85:
            return 'A'
        elif mark_value >= 80:
            return 'A-'
        elif mark_value >= 75:
            return 'B+'
        elif mark_value >= 70:
            return 'B'
        elif mark_value >= 65:
            return 'B-'
        elif mark_value >= 60:
            return 'C+'
        elif mark_value >= 55:
            return 'C'
        elif mark_value >= 50:
            return 'C-'
        elif mark_value >= 45:
            return 'D+'
        elif mark_value >= 40:
            return 'D'
        else:
            return 'F'
    
    def _calculate_grade_point(self, letter_grade: str) -> float:
        """Calculate grade point from letter grade."""
        grade_points = {
            'A+': 4.3, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0
        }
        return grade_points.get(letter_grade, 0.0)
    
    def _is_passing_grade(self, mark_value: float) -> bool:
        """Check if mark is passing."""
        return mark_value >= 40
    
    def _calculate_grade_distribution(self, marks: List[float]) -> Dict[str, int]:
        """Calculate grade distribution from marks."""
        distribution = {}
        
        for mark in marks:
            letter_grade = self._convert_to_letter_grade(mark)
            distribution[letter_grade] = distribution.get(letter_grade, 0) + 1
        
        return distribution
    
    def _apply_linear_curve(self, marks: List[float]) -> Dict[str, Any]:
        """Apply linear curve to marks."""
        if not marks:
            return {}
        
        original_mean = statistics.mean(marks)
        original_std = statistics.stdev(marks) if len(marks) > 1 else 1
        
        # Target mean and standard deviation
        target_mean = 75
        target_std = 10
        
        if original_std == 0:
            # No variation, adjust only mean
            adjustment = target_mean - original_mean
            curved_marks = [mark + adjustment for mark in marks]
        else:
            # Apply linear transformation
            slope = target_std / original_std
            intercept = target_mean - slope * original_mean
            curved_marks = [mark * slope + intercept for mark in marks]
        
        return {
            "original_marks": marks,
            "curved_marks": [round(m, 2) for m in curved_marks],
            "curve_method": "linear",
            "adjustment": {
                "original_mean": round(original_mean, 2),
                "original_std": round(original_std, 2),
                "target_mean": target_mean,
                "target_std": target_std
            }
        }
    
    def _apply_bell_curve(self, marks: List[float]) -> Dict[str, Any]:
        """Apply bell curve to marks."""
        if not marks:
            return {}
        
        sorted_marks = sorted(marks)
        n = len(marks)
        
        # Assign grades based on percentile
        percentiles = [(i + 0.5) / n * 100 for i in range(n)]
        curved_marks = []
        
        for i, mark in enumerate(sorted_marks):
            percentile = percentiles[i]
            if percentile >= 90:
                curved_marks.append(min(mark * 1.1, 100))
            elif percentile >= 70:
                curved_marks.append(min(mark * 1.05, 100))
            elif percentile >= 30:
                curved_marks.append(mark)
            elif percentile >= 10:
                curved_marks.append(mark * 0.95)
            else:
                curved_marks.append(max(mark * 0.9, 0))
        
        return {
            "original_marks": marks,
            "curved_marks": [round(m, 2) for m in curved_marks],
            "curve_method": "bell",
            "percentiles": percentiles
        }
    
    def _apply_fixed_curve(self, marks: List[float]) -> Dict[str, Any]:
        """Apply fixed curve to marks."""
        if not marks:
            return {}
        
        curved_marks = []
        
        for mark in marks:
            if mark >= 85:
                curved_marks.append(100)
            elif mark >= 75:
                curved_marks.append(90)
            elif mark >= 65:
                curved_marks.append(80)
            elif mark >= 55:
                curved_marks.append(70)
            elif mark >= 45:
                curved_marks.append(60)
            else:
                curved_marks.append(50)
        
        return {
            "original_marks": marks,
            "curved_marks": curved_marks,
            "curve_method": "fixed"
        }
    
    async def _update_student_grade(self, student_id: str) -> None:
        """Update student grade based on marks."""
        try:
            # This would update student's overall grade record
            # For now, just log the operation
            logger.info(f"Updating student grade for {student_id}")
            
        except Exception as e:
            logger.error(f"Failed to update student grade for {student_id}: {str(e)}")
            raise
    
    async def _invalidate_cache(self) -> None:
        """Invalidate mark cache."""
        self._cache.clear()