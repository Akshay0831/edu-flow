"""
Test script for Feedback Processing API

This script provides basic tests for the feedback processing API endpoints:
- Submit feedback test
- Get feedback test
- Update feedback test
- Response management test
- Analytics test
- Campaign test

Author: Edu-Flow Team
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
import unittest
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.v1 import app
from src.core.database_abstraction import DatabaseManager
from src.core.service_container import get_service_container
from src.models.feedback import Feedback, FeedbackResponse, FeedbackCampaign, FeedbackReport
from src.services.feedback_service import FeedbackService


class TestFeedbackAPI(unittest.TestCase):
    """Test class for Feedback Processing API"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        
        # Mock database
        self.db_manager = Mock(spec=DatabaseManager)
        self.db_session = Mock()
        self.db_manager.get_session.return_value = self.db_session
        
        # Mock service container
        self.service_container = Mock()
        self.feedback_service = Mock(spec=FeedbackService)
        self.service_container.get_feedback_service.return_value = self.feedback_service
        
        # Mock JWT token
        self.valid_token = "mock.jwt.token"
        self.headers = {"Authorization": f"Bearer {self.valid_token}"}
        
        # Mock current user
        self.mock_user = {
            "user_id": "test_student_1",
            "role": "student",
            "email": "test@student.edu",
            "full_name": "Test Student"
        }
    
    def test_submit_feedback(self):
        """Test feedback submission endpoint"""
        # Mock feedback data
        feedback_data = {
            "course_id": "course_1",
            "feedback_type": "course_content",
            "rating": 4.5,
            "comments": "Great course content!"
        }
        
        # Mock service response
        mock_feedback = Mock()
        mock_feedback.__dict__ = {
            "id": "feedback_1",
            "student_id": "test_student_1",
            "course_id": "course_1",
            "feedback_type": "course_content",
            "rating": 4.5,
            "comments": "Great course content!",
            "submission_date": datetime.now()
        }
        self.feedback_service.create_feedback.return_value = mock_feedback
        
        # Make API call
        response = self.client.post(
            "/feedback/submit",
            json=feedback_data,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)
        self.assertIn("feedback_1", response.json()["data"]["id"])
        
        # Verify service call
        self.feedback_service.create_feedback.assert_called_once()
    
    def test_get_feedback(self):
        """Test get feedback endpoint"""
        feedback_id = "feedback_1"
        
        # Mock service response
        mock_feedback = Mock()
        mock_feedback.__dict__ = {
            "id": feedback_id,
            "student_id": "test_student_1",
            "course_id": "course_1",
            "feedback_type": "course_content",
            "rating": 4.5,
            "comments": "Great course content!"
        }
        self.feedback_service.get_feedback_by_id.return_value = mock_feedback
        
        # Make API call
        response = self.client.get(
            f"/feedback/{feedback_id}",
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["id"], feedback_id)
        
        # Verify service call
        self.feedback_service.get_feedback_by_id.assert_called_once_with(feedback_id)
    
    def test_get_feedback_list(self):
        """Test get feedback list endpoint"""
        # Mock service response
        mock_feedback_list = [
            Mock(),
            Mock()
        ]
        mock_feedback_list[0].__dict__ = {
            "id": "feedback_1",
            "student_id": "test_student_1",
            "course_id": "course_1",
            "rating": 4.5
        }
        mock_feedback_list[1].__dict__ = {
            "id": "feedback_2",
            "student_id": "test_student_2",
            "course_id": "course_2",
            "rating": 3.0
        }
        self.feedback_service.get_feedback.return_value = mock_feedback_list
        
        # Make API call
        response = self.client.get(
            "/feedback/?course_id=course_1",
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(len(response.json()["data"]), 2)
        
        # Verify service call
        self.feedback_service.get_feedback.assert_called_once()
    
    def test_update_feedback(self):
        """Test update feedback endpoint"""
        feedback_id = "feedback_1"
        updates = {"status": "analyzed"}
        
        # Mock service response
        mock_feedback = Mock()
        mock_feedback.__dict__ = {
            "id": feedback_id,
            "student_id": "test_student_1",
            "course_id": "course_1",
            "feedback_type": "course_content",
            "rating": 4.5,
            "status": "analyzed"
        }
        self.feedback_service.update_feedback.return_value = mock_feedback
        
        # Make API call
        response = self.client.put(
            f"/feedback/{feedback_id}",
            json=updates,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["status"], "analyzed")
        
        # Verify service call
        self.feedback_service.update_feedback.assert_called_once_with(feedback_id, updates)
    
    def test_analyze_feedback(self):
        """Test analyze feedback endpoint"""
        feedback_id = "feedback_1"
        
        # Mock service response
        mock_feedback = Mock()
        mock_feedback.__dict__ = {
            "id": feedback_id,
            "status": "analyzed",
            "sentiment_category": "positive",
            "priority_score": 75
        }
        
        # Mock service calls
        self.feedback_service.get_feedback_by_id.return_value = mock_feedback
        self.feedback_service._analyze_feedback.return_value = None
        self.feedback_service._generate_response_suggestion.return_value = None
        self.feedback_service._calculate_priority_score.return_value = None
        
        # Make API call
        response = self.client.post(
            f"/feedback/{feedback_id}/analyze",
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["status"], "analyzed")
        
        # Verify service calls
        self.feedback_service._analyze_feedback.assert_called_once_with(feedback_id)
        self.feedback_service._generate_response_suggestion.assert_called_once_with(feedback_id)
        self.feedback_service._calculate_priority_score.assert_called_once_with(feedback_id)
    
    def test_create_response(self):
        """Test create response endpoint"""
        feedback_id = "feedback_1"
        response_data = {
            "response_text": "Thank you for your feedback!",
            "course_id": "course_1"
        }
        
        # Mock service response
        mock_response = Mock()
        mock_response.__dict__ = {
            "id": "response_1",
            "feedback_id": feedback_id,
            "teacher_id": "test_teacher_1",
            "response_text": "Thank you for your feedback!",
            "response_date": datetime.now()
        }
        self.feedback_service.create_response.return_value = mock_response
        
        # Make API call
        response = self.client.post(
            f"/feedback/{feedback_id}/response",
            json=response_data,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["feedback_id"], feedback_id)
        
        # Verify service call
        self.feedback_service.create_response.assert_called_once()
    
    def test_approve_response(self):
        """Test approve response endpoint"""
        response_id = "response_1"
        approval_data = {
            "approval_comments": "Approved with minor changes"
        }
        
        # Mock service response
        mock_response = Mock()
        mock_response.__dict__ = {
            "id": response_id,
            "status": "approved",
            "approval_comments": "Approved with minor changes"
        }
        self.feedback_service.approve_response.return_value = mock_response
        
        # Make API call
        response = self.client.put(
            f"/feedback/responses/{response_id}/approve",
            json=approval_data,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["status"], "approved")
        
        # Verify service call
        self.feedback_service.approve_response.assert_called_once()
    
    def test_generate_report(self):
        """Test generate report endpoint"""
        report_config = {
            "report_type": "course_report",
            "generated_by": "teacher_1",
            "academic_year": "2023",
            "semester": "fall"
        }
        
        # Mock service response
        mock_report = Mock()
        mock_report.__dict__ = {
            "id": "report_1",
            "report_type": "course_report",
            "generated_by": "teacher_1",
            "report_data": {"summary": "Great course feedback"},
            "generation_status": "completed"
        }
        self.feedback_service.generate_feedback_report.return_value = mock_report
        
        # Make API call
        response = self.client.post(
            "/feedback/reports/generate",
            json=report_config,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["report_type"], "course_report")
        
        # Verify service call
        self.feedback_service.generate_feedback_report.assert_called_once()
    
    def test_get_analytics(self):
        """Test get analytics endpoint"""
        course_id = "course_1"
        
        # Mock analytics data
        analytics_data = {
            "course_id": course_id,
            "total_feedback": 10,
            "average_rating": 4.2,
            "rating_distribution": {"5": 5, "4": 3, "3": 2},
            "sentiment_distribution": {"positive": 6, "neutral": 3, "negative": 1}
        }
        
        # Mock service response
        self.feedback_service.get_feedback.return_value = []
        
        # Make API call
        response = self.client.get(
            f"/feedback/analytics/course/{course_id}",
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertIn("course_id", response.json()["data"])
        
        # Verify service call
        self.feedback_service.get_feedback.assert_called_once()
    
    def test_create_campaign(self):
        """Test create campaign endpoint"""
        campaign_data = {
            "name": "Fall 2023 Feedback Campaign",
            "description": "Collecting feedback for Fall 2023 courses",
            "academic_year": "2023",
            "semester": "fall",
            "start_date": "2023-08-01T00:00:00",
            "end_date": "2023-12-01T00:00:00",
            "campaign_config": {"target_audience": "students"}
        }
        
        # Mock service response
        mock_campaign = Mock()
        mock_campaign.__dict__ = {
            "id": "campaign_1",
            "name": "Fall 2023 Feedback Campaign",
            "academic_year": "2023",
            "semester": "fall",
            "start_date": datetime.fromisoformat("2023-08-01T00:00:00"),
            "end_date": datetime.fromisoformat("2023-12-01T00:00:00")
        }
        self.feedback_service.create_campaign.return_value = mock_campaign
        
        # Make API call
        response = self.client.post(
            "/feedback/campaigns",
            json=campaign_data,
            headers=self.headers
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(response.json()["data"]["name"], "Fall 2023 Feedback Campaign")
        
        # Verify service call
        self.feedback_service.create_campaign.assert_called_once()


class TestFeedbackService(unittest.TestCase):
    """Test class for Feedback Service"""
    
    def setUp(self):
        """Set up test environment"""
        self.feedback_service = FeedbackService("test_feedback_service")
        self.db_session = Mock()
        
        # Mock feedback model
        self.mock_feedback = Mock()
        self.mock_feedback.__dict__ = {
            "id": "feedback_1",
            "student_id": "test_student_1",
            "course_id": "course_1",
            "feedback_type": "course_content",
            "rating": 4.5,
            "submission_date": datetime.now()
        }
    
    def test_analyze_feedback(self):
        """Test feedback analysis"""
        feedback_id = "feedback_1"
        
        # Mock database
        self.feedback_service.db = Mock()
        self.feedback_service.db.query.return_value.filter.return_value.first.return_value = self.mock_feedback
        
        # Mock analysis methods
        self.feedback_service._analyze_text = Mock(return_value={"sentiment": "positive"})
        self.feedback_service._extract_keywords = Mock(return_value=["great", "content"])
        self.feedback_service._identify_areas = Mock(return_value=["course_content"])
        
        # Mock update
        self.feedback_service.db.commit = Mock()
        
        # Call method
        asyncio.run(self.feedback_service._analyze_feedback(feedback_id))
        
        # Verify calls
        self.feedback_service.db.commit.assert_called_once()
    
    def test_generate_response_suggestion(self):
        """Test response suggestion generation"""
        feedback_id = "feedback_1"
        
        # Mock database
        self.feedback_service.db = Mock()
        self.feedback_service.db.query.return_value.filter.return_value.first.return_value = self.mock_feedback
        
        # Mock suggestion method
        self.feedback_service._generate_ai_suggestion = Mock(return_value="Thank you for your feedback!")
        
        # Mock update
        self.feedback_service.db.commit = Mock()
        
        # Call method
        asyncio.run(self.feedback_service._generate_response_suggestion(feedback_id))
        
        # Verify calls
        self.feedback_service.db.commit.assert_called_once()
    
    def test_calculate_priority_score(self):
        """Test priority score calculation"""
        feedback_id = "feedback_1"
        
        # Mock database
        self.feedback_service.db = Mock()
        self.feedback_service.db.query.return_value.filter.return_value.first.return_value = self.mock_feedback
        
        # Mock update
        self.feedback_service.db.commit = Mock()
        
        # Call method
        asyncio.run(self.feedback_service._calculate_priority_score(feedback_id))
        
        # Verify calls
        self.feedback_service.db.commit.assert_called_once()


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)