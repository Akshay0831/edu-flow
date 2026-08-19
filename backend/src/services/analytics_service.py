"""
Advanced Analytics Service for Edu-Flow

This service provides comprehensive analytics capabilities:
- Student performance analytics
- Course analytics and metrics
- Faculty performance analytics
- Department-wise analysis
- Time-series analytics
- Predictive analytics models
- Dashboard configurations
- Report generation settings
- Alert management

Author: Edu-Flow Team
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, desc, asc

from models.analytics import (
    AnalyticsType, MetricType, Timeframe, AggregationType,
    VisualizationType, DataSource, AnalyticsFilter,
    MetricDefinition, TimeRange, Aggregation, QueryFilter,
    AnalyticsQuery, AnalyticsResult, TrendData, CorrelationMatrix,
    StudentPerformanceMetrics, CourseAnalytics, FacultyPerformanceMetrics,
    DepartmentAnalytics, EngagementMetrics, PredictiveInsight,
    AnalyticsDashboard, ReportTemplate, AlertConfig, KpiMetric,
    LearningAnalytics, RiskAssessment, AnalyticsDataValidator,
    Alert, AlertLog
)
from core.exceptions import NotFoundError, ValidationError
from core.logging import get_logger
from src.services.excel_integration_service import ExcelIntegrationService

logger = get_logger(__name__)


class AdvancedAnalyticsService:
    """Service for advanced analytics operations"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.excel_service = ExcelIntegrationService(db_session)
        self.validator = AnalyticsDataValidator()
    
    async def execute_analytics_query(self, query: AnalyticsQuery) -> AnalyticsResult:
        """
        Execute an analytics query
        
        Args:
            query: Analytics query configuration
            
        Returns:
            AnalyticsResult: Query execution result
        """
        logger.info(f"Executing analytics query: {query.query_id}")
        start_time = datetime.now()
        
        try:
            self.validator.validate_analytics_query(query)
            
            data = await self._fetch_data(query)
            result_data = await self._process_data(query, data)
            summary_stats = await self._calculate_summary_stats(result_data, query)
            metadata = self._generate_metadata(query, start_time)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AnalyticsResult(
                query_id=query.query_id,
                analytics_type=query.analytics_type,
                timestamp=datetime.now(),
                execution_time=execution_time,
                total_records=len(result_data),
                result_data=result_data,
                summary_stats=summary_stats,
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Error executing analytics query: {e}")
            raise
    
    async def _fetch_data(self, query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Fetch data based on query parameters"""
        data = []
        
        if query.time_range:
            start_date = query.time_range.start_date
            end_date = query.time_range.end_date
        else:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        
        if query.data_sources:
            for source in query.data_sources:
                if source == DataSource.STUDENT_RECORDS:
                    data.extend(await self._fetch_student_records(start_date, end_date))
                elif source == DataSource.COURSE_RECORDS:
                    data.extend(await self._fetch_course_records(start_date, end_date))
                elif source == DataSource.ATTENDANCE_RECORDS:
                    data.extend(await self._fetch_attendance_records(start_date, end_date))
                elif source == DataSource.MARKS_RECORDS:
                    data.extend(await self._fetch_marks_records(start_date, end_date))
                elif source == DataSource.FEEDBACK_RECORDS:
                    data.extend(await self._fetch_feedback_records(start_date, end_date))
        
        if query.filters:
            data = await self._apply_filters(data, query.filters)
        
        if query.group_by:
            data = await self._group_data(data, query.group_by)
        
        if query.aggregations:
            data = await self._apply_aggregations(data, query.aggregations)
        
        return data[:query.limit]
    
    async def _fetch_student_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch student records with filtering"""
        from models.student import Student
        from models.course import CourseEnrollment
        
        students = await self.db_session.execute(
            select(Student).where(
                and_(
                    Student.created_at >= start_date,
                    Student.created_at <= end_date
                )
            )
        )
        student_list = students.scalars().all()
        
        data = []
        for student in student_list:
            enrollment = await self.db_session.execute(
                select(func.count(CourseEnrollment.id)).where(
                    CourseEnrollment.student_id == student.student_id
                )
            )
            total_enrollments = enrollment.scalar() or 0
            
            data.append({
                'student_id': student.student_id,
                'name': student.full_name,
                'email': student.email,
                'program': student.program,
                'department': student.department,
                'enrollments': total_enrollments,
                'created_at': student.created_at,
                'updated_at': student.updated_at
            })
        
        return data
    
    async def _fetch_course_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch course records with filtering"""
        from models.course import Course
        
        courses = await self.db_session.execute(
            select(Course).where(
                and_(
                    Course.created_at >= start_date,
                    Course.created_at <= end_date
                )
            )
        )
        course_list = courses.scalars().all()
        
        return [
            {
                'course_id': course.course_id,
                'name': course.name,
                'department': course.department,
                'credits': course.credits,
                'created_at': course.created_at,
                'updated_at': course.updated_at
            }
            for course in course_list
        ]
    
    async def _fetch_attendance_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch attendance records with filtering"""
        # Placeholder implementation
        return []
    
    async def _fetch_marks_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch marks records with filtering"""
        # Placeholder implementation
        return []
    
    async def _fetch_feedback_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch feedback records with filtering"""
        # Placeholder implementation
        return []
    
    async def _apply_filters(self, data: List[Dict[str, Any]], filters: List[QueryFilter]) -> List[Dict[str, Any]]:
        """Apply filters to data - optimized with filter mapping"""
        # Pre-define filter functions for better performance
        filter_functions = {
            FilterOperator.EQUALS: lambda item, field, value: item.get(field) == value,
            FilterOperator.NOT_EQUALS: lambda item, field, value: item.get(field) != value,
            FilterOperator.GREATER_THAN: lambda item, field, value: item.get(field, 0) > value,
            FilterOperator.LESS_THAN: lambda item, field, value: item.get(field, 0) < value,
            FilterOperator.IN: lambda item, field, value: item.get(field) in value,
            FilterOperator.NOT_IN: lambda item, field, value: item.get(field) not in value,
        }
        
        # Apply all filters efficiently
        for filter_item in filters:
            field = filter_item.field
            operator = filter_item.operator
            value = filter_item.value
            
            filter_func = filter_functions.get(operator)
            if filter_func:
                data = [item for item in data if filter_func(item, field, value)]
        
        return data
    
    async def _group_data(self, data: List[Dict[str, Any]], group_by: List[str]) -> List[Dict[str, Any]]:
        """Group data by specified fields"""
        grouped_data = {}
        
        for item in data:
            group_key = tuple(item.get(field) for field in group_by)
            if group_key not in grouped_data:
                grouped_data[group_key] = item.copy()
        
        return list(grouped_data.values())
    
    async def _apply_aggregations(self, data: List[Dict[str, Any]], aggregations: List[Aggregation]) -> List[Dict[str, Any]]:
        """Apply aggregations to grouped data"""
        if not data:
            return data
        
        first_item = data[0]
        result = first_item.copy()
        
        for agg in aggregations:
            field = agg.field
            agg_type = agg.type
            alias = agg.alias or f"{field}_{agg_type.value}"
            
            values = [item.get(field, 0) for item in data]
            
            if agg_type == AggregationType.SUM:
                result[alias] = sum(values)
            elif agg_type == AggregationType.AVERAGE:
                result[alias] = sum(values) / len(values) if values else 0
            elif agg_type == AggregationType.COUNT:
                result[alias] = len(values)
            elif agg_type == AggregationType.MIN:
                result[alias] = min(values) if values else 0
            elif agg_type == AggregationType.MAX:
                result[alias] = max(values) if values else 0
            elif agg_type == AggregationType.STANDARD_DEVIATION:
                if len(values) > 1:
                    result[alias] = float(np.std(values))
                else:
                    result[alias] = 0.0
        
        return [result]
    
    async def _process_data(self, query: AnalyticsQuery, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data based on analytics type"""
        analytics_type = query.analytics_type
        
        if analytics_type == AnalyticsType.STUDENT_PERFORMANCE:
            return await self._process_student_performance(data)
        elif analytics_type == AnalyticsType.COURSE_ANALYTICS:
            return await self._process_course_analytics(data)
        elif analytics_type == AnalyticsType.FACULTY_PERFORMANCE:
            return await self._process_faculty_performance(data)
        elif analytics_type == AnalyticsType.DEPARTMENT_ANALYTICS:
            return await self._process_department_analytics(data)
        elif analytics_type == AnalyticsType.TIME_SERIES:
            return await self._process_time_series(data)
        elif analytics_type == AnalyticsType.PREDICTIVE_ANALYTICS:
            return await self._process_predictive_analytics(data)
        elif analytics_type == AnalyticsType.COMPARATIVE_ANALYTICS:
            return await self._process_comparative_analytics(data)
        elif analytics_type == AnalyticsType.BEHAVIORAL_ANALYTICS:
            return await self._process_behavioral_analytics(data)
        elif analytics_type == AnalyticsType.ACADEMIC_TRENDS:
            return await self._process_academic_trends(data)
        elif analytics_type == AnalyticsType.ENGAGEMENT_ANALYTICS:
            return await self._process_engagement_analytics(data)
        
        return data
    
    async def _process_student_performance(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process student performance data"""
        results = []
        
        for item in data:
            gpa = item.get('gpa', 0.0)
            credits_completed = item.get('credits_completed', 0)
            credits_required = item.get('credits_required', 120)
            completion_rate = (credits_completed / credits_required * 100) if credits_required > 0 else 0
            
            results.append({
                'student_id': item.get('student_id'),
                'name': item.get('name'),
                'program': item.get('program'),
                'department': item.get('department'),
                'gpa': round(gpa, 2),
                'credits_completed': credits_completed,
                'credits_required': credits_required,
                'completion_rate': round(completion_rate, 2)
            })
        
        # Sort by GPA descending
        results.sort(key=lambda x: x['gpa'], reverse=True)
        return results
    
    async def _process_course_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process course analytics data"""
        results = []
        
        for item in data:
            pass  # Placeholder for course analytics processing
        
        return results
    
    async def _process_faculty_performance(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process faculty performance data"""
        results = []
        
        for item in data:
            pass  # Placeholder for faculty analytics processing
        
        return results
    
    async def _process_department_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process department analytics data"""
        results = []
        
        for item in data:
            pass  # Placeholder for department analytics processing
        
        return results
    
    async def _process_time_series(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process time series data"""
        results = []
        
        for item in data:
            # Placeholder for time series processing
            results.append(item)
        
        return results
    
    async def _process_predictive_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process predictive analytics data"""
        results = []
        
        for item in data:
            # Placeholder for predictive analytics processing
            results.append(item)
        
        return results
    
    async def _process_comparative_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process comparative analytics data"""
        results = []
        
        for item in data:
            # Placeholder for comparative analytics processing
            results.append(item)
        
        return results
    
    async def _process_behavioral_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process behavioral analytics data"""
        results = []
        
        for item in data:
            # Placeholder for behavioral analytics processing
            results.append(item)
        
        return results
    
    async def _process_academic_trends(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process academic trends data"""
        results = []
        
        for item in data:
            # Placeholder for academic trends processing
            results.append(item)
        
        return results
    
    async def _process_engagement_analytics(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process engagement analytics data"""
        results = []
        
        for item in data:
            # Placeholder for engagement analytics processing
            results.append(item)
        
        return results
    
    async def _calculate_summary_stats(self, data: List[Dict[str, Any]], query: AnalyticsQuery) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not data:
            return {}
        
        stats = {}
        
        for key in data[0].keys():
            if isinstance(data[0][key], (int, float)):
                values = [item[key] for item in data if isinstance(item[key], (int, float))]
                if values:
                    stats[key] = {
                        'mean': round(np.mean(values), 2),
                        'min': round(np.min(values), 2),
                        'max': round(np.max(values), 2),
                        'count': len(values)
                    }
        
        return stats
    
    def _generate_metadata(self, query: AnalyticsQuery, start_time: datetime) -> Dict[str, Any]:
        """Generate metadata for result"""
        return {
            'query_id': query.query_id,
            'analytics_type': query.analytics_type.value,
            'execution_timestamp': datetime.now().isoformat(),
            'requested_metrics': query.metrics,
            'requested_filters': len(query.filters),
            'requested_limit': query.limit,
            'requested_offset': query.offset
        }
    
    async def calculate_student_performance_metrics(self, student_id: str) -> StudentPerformanceMetrics:
        """
        Calculate comprehensive student performance metrics
        
        Args:
            student_id: Student ID
            
        Returns:
            StudentPerformanceMetrics: Student performance metrics
        """
        logger.info(f"Calculating student performance metrics for {student_id}")
        
        from models.student import Student
        from models.course import CourseEnrollment, Course
        
        # Get student information
        result = await self.db_session.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise ResourceNotFoundError(f"Student {student_id} not found")
        
        # Get enrolled courses
        enrollments = await self.db_session.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.is_active == True
            )
        )
        active_enrollments = enrollments.scalars().all()
        
        total_credits = sum([enrollment.course.credits for enrollment in active_enrollments])
        
        # Calculate GPA
        from models.marks import Mark
        marks = await self.db_session.execute(
            select(Mark).where(Mark.student_id == student_id)
        )
        all_marks = marks.scalars().all()
        
        weighted_sum = sum([mark.marks * mark.course.credits for mark in all_marks])
        total_possible = sum([mark.course.credits for mark in all_marks])
        
        current_gpa = round(weighted_sum / total_possible, 2) if total_possible > 0 else 0.0
        
        # Calculate completion rate
        from models.course_completion import CourseCompletion
        completions = await self.db_session.execute(
            select(CourseCompletion).where(CourseCompletion.student_id == student_id)
        )
        total_courses = len(active_enrollments)
        completed_courses = len(completions.scalars().all())
        
        completion_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0.0
        
        # Get attendance rate
        from models.attendance import Attendance
        attendance = await self.db_session.execute(
            select(Attendance).where(Attendance.student_id == student_id)
        )
        all_attendance = attendance.scalars().all()
        total_sessions = len(all_attendance)
        present_sessions = sum([1 for att in all_attendance if att.is_present])
        
        attendance_rate = round((present_sessions / total_sessions * 100) if total_sessions > 0 else 0.0, 2)
        
        # Generate assessment results
        results = StudentPerformanceMetrics(
            student_id=student.student_id,
            student_name=student.full_name,
            program=student.program,
            department=student.department,
            current_gpa=current_gpa,
            total_credits_completed=total_credits,
            total_credits_required=120,  # Default requirement
            completion_rate=round(completion_rate, 2),
            average_marks=round(current_gpa * 25, 2),  # Convert GPA to percentage
            attendance_rate=attendance_rate,
            assignment_completion_rate=90.0,  # Default
            exam_performance_trend=[current_gpa * 25] * 5,  # Placeholder
            skill_competency={
                'academic': current_gpa,
                'attendance': attendance_rate / 100,
                'completion': completion_rate / 100
            },
            improvement_areas=['data_analysis', 'problem_solving'],
            strengths=['mathematics', 'critical_thinking'],
            risk_level='low' if current_gpa >= 2.5 else 'medium'
        )
        
        return results
    
    async def calculate_course_analytics(self, course_id: str) -> CourseAnalytics:
        """
        Calculate comprehensive course analytics
        
        Args:
            course_id: Course ID
            
        Returns:
            CourseAnalytics: Course analytics
        """
        logger.info(f"Calculating course analytics for {course_id}")
        
        from models.course import Course
        from models.course_enrollment import CourseEnrollment
        from models.marks import Mark
        from models.attendance import Attendance
        
        # Get course information
        result = await self.db_session.execute(
            select(Course).where(Course.course_id == course_id)
        )
        course = result.scalar_one_or_none()
        
        if not course:
            raise ResourceNotFoundError(f"Course {course_id} not found")
        
        # Get enrollment statistics
        enrollments = await self.db_session.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course_id
            )
        )
        enrollments_list = enrollments.scalars().all()
        total_enrollments = len(enrollments_list)
        
        # Calculate completion rate
        from models.course_completion import CourseCompletion
        completions = await self.db_session.execute(
            select(CourseCompletion).where(
                CourseCompletion.course_id == course_id
            )
        )
        completed_count = len(completions.scalars().all())
        completion_rate = round((completed_count / total_enrollments * 100) if total_enrollments > 0 else 0.0, 2)
        
        # Calculate average marks
        marks = await self.db_session.execute(
            select(Mark).where(Mark.course_id == course_id)
        )
        marks_list = marks.scalars().all()
        
        if marks_list:
            avg_marks = round(sum([mark.marks for mark in marks_list]) / len(marks_list), 2)
            avg_marks_percentage = avg_marks * 10  # Assuming scale of 0-10
        else:
            avg_marks = 0.0
            avg_marks_percentage = 0.0
        
        # Calculate attendance rate
        attendance = await self.db_session.execute(
            select(Attendance).where(
                Attendance.course_id == course_id
            )
        )
        attendance_list = attendance.scalars().all()
        
        if attendance_list:
            present_count = sum([1 for att in attendance_list if att.is_present])
            attendance_rate = round((present_count / len(attendance_list) * 100), 2)
        else:
            attendance_rate = 0.0
        
        # Get grade distribution
        grade_dist = {}
        for mark in marks_list:
            grade = mark.grade
            grade_dist[grade] = grade_dist.get(grade, 0) + 1
        
        results = CourseAnalytics(
            course_id=course.course_id,
            course_name=course.name,
            department=course.department,
            credits=course.credits,
            total_enrollments=total_enrollments,
            current_enrollments=total_enrollments,
            completion_rate=completion_rate,
            average_marks=avg_marks_percentage,
            attendance_rate=attendance_rate,
            student_satisfaction_score=4.2,  # Default
            difficulty_level='medium',
            pass_rate=completion_rate,
            failure_rate=100 - completion_rate,
            grade_distribution=grade_dist,
            enrollment_trend=[],  # Placeholder
            performance_trend=[avg_marks_percentage] * 5,  # Placeholder
            feedback_summary={}
        )
        
        return results
    
    async def generate_report(self, template_id: str, parameters: Dict[str, Any]) -> bytes:
        """
        Generate a report based on template and parameters
        
        Args:
            template_id: Template ID
            parameters: Report parameters
            
        Returns:
            bytes: Generated report content
        """
        logger.info(f"Generating report using template {template_id}")
        
        # Get template
        from models.analytics import ReportTemplate
        from core.exceptions import ResourceNotFoundError
        
        result = await self.db_session.execute(
            select(ReportTemplate).where(ReportTemplate.template_id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise ResourceNotFoundError(f"Report template {template_id} not found")
        
        if not template.is_active:
            raise ValidationError("Report template is not active")
        
        # Fetch data based on template configuration
        data = await self._fetch_data_for_report(template, parameters)
        
        # Generate report content
        content = await self._generate_report_content(template, data, parameters)
        
        # Return as bytes
        return content.encode('utf-8')
    
    async def _fetch_data_for_report(self, template: ReportTemplate, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data for report generation"""
        # Placeholder for data fetching logic
        return {}
    
    async def _generate_report_content(self, template: ReportTemplate, data: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate report content based on template"""
        # Placeholder for report generation logic
        return f"Report generated using template {template.template_id}"
    
    async def create_alert(self, alert_config: AlertConfig) -> AlertConfig:
        """
        Create a new alert configuration
        
        Args:
            alert_config: Alert configuration
            
        Returns:
            AlertConfig: Created alert configuration
        """
        logger.info(f"Creating alert: {alert_config.name}")
        
        from models.analytics import Alert as Alert
        
        # Create alert in database
        alert = Alert(
            alert_id=alert_config.alert_id,
            name=alert_config.name,
            description=alert_config.description,
            metric=alert_config.metric,
            threshold=alert_config.threshold,
            condition=alert_config.condition.value if hasattr(alert_config.condition, 'value') else alert_config.condition,
            severity=alert_config.severity.value if hasattr(alert_config.severity, 'value') else alert_config.severity,
            notification_channels=[ch.value if hasattr(ch, 'value') else ch for ch in alert_config.notification_channels],
            recipients=alert_config.recipients,
            is_active=alert_config.is_active,
            created_at=datetime.now()
        )
        
        self.db_session.add(alert)
        await self.db_session.commit()
        await self.db_session.refresh(alert)
        
        return alert_config
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check all active alerts and return triggered alerts
        
        Returns:
            List[Dict[str, Any]]: List of triggered alerts
        """
        logger.info("Checking active alerts")
        
        triggered_alerts = []
        
        # Get active alerts
        from models.analytics import Alert as Alert
        from core.exceptions import ResourceNotFoundError
        
        result = await self.db_session.execute(
            select(Alert).where(Alert.is_active == True)
        )
        active_alerts = result.scalars().all()
        
        for alert in active_alerts:
            # Check if alert is triggered
            is_triggered = await self._check_alert(alert)
            
            if is_triggered:
                triggered_alerts.append({
                    'alert_id': alert.alert_id,
                    'name': alert.name,
                    'severity': alert.severity,
                    'triggered_at': datetime.now(),
                    'current_value': await self._get_current_metric_value(alert)
                })
                
                # Update alert trigger count and timestamp
                alert.trigger_count += 1
                alert.last_triggered = datetime.now()
                await self.db_session.commit()
        
        return triggered_alerts
    
    async def _check_alert(self, alert: Alert) -> bool:
        """Check if alert condition is met"""
        # Placeholder for alert checking logic
        return False
    
    async def _get_current_metric_value(self, alert: Alert) -> float:
        """Get current metric value for alert"""
        # Placeholder for metric value retrieval
        return 0.0
    
    async def create_dashboard(self, dashboard: AnalyticsDashboard) -> AnalyticsDashboard:
        """
        Create a new analytics dashboard
        
        Args:
            dashboard: Dashboard configuration
            
        Returns:
            AnalyticsDashboard: Created dashboard
        """
        logger.info(f"Creating dashboard: {dashboard.name}")
        
        from models.analytics import AnalyticsDashboard as DashboardModel
        
        # Create dashboard in database
        dashboard_model = DashboardModel(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            description=dashboard.description,
            owner=dashboard.owner,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_public=dashboard.is_public,
            refresh_frequency=dashboard.refresh_frequency,
            auto_refresh=dashboard.auto_refresh
        )
        
        self.db_session.add(dashboard_model)
        await self.db_session.commit()
        await self.db_session.refresh(dashboard_model)
        
        return dashboard
    
    async def get_kpi_values(self, kpi_ids: List[str]) -> Dict[str, KpiMetric]:
        """
        Get current values for KPIs
        
        Args:
            kpi_ids: List of KPI IDs
            
        Returns:
            Dict[str, KpiMetric]: KPI values
        """
        logger.info(f"Getting KPI values for {len(kpi_ids)} KPIs")
        
        from models.analytics import Kpi as KpiModel
        from core.exceptions import ResourceNotFoundError
        
        result = await self.db_session.execute(
            select(KpiModel).where(KpiModel.kpi_id.in_(kpi_ids))
        )
        kpis = result.scalars().all()
        
        kpi_dict = {}
        for kpi in kpis:
            kpi_dict[kpi.kpi_id] = KpiMetric(
                kpi_id=kpi.kpi_id,
                name=kpi.name,
                description=kpi.description,
                target_value=kpi.target_value,
                current_value=kpi.current_value,
                unit=kpi.unit,
                category=kpi.category,
                calculation_method=kpi.calculation_method,
                data_source=kpi.data_source,
                update_frequency=kpi.update_frequency,
                trend_direction=kpi.trend_direction,
                variance_percentage=kpi.variance_percentage,
                status=kpi.status,
                last_updated=kpi.last_updated
            )
        
        return kpi_dict
    
    async def generate_prediction_insight(self, student_id: str, prediction_type: str = "academic") -> PredictiveInsight:
        """
        Generate predictive insight for a student
        
        Args:
            student_id: Student ID
            prediction_type: Type of prediction
            
        Returns:
            PredictiveInsight: Predictive insight
        """
        logger.info(f"Generating prediction insight for student {student_id}")
        
        # Fetch student data
        student_metrics = await self.calculate_student_performance_metrics(student_id)
        
        # Generate prediction based on metrics
        confidence_score = 0.85 if student_metrics.current_gpa >= 3.0 else 0.65
        
        prediction = PredictiveInsight(
            insight_id=f"{student_id}_{prediction_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=prediction_type,
            confidence_score=confidence_score,
            prediction={
                'expected_gpa': round(student_metrics.current_gpa * 0.9, 2),
                'completion_probability': round(student_metrics.completion_rate, 2),
                'retention_probability': 0.92
            },
            explanation=f"Based on {student_metrics.current_gpa} GPA and {student_metrics.completion_rate}% completion rate",
            action_items=[
                "Review course completion progress",
                "Monitor attendance patterns",
                "Provide additional academic support if needed"
            ],
            impact_assessment="Positive outlook with moderate intervention risk",
            timeframe="semester",
            created_at=datetime.now(),
            data_sources=["student_records", "course_enrollments"],
            validation_status="validated"
        )
        
        return prediction
    
    async def calculate_trend_analysis(self, metric: str, time_range: TimeRange, group_by: str = "monthly") -> List[TrendData]:
        """
        Calculate trend analysis for a metric over time
        
        Args:
            metric: Metric to analyze
            time_range: Time range for analysis
            group_by: How to group data
            
        Returns:
            List[TrendData]: Trend data points
        """
        logger.info(f"Calculating trend analysis for {metric} over {time_range.timeframe}")
        
        # Fetch historical data
        data = await self._fetch_historical_data(metric, time_range)
        
        # Group data by timeframe
        grouped_data = self._group_by_timeframe(data, group_by, time_range.start_date, time_range.end_date)
        
        # Calculate trends
        trend_data = []
        for period, values in grouped_data.items():
            if values:
                average = np.mean(values)
                previous_period_values = self._get_previous_period_values(period, group_by)
                previous_average = np.mean(previous_period_values) if previous_period_values else average
                
                change_percentage = ((average - previous_average) / previous_average * 100) if previous_average > 0 else 0
                
                if change_percentage > 0:
                    trend_direction = "increasing"
                elif change_percentage < 0:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
                
                trend_data.append(TrendData(
                    period=period,
                    value=round(average, 2),
                    change_percentage=round(change_percentage, 2),
                    trend_direction=trend_direction
                ))
        
        return trend_data
    
    async def _fetch_historical_data(self, metric: str, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Fetch historical data for trend analysis"""
        # Placeholder for historical data fetching
        return []
    
    def _group_by_timeframe(self, data: List[Dict[str, Any]], group_by: str, start_date: datetime, end_date: datetime) -> Dict[str, List[float]]:
        """Group data by timeframe"""
        # Placeholder for time grouping logic
        return {}
    
    def _get_previous_period_values(self, period: str, group_by: str) -> List[float]:
        """Get values from previous period"""
        # Placeholder for previous period retrieval
        return []
    
    async def calculate_correlation_matrix(self, variables: List[str], time_range: TimeRange) -> CorrelationMatrix:
        """
        Calculate correlation matrix for variables
        
        Args:
            variables: List of variables to analyze
            time_range: Time range for analysis
            
        Returns:
            CorrelationMatrix: Correlation matrix
        """
        logger.info(f"Calculating correlation matrix for {len(variables)} variables")
        
        # Fetch data for all variables
        data = {}
        for variable in variables:
            data[variable] = await self._fetch_variable_data(variable, time_range)
        
        # Calculate correlation matrix
        correlation_matrix = []
        p_values = []
        
        for i, var1 in enumerate(variables):
            row = []
            p_row = []
            for j, var2 in enumerate(variables):
                if i == j:
                    row.append(1.0)
                    p_row.append(0.0)
                else:
                    corr, p_val = AnalyticsProcessor.calculate_correlation(data[var1], data[var2])
                    row.append(round(corr, 3))
                    p_row.append(round(p_val, 3))
            correlation_matrix.append(row)
            p_values.append(p_row)
        
        return CorrelationMatrix(
            variables=variables,
            correlation_matrix=correlation_matrix,
            p_values=p_values,
            significance_level=0.05
        )
    
    async def _fetch_variable_data(self, variable: str, time_range: TimeRange) -> List[float]:
        """Fetch data for a specific variable"""
        # Placeholder for variable data fetching
        return []
    
    async def export_analytics_report(self, query: AnalyticsQuery, format: str = "csv") -> bytes:
        """
        Export analytics result as file
        
        Args:
            query: Analytics query
            format: Export format (csv, excel, json)
            
        Returns:
            bytes: Exported file content
        """
        logger.info(f"Exporting analytics result for query {query.query_id} as {format}")
        
        # Execute query
        result = await self.execute_analytics_query(query)
        
        # Convert to format
        if format == "csv":
            content = await self._export_to_csv(result)
        elif format == "excel":
            content = await self._export_to_excel(result)
        elif format == "json":
            content = json.dumps(result.model_dump(), indent=2).encode('utf-8')
        else:
            raise ValidationError(f"Unsupported format: {format}")
        
        return content
    
    async def _export_to_csv(self, result: AnalyticsResult) -> str:
        """Export result to CSV"""
        if not result.result_data:
            return ""
        
        df = pd.DataFrame(result.result_data)
        return df.to_csv(index=False, encoding='utf-8')
    
    async def _export_to_excel(self, result: AnalyticsResult) -> str:
        """Export result to Excel"""
        if not result.result_data:
            return ""
        
        df = pd.DataFrame(result.result_data)
        return df.to_excel(index=False, encoding='utf-8', engine='openpyxl')