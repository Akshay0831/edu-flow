"""
Grade Management Repository

This module provides database operations for grade management:
- CRUD operations for grade records
- Grade calculation and validation
- Bulk upload and batch operations
- Grade analytics and reporting
- Grade policy enforcement
- Academic performance tracking

Author: Edu-Flow Team
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from uuid import uuid4
from decimal import Decimal

from src.core.exceptions import NotFoundError, ValidationError, DatabaseError, ConflictError
from src.core.logging import get_logger
from src.core.database_abstraction import DatabaseManager, DatabaseInterface
from src.infrastructure.repositories.base_repository_with_db import BaseRepositoryWithDB, QueryResult
from src.models.grade import (
    GradeCreate, GradeUpdate, GradeResponse, GradePolicy,
    GradeCalculation, GradeAnalytics, GradeStatistics, GradeTrend,
    StudentGradeSummary, ClassGradeSummary, SubjectGradeSummary
)

logger = get_logger(__name__)


class GradeRepository(BaseRepositoryWithDB):
    """Grade management repository with comprehensive functionality."""
    
    def __init__(self, database_manager):
        super().__init__("grades", database_manager)
        
    # Core CRUD Operations
    
    async def get_by_id(self, grade_id: str) -> Optional[GradeResponse]:
        """Get a grade record by ID."""
        try:
            result = await self._find_one(self._collection, {"grade_id": grade_id})
            if result:
                return GradeResponse(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting grade by ID {grade_id}: {str(e)}")
            raise DatabaseError(f"Failed to get grade record: {str(e)}")
    
    async def get_all(self, skip: int = 0, limit: int = 100, 
                     filters: Dict[str, Any] = None) -> List[GradeResponse]:
        """Get all grade records with optional filtering."""
        try:
            query_filter = filters or {}
            result = await self._find_many(
                self._collection, 
                query_filter,
                skip=skip,
                limit=limit,
                sort=[("created_at", -1)]
            )
            
            return [GradeResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting all grades: {str(e)}")
            raise DatabaseError(f"Failed to fetch grade records: {str(e)}")
    
    async def create(self, **data) -> GradeResponse:
        """Create a new grade record."""
        try:
            # Add required fields
            if 'grade_id' not in data:
                data['grade_id'] = str(uuid4())
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Validate grade data
            await self._validate_grade_data(data)
            
            # Insert into database
            result = await self._insert(self._collection, data)
            if result.inserted_id:
                created_grade = await self.get_by_id(data['grade_id'])
                return created_grade
            else:
                raise DatabaseError("Failed to create grade record")
                
        except Exception as e:
            logger.error(f"Error creating grade record: {str(e)}")
            raise DatabaseError(f"Failed to create grade record: {str(e)}")
    
    async def update(self, grade_id: str, **data) -> Optional[GradeResponse]:
        """Update an existing grade record."""
        try:
            # Update timestamps
            data['updated_at'] = datetime.utcnow()
            
            # Validate updated grade data
            await self._validate_grade_data(data)
            
            # Update in database
            result = await self._update(
                self._collection,
                {"grade_id": grade_id},
                {"$set": data}
            )
            
            if result.modified_count > 0:
                updated_grade = await self.get_by_id(grade_id)
                return updated_grade
            else:
                raise NotFoundError(f"Grade record not found with ID: {grade_id}")
                
        except Exception as e:
            logger.error(f"Error updating grade record {grade_id}: {str(e)}")
            raise DatabaseError(f"Failed to update grade record: {str(e)}")
    
    async def delete(self, grade_id: str) -> bool:
        """Delete a grade record."""
        try:
            result = await self._delete(self._collection, {"grade_id": grade_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting grade record {grade_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete grade record: {str(e)}")
    
    # Grade-specific Operations
    
    async def get_student_grades(self, student_id: str, academic_year: str = None, 
                               semester: str = None) -> List[GradeResponse]:
        """Get all grades for a specific student."""
        try:
            query_filter = {"student_id": student_id}
            
            if academic_year:
                query_filter["academic_year"] = academic_year
            if semester:
                query_filter["semester"] = semester
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("semester", 1), ("subject_id", 1)]
            )
            
            return [GradeResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting student grades for {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch student grades: {str(e)}")
    
    async def get_class_grades(self, class_id: str, academic_year: str = None, 
                             semester: str = None) -> List[GradeResponse]:
        """Get all grades for a specific class."""
        try:
            query_filter = {"class_id": class_id}
            
            if academic_year:
                query_filter["academic_year"] = academic_year
            if semester:
                query_filter["semester"] = semester
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("student_id", 1), ("subject_id", 1)]
            )
            
            return [GradeResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting class grades for {class_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch class grades: {str(e)}")
    
    async def get_subject_grades(self, subject_id: str, academic_year: str = None, 
                               semester: str = None) -> List[GradeResponse]:
        """Get all grades for a specific subject."""
        try:
            query_filter = {"subject_id": subject_id}
            
            if academic_year:
                query_filter["academic_year"] = academic_year
            if semester:
                query_filter["semester"] = semester
            
            result = await self._find_many(
                self._collection,
                query_filter,
                sort=[("class_id", 1), ("student_id", 1)]
            )
            
            return [GradeResponse(**item) for item in result]
            
        except Exception as e:
            logger.error(f"Error getting subject grades for {subject_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch subject grades: {str(e)}")
    
    # Grade Calculation and Validation
    
    async def calculate_gpa(self, student_id: str, academic_year: str = None, 
                          semester: str = None) -> Decimal:
        """Calculate GPA for a student."""
        try:
            grades = await self.get_student_grades(student_id, academic_year, semester)
            
            if not grades:
                return Decimal('0.00')
            
            total_credits = 0
            total_grade_points = Decimal('0.00')
            
            for grade in grades:
                credit = grade.credit_earned or Decimal('1.0')
                grade_point = self._letter_to_grade_point(grade.letter_grade)
                
                total_credits += credit
                total_grade_points += grade_point * credit
            
            if total_credits == 0:
                return Decimal('0.00')
            
            gpa = total_grade_points / total_credits
            return round(gpa, 2)
            
        except Exception as e:
            logger.error(f"Error calculating GPA for {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to calculate GPA: {str(e)}")
    
    async def validate_grade_entry(self, student_id: str, subject_id: str, 
                                 academic_year: str, semester: str) -> bool:
        """Validate if a grade entry already exists for the same student, subject, year, and semester."""
        try:
            query_filter = {
                "student_id": student_id,
                "subject_id": subject_id,
                "academic_year": academic_year,
                "semester": semester
            }
            
            result = await self._find_one(self._collection, query_filter)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error validating grade entry: {str(e)}")
            raise DatabaseError(f"Failed to validate grade entry: {str(e)}")
    
    async def apply_grade_policy(self, grade: Decimal) -> Dict[str, Any]:
        """Apply grade policy to determine letter grade and other attributes."""
        try:
            policy = await self._get_grade_policy()
            
            # Determine letter grade based on score
            for grade_range in policy['grade_ranges']:
                if grade >= grade_range['min'] and (grade <= grade_range['max'] or grade_range['max'] is None):
                    return {
                        'letter_grade': grade_range['letter'],
                        'grade_point': grade_range['grade_point'],
                        'status': grade_range['status'],
                        'remarks': grade_range['remarks'],
                        'policy_id': policy['policy_id']
                    }
            
            # Default if no range matches
            return {
                'letter_grade': 'F',
                'grade_point': Decimal('0.0'),
                'status': 'fail',
                'remarks': 'Below minimum passing grade',
                'policy_id': policy['policy_id']
            }
            
        except Exception as e:
            logger.error(f"Error applying grade policy: {str(e)}")
            raise DatabaseError(f"Failed to apply grade policy: {str(e)}")
    
    # Analytics and Reporting
    
    async def get_grade_statistics(self, class_id: str, subject_id: str = None, 
                                 academic_year: str = None, semester: str = None) -> GradeStatistics:
        """Calculate grade statistics for a class or subject."""
        try:
            query_filter = {"class_id": class_id}
            
            if subject_id:
                query_filter["subject_id"] = subject_id
            if academic_year:
                query_filter["academic_year"] = academic_year
            if semester:
                query_filter["semester"] = semester
            
            result = await self._find_many(self._collection, query_filter)
            
            if not result:
                return GradeStatistics(
                    class_id=class_id,
                    subject_id=subject_id,
                    total_students=0,
                    average_grade=Decimal('0.00'),
                    median_grade=Decimal('0.00'),
                    highest_grade=Decimal('0.00'),
                    lowest_grade=Decimal('0.00'),
                    pass_rate=Decimal('0.00'),
                    fail_rate=Decimal('0.00'),
                    grade_distribution={},
                    performance_level_distribution={}
                )
            
            grades = [Decimal(item['numeric_grade']) for item in result if item.get('numeric_grade')]
            letter_grades = [item['letter_grade'] for item in result if item.get('letter_grade')]
            
            # Calculate statistics
            total_students = len(result)
            average_grade = sum(grades) / len(grades) if grades else Decimal('0.00')
            
            sorted_grades = sorted(grades)
            median_grade = (sorted_grades[len(sorted_grades)//2] + sorted_grades[-(len(sorted_grades)//2+1)]) / 2 if grades else Decimal('0.00')
            
            highest_grade = max(grades) if grades else Decimal('0.00')
            lowest_grade = min(grades) if grades else Decimal('0.00')
            
            # Calculate pass/fail rates
            pass_count = sum(1 for item in result if item.get('status') == 'pass')
            fail_count = total_students - pass_count
            
            pass_rate = (pass_count / total_students * 100) if total_students > 0 else Decimal('0.00')
            fail_rate = (fail_count / total_students * 100) if total_students > 0 else Decimal('0.00')
            
            # Grade distribution
            grade_counts = {}
            for grade in letter_grades:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            grade_distribution = {grade: (count / total_students * 100) for grade, count in grade_counts.items()}
            
            # Performance level distribution
            performance_levels = {'excellent': 0, 'good': 0, 'satisfactory': 0, 'needs_improvement': 0}
            for item in result:
                status = item.get('status', '')
                if status == 'excellent':
                    performance_levels['excellent'] += 1
                elif status == 'good':
                    performance_levels['good'] += 1
                elif status == 'pass':
                    performance_levels['satisfactory'] += 1
                else:
                    performance_levels['needs_improvement'] += 1
            
            performance_level_distribution = {level: (count / total_students * 100) for level, count in performance_levels.items()}
            
            return GradeStatistics(
                class_id=class_id,
                subject_id=subject_id,
                total_students=total_students,
                average_grade=round(average_grade, 2),
                median_grade=round(median_grade, 2),
                highest_grade=round(highest_grade, 2),
                lowest_grade=round(lowest_grade, 2),
                pass_rate=round(pass_rate, 2),
                fail_rate=round(fail_rate, 2),
                grade_distribution=grade_distribution,
                performance_level_distribution=performance_level_distribution
            )
            
        except Exception as e:
            logger.error(f"Error calculating grade statistics: {str(e)}")
            raise DatabaseError(f"Failed to calculate grade statistics: {str(e)}")
    
    async def get_grade_trends(self, student_id: str, subject_id: str = None, 
                             academic_year: str = None, semester: str = None) -> GradeTrend:
        """Get grade trends for a student over time."""
        try:
            grades = await self.get_student_grades(student_id, academic_year, semester)
            
            if not grades:
                return GradeTrend(
                    student_id=student_id,
                    subject_id=subject_id,
                    total_semesters=0,
                    average_grade=Decimal('0.00'),
                    trend_direction='stable',
                    improvement_rate=Decimal('0.00'),
                    grade_stability=Decimal('0.00')
                )
            
            # Group grades by semester
            semester_grades = {}
            for grade in grades:
                semester_key = f"{grade.academic_year}_{grade.semester}"
                if semester_key not in semester_grades:
                    semester_grades[semester_key] = []
                semester_grades[semester_key].append(grade.numeric_grade)
            
            # Calculate average per semester
            semester_averages = []
            for semester_key, grade_list in semester_grades.items():
                avg_grade = sum(grade_list) / len(grade_list)
                semester_averages.append({
                    'semester': semester_key,
                    'average': avg_grade
                })
            
            # Sort by semester (assuming YYYY_S format)
            semester_averages.sort(key=lambda x: x['semester'])
            
            # Calculate trends
            if len(semester_averages) < 2:
                trend_direction = 'stable'
                improvement_rate = Decimal('0.00')
            else:
                # Determine trend direction
                first_avg = semester_averages[0]['average']
                last_avg = semester_averages[-1]['average']
                
                if last_avg > first_avg:
                    trend_direction = 'improving'
                    improvement_rate = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else Decimal('0.00')
                elif last_avg < first_avg:
                    trend_direction = 'declining'
                    improvement_rate = ((first_avg - last_avg) / first_avg * 100) if first_avg > 0 else Decimal('0.00')
                else:
                    trend_direction = 'stable'
                    improvement_rate = Decimal('0.00')
            
            # Calculate grade stability (how consistent grades are)
            if semester_averages:
                grade_stability = self._calculate_grade_stability([item['average'] for item in semester_averages])
            else:
                grade_stability = Decimal('0.00')
            
            overall_average = sum(item['average'] for item in semester_averages) / len(semester_averages) if semester_averages else Decimal('0.00')
            
            return GradeTrend(
                student_id=student_id,
                subject_id=subject_id,
                total_semesters=len(semester_averages),
                average_grade=round(overall_average, 2),
                trend_direction=trend_direction,
                improvement_rate=round(improvement_rate, 2),
                grade_stability=round(grade_stability, 2)
            )
            
        except Exception as e:
            logger.error(f"Error calculating grade trends for {student_id}: {str(e)}")
            raise DatabaseError(f"Failed to calculate grade trends: {str(e)}")
    
    # Helper Methods
    
    async def _validate_grade_data(self, data: Dict[str, Any]) -> None:
        """Validate grade data before insertion or update."""
        required_fields = ['student_id', 'subject_id', 'class_id', 'academic_year', 'semester']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Required field '{field}' is missing or empty")
        
        # Validate numeric grade
        if 'numeric_grade' in data:
            try:
                numeric_grade = Decimal(str(data['numeric_grade']))
                if not (0 <= numeric_grade <= 100):
                    raise ValidationError("Numeric grade must be between 0 and 100")
            except (ValueError, TypeError):
                raise ValidationError("Invalid numeric grade format")
        
        # Validate letter grade format
        if 'letter_grade' in data:
            valid_letter_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
            if data['letter_grade'] not in valid_letter_grades:
                raise ValidationError(f"Invalid letter grade. Must be one of: {valid_letter_grades}")
        
        # Validate semester format
        if 'semester' in data and data['semester']:
            valid_semesters = ['fall', 'spring', 'summer', 'winter']
            if data['semester'].lower() not in valid_semesters:
                raise ValidationError(f"Invalid semester. Must be one of: {valid_semesters}")
    
    async def _get_grade_policy(self) -> Dict[str, Any]:
        """Get the current grade policy."""
        try:
            # Get grade policy from database
            policy = await self._find_one("grade_policies", {"is_active": True}, limit=1)
            
            if not policy:
                # Default grade policy
                return {
                    'policy_id': 'default',
                    'is_active': True,
                    'grade_ranges': [
                        {'min': 90, 'max': 100, 'letter': 'A+', 'grade_point': Decimal('4.0'), 'status': 'excellent', 'remarks': 'Excellent'},
                        {'min': 85, 'max': 89.9, 'letter': 'A', 'grade_point': Decimal('4.0'), 'status': 'excellent', 'remarks': 'Excellent'},
                        {'min': 80, 'max': 84.9, 'letter': 'A-', 'grade_point': Decimal('3.7'), 'status': 'good', 'remarks': 'Good'},
                        {'min': 75, 'max': 79.9, 'letter': 'B+', 'grade_point': Decimal('3.3'), 'status': 'good', 'remarks': 'Good'},
                        {'min': 70, 'max': 74.9, 'letter': 'B', 'grade_point': Decimal('3.0'), 'status': 'good', 'remarks': 'Good'},
                        {'min': 65, 'max': 69.9, 'letter': 'B-', 'grade_point': Decimal('2.7'), 'status': 'satisfactory', 'remarks': 'Satisfactory'},
                        {'min': 60, 'max': 64.9, 'letter': 'C+', 'grade_point': Decimal('2.3'), 'status': 'satisfactory', 'remarks': 'Satisfactory'},
                        {'min': 55, 'max': 59.9, 'letter': 'C', 'grade_point': Decimal('2.0'), 'status': 'satisfactory', 'remarks': 'Satisfactory'},
                        {'min': 50, 'max': 54.9, 'letter': 'C-', 'grade_point': Decimal('1.7'), 'status': 'needs_improvement', 'remarks': 'Needs Improvement'},
                        {'min': 45, 'max': 49.9, 'letter': 'D+', 'grade_point': Decimal('1.3'), 'status': 'needs_improvement', 'remarks': 'Needs Improvement'},
                        {'min': 40, 'max': 44.9, 'letter': 'D', 'grade_point': Decimal('1.0'), 'status': 'needs_improvement', 'remarks': 'Needs Improvement'},
                        {'min': 0, 'max': 39.9, 'letter': 'F', 'grade_point': Decimal('0.0'), 'status': 'fail', 'remarks': 'Fail'}
                    ]
                }
            
            return policy
            
        except Exception as e:
            logger.error(f"Error getting grade policy: {str(e)}")
            raise DatabaseError(f"Failed to get grade policy: {str(e)}")
    
    def _letter_to_grade_point(self, letter_grade: str) -> Decimal:
        """Convert letter grade to grade point."""
        grade_mapping = {
            'A+': Decimal('4.0'),
            'A': Decimal('4.0'),
            'A-': Decimal('3.7'),
            'B+': Decimal('3.3'),
            'B': Decimal('3.0'),
            'B-': Decimal('2.7'),
            'C+': Decimal('2.3'),
            'C': Decimal('2.0'),
            'C-': Decimal('1.7'),
            'D+': Decimal('1.3'),
            'D': Decimal('1.0'),
            'F': Decimal('0.0')
        }
        
        return grade_mapping.get(letter_grade, Decimal('0.0'))
    
    def _calculate_grade_stability(self, grades: List[Decimal]) -> Decimal:
        """Calculate grade stability (how consistent grades are)."""
        if len(grades) < 2:
            return Decimal('100.00')
        
        # Calculate standard deviation
        mean = sum(grades) / len(grades)
        variance = sum((x - mean) ** 2 for x in grades) / len(grades)
        std_dev = variance ** 0.5
        
        # Convert to stability percentage (lower std dev = higher stability)
        max_deviation = max(grades) - min(grades)
        if max_deviation == 0:
            return Decimal('100.00')
        
        stability = (1 - (std_dev / max_deviation)) * 100
        return max(0, min(100, round(stability, 2)))