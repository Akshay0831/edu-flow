"""
Course Recommendation Service

This service provides intelligent course recommendations based on:
- Student performance history
- Learning goals and preferences
- Course prerequisites
- Student interests and strengths
- Market demand and trends

Author: Edu-Flow Team
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from .registry import ServiceInstance
from .config import AIServiceConfig, ModelConfig, config_manager

logger = logging.getLogger(__name__)


@dataclass
class StudentProfile:
    """Student profile for recommendation"""
    student_id: str
    name: str
    current_program: str
    current_semester: int
    gpa: float
    interests: List[str]
    strengths: List[str]
    preferred_learning_style: str
    career_goals: List[str]


@dataclass
class CourseRecommendation:
    """Individual course recommendation"""
    course_id: str
    course_name: str
    course_category: str
    recommended: bool
    confidence: float
    reason: str
    prerequisites_met: bool
    difficulty_level: str
    estimated_score: float
    recommended_when: str  # semester
    practical_experience_required: bool


@dataclass
class CourseRecommendationsResult:
    """Complete recommendation result"""
    student_profile: StudentProfile
    recommendations: List[CourseRecommendation]
    total_score: float
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]


class CourseRecommendationService:
    """Service for generating course recommendations"""
    
    def __init__(self, config: AIServiceConfig, model_config: ModelConfig):
        """
        Initialize course recommendation service
        
        Args:
            config: Service configuration
            model_config: Model configuration
        """
        self.config = config
        self.model_config = model_config
        self._instance: Optional[ServiceInstance] = None
        self._recommendation_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: int = config_manager.get_cache_config().ttl
        
    def set_instance(self, instance: ServiceInstance):
        """Set service instance"""
        self._instance = instance
    
    async def get_recommendations(
        self,
        student_profile: StudentProfile,
        semester: int = None,
        limit: int = 5,
        preferences: Dict[str, Any] = None
    ) -> CourseRecommendationsResult:
        """
        Get course recommendations for a student
        
        Args:
            student_profile: Student profile
            semester: Target semester (default: current semester + 1)
            limit: Maximum number of recommendations
            preferences: Additional preference filters
            
        Returns:
            CourseRecommendationsResult: Recommendation result
        """
        if semester is None:
            semester = student_profile.current_semester + 1
        
        # Check cache
        cache_key = self._generate_cache_key(student_profile.student_id, semester, preferences)
        if cache_key in self._recommendation_cache:
            cached_result = self._recommendation_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < timedelta(seconds=self._cache_ttl):
                logger.info(f"Returning cached recommendations for student {student_profile.student_id}")
                return cached_result['result']
        
        # Generate recommendations
        logger.info(f"Generating course recommendations for student {student_profile.student_id}")
        
        # Get available courses
        available_courses = await self._fetch_available_courses(student_profile)
        
        # Get student's academic history
        academic_history = await self._fetch_academic_history(student_profile)
        
        # Get student's course completions
        completed_courses = await self._fetch_completed_courses(student_profile)
        
        # Generate recommendations using ML model
        recommendations = await self._generate_recommendations(
            student_profile=student_profile,
            available_courses=available_courses,
            academic_history=academic_history,
            completed_courses=completed_courses,
            semester=semester,
            preferences=preferences or {}
        )
        
        # Sort and limit recommendations
        recommendations = sorted(recommendations, key=lambda x: x.confidence, reverse=True)[:limit]
        
        # Calculate totals
        total_score = sum(r.confidence for r in recommendations)
        avg_confidence = total_score / len(recommendations) if recommendations else 0.0
        
        result = CourseRecommendationsResult(
            student_profile=student_profile,
            recommendations=recommendations,
            total_score=total_score,
            confidence=avg_confidence,
            timestamp=datetime.now(),
            metadata={
                "semester": semester,
                "total_available_courses": len(available_courses),
                "total_completed_courses": len(completed_courses),
                "algorithm": "collaborative_filtering",
                "filters_applied": list(preferences.keys()) if preferences else [],
            }
        )
        
        # Cache result
        self._recommendation_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now()
        }
        
        logger.info(f"Generated {len(recommendations)} recommendations for student {student_profile.student_id}")
        
        return result
    
    async def _fetch_available_courses(self, student_profile: StudentProfile) -> List[Dict[str, Any]]:
        """Fetch available courses for student's program"""
        # TODO: Implement actual database query
        # This would query the database for courses available in the student's program
        logger.debug(f"Fetching available courses for {student_profile.student_id}")
        
        return []
    
    async def _fetch_academic_history(self, student_profile: StudentProfile) -> List[Dict[str, Any]]:
        """Fetch student's academic history"""
        # TODO: Implement actual database query
        logger.debug(f"Fetching academic history for {student_profile.student_id}")
        
        return []
    
    async def _fetch_completed_courses(self, student_profile: StudentProfile) -> List[str]:
        """Fetch list of completed course IDs"""
        # TODO: Implement actual database query
        logger.debug(f"Fetching completed courses for {student_profile.student_id}")
        
        return []
    
    async def _generate_recommendations(
        self,
        student_profile: StudentProfile,
        available_courses: List[Dict[str, Any]],
        academic_history: List[Dict[str, Any]],
        completed_courses: List[str],
        semester: int,
        preferences: Dict[str, Any]
    ) -> List[CourseRecommendation]:
        """Generate course recommendations using ML model"""
        # TODO: Implement actual recommendation algorithm
        # This would use the ML model to generate recommendations
        logger.debug(f"Generating recommendations using ML model")
        
        # Placeholder recommendations
        recommendations = []
        
        for course in available_courses:
            recommendation = CourseRecommendation(
                course_id=course.get('id', ''),
                course_name=course.get('name', ''),
                course_category=course.get('category', ''),
                recommended=True,
                confidence=0.7 + (0.3 * len(student_profile.interests) / len(available_courses)),
                reason=f"Based on interest in {student_profile.interests[0]}",
                prerequisites_met=True,
                difficulty_level=course.get('difficulty', 'medium'),
                estimated_score=student_profile.gpa + 0.5,
                recommended_when=semester,
                practical_experience_required=course.get('requires_practical', False)
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_cache_key(self, student_id: str, semester: int, preferences: Dict[str, Any]) -> str:
        """Generate cache key for recommendations"""
        import hashlib
        pref_str = json.dumps(preferences, sort_keys=True) if preferences else ""
        key_str = f"{student_id}_{semester}_{pref_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get_personalized_path(self, student_profile: StudentProfile) -> Dict[str, Any]:
        """
        Get personalized learning path
        
        Args:
            student_profile: Student profile
            
        Returns:
            Dict[str, Any]: Personalized learning path
        """
        logger.info(f"Generating personalized learning path for {student_profile.student_id}")
        
        # Get semester-wise recommendations
        recommendations = []
        for semester in range(student_profile.current_semester + 1, student_profile.current_semester + 6):
            result = await self.get_recommendations(student_profile, semester, limit=3)
            recommendations.extend(result.recommendations)
        
        # Group by semester
        learning_path = {}
        for rec in recommendations:
            if rec.recommended_when not in learning_path:
                learning_path[rec.recommended_when] = []
            learning_path[rec.recommended_when].append(rec)
        
        return {
            "student_id": student_profile.student_id,
            "current_semester": student_profile.current_semester,
            "learning_path": learning_path,
            "total_courses": len(recommendations),
            "personalization_strategy": "sequential_semester_planning",
        }
    
    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            return {
                "status": "healthy",
                "service_name": "course_recommendation",
                "configured": self.config is not None,
                "model_configured": self.model_config is not None,
                "cache_size": len(self._recommendation_cache),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
