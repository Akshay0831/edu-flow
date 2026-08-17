"""
SEE Prediction Models for Edu-Flow

This module provides models for Student Educational Outcome (SEE) mark prediction:
- Prediction model for academic performance forecasting
- Model training and evaluation data structures
- Feature engineering components
- Model version management
- Prediction results and analysis

Author: Edu-Flow Team
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import numpy as np
import pandas as pd

from src.core.exceptions import ValidationError


class PredictionType(str, Enum):
    """Types of SEE predictions"""
    MARKS_PREDICTION = "marks_prediction"
    GRADE_PREDICTION = "grade_prediction"
    PERFORMANCE_PREDICTION = "performance_prediction"
    AT_RISK_PREDICTION = "at_risk_prediction"
    STUDENT_SUCCESS_PREDICTION = "student_success_prediction"


class ModelStatus(str, Enum):
    """Model deployment status"""
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    ERROR = "error"


class ModelType(str, Enum):
    """Types of ML models"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    SVM = "svm"
    NAIVE_BAYES = "naive_bayes"


class EvaluationMetric(str, Enum):
    """Evaluation metrics for models"""
    MAE = "mae"  # Mean Absolute Error
    RMSE = "rmse"  # Root Mean Square Error
    R2_SCORE = "r2_score"  # R-squared
    ACCURACY = "accuracy"  # Classification accuracy
    PRECISION = "precision"  # Precision
    RECALL = "recall"  # Recall
    F1_SCORE = "f1_score"  # F1 score
    AUC_ROC = "auc_roc"  # Area Under ROC Curve


class FeatureImportance(BaseModel):
    """Feature importance data"""
    feature_name: str
    importance_score: float
    importance_rank: int
    description: Optional[str] = None
    category: str = "academic"
    
    @field_validator('importance_score')
    def validate_importance_score(cls, v):
        if not -1.0 <= v <= 1.0:
            raise ValidationError('Importance score must be between -1.0 and 1.0')
        return v


class PredictionFeature(BaseModel):
    """Feature for prediction"""
    name: str
    value: Union[float, int, str, bool]
    type: str = "numerical"  # numerical, categorical, datetime
    importance: Optional[float] = None
    is_required: bool = True
    category: str = "academic"
    
    @field_validator('value')
    def validate_value(cls, v, values):
        feature_type = values.get('type', 'numerical')
        
        if feature_type == 'numerical':
            try:
                float(v)
            except (ValueError, TypeError):
                raise ValidationError('Numerical feature must be a number')
        elif feature_type == 'categorical':
            if not isinstance(v, str):
                raise ValidationError('Categorical feature must be a string')
        
        return v


class PredictionRequest(BaseModel):
    """Prediction request data"""
    student_id: str = Field(..., description="Student identifier")
    course_id: str = Field(..., description="Course identifier")
    academic_year: str = Field(..., description="Academic year (e.g., '2023-2024')")
    semester: int = Field(..., ge=1, le=2, description="Semester (1 or 2)")
    exam_type: str = Field(..., description="Type of exam (midterm, final, assignment)")
    prediction_type: PredictionType = Field(..., description="Type of prediction to make")
    features: List[PredictionFeature] = Field(..., description="Features for prediction")
    prediction_horizon: Optional[int] = Field(None, ge=1, le=4, description="Number of semesters ahead to predict")
    
    @field_validator('semester')
    def validate_semester(cls, v):
        if v not in [1, 2]:
            raise ValidationError('Semester must be 1 or 2')
        return v
    
    @field_validator('features')
    def validate_features(cls, v):
        if not v:
            raise ValidationError('At least one feature is required')
        
        # Check for required features
        feature_names = [f.name for f in v]
        required_features = ['attendance_rate', 'assignment_completion', 'previous_marks', 'study_hours']
        
        for req_feature in required_features:
            if req_feature not in feature_names:
                raise ValidationError(f'Required feature missing: {req_feature}')
        
        return v


class PredictionResult(BaseModel):
    """Prediction result data"""
    request_id: str
    student_id: str
    course_id: str
    prediction_type: PredictionType
    predicted_value: Union[float, str]
    confidence_score: float
    prediction_interval: Optional[Tuple[float, float]] = None
    timestamp: datetime
    model_version: str
    model_name: str
    explanation: Optional[str] = None
    feature_importances: Optional[List[FeatureImportance]] = None
    
    @field_validator('confidence_score')
    def validate_confidence_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError('Confidence score must be between 0.0 and 1.0')
        return v


class ModelTrainingConfig(BaseModel):
    """Model training configuration"""
    model_type: ModelType
    hyperparameters: Dict[str, Any]
    features: List[str]
    target_variable: str
    train_test_split: float = Field(0.8, ge=0.5, le=0.9)
    cross_validation_folds: int = Field(5, ge=2, le=10)
    random_state: int = Field(42)
    scaling_method: str = Field("standard", pattern=r"^(standard|minmax|robust|none)$")
    feature_selection: bool = True
    outlier_removal: bool = True
    missing_values_handling: str = Field("median", pattern=r"^(median|mean|mode|forward_fill|drop)$")
    
    @field_validator('hyperparameters')
    def validate_hyperparameters(cls, v):
        # Basic validation for common hyperparameters
        if v.get('learning_rate', 1.0) <= 0:
            raise ValidationError('Learning rate must be positive')
        if v.get('n_estimators', 100) < 1:
            raise ValidationError('Number of estimators must be positive')
        return v


class ModelEvaluation(BaseModel):
    """Model evaluation results"""
    model_id: str
    model_version: str
    evaluation_metrics: Dict[str, float]
    cross_validation_scores: List[float]
    confusion_matrix: Optional[List[List[float]]] = None
    classification_report: Optional[Dict[str, Any]] = None
    training_time: float
    prediction_time: float
    dataset_size: int
    test_size: int
    evaluation_timestamp: datetime
    
    @field_validator('evaluation_metrics')
    def validate_metrics(cls, v):
        # Check if metrics are valid values
        for metric_name, value in v.items():
            if metric_name == 'auc_roc':
                if not 0.0 <= value <= 1.0:
                    raise ValidationError(f'AUC ROC score must be between 0.0 and 1.0, got {value}')
            elif metric_name in ['accuracy', 'precision', 'recall', 'f1_score']:
                if not 0.0 <= value <= 1.0:
                    raise ValidationError(f'{metric_name} must be between 0.0 and 1.0, got {value}')
            elif metric_name in ['mae', 'rmse']:
                if value < 0:
                    raise ValidationError(f'{metric_name} must be non-negative, got {value}')
        return v


class ModelVersion(BaseModel):
    """Model version information"""
    version_id: str
    model_id: str
    model_name: str
    version_number: str
    description: Optional[str] = None
    model_type: ModelType
    training_config: ModelTrainingConfig
    training_timestamp: datetime
    training_dataset_hash: str
    model_file_path: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None
    is_active: bool = False
    deployment_notes: Optional[str] = None
    created_by: Optional[str] = None
    
    @field_validator('version_number')
    def validate_version_number(cls, v):
        # Basic semantic version validation (e.g., "1.0.0")
        if not all(part.isdigit() for part in v.split('.')):
            raise ValidationError('Version number must be in format X.Y.Z')
        return v


class StudentProfile(BaseModel):
    """Student academic profile for predictions"""
    student_id: str
    full_name: str
    program: str
    department: str
    current_year: int
    current_semester: int
    cumulative_gpa: float
    total_credits_completed: float
    total_credits_required: float
    academic_standing: str  # "excellent", "good", "average", "needs_improvement", "poor"
    
    @field_validator('cumulative_gpa')
    def validate_gpa(cls, v):
        if not 0.0 <= v <= 4.0:
            raise ValidationError('GPA must be between 0.0 and 4.0')
        return v


class CoursePerformance(BaseModel):
    """Course performance history"""
    student_id: str
    course_id: str
    course_name: str
    department: str
    academic_year: str
    semester: int
    marks_obtained: float
    total_marks: float
    percentage: float
    grade: str
    credits: float
    attendance_percentage: float
    completion_rate: float
    study_hours_per_week: float
    feedback_rating: Optional[float] = None
    
    @field_validator('percentage')
    def validate_percentage(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValidationError('Percentage must be between 0.0 and 100.0')
        return v


class LearningPattern(BaseModel):
    """Student learning patterns"""
    student_id: str
    study_hours_trend: List[float]  # Average study hours per week
    performance_trend: List[float]  # Marks over time
    attendance_pattern: List[float]  # Attendance percentage over time
    submission_pattern: List[float]  # On-time submission rate
    improvement_areas: List[str]  # Areas needing improvement
    strengths: List[str]  # Student's academic strengths
    preferred_learning_style: str  # visual, auditory, kinesthetic, reading
    learning_rate: float  # How quickly student learns new concepts
    
    @field_validator('learning_rate')
    def validate_learning_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError('Learning rate must be between 0.0 and 1.0')
        return v


class PredictionAnalysis(BaseModel):
    """Detailed prediction analysis"""
    prediction_id: str
    request_id: str
    confidence_level: str  # "high", "medium", "low"
    risk_factors: List[str]  # Factors affecting prediction
    opportunities: List[str]  # Areas for improvement
    recommendations: List[str]  # Specific recommendations
    historical_context: Optional[Dict[str, Any]] = None
    comparative_analysis: Optional[Dict[str, Any]] = None
    forecast_summary: Optional[str] = None


class PredictionHistory(BaseModel):
    """Prediction history for a student"""
    student_id: str
    course_id: Optional[str] = None
    prediction_requests: List[PredictionResult]
    actual_results: List[Dict[str, Any]]
    prediction_accuracy: float
    last_prediction_date: datetime
    total_predictions: int
    successful_predictions: int
    failed_predictions: int
    
    @field_validator('prediction_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError('Prediction accuracy must be between 0.0 and 1.0')
        return v


class ModelRegistry(BaseModel):
    """Model registry for managing ML models"""
    registry_id: str
    name: str
    description: str
    models: List[ModelVersion]
    best_model: Optional[ModelVersion] = None
    current_active_model: Optional[ModelVersion] = None
    created_at: datetime
    updated_at: datetime
    domain: str = "education"
    problem_type: str = "regression"  # regression, classification, clustering
    
    @field_validator('models')
    def validate_models(cls, v):
        if len(v) < 1:
            raise ValidationError('At least one model is required in registry')
        return v


class DatasetInfo(BaseModel):
    """Information about the training dataset"""
    dataset_id: str
    name: str
    description: str
    size: int
    columns: List[str]
    target_variable: str
    feature_count: int
    class_distribution: Optional[Dict[str, int]] = None
    missing_data_percentage: float
    data_quality_score: float
    creation_date: datetime
    
    @field_validator('data_quality_score')
    def validate_quality_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValidationError('Data quality score must be between 0.0 and 1.0')
        return v


class TrainingSession(BaseModel):
    """Model training session information"""
    session_id: str
    model_id: str
    session_type: str  # "training", "evaluation", "prediction"
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # "pending", "running", "completed", "failed"
    progress: float = Field(0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None
    logs: List[str] = []
    resources_used: Dict[str, Any] = {}
    
    @field_validator('progress')
    def validate_progress(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValidationError('Progress must be between 0.0 and 100.0')
        return v


class FeatureEngineeringConfig(BaseModel):
    """Configuration for feature engineering"""
    config_id: str
    name: str
    description: str
    feature_creation_rules: Dict[str, Any]
    feature_selection_method: str  # "correlation", "mutual_info", "feature_importance", "rfe"
    feature_transformation: Dict[str, str]  # Column name to transformation type
    dimensionality_reduction: bool = False
    reduction_method: Optional[str] = None
    feature_extraction: Dict[str, Any] = {}
    
    @field_validator('feature_selection_method')
    def validate_selection_method(cls, v):
        valid_methods = ["correlation", "mutual_info", "feature_importance", "rfe", "variance_threshold"]
        if v not in valid_methods:
            raise ValidationError(f'Invalid feature selection method: {v}')
        return v


class ModelPerformance(BaseModel):
    """Model performance tracking"""
    performance_id: str
    model_id: str
    version: str
    evaluation_period: str  # "weekly", "monthly", "quarterly"
    key_metrics: Dict[str, float]
    trend_analysis: Dict[str, List[float]]  # Metric values over time
    drift_detection: Dict[str, Any]  # Data drift and concept drift metrics
    performance_degradation: Optional[float] = None
    last_updated: datetime
    
    @field_validator('performance_degradation')
    def validate_degradation(cls, v):
        if v is not None and (v < -1.0 or v > 1.0):
            raise ValidationError('Performance degradation must be between -1.0 and 1.0')
        return v


# Utility classes for prediction processing
class PredictionProcessor:
    """Utility class for prediction processing"""
    
    @staticmethod
    def calculate_features(student_data: List[CoursePerformance]) -> List[PredictionFeature]:
        """Calculate features from student performance data"""
        features = []
        
        if not student_data:
            return features
        
        # Calculate average marks
        marks = [cp.marks_obtained / cp.total_marks * 100 for cp in student_data if cp.total_marks > 0]
        if marks:
            avg_marks = np.mean(marks)
            features.append(PredictionFeature(
                name="average_marks",
                value=avg_marks,
                type="numerical",
                category="academic"
            ))
        
        # Calculate attendance rate
        attendance_rates = [cp.attendance_percentage for cp in student_data]
        if attendance_rates:
            avg_attendance = np.mean(attendance_rates)
            features.append(PredictionFeature(
                name="attendance_rate",
                value=avg_attendance,
                type="numerical",
                category="academic"
            ))
        
        # Calculate completion rate
        completion_rates = [cp.completion_rate for cp in student_data]
        if completion_rates:
            avg_completion = np.mean(completion_rates)
            features.append(PredictionFeature(
                name="completion_rate",
                value=avg_completion,
                type="numerical",
                category="academic"
            ))
        
        # Study hours trend
        study_hours = [cp.study_hours_per_week for cp in student_data]
        if study_hours:
            avg_study_hours = np.mean(study_hours)
            features.append(PredictionFeature(
                name="study_hours_per_week",
                value=avg_study_hours,
                type="numerical",
                category="academic"
            ))
        
        return features
    
    @staticmethod
    def determine_academic_standing(student_data: List[CoursePerformance]) -> str:
        """Determine student academic standing"""
        if not student_data:
            return "unknown"
        
        avg_marks = np.mean([cp.percentage for cp in student_data])
        
        if avg_marks >= 90:
            return "excellent"
        elif avg_marks >= 75:
            return "good"
        elif avg_marks >= 60:
            return "average"
        elif avg_marks >= 45:
            return "needs_improvement"
        else:
            return "poor"
    
    @staticmethod
    def identify_learning_patterns(student_data: List[CoursePerformance]) -> Dict[str, Any]:
        """Identify student learning patterns"""
        if not student_data:
            return {}
        
        marks_trend = [cp.percentage for cp in student_data]
        attendance_trend = [cp.attendance_percentage for cp in student_data]
        completion_trend = [cp.completion_rate for cp in student_data]
        
        # Calculate trends
        marks_improvement = marks_trend[-1] - marks_trend[0] if len(marks_trend) > 1 else 0
        attendance_improvement = attendance_trend[-1] - attendance_trend[0] if len(attendance_trend) > 1 else 0
        completion_improvement = completion_trend[-1] - completion_trend[0] if len(completion_trend) > 1 else 0
        
        return {
            "marks_trend": marks_trend,
            "attendance_trend": attendance_trend,
            "completion_trend": completion_trend,
            "improvement_indicators": {
                "marks_improvement": marks_improvement,
                "attendance_improvement": attendance_improvement,
                "completion_improvement": completion_improvement
            }
        }


# Data validation utilities
class PredictionDataValidator:
    """Validation utilities for prediction data"""
    
    @staticmethod
    def validate_student_data(student_data: List[CoursePerformance]) -> bool:
        """Validate student performance data"""
        if not student_data:
            raise ValidationError("Student data cannot be empty")
        
        required_fields = ['student_id', 'course_id', 'marks_obtained', 'total_marks']
        for record in student_data:
            for field in required_fields:
                if not hasattr(record, field) or getattr(record, field) is None:
                    raise ValidationError(f"Missing required field: {field}")
        
        return True
    
    @staticmethod
    def validate_features_for_prediction(features: List[PredictionFeature], prediction_type: PredictionType) -> bool:
        """Validate features for specific prediction type"""
        required_features = {
            PredictionType.MARKS_PREDICTION: ['attendance_rate', 'previous_marks', 'study_hours_per_week'],
            PredictionType.GRADE_PREDICTION: ['attendance_rate', 'previous_marks', 'completion_rate'],
            PredictionType.PERFORMANCE_PREDICTION: ['attendance_rate', 'previous_marks', 'study_hours_per_week', 'completion_rate'],
            PredictionType.AT_RISK_PREDICTION: ['attendance_rate', 'previous_marks', 'study_hours_per_week', 'completion_rate'],
            PredictionType.STUDENT_SUCCESS_PREDICTION: ['attendance_rate', 'previous_marks', 'study_hours_per_week', 'completion_rate', 'gpa']
        }
        
        if prediction_type in required_features:
            required = required_features[prediction_type]
            feature_names = [f.name for f in features]
            for req_feature in required:
                if req_feature not in feature_names:
                    raise ValidationError(f"Missing required feature for {prediction_type.value}: {req_feature}")
        
        return True