"""
Feedback Processing Service for Edu-Flow

This service provides comprehensive feedback processing functionality:
- Student feedback collection and management
- Automated feedback analysis (sentiment, keywords, topics)
- Response management and approval workflow
- Report generation and trend analysis
- Campaign management for systematic feedback
- Integration with Excel processing for bulk feedback

Author: Edu-Flow Team
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import uuid

from src.api.deps import get_db
from src.models.feedback import (
    Feedback, FeedbackCategory, FeedbackResponse, FeedbackAnalysis,
    FeedbackReport, FeedbackTemplate, FeedbackCampaign, FeedbackStatus,
    FeedbackResponseStatus, Sentiment
)
from src.services.base_service import BaseService
from src.core.exceptions import NotFoundError, ValidationError, ConfigurationError
from src.core.cache_abstraction import CacheManager, CacheConfig
from src.config.settings import settings

class FeedbackService(BaseService):
    """Feedback Processing Service"""
    
    def __init__(self, db: Session, cache_manager: CacheManager):
        super().__init__(db, cache_manager)
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.cache_key_prefix = "feedback"
        
        # Configuration-based analysis settings
        self.analysis_config = {
            "sentiment_model": self.settings.feedback.get("sentiment_model", "basic"),
            "keyword_extraction": self.settings.feedback.get("keyword_extraction", True),
            "topic_classification": self.settings.feedback.get("topic_classification", True),
            "language": self.settings.feedback.get("language", "en")
        }
        
        # Response templates
        self.response_templates = {
            "positive": "Thank you for your positive feedback! We're glad you had a good experience.",
            "neutral": "Thank you for your feedback. We'll consider your suggestions for improvement.",
            "negative": "We appreciate your constructive feedback and will work to address your concerns.",
            "appreciation": "Thank you for your time and detailed feedback.",
            "suggestion": "Thank you for your valuable suggestions. We'll evaluate and implement them as appropriate."
        }
    
    # region: Basic CRUD Operations
    async def create_feedback(
        self,
        student_id: str,
        course_id: str,
        feedback_data: Dict[str, Any],
        teacher_id: Optional[str] = None,
        anonymous: bool = False,
        semester: Optional[str] = None,
        academic_year: Optional[str] = None
    ) -> Feedback:
        """Create new feedback submission"""
        
        # Validate feedback data
        validated_data = await self._validate_feedback_data(feedback_data)
        
        # Determine academic year and semester if not provided
        if not academic_year:
            academic_year = datetime.now().year
        if not semester:
            semester = self._get_current_semester()
        
        # Create feedback record
        feedback = Feedback(
            student_id=student_id,
            course_id=course_id,
            teacher_id=teacher_id,
            semester=semester,
            academic_year=academic_year,
            feedback_type=validated_data.get("feedback_type", "overall"),
            rating=validated_data.get("rating"),
            overall_rating=validated_data.get("overall_rating"),
            comments=validated_data.get("comments"),
            strengths=validated_data.get("strengths"),
            improvements=validated_data.get("improvements"),
            additional_comments=validated_data.get("additional_comments"),
            anonymous=anonymous,
            scale_used=validated_data.get("scale", "five_point"),
            ratings=validated_data.get("ratings")
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        # Process feedback asynchronously
        asyncio.create_task(self._process_feedback_async(feedback.id))
        
        self.logger.info(f"Created feedback: {feedback.id}")
        return feedback
    
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID"""
        cache_key = f"{self.cache_key_prefix}_feedback_{feedback_id}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Get from database
        feedback = self.db.query(Feedback).filter(
            Feedback.id == feedback_id
        ).first()
        
        if feedback:
            await self.cache_manager.set(cache_key, feedback, ttl=3600)  # 1 hour
        
        return feedback
    
    async def get_feedback(
        self,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        teacher_id: Optional[str] = None,
        semester: Optional[str] = None,
        academic_year: Optional[str] = None,
        feedback_type: Optional[str] = None,
        status: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """Get feedback with filters"""
        cache_key = f"{self.cache_key_prefix}_query_{hash(str(locals()))}"
        
        # Check cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Build query
        query = self.db.query(Feedback)
        
        if student_id:
            query = query.filter(Feedback.student_id == student_id)
        if course_id:
            query = query.filter(Feedback.course_id == course_id)
        if teacher_id:
            query = query.filter(Feedback.teacher_id == teacher_id)
        if semester:
            query = query.filter(Feedback.semester == semester)
        if academic_year:
            query = query.filter(Feedback.academic_year == academic_year)
        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)
        if status:
            query = query.filter(Feedback.status == status)
        if min_rating is not None:
            query = query.filter(Feedback.rating >= min_rating)
        if max_rating is not None:
            query = query.filter(Feedback.rating <= max_rating)
        
        feedback_list = query.order_by(desc(Feedback.submission_date)).limit(limit).all()
        
        if feedback_list:
            await self.cache_manager.set(cache_key, feedback_list, ttl=3600)  # 1 hour
        
        return feedback_list
    
    async def update_feedback(
        self,
        feedback_id: str,
        updates: Dict[str, Any]
    ) -> Feedback:
        """Update feedback"""
        feedback = await self.get_feedback_by_id(feedback_id)
        
        if not feedback:
            raise NotFoundError(f"Feedback not found: {feedback_id}")
        
        # Update allowed fields
        allowed_fields = [
            "status", "rating", "overall_rating", "comments", 
            "strengths", "improvements", "additional_comments",
            "is_processed", "priority_score"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(feedback, field, value)
        
        feedback.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(feedback)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Updated feedback: {feedback_id}")
        return feedback
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback"""
        feedback = await self.get_feedback_by_id(feedback_id)
        
        if not feedback:
            raise NotFoundError(f"Feedback not found: {feedback_id}")
        
        # Remove related responses
        self.db.query(FeedbackResponse).filter(
            FeedbackResponse.feedback_id == feedback_id
        ).delete()
        
        # Remove related analysis
        self.db.query(FeedbackAnalysis).filter(
            FeedbackAnalysis.feedback_id == feedback_id
        ).delete()
        
        self.db.delete(feedback)
        self.db.commit()
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Deleted feedback: {feedback_id}")
        return True
    
    # region: Feedback Analysis
    async def _process_feedback_async(self, feedback_id: str):
        """Asynchronously process feedback"""
        try:
            await self._analyze_feedback(feedback_id)
            await self._generate_response_suggestion(feedback_id)
            await self._calculate_priority_score(feedback_id)
            
            # Update processing status
            feedback = await self.get_feedback_by_id(feedback_id)
            if feedback:
                feedback.is_processed = True
                feedback.processed_date = datetime.utcnow()
                self.db.commit()
                self.db.refresh(feedback)
                
        except Exception as e:
            self.logger.error(f"Error processing feedback {feedback_id}: {str(e)}")
    
    async def _analyze_feedback(self, feedback_id: str):
        """Analyze feedback for sentiment, keywords, and topics"""
        feedback = await self.get_feedback_by_id(feedback_id)
        if not feedback:
            return
        
        analysis_results = {}
        
        # Sentiment analysis
        if self.analysis_config["sentiment_model"]:
            sentiment_score, sentiment_category = await self._analyze_sentiment(
                feedback.comments or ""
            )
            analysis_results["sentiment"] = {
                "score": float(sentiment_score),
                "category": sentiment_category
            }
        
        # Keyword extraction
        if self.analysis_config["keyword_extraction"]:
            keywords = await self._extract_keywords(
                feedback.comments or "",
                feedback.strengths or "",
                feedback.improvements or ""
            )
            analysis_results["keywords"] = keywords
        
        # Topic classification
        if self.analysis_config["topic_classification"]:
            topics = await self._classify_topics(
                feedback.comments or "",
                feedback.feedback_type
            )
            analysis_results["topics"] = topics
        
        # Save analysis
        analysis = FeedbackAnalysis(
            feedback_id=feedback_id,
            analysis_type="comprehensive",
            analysis_results=analysis_results,
            model_version=self.analysis_config["sentiment_model"],
            confidence_score=0.85  # Placeholder confidence
        )
        
        self.db.add(analysis)
        self.db.commit()
        
        # Update feedback with analysis results
        feedback.sentiment_score = analysis_results.get("sentiment", {}).get("score")
        feedback.sentiment_category = analysis_results.get("sentiment", {}).get("category")
        feedback.keyword_analysis = analysis_results.get("keywords")
        feedback.topic_classification = analysis_results.get("topics")
        
        self.db.commit()
        self.db.refresh(feedback)
    
    async def _analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """Analyze sentiment of feedback text"""
        # Simple sentiment analysis (placeholder - replace with actual ML model)
        text_lower = text.lower()
        
        positive_words = ["good", "excellent", "great", "amazing", "wonderful", "fantastic", "love", "best"]
        negative_words = ["bad", "poor", "terrible", "awful", "worst", "hate", "dislike", "problem"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 0.7, "positive"
        elif negative_count > positive_count:
            return -0.7, "negative"
        else:
            return 0.0, "neutral"
    
    async def _extract_keywords(self, *texts: str) -> Dict[str, Any]:
        """Extract keywords from feedback text"""
        # Simple keyword extraction (placeholder - replace with actual NLP)
        all_text = " ".join(texts).lower()
        
        # Common words to exclude
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "this", "that"}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)  # Words with 3+ letters
        words = [word for word in words if word not in stopwords]
        
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return {"keywords": dict(sorted_words[:10]), "total_words": len(words)}
    
    async def _classify_topics(self, text: str, feedback_type: str) -> Dict[str, Any]:
        """Classify feedback topics"""
        # Simple topic classification (placeholder - replace with actual ML model)
        topic_keywords = {
            "course_content": ["content", "material", "syllabus", "curriculum", "topics"],
            "teaching_method": ["teaching", "method", "style", "approach", "delivery"],
            "assessment": ["exam", "test", "assignment", "grading", "evaluation"],
            "infrastructure": ["lab", "classroom", "facility", "equipment", "technology"],
            "administration": ["management", "process", "system", "service", "support"]
        }
        
        text_lower = text.lower()
        topics = {}
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords) or topic == feedback_type:
                topics[topic] = True
            else:
                topics[topic] = False
        
        return {"classified_topics": topics, "confidence": 0.75}  # Placeholder confidence
    
    async def _generate_response_suggestion(self, feedback_id: str):
        """Generate suggested response based on feedback sentiment"""
        feedback = await self.get_feedback_by_id(feedback_id)
        if not feedback:
            return
        
        # Determine response template based on sentiment
        if feedback.sentiment_category == "positive":
            response_type = "positive"
        elif feedback.sentiment_category == "negative":
            response_type = "negative"
        elif feedback.feedback_type == "overall":
            response_type = "appreciation"
        else:
            response_type = "neutral"
        
        # Generate response with feedback-specific content
        base_response = self.response_templates.get(response_type, "")
        
        if feedback.strengths:
            base_response += f"\n\nWe're pleased you found these aspects helpful: {feedback.strengths}"
        
        if feedback.improvements:
            base_response += f"\n\nWe'll address your suggestions: {feedback.improvements}"
        
        # Add action items
        action_items = await self._generate_action_items(feedback)
        if action_items:
            base_response += f"\n\nAction items: {', '.join(action_items)}"
        
        # Save response suggestion
        feedback.response_suggestion = base_response
        self.db.commit()
        self.db.refresh(feedback)
    
    async def _generate_action_items(self, feedback: Feedback) -> List[str]:
        """Generate action items from feedback"""
        action_items = []
        
        if feedback.improvements:
            improvements_text = feedback.improvements.lower()
            if "exam" in improvements_text:
                action_items.append("Review examination process")
            if "assignment" in improvements_text:
                action_items.append("Update assignment structure")
            if "material" in improvements_text:
                action_items.append("Enhance course materials")
            if "communication" in improvements_text:
                action_items.append("Improve communication channels")
            if "support" in improvements_text:
                action_items.append("Increase student support")
        
        return action_items
    
    async def _calculate_priority_score(self, feedback_id: str):
        """Calculate priority score for feedback"""
        feedback = await self.get_feedback_by_id(feedback_id)
        if not feedback:
            return
        
        priority_score = 0
        
        # Rating impact
        if feedback.rating:
            if feedback.rating < 2.0:  # Very low rating
                priority_score += 30
            elif feedback.rating < 3.0:  # Low rating
                priority_score += 20
            elif feedback.rating > 4.5:  # Very high rating
                priority_score -= 10  # Lower priority for positive feedback
        
        # Feedback type impact
        type_weights = {
            "course_content": 10,
            "teaching_method": 15,
            "assessment": 20,
            "infrastructure": 5,
            "administration": 8,
            "overall": 12
        }
        
        feedback_type = feedback.feedback_type
        priority_score += type_weights.get(feedback_type, 5)
        
        # Comment length impact (more detailed feedback gets higher priority)
        if feedback.comments:
            comment_length = len(feedback.comments)
            if comment_length > 500:
                priority_score += 15
            elif comment_length > 200:
                priority_score += 10
        
        # Anonymous feedback impact
        if feedback.anonymous:
            priority_score += 5  # Anonymous feedback might need more attention
        
        # Set priority score (capped at 100)
        feedback.priority_score = min(priority_score, 100)
        self.db.commit()
        self.db.refresh(feedback)
    
    # region: Response Management
    async def create_response(
        self,
        feedback_id: str,
        teacher_id: str,
        response_data: Dict[str, Any],
        course_id: Optional[str] = None
    ) -> FeedbackResponse:
        """Create feedback response"""
        
        required_fields = ["response_text"]
        for field in required_fields:
            if field not in response_data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Get feedback to get course_id if not provided
        if not course_id:
            feedback = await self.get_feedback_by_id(feedback_id)
            if not feedback:
                raise NotFoundError(f"Feedback not found: {feedback_id}")
            course_id = feedback.course_id
        
        response = FeedbackResponse(
            feedback_id=feedback_id,
            teacher_id=teacher_id,
            course_id=course_id,
            response_text=response_data["response_text"],
            action_taken=response_data.get("action_taken"),
            implementation_plan=response_data.get("implementation_plan"),
            timeline=response_data.get("timeline"),
            resources_needed=response_data.get("resources_needed"),
            response_status=FeedbackResponseStatus.DRAFT.value,
            priority_level=response_data.get("priority_level", 1)
        )
        
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Created response: {response.id}")
        return response
    
    async def approve_response(
        self,
        response_id: str,
        approver_id: str,
        approval_comments: Optional[str] = None
    ) -> FeedbackResponse:
        """Approve feedback response"""
        
        response = self.db.query(FeedbackResponse).filter(
            FeedbackResponse.id == response_id
        ).first()
        
        if not response:
            raise NotFoundError(f"Response not found: {response_id}")
        
        response.response_status = FeedbackResponseStatus.APPROVED.value
        response.approved_by = approver_id
        response.approval_date = datetime.utcnow()
        response.approval_comments = approval_comments
        
        self.db.commit()
        self.db.refresh(response)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Approved response: {response_id}")
        return response
    
    # region: Campaign Management
    async def create_campaign(
        self,
        name: str,
        description: str,
        academic_year: str,
        semester: str,
        start_date: datetime,
        end_date: datetime,
        campaign_config: Dict[str, Any]
    ) -> FeedbackCampaign:
        """Create feedback collection campaign"""
        
        required_fields = ["target_audience", "campaign_type", "distribution_method"]
        for field in required_fields:
            if field not in campaign_config:
                raise ValidationError(f"Missing required field: {field}")
        
        campaign = FeedbackCampaign(
            name=name,
            description=description,
            academic_year=academic_year,
            semester=semester,
            start_date=start_date,
            end_date=end_date,
            target_audience=campaign_config["target_audience"],
            campaign_type=campaign_config["campaign_type"],
            distribution_method=campaign_config["distribution_method"],
            reminder_config=campaign_config.get("reminder_config"),
            notification_config=campaign_config.get("notification_config")
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Created campaign: {campaign.id}")
        return campaign
    
    async def get_campaign_responses(
        self,
        campaign_id: str,
        limit: int = 100
    ) -> List[Feedback]:
        """Get responses for a campaign"""
        
        campaign = self.db.query(FeedbackCampaign).filter(
            FeedbackCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise NotFoundError(f"Campaign not found: {campaign_id}")
        
        # Get feedback for this campaign's time period
        feedback_list = self.db.query(Feedback).filter(
            Feedback.academic_year == campaign.academic_year,
            Feedback.semester == campaign.semester
        ).order_by(desc(Feedback.submission_date)).limit(limit).all()
        
        return feedback_list
    
    async def generate_campaign_report(
        self,
        campaign_id: str,
        include_responses: bool = False,
        include_anonymized: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive campaign report"""
        
        campaign = self.db.query(FeedbackCampaign).filter(
            FeedbackCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise NotFoundError(f"Campaign not found: {campaign_id}")
        
        # Get campaign responses
        responses = await self.get_campaign_responses(campaign_id)
        
        # Calculate statistics
        total_responses = len(responses)
        response_rate = (total_responses / 100) * 100  # Assuming 100 target responses
        
        # Rating statistics
        ratings = [r.rating for r in responses if r.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Sentiment analysis
        sentiment_counts = {}
        for response in responses:
            sentiment = response.sentiment_category or "neutral"
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Generate recommendations
        recommendations = await self._generate_campaign_recommendations(responses)
        
        # Generate report
        report = {
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "academic_year": campaign.academic_year,
                "semester": campaign.semester,
                "response_rate": response_rate,
                "total_responses": total_responses
            },
            "statistics": {
                "average_rating": avg_rating,
                "total_responses": total_responses,
                "response_rate": response_rate,
                "sentiment_distribution": sentiment_counts
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
            "include_responses": include_responses,
            "include_anonymized": include_anonymized
        }
        
        return report
    
    async def _generate_campaign_recommendations(self, responses: List[Feedback]) -> List[str]:
        """Generate recommendations based on campaign feedback"""
        recommendations = []
        
        if not responses:
            return recommendations
        
        # Analyze common issues
        issues = []
        for response in responses:
            if response.rating and response.rating < 3.0:
                issues.append(response.feedback_type)
        
        # Generate recommendations based on issues
        if "assessment" in issues:
            recommendations.append("Review and improve assessment methods")
        
        if "teaching_method" in issues:
            recommendations.append("Enhance teaching methods and instructor training")
        
        if "course_content" in issues:
            recommendations.append("Update and improve course content")
        
        if "infrastructure" in issues:
            recommendations.append("Address infrastructure and facility issues")
        
        # Generic recommendation if no specific issues
        if not issues:
            recommendations.append("Maintain current quality standards")
        
        return recommendations
    
    # region: Report Generation
    async def generate_feedback_report(
        self,
        report_config: Dict[str, Any],
        academic_year: Optional[str] = None,
        semester: Optional[str] = None,
        course_id: Optional[str] = None,
        teacher_id: Optional[str] = None
    ) -> FeedbackReport:
        """Generate comprehensive feedback report"""
        
        required_fields = ["report_type", "generated_by"]
        for field in required_fields:
            if field not in report_config:
                raise ValidationError(f"Missing required field: {field}")
        
        # Get feedback data based on filters
        feedback_list = await self.get_feedback(
            academic_year=academic_year,
            semester=semester,
            course_id=course_id,
            teacher_id=teacher_id
        )
        
        # Generate report data
        report_data = await self._generate_report_data(feedback_list, report_config)
        
        # Create report
        report = FeedbackReport(
            report_type=report_config["report_type"],
            academic_year=academic_year or datetime.now().year,
            semester=semester or self._get_current_semester(),
            generated_by=report_config["generated_by"],
            report_data=report_data,
            summary_stats=report_data["summary_statistics"],
            key_findings=report_data["key_findings"],
            trend_analysis=report_data["trend_analysis"],
            recommendations=report_data["recommendations"],
            format_type=report_config.get("format_type", "html"),
            include_individual_responses=report_config.get("include_individual_responses", False),
            include_anonymized_data=report_config.get("include_anonymized_data", True),
            generation_status="completed"
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        # Clear cache
        await self.cache_manager.delete_pattern(f"{self.cache_key_prefix}*")
        
        self.logger.info(f"Generated report: {report.id}")
        return report
    
    async def _generate_report_data(self, feedback_list: List[Feedback], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report data from feedback"""
        
        if not feedback_list:
            return {
                "summary_statistics": {},
                "key_findings": [],
                "trend_analysis": {},
                "recommendations": []
            }
        
        # Basic statistics
        total_responses = len(feedback_list)
        avg_rating = sum(f.rating for f in feedback_list if f.rating is not None) / len([f for f in feedback_list if f.rating is not None]) or 0
        
        # Distribution by feedback type
        type_distribution = {}
        for feedback in feedback_list:
            feedback_type = feedback.feedback_type
            type_distribution[feedback_type] = type_distribution.get(feedback_type, 0) + 1
        
        # Sentiment distribution
        sentiment_distribution = {}
        for feedback in feedback_list:
            sentiment = feedback.sentiment_category or "neutral"
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # Key findings
        key_findings = [
            f"Total feedback responses: {total_responses}",
            f"Average rating: {avg_rating:.2f}",
            f"Most common feedback type: {max(type_distribution.items(), key=lambda x: x[1])[0]}",
            f"Sentiment distribution: {sentiment_distribution}"
        ]
        
        # Recommendations
        recommendations = await self._generate_report_recommendations(feedback_list)
        
        # Trend analysis (placeholder)
        trend_analysis = {
            "rating_trend": "stable",
            "sentiment_trend": "improving",
            "response_volume_trend": "increasing"
        }
        
        return {
            "summary_statistics": {
                "total_responses": total_responses,
                "average_rating": avg_rating,
                "type_distribution": type_distribution,
                "sentiment_distribution": sentiment_distribution
            },
            "key_findings": key_findings,
            "trend_analysis": trend_analysis,
            "recommendations": recommendations
        }
    
    async def _generate_report_recommendations(self, feedback_list: List[Feedback]) -> List[str]:
        """Generate recommendations based on feedback report"""
        recommendations = []
        
        if not feedback_list:
            return recommendations
        
        # Analyze areas needing improvement
        low_rating_feedback = [f for f in feedback_list if f.rating is not None and f.rating < 3.0]
        
        if low_rating_feedback:
            feedback_types = [f.feedback_type for f in low_rating_feedback]
            most_problematic = max(set(feedback_types), key=feedback_types.count)
            
            improvement_areas = {
                "course_content": "Review and update course content",
                "teaching_method": "Enhance teaching methods and provide additional training",
                "assessment": "Revise assessment methods and provide clearer criteria",
                "infrastructure": "Address infrastructure issues and improve facilities",
                "administration": "Improve administrative processes and communication"
            }
            
            recommendation = improvement_areas.get(most_problematic, "Address areas needing improvement")
            recommendations.append(recommendation)
        
        # Positive reinforcement
        high_rating_feedback = [f for f in feedback_list if f.rating is not None and f.rating >= 4.0]
        if high_rating_feedback:
            success_areas = [f.feedback_type for f in high_rating_feedback if f.feedback_type != "overall"]
            if success_areas:
                recommendations.append(f"Continue successful practices in: {', '.join(set(success_areas))}")
        
        return recommendations
    
    # region: Helper Methods
    def _validate_feedback_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feedback data"""
        validated = {}
        
        # Validate feedback type
        if "feedback_type" in data:
            allowed_types = [ft.value for ft in FeedbackType]
            if data["feedback_type"] not in allowed_types:
                raise ValidationError(f"Invalid feedback type: {data['feedback_type']}")
            validated["feedback_type"] = data["feedback_type"]
        
        # Validate rating
        if "rating" in data and data["rating"] is not None:
            rating = float(data["rating"])
            if not (0 <= rating <= 5):
                raise ValidationError("Rating must be between 0 and 5")
            validated["rating"] = rating
        
        # Validate overall rating
        if "overall_rating" in data and data["overall_rating"] is not None:
            rating = float(data["overall_rating"])
            if not (0 <= rating <= 5):
                raise ValidationError("Overall rating must be between 0 and 5")
            validated["overall_rating"] = rating
        
        # Validate scale
        if "scale" in data:
            allowed_scales = [fs.value for fs in FeedbackScale]
            if data["scale"] not in allowed_scales:
                raise ValidationError(f"Invalid scale: {data['scale']}")
            validated["scale"] = data["scale"]
        
        # Copy other fields
        for key, value in data.items():
            if key not in ["feedback_type", "rating", "overall_rating", "scale"]:
                validated[key] = value
        
        return validated
    
    def _get_current_semester(self) -> str:
        """Get current semester based on date"""
        month = datetime.now().month
        if month in [1, 2, 3, 4, 5, 6]:
            return "spring"
        elif month in [7, 8]:
            return "summer"
        else:
            return "fall"