"""
Advanced Analytics Models for Edu-Flow

This module provides models for advanced analytics and reporting:
- Student performance analytics
- Course analytics and metrics
- Faculty performance analytics
- Department-wise analysis
- Time-series analytics
- Predictive analytics models
- Dashboard configurations
- Report generation settings

Author: Edu-Flow Team
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import numpy as np
import pandas as pd
import json

from core.exceptions import ValidationError
from infrastructure.models.base_model import Base


class AnalyticsType(str, Enum):
    """Types of analytics operations"""
    STUDENT_PERFORMANCE = "student_performance"
    COURSE_ANALYTICS = "course_analytics"
    FACULTY_PERFORMANCE = "faculty_performance"
    DEPARTMENT_ANALYTICS = "department_analytics"
    TIME_SERIES = "time_series"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    COMPARATIVE_ANALYTICS = "comparative_analytics"
    BEHAVIORAL_ANALYTICS = "behavioral_analytics"
    ACADEMIC_TRENDS = "academic_trends"
    ENGAGEMENT_ANALYTICS = "engagement_analytics"


class MetricType(str, Enum):
    """Types of metrics"""
    ACADEMIC = "academic"
    ENGAGEMENT = "engagement"
    BEHAVIORAL = "behavioral"
    ATTENDANCE = "attendance"
    PERFORMANCE = "performance"
    SATISFACTION = "satisfaction"
    RETENTION = "retention"
    COMPLETION = "completion"
    ACHIEVEMENT = "achievement"
    PROGRESS = "progress"


class Timeframe(str, Enum):
    """Timeframes for analysis"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMESTERLY = "semesterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class FilterOperator(str, Enum):
    """Filter operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"
    DATE_RANGE = "date_range"


class AggregationType(str, Enum):
    """Aggregation types"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    MEDIAN = "median"
    MODE = "mode"
    STANDARD_DEVIATION = "standard_deviation"
    VARIANCE = "variance"
    PERCENTILE = "percentile"
    QUANTILE = "quantile"


class VisualizationType(str, Enum):
    """Visualization types"""
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    AREA_CHART = "area_chart"
    RADAR_CHART = "radar_chart"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION_MATRIX = "correlation_matrix"
    GANTT_CHART = "gantt_chart"
    SANKEY_DIAGRAM = "sankey_diagram"


class DataSource(str, Enum):
    """Data sources for analytics"""
    STUDENT_RECORDS = "student_records"
    COURSE_RECORDS = "course_records"
    ATTENDANCE_RECORDS = "attendance_records"
    MARKS_RECORDS = "marks_records"
    FEEDBACK_RECORDS = "feedback_records"
    ENROLLMENT_RECORDS = "enrollment_records"
    COMPLETION_RECORDS = "completion_records"
    PERFORMANCE_RECORDS = "performance_records"
    ENGAGEMENT_RECORDS = "engagement_records"
    BEHAVIORAL_RECORDS = "behavioral_records"


class AnalyticsFilter(BaseModel):
    """Filter for analytics queries"""
    field: str
    operator: FilterOperator
    value: Union[str, int, float, List[Any]]
    optional: bool = False
    
    @field_validator('operator')
    def validate_operator(cls, v):
        if not FilterOperator(v):
            raise ValidationError(f"Invalid filter operator: {v}")
        return v


class MetricDefinition(BaseModel):
    """Definition of a metric"""
    metric_id: str
    name: str
    description: str
    type: MetricType
    data_source: DataSource
    calculation_formula: str
    unit: Optional[str] = None
    format_type: str = "number"  # number, percentage, currency, text, date
    decimal_places: int = 2
    category: str = "general"
    tags: List[str] = []
    
    @field_validator('calculation_formula')
    def validate_formula(cls, v):
        # Basic validation for formula syntax
        if not v or len(v.strip()) == 0:
            raise ValidationError("Calculation formula cannot be empty")
        return v


class TimeRange(BaseModel):
    """Time range for analysis"""
    start_date: datetime
    end_date: datetime
    timeframe: Timeframe
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v, values):
        if 'end_date' in values and v > values['end_date']:
            raise ValidationError("Start date must be before end date")
        return v
    
    @field_validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValidationError("End date must be after start date")
        return v


class Aggregation(BaseModel):
    """Aggregation configuration"""
    field: str
    type: AggregationType
    alias: Optional[str] = None
    
    @field_validator('type')
    def validate_aggregation_type(cls, v):
        if not AggregationType(v):
            raise ValidationError(f"Invalid aggregation type: {v}")
        return v


class QueryFilter(BaseModel):
    """Query filter for analytics"""
    field: str
    operator: FilterOperator
    value: Union[str, int, float, List[Any], Tuple[Any, Any]]
    
    @field_validator('operator')
    def validate_operator(cls, v):
        if not FilterOperator(v):
            raise ValidationError(f"Invalid filter operator: {v}")
        return v


class AnalyticsQuery(BaseModel):
    """Analytics query configuration"""
    query_id: str
    name: str
    description: str
    analytics_type: AnalyticsType
    metrics: List[str]  # List of metric IDs
    filters: List[QueryFilter] = []
    aggregations: List[Aggregation] = []
    group_by: List[str] = []
    time_range: Optional[TimeRange] = None
    data_sources: List[DataSource] = []
    limit: int = 1000
    offset: int = 0
    
    @field_validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100000:
            raise ValidationError("Limit must be between 1 and 100000")
        return v
    
    @field_validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValidationError("Offset must be non-negative")
        return v


class AnalyticsResult(BaseModel):
    """Result of analytics query"""
    query_id: str
    analytics_type: AnalyticsType
    timestamp: datetime
    execution_time: float
    total_records: int
    result_data: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]
    metadata: Dict[str, Any]
    
    @field_validator('execution_time')
    def validate_execution_time(cls, v):
        if v < 0:
            raise ValidationError("Execution time must be non-negative")
        return v


class TrendData(BaseModel):
    """Trend analysis data"""
    period: str
    value: float
    change_percentage: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    confidence_interval: Optional[Tuple[float, float]] = None
    seasonality_factor: Optional[float] = None
    outlier_detected: bool = False


class CorrelationMatrix(BaseModel):
    """Correlation matrix data"""
    variables: List[str]
    correlation_matrix: List[List[float]]
    p_values: List[List[float]] = []
    significance_level: float = 0.05
    
    @field_validator('correlation_matrix')
    def validate_correlation_matrix(cls, v):
        if not v or len(v) == 0:
            raise ValidationError("Correlation matrix cannot be empty")
        if len(v) != len(v[0]):
            raise ValidationError("Correlation matrix must be square")
        return v


class StudentPerformanceMetrics(BaseModel):
    """Student performance metrics"""
    student_id: str
    student_name: str
    program: str
    department: str
    current_gpa: float
    total_credits_completed: float
    total_credits_required: float
    completion_rate: float
    average_marks: float
    attendance_rate: float
    assignment_completion_rate: float
    exam_performance_trend: List[float]
    skill_competency: Dict[str, float]
    improvement_areas: List[str]
    strengths: List[str]
    risk_level: str  # "low", "medium", "high"
    
    @field_validator('current_gpa')
    def validate_gpa(cls, v):
        if not 0.0 <= v <= 4.0:
            raise ValidationError("GPA must be between 0.0 and 4.0")
        return v
    
    @field_validator('completion_rate')
    def validate_completion_rate(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValidationError("Completion rate must be between 0.0 and 100.0")
        return v


class CourseAnalytics(BaseModel):
    """Course analytics data"""
    course_id: str
    course_name: str
    department: str
    credits: float
    total_enrollments: int
    current_enrollments: int
    completion_rate: float
    average_marks: float
    attendance_rate: float
    student_satisfaction_score: float
    difficulty_level: str  # "easy", "medium", "hard"
    pass_rate: float
    failure_rate: float
    grade_distribution: Dict[str, int]
    enrollment_trend: List[Tuple[str, int]]
    performance_trend: List[Tuple[str, float]]
    feedback_summary: Dict[str, Any]
    
    @field_validator('completion_rate')
    def validate_completion_rate(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValidationError("Completion rate must be between 0.0 and 100.0")
        return v


class FacultyPerformanceMetrics(BaseModel):
    """Faculty performance metrics"""
    faculty_id: str
    faculty_name: str
    department: str
    designation: str
    total_courses_taught: int
    total_students_taught: int
    average_student_rating: float
    course_completion_rate: float
    student_satisfaction_score: float
    teaching_effectiveness_score: float
    research_productivity_score: float
    student_feedback_score: float
    peer_review_score: float
    administrative_tasks_completed: int
    student_mentoring_hours: float
    professional_development_hours: float
    performance_trend: List[Tuple[str, float]]
    
    @field_validator('average_student_rating')
    def validate_rating(cls, v):
        if not 1.0 <= v <= 5.0:
            raise ValidationError("Average rating must be between 1.0 and 5.0")
        return v


class DepartmentAnalytics(BaseModel):
    """Department analytics data"""
    department_id: str
    department_name: str
    head_of_department: str
    total_faculty: int
    total_students: int
    student_faculty_ratio: float
    average_gpa: float
    graduation_rate: float
    employment_rate: float
    research_output: int
    industry_collaborations: int
    student_satisfaction_score: float
    faculty_satisfaction_score: float
    program_completion_rate: float
    course_utilization_rate: float
    budget_utilization: float
    facilities_rating: float
    
    @field_validator('student_faculty_ratio')
    def validate_ratio(cls, v):
        if v < 0:
            raise ValidationError("Student-faculty ratio must be non-negative")
        return v
    
    @field_validator('average_gpa')
    def validate_gpa(cls, v):
        if not 0.0 <= v <= 4.0:
            raise ValidationError("Average GPA must be between 0.0 and 4.0")
        return v


class EngagementMetrics(BaseModel):
    """Student engagement metrics"""
    student_id: str
    course_id: str
    login_frequency: int
    time_spent_hours: float
    resources_accessed: int
    discussion_participation: int
    assignment_submissions: int
    peer_interactions: int
    help_requests: int
    navigation_pattern: List[str]
    engagement_score: float
    engagement_level: str  # "high", "medium", "low", "inactive"
    risk_factors: List[str]
    improvement_suggestions: List[str]
    
    @field_validator('engagement_score')
    def validate_engagement_score(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValidationError("Engagement score must be between 0.0 and 100.0")
        return v


class PredictiveInsight(BaseModel):
    """Predictive insights"""
    insight_id: str
    type: str
    confidence_score: float
    prediction: Any
    explanation: str
    action_items: List[str]
    impact_assessment: str
    timeframe: str
    created_at: datetime
    data_sources: List[str]
    validation_status: str  # "validated", "pending", "rejected"
    
    @field_validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError("Confidence score must be between 0.0 and 1.0")
        return v


class AnalyticsDashboard(BaseModel):
    """Analytics dashboard configuration"""
    dashboard_id: str
    name: str
    description: str
    owner: str
    created_at: datetime
    updated_at: datetime
    widgets: List[Dict[str, Any]]
    filters: Dict[str, Any] = {}
    shared_with: List[str] = []
    is_public: bool = False
    layout_config: Dict[str, Any] = {}
    refresh_frequency: str = "daily"  # real_time, hourly, daily, weekly, monthly
    auto_refresh: bool = True
    
    @field_validator('refresh_frequency')
    def validate_refresh_frequency(cls, v):
        valid_frequencies = ["real_time", "hourly", "daily", "weekly", "monthly"]
        if v not in valid_frequencies:
            raise ValidationError(f"Invalid refresh frequency: {v}")
        return v


class ReportTemplate(BaseModel):
    """Report template"""
    template_id: str
    name: str
    description: str
    report_type: str
    template_content: str
    parameters: Dict[str, Any] = {}
    data_sources: List[DataSource] = []
    output_format: str = "pdf"  # pdf, excel, csv, json, html
    schedule_config: Dict[str, Any] = {}
    generated_reports: List[str] = []
    is_active: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    @field_validator('output_format')
    def validate_output_format(cls, v):
        valid_formats = ["pdf", "excel", "csv", "json", "html"]
        if v not in valid_formats:
            raise ValidationError(f"Invalid output format: {v}")
        return v


class AlertConfig(BaseModel):
    """Alert configuration"""
    alert_id: str
    name: str
    description: str
    metric: str
    threshold: Union[float, int]
    condition: str  # "greater_than", "less_than", "equals", "not_equals"
    severity: str  # "low", "medium", "high", "critical"
    notification_channels: List[str] = []
    recipients: List[str] = []
    is_active: bool = True
    created_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    @field_validator('severity')
    def validate_severity(cls, v):
        valid_severities = ["low", "medium", "high", "critical"]
        if v not in valid_severities:
            raise ValidationError(f"Invalid severity level: {v}")
        return v


class KpiMetric(BaseModel):
    """Key Performance Indicator metric"""
    kpi_id: str
    name: str
    description: str
    target_value: float
    current_value: float
    unit: str
    category: str
    calculation_method: str
    data_source: str
    update_frequency: str
    trend_direction: str  # "up", "down", "stable"
    variance_percentage: float
    status: str  # "on_track", "at_risk", "behind"
    last_updated: datetime
    
    @field_validator('variance_percentage')
    def validate_variance_percentage(cls, v):
        if v < -100 or v > 100:
            raise ValidationError("Variance percentage must be between -100 and 100")
        return v


class LearningAnalytics(BaseModel):
    """Learning analytics data"""
    learning_session_id: str
    student_id: str
    course_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    activities_completed: int
    skills_practiced: List[str]
    knowledge_gains: Dict[str, float]
    learning_efficiency: float
    cognitive_load: float
    engagement_level: str
    learning_path_efficiency: float
    time_distribution: Dict[str, float]  # "reading", "practice", "assessment", "review"
    interaction_patterns: Dict[str, int]
    learning_outcomes: List[Dict[str, Any]]
    
    @field_validator('learning_efficiency')
    def validate_learning_efficiency(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError("Learning efficiency must be between 0.0 and 1.0")
        return v


class RiskAssessment(BaseModel):
    """Risk assessment data"""
    assessment_id: str
    student_id: str
    course_id: str
    risk_level: str  # "low", "medium", "high", "critical"
    risk_factors: List[str]
    risk_score: float
    intervention_strategies: List[str]
    predicted_outcome: str
    confidence_score: float
    assessment_date: datetime
    next_review_date: datetime
    interventions_applied: List[str]
    intervention_effectiveness: Optional[float] = None
    
    @field_validator('risk_score')
    def validate_risk_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError("Risk score must be between 0.0 and 1.0")
        return v


# Utility classes for analytics processing
class AnalyticsProcessor:
    """Utility class for analytics processing"""
    
    @staticmethod
    def calculate_descriptive_stats(data: List[float]) -> Dict[str, float]:
        """Calculate descriptive statistics"""
        if not data:
            return {}
        
        data_array = np.array(data)
        return {
            'mean': np.mean(data_array),
            'median': np.median(data_array),
            'std': np.std(data_array),
            'min': np.min(data_array),
            'max': np.max(data_array),
            'count': len(data_array),
            'variance': np.var(data_array),
            'range': np.max(data_array) - np.min(data_array)
        }
    
    @staticmethod
    def calculate_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
        """Calculate correlation between two variables"""
        if len(x) != len(y) or len(x) < 2:
            return {'correlation': 0.0, 'p_value': 1.0}
        
        x_array = np.array(x)
        y_array = np.array(y)
        
        # Pearson correlation
        correlation = np.corrcoef(x_array, y_array)[0, 1]
        
        return {
            'correlation': correlation,
            'p_value': 0.05  # Simplified p-value calculation
        }
    
    @staticmethod
    def detect_outliers(data: List[float], method: str = "iqr") -> List[int]:
        """Detect outliers in data"""
        if not data:
            return []
        
        data_array = np.array(data)
        outlier_indices = []
        
        if method == "iqr":
            Q1 = np.percentile(data_array, 25)
            Q3 = np.percentile(data_array, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            for i, value in enumerate(data_array):
                if value < lower_bound or value > upper_bound:
                    outlier_indices.append(i)
        
        elif method == "zscore":
            z_scores = np.abs((data_array - np.mean(data_array)) / np.std(data_array))
            outlier_indices = np.where(z_scores > 3)[0].tolist()
        
        return outlier_indices
    
    @staticmethod
    def calculate_trend(data: List[float]) -> Dict[str, Any]:
        """Calculate trend in data"""
        if len(data) < 2:
            return {'trend': 'stable', 'slope': 0.0}
        
        x = np.arange(len(data))
        y = np.array(data)
        
        # Linear regression
        slope, intercept = np.polyfit(x, y, 1)
        
        # Determine trend direction
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'trend': trend,
            'slope': slope,
            'r_squared': np.corrcoef(x, y)[0, 1] ** 2 if len(x) > 1 else 0.0
        }
    
    @staticmethod
    def aggregate_data(data: List[Dict[str, Any]], group_by: str, agg_type: str) -> Dict[str, float]:
        """Aggregate data by field"""
        if not data:
            return {}
        
        groups = {}
        for item in data:
            key = item.get(group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        result = {}
        for group, group_data in groups.items():
            values = [item.get('value', 0) for item in group_data]
            
            if agg_type == 'sum':
                result[group] = sum(values)
            elif agg_type == 'average':
                result[group] = sum(values) / len(values) if values else 0
            elif agg_type == 'count':
                result[group] = len(values)
            elif agg_type == 'max':
                result[group] = max(values) if values else 0
            elif agg_type == 'min':
                result[group] = min(values) if values else 0
            elif agg_type == 'median':
                sorted_values = sorted(values)
                n = len(sorted_values)
                if n % 2 == 1:
                    result[group] = sorted_values[n//2]
                else:
                    result[group] = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        
        return result


# Data validation utilities
class AnalyticsDataValidator:
    """Validation utilities for analytics data"""
    
    @staticmethod
    def validate_analytics_query(query: AnalyticsQuery) -> bool:
        """Validate analytics query"""
        if not query.name or not query.description:
            raise ValidationError("Query name and description are required")
        
        if not query.metrics:
            raise ValidationError("At least one metric is required")
        
        if query.time_range:
            if query.time_range.start_date >= query.time_range.end_date:
                raise ValidationError("Start date must be before end date")
        
        if query.limit < 1 or query.limit > 100000:
            raise ValidationError("Limit must be between 1 and 100000")
        
        return True
    
    @staticmethod
    def validate_metric_definition(metric: MetricDefinition) -> bool:
        """Validate metric definition"""
        if not metric.name or not metric.description:
            raise ValidationError("Metric name and description are required")
        
        if not metric.calculation_formula:
            raise ValidationError("Calculation formula is required")
        
        if metric.format_type not in ["number", "percentage", "currency", "text", "date"]:
            raise ValidationError("Invalid format type")
        
        return True
    
    @staticmethod
    def validate_time_range(time_range: TimeRange) -> bool:
        """Validate time range"""
        if time_range.start_date >= time_range.end_date:
            raise ValidationError("Start date must be before end date")
        
        if time_range.timeframe not in ["daily", "weekly", "monthly", "quarterly", "yearly"]:
            raise ValidationError("Invalid timeframe")


# SQLAlchemy models for database storage
class Alert(Base):
    """
    Alert model for storing alert configurations and trigger history.
    
    Represents monitoring alerts for metrics and KPIs.
    """
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    metric = Column(String(255), nullable=False, index=True)
    threshold = Column(Float, nullable=False)
    condition = Column(String(50), nullable=False, default="greater_than")
    severity = Column(String(50), nullable=False, default="medium")
    notification_channels = Column(Text, nullable=True)
    recipients = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    last_triggered = Column(DateTime, nullable=True, index=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    alert_logs = relationship("AlertLog", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.alert_id}, name={self.name}, severity={self.severity})>"


class AlertLog(Base):
    """
    Alert log model for tracking alert trigger history.
    
    Represents individual alert trigger events.
    """
    __tablename__ = "alert_logs"
    
    log_id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, ForeignKey("alerts.alert_id"), nullable=False, index=True)
    triggered_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    current_value = Column(Float, nullable=True)
    previous_value = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    handled = Column(Boolean, default=False, nullable=False, index=True)
    handled_at = Column(DateTime, nullable=True)
    
    # Relationship
    alert = relationship("Alert", back_populates="alert_logs")
    
    def __repr__(self):
        return f"<AlertLog(id={self.log_id}, alert_id={self.alert_id}, triggered_at={self.triggered_at})>"
        
        return True