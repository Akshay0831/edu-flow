"""
CO-PO Mapping Service for Edu-Flow

This service provides functionality for Course Outcome (CO) to Program Outcome (PO) mapping:
- Create and manage CO-PO mappings
- Calculate attainment levels
- Generate attainment reports
- Analyze CO-PO attainment data
- Configuration-based calculation methods

Author: Edu-Flow Team
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.deps import get_db
from models.co_po_mapping import (
    COPOMapping, CourseOutcome, ProgramOutcome, AttainmentReport, COPOMappingConfig,
    AttainmentLevel, AttainmentGrade
)
from src.services.base_service import BaseService
from core.exceptions import NotFoundError, ValidationError, ConfigurationError
from core.cache import CacheManager
from config.settings import get_settings

class COPOMappingService(BaseService):
    """CO-PO Mapping Service"""
    
    def __init__(self, db: Session, cache_manager: CacheManager):
        super().__init__(db, cache_manager)
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        self.cache_key_prefix = "co_po_mapping"
        
    # region: Basic CRUD Operations
    async def create_mapping(
        self, 
        course_id: str, 
        program_outcome_id: str, 
        course_outcome_id: str,
        weight: float = 1.0,
        mapping_type: str = "direct",
        attainment_thresholds: Optional[Dict] = None,
        mapping_description: Optional[str] = None
    ) -> COPOMapping:
        """Create a new CO-PO mapping"""
        
        # Validate data exists
        course = self._get_course_by_id(course_id)
        program_outcome = self._get_program_outcome_by_id(program_outcome_id)
        course_outcome = self._get_course_outcome_by_id(course_outcome_id)
        
        # Check for duplicate mapping
        existing_mapping = self.db.query(COPOMapping).filter(
            and_(
                COPOMapping.course_id == course_id,
                COPOMapping.program_outcome_id == program_outcome_id,
                COPOMapping.course_outcome_id == course_outcome_id
            )
        ).first()
        
        if existing_mapping:
            raise ValidationError(f"CO-PO mapping already exists for course {course_id}, PO {program_outcome_id}, CO {course_outcome_id}")
        
        # Create mapping
        mapping = COPOMapping(
            course_id=course_id,
            program_outcome_id=program_outcome_id,
            course_outcome_id=course_outcome_id,
            weight=weight,
            mapping_type=mapping_type,
            attainment_thresholds=attainment_thresholds,
            mapping_description=mapping_description
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Created CO-PO mapping: {mapping.id}")
        return mapping
    
    async def get_mapping_by_id(self, mapping_id: str) -> Optional[COPOMapping]:
        """Get CO-PO mapping by ID"""
        cache_key = f"{self.cache_key_prefix}_mapping_{mapping_id}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database
        mapping = self.db.query(COPOMapping).filter(COPOMapping.id == mapping_id).first()
        
        if mapping:
            await self.cache_manager.set(cache_key, mapping, ttl=3600)  # 1 hour
        
        return mapping
    
    async def get_mappings_by_course(self, course_id: str) -> List[COPOMapping]:
        """Get all CO-PO mappings for a course"""
        cache_key = f"{self.cache_key_prefix}_course_{course_id}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database
        mappings = self.db.query(COPOMapping).filter(
            COPOMapping.course_id == course_id,
            COPOMapping.is_active == True
        ).all()
        
        if mappings:
            await self.cache_manager.set(cache_key, mappings, ttl=3600)  # 1 hour
        
        return mappings
    
    async def get_mappings_by_program_outcome(self, program_outcome_id: str) -> List[COPOMapping]:
        """Get all CO-PO mappings for a program outcome"""
        cache_key = f"{self.cache_key_prefix}_po_{program_outcome_id}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database
        mappings = self.db.query(COPOMapping).filter(
            COPOMapping.program_outcome_id == program_outcome_id,
            COPOMapping.is_active == True
        ).all()
        
        if mappings:
            await self.cache_manager.set(cache_key, mappings, ttl=3600)  # 1 hour
        
        return mappings
    
    async def update_mapping(
        self, 
        mapping_id: str, 
        updates: Dict[str, Any]
    ) -> COPOMapping:
        """Update a CO-PO mapping"""
        mapping = await self.get_mapping_by_id(mapping_id)
        
        if not mapping:
            raise NotFoundError(f"CO-PO mapping not found: {mapping_id}")
        
        # Update allowed fields
        allowed_fields = [
            "weight", "mapping_type", "attainment_thresholds", 
            "mapping_description", "is_active"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(mapping, field, value)
        
        mapping.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(mapping)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Updated CO-PO mapping: {mapping_id}")
        return mapping
    
    async def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a CO-PO mapping"""
        mapping = await self.get_mapping_by_id(mapping_id)
        
        if not mapping:
            raise NotFoundError(f"CO-PO mapping not found: {mapping_id}")
        
        mapping.is_active = False
        mapping.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Deleted CO-PO mapping: {mapping_id}")
        return True
    
    # region: Attainment Calculation
    async def calculate_student_attainment(
        self, 
        student_id: str, 
        course_id: str, 
        assessment_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate attainment for a student in a course"""
        
        # Get all mappings for the course
        mappings = await self.get_mappings_by_course(course_id)
        
        if not mappings:
            raise ValidationError(f"No CO-PO mappings found for course {course_id}")
        
        # Calculate attainment for each mapping
        attainment_results = []
        total_weight = 0.0
        weighted_attainment = 0.0
        
        for mapping in mappings:
            # Get scores relevant to this course outcome
            student_scores = {}
            for score_key, score_value in assessment_scores.items():
                if mapping.course_outcome_id in score_key:
                    student_scores[score_key] = score_value
            
            # Calculate attainment
            attainment_data = mapping.calculate_attainment(student_scores)
            attainment_results.append(attainment_data)
            
            # Calculate weighted attainment
            if mapping.weight > 0:
                weighted_attainment += attainment_data["percentage"] * mapping.weight
                total_weight += mapping.weight
        
        # Calculate overall attainment
        overall_attainment = weighted_attainment / total_weight if total_weight > 0 else 0.0
        
        # Generate summary
        summary = {
            "student_id": student_id,
            "course_id": course_id,
            "overall_attainment_percentage": overall_attainment,
            "overall_attainment_level": self._get_attainment_level(overall_attainment),
            "overall_attainment_grade": self._get_attainment_grade(overall_attainment),
            "mapping_count": len(mappings),
            "assessment_count": len(assessment_scores),
            "attainment_details": attainment_results,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        return summary
    
    async def calculate_batch_attainment(
        self, 
        course_id: str, 
        batch_id: str, 
        academic_year: str, 
        semester: str,
        student_assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate attainment for an entire batch"""
        
        # Get all mappings for the course
        mappings = await self.get_mappings_by_course(course_id)
        
        if not mappings:
            raise ValidationError(f"No CO-PO mappings found for course {course_id}")
        
        batch_results = []
        student_count = len(student_assessments)
        
        for student_assessment in student_assessments:
            student_attainment = await self.calculate_student_attainment(
                student_assessment["student_id"],
                course_id,
                student_assessment["assessment_scores"]
            )
            batch_results.append(student_attainment)
        
        # Calculate batch-wide statistics
        total_attainments = 0
        attainment_distribution = {
            "excellent": 0, "very_good": 0, "good": 0, 
            "satisfactory": 0, "poor": 0, "not_achieved": 0
        }
        
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
        
        for result in batch_results:
            total_attainments += result["overall_attainment_percentage"]
            
            level = result["overall_attainment_level"].value
            attainment_distribution[level] += 1
            
            grade = result["overall_attainment_grade"].value
            grade_distribution[grade] += 1
        
        # Generate batch summary
        batch_summary = {
            "course_id": course_id,
            "batch_id": batch_id,
            "academic_year": academic_year,
            "semester": semester,
            "total_students": student_count,
            "average_attainment_percentage": total_attainments / student_count if student_count > 0 else 0,
            "attainment_distribution": attainment_distribution,
            "grade_distribution": grade_distribution,
            "course_outcome_attainments": self._calculate_co_attainments(batch_results),
            "program_outcome_attainments": await self._calculate_po_attainments(course_id, batch_results),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Save attainment report
        await self._save_attainment_report(batch_summary)
        
        return batch_summary
    
    # region: Report Generation
    async def generate_attainment_report(
        self, 
        course_id: str, 
        program_outcome_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        academic_year: Optional[str] = None,
        semester: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive attainment report"""
        
        # Get filters
        filters = {
            "course_id": course_id,
            "program_outcome_id": program_outcome_id,
            "batch_id": batch_id,
            "academic_year": academic_year,
            "semester": semester
        }
        
        # Get attainment data
        attainment_data = await self._get_attainment_data(filters)
        
        # Generate report
        report = {
            "report_type": "attainment_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "filters": filters,
            "summary": await self._generate_report_summary(attainment_data),
            "course_outcome_analysis": await self._analyze_course_outcomes(attainment_data),
            "program_outcome_analysis": await self._analyze_program_outcomes(course_id, program_outcome_id, attainment_data),
            "recommendations": await self._generate_recommendations(attainment_data),
            "data": attainment_data
        }
        
        return report
    
    async def export_attainment_report(
        self, 
        course_id: str, 
        format: str = "pdf",
        **filters
    ) -> str:
        """Export attainment report in specified format"""
        
        # Generate report data
        report_data = await self.generate_attainment_report(course_id, **filters)
        
        # Export based on format
        if format.lower() == "pdf":
            return await self._export_pdf_report(report_data)
        elif format.lower() == "excel":
            return await self._export_excel_report(report_data)
        elif format.lower() == "json":
            return json.dumps(report_data, indent=2, default=str)
        else:
            raise ValidationError(f"Unsupported export format: {format}")
    
    # region: Configuration Management
    async def create_mapping_config(
        self,
        mapping_type: str,
        calculation_method: str = "weighted_average",
        default_thresholds: Optional[Dict] = None,
        description: Optional[str] = None
    ) -> COPOMappingConfig:
        """Create mapping configuration"""
        
        config = COPOMappingConfig(
            mapping_type=mapping_type,
            calculation_method=calculation_method,
            default_thresholds=default_thresholds,
            description=description
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        return config
    
    async def get_default_config(self, mapping_type: str) -> Optional[COPOMappingConfig]:
        """Get default configuration for mapping type"""
        
        return self.db.query(COPOMappingConfig).filter(
            COPOMappingConfig.mapping_type == mapping_type,
            COPOMappingConfig.is_active == True
        ).first()
    
    # region: Helper Methods
    def _get_course_by_id(self, course_id: str):
        """Get course by ID (placeholder - implement actual course service)"""
        # This would integrate with your course service
        pass
    
    def _get_program_outcome_by_id(self, program_outcome_id: str):
        """Get program outcome by ID (placeholder - implement actual program outcome service)"""
        # This would integrate with your program outcome service
        pass
    
    def _get_course_outcome_by_id(self, course_outcome_id: str):
        """Get course outcome by ID (placeholder - implement actual course outcome service)"""
        # This would integrate with your course outcome service
        pass
    
    def _get_attainment_level(self, percentage: float) -> AttainmentLevel:
        """Get attainment level based on percentage"""
        if percentage >= 90:
            return AttainmentLevel.EXCELLENT
        elif percentage >= 80:
            return AttainmentLevel.VERY_GOOD
        elif percentage >= 70:
            return AttainmentLevel.GOOD
        elif percentage >= 60:
            return AttainmentLevel.SATISFACTORY
        elif percentage >= 40:
            return AttainmentLevel.POOR
        else:
            return AttainmentLevel.NOT_ACHIEVED
    
    def _get_attainment_grade(self, percentage: float) -> AttainmentGrade:
        """Get attainment grade based on percentage"""
        if percentage >= 90:
            return AttainmentGrade.A
        elif percentage >= 80:
            return AttainmentGrade.B
        elif percentage >= 70:
            return AttainmentGrade.C
        elif percentage >= 60:
            return AttainmentGrade.D
        elif percentage >= 40:
            return AttainmentGrade.E
        else:
            return AttainmentGrade.F
    
    async def _calculate_co_attainments(self, batch_results: List[Dict]) -> Dict[str, Any]:
        """Calculate course outcome attainments for batch"""
        co_attainments = {}
        
        for result in batch_results:
            for detail in result["attainment_details"]:
                co_id = detail["co_id"]
                if co_id not in co_attainments:
                    co_attainments[co_id] = []
                co_attainments[co_id].append(detail["percentage"])
        
        # Calculate statistics for each course outcome
        co_stats = {}
        for co_id, percentages in co_attainments.items():
            co_stats[co_id] = {
                "average": sum(percentages) / len(percentages),
                "max": max(percentages),
                "min": min(percentages),
                "count": len(percentages)
            }
        
        return co_stats
    
    async def _calculate_po_attainments(self, course_id: str, batch_results: List[Dict]) -> Dict[str, Any]:
        """Calculate program outcome attainments for course"""
        mappings = await self.get_mappings_by_course(course_id)
        
        po_attainments = {}
        for mapping in mappings:
            po_id = mapping.program_outcome_id
            if po_id not in po_attainments:
                po_attainments[po_id] = []
        
        # Aggregate by program outcome
        for result in batch_results:
            for detail in result["attainment_details"]:
                po_id = detail["po_id"]
                po_attainments[po_id].append(detail["percentage"])
        
        # Calculate statistics for each program outcome
        po_stats = {}
        for po_id, percentages in po_attainments.items():
            po_stats[po_id] = {
                "average": sum(percentages) / len(percentages),
                "max": max(percentages),
                "min": min(percentages),
                "count": len(percentages)
            }
        
        return po_stats
    
    async def _save_attainment_report(self, batch_summary: Dict[str, Any]) -> AttainmentReport:
        """Save attainment report to database"""
        report = AttainmentReport(
            course_id=batch_summary["course_id"],
            program_outcome_id=batch_summary.get("program_outcome_id"),
            batch_id=batch_summary["batch_id"],
            academic_year=batch_summary["academic_year"],
            semester=batch_summary["semester"],
            total_students=batch_summary["total_students"],
            attainment_data=batch_summary
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    async def _get_attainment_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get attainment data based on filters (placeholder)"""
        # This would query your database based on the provided filters
        return []
    
    async def _generate_report_summary(self, attainment_data: List[Dict]) -> Dict[str, Any]:
        """Generate report summary"""
        return {
            "total_students": len(attainment_data),
            "average_attainment": sum(d.get("overall_attainment_percentage", 0) for d in attainment_data) / len(attainment_data) if attainment_data else 0,
            "highest_attainment": max(d.get("overall_attainment_percentage", 0) for d in attainment_data) if attainment_data else 0,
            "lowest_attainment": min(d.get("overall_attainment_percentage", 0) for d in attainment_data) if attainment_data else 0
        }
    
    async def _analyze_course_outcomes(self, attainment_data: List[Dict]) -> Dict[str, Any]:
        """Analyze course outcomes"""
        # Placeholder implementation
        return {}
    
    async def _analyze_program_outcomes(self, course_id: str, po_id: Optional[str], attainment_data: List[Dict]) -> Dict[str, Any]:
        """Analyze program outcomes"""
        # Placeholder implementation
        return {}
    
    async def _generate_recommendations(self, attainment_data: List[Dict]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if attainment_data:
            avg_attainment = sum(d.get("overall_attainment_percentage", 0) for d in attainment_data) / len(attainment_data)
            
            if avg_attainment < 60:
                recommendations.append("Consider revising teaching methods for better outcome achievement")
            elif avg_attainment < 75:
                recommendations.append("Focus on improving weak course outcomes")
            else:
                recommendations.append("Maintain current teaching standards and continue improvement")
        
        return recommendations
    
    async def _export_pdf_report(self, report_data: Dict) -> str:
        """Export report as PDF (placeholder)"""
        # Would implement PDF generation using libraries like ReportLab
        return "pdf_export_path"
    
    async def _export_excel_report(self, report_data: Dict) -> str:
        """Export report as Excel (placeholder)"""
        # Would implement Excel generation using libraries like openpyxl
        return "excel_export_path"