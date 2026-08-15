"""
CO-PO Mapping Models for Edu-Flow

This module defines the data models for Course Outcome (CO) to Program Outcome (PO) mapping:
- COPOMapping: Maps course outcomes to program outcomes
- AttainmentLevel: Defines different levels of outcome attainment
- MappingCalculation: Contains calculation methods for attainment analysis

Author: Edu-Flow Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid

from src.infrastructure.models.base_model import Base

class AttainmentLevel(Enum):
    """Enumeration of different attainment levels"""
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    POOR = "poor"
    NOT_ACHIEVED = "not_achieved"

class AttainmentGrade(Enum):
    """Enumeration for attainment grade mapping"""
    A = "A"  # 5 - Excellent
    B = "B"  # 4 - Very Good
    C = "C"  # 3 - Good
    D = "D"  # 2 - Satisfactory
    E = "E"  # 1 - Poor
    F = "F"  # 0 - Not Achieved

class COPOMapping(Base):
    """Course Outcome to Program Outcome mapping model"""
    
    __tablename__ = "co_po_mapping"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    program_outcome_id = Column(String, nullable=False)
    course_outcome_id = Column(String, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)  # Weight of this mapping
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    course = relationship("Course", foreign_keys=[course_id])
    program_outcome = relationship("ProgramOutcome")
    course_outcome = relationship("CourseOutcome")
    
    # Configuration-based attributes
    attainment_thresholds = Column(Dict, nullable=True)  # Custom attainment thresholds
    mapping_description = Column(Text, nullable=True)
    mapping_type = Column(String, default="direct", nullable=True)  # direct, indirect, assessment
    
    def calculate_attainment(self, student_scores: Dict[str, float]) -> Dict[str, Any]:
        """Calculate attainment level based on student scores"""
        attainment_data = {
            "co_id": self.course_outcome_id,
            "po_id": self.program_outcome_id,
            "mapping_id": self.id,
            "weight": self.weight,
            "scores": student_scores,
            "attainment_level": None,
            "attainment_grade": None,
            "percentage": 0.0
        }
        
        # Calculate weighted average score
        total_score = 0.0
        count = 0
        
        for score_key, score_value in student_scores.items():
            if score_key in [self.course_outcome_id, f"{self.course_outcome_id}_score"]:
                # Apply weight if specified
                weighted_score = score_value * self.weight
                total_score += weighted_score
                count += 1
        
        if count > 0:
            percentage = (total_score / count) * 100
            attainment_data["percentage"] = percentage
            
            # Determine attainment level based on percentage
            attainment_data["attainment_level"] = self._get_attainment_level(percentage)
            attainment_data["attainment_grade"] = self._get_attainment_grade(percentage)
        
        return attainment_data
    
    def _get_attainment_level(self, percentage: float) -> AttainmentLevel:
        """Determine attainment level based on percentage"""
        thresholds = self.attainment_thresholds or {
            "excellent": 90,
            "very_good": 80,
            "good": 70,
            "satisfactory": 60,
            "poor": 40
        }
        
        if percentage >= thresholds.get("excellent", 90):
            return AttainmentLevel.EXCELLENT
        elif percentage >= thresholds.get("very_good", 80):
            return AttainmentLevel.VERY_GOOD
        elif percentage >= thresholds.get("good", 70):
            return AttainmentLevel.GOOD
        elif percentage >= thresholds.get("satisfactory", 60):
            return AttainmentLevel.SATISFACTORY
        elif percentage >= thresholds.get("poor", 40):
            return AttainmentLevel.POOR
        else:
            return AttainmentLevel.NOT_ACHIEVED
    
    def _get_attainment_grade(self, percentage: float) -> AttainmentGrade:
        """Convert percentage to letter grade"""
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

class CourseOutcome(Base):
    """Course outcome model"""
    
    __tablename__ = "course_outcomes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    outcome_code = Column(String, nullable=False)  # CO1, CO2, etc.
    outcome_description = Column(Text, nullable=False)
    outcome_type = Column(String, default="cognitive", nullable=True)  # cognitive, psychomotor, affective
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    course = relationship("Course")
    copo_mappings = relationship("COPOMapping", foreign_keys="COPOMapping.course_outcome_id")

class ProgramOutcome(Base):
    """Program outcome model"""
    
    __tablename__ = "program_outcomes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outcome_code = Column(String, nullable=False)  # PO1, PO2, etc.
    outcome_description = Column(Text, nullable=False)
    outcome_type = Column(String, default="knowledge", nullable=True)  # knowledge, skill, attitude
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    copo_mappings = relationship("COPOMapping", foreign_keys="COPOMapping.program_outcome_id")

class AttainmentReport(Base):
    """Attainment report model"""
    
    __tablename__ = "attainment_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    program_outcome_id = Column(String, ForeignKey("program_outcomes.id"), nullable=False)
    batch_id = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    total_students = Column(Integer, nullable=False)
    attainment_data = Column(Dict, nullable=False)  # JSON containing all attainment calculations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    course = relationship("Course")
    program_outcome = relationship("ProgramOutcome")

class COPOMappingConfig(Base):
    """Configuration for CO-PO mapping calculations"""
    
    __tablename__ = "co_po_mapping_config"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mapping_type = Column(String, nullable=False)  # direct, indirect, assessment
    calculation_method = Column(String, default="weighted_average", nullable=True)  # weighted_average, maximum, minimum
    default_thresholds = Column(Dict, nullable=True)  # Default attainment thresholds
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to many mappings
    mappings = relationship("COPOMapping")