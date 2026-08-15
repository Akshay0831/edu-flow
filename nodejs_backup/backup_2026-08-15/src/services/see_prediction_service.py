"""
SEE Prediction Service for Edu-Flow

This module provides comprehensive SEE (Student Educational Outcome) prediction functionality:
- ML model management and deployment
- Real-time prediction generation
- Model training and evaluation
- Feature engineering and selection
- Performance monitoring and drift detection
- Historical analysis and trend detection
- Risk assessment and intervention suggestions

Author: Edu-Flow Team
"""

import asyncio
import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Type
import numpy as np
import pandas as pd
import logging
import joblib
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.core.exceptions import ValidationError, NotFoundError, DatabaseError
from src.core.database_abstraction import DatabaseInterface
from src.core.cache_abstraction import CacheManager
from src.core.logging import get_logger
from src.core.service_container import get_service_container
from src.models.see_prediction import (
    PredictionRequest, PredictionResult, ModelVersion, ModelEvaluation,
    ModelTrainingConfig, PredictionFeature, FeatureImportance,
    PredictionType, ModelType, ModelStatus, EvaluationMetric,
    StudentProfile, CoursePerformance, LearningPattern, PredictionAnalysis,
    PredictionHistory, ModelRegistry, DatasetInfo, TrainingSession,
    FeatureEngineeringConfig, ModelPerformance, PredictionProcessor,
    PredictionDataValidator
)
from src.services.base_service import BaseService

logger = get_logger(__name__)


class SEEPredictionService(BaseService):
    """SEE Prediction Service for managing ML models and predictions"""
    
    def __init__(self, service_name: str = "see_prediction_service"):
        super().__init__(service_name)
        self._model_cache = {}
        self._active_models = {}
        self._training_queue = asyncio.Queue()
        self._model_paths = Path("models/see_prediction")
        self._data_paths = Path("data/see_prediction")
        
        # Create directories
        self._model_paths.mkdir(parents=True, exist_ok=True)
        self._data_paths.mkdir(parents=True, exist_ok=True)
        self._data_paths.joinpath("training_data").mkdir(exist_ok=True)
        self._data_paths.joinpath("evaluation_data").mkdir(exist_ok=True)
        self._data_paths.joinpath("features").mkdir(exist_ok=True)
        
        # Configuration
        self._default_training_config = {
            'model_type': ModelType.RANDOM_FOREST,
            'hyperparameters': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'random_state': 42
            },
            'features': [
                'attendance_rate',
                'assignment_completion',
                'previous_marks',
                'study_hours',
                'participation_score',
                'quiz_marks'
            ],
            'target_variable': 'final_marks',
            'train_test_split': 0.8,
            'cross_validation_folds': 5,
            'feature_selection': True,
            'scaling_method': 'standard'
        }
        
        self._prediction_cache_ttl = 3600  # 1 hour
        self._model_retention_days = 90
        
        # Async initialization will be called during startup
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service and load default models"""
        if not self._initialized:
            await self._initialize_default_models()
            self._initialized = True
            logger.info("✅ SEE Prediction Service initialized successfully")
    
    async def dispose(self):
        """Clean up resources"""
        self._model_cache.clear()
        self._active_models.clear()
        await self._training_queue.join()
        self._training_queue = asyncio.Queue()
        logger.info("🗑️  SEE Prediction Service disposed")
    
    # region: Model Management
    
    async def create_model_version(
        self,
        model_name: str,
        model_type: ModelType,
        description: str,
        training_config: Dict[str, Any],
        features: List[str],
        target_variable: str,
        created_by: str
    ) -> ModelVersion:
        """Create a new model version"""
        try:
            # Validate configuration
            training_config_model = ModelTrainingConfig(**training_config)
            
            # Create model version
            version_id = self._generate_model_version_id()
            model_version = ModelVersion(
                version_id=version_id,
                model_id=self._generate_model_id(),
                model_name=model_name,
                version_number="1.0.0",
                description=description,
                model_type=model_type,
                training_config=training_config_model,
                training_timestamp=datetime.utcnow(),
                training_dataset_hash="",
                created_by=created_by
            )
            
            # Save to database
            await self.insert_one('model_versions', model_version.__dict__)
            
            logger.info(f"Model version created: {model_name} ({version_id})")
            return model_version
            
        except Exception as e:
            logger.error(f"Error creating model version: {str(e)}")
            raise DatabaseError(f"Failed to create model version: {str(e)}")
    
    async def get_model_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get model version by ID"""
        try:
            model_data = await self.find_one('model_versions', {'version_id': version_id})
            if not model_data:
                return None
            
            return ModelVersion(**model_data)
            
        except Exception as e:
            logger.error(f"Error getting model version: {str(e)}")
            raise DatabaseError(f"Failed to get model version: {str(e)}")
    
    async def get_active_models(self, model_name: Optional[str] = None) -> List[ModelVersion]:
        """Get all active models"""
        try:
            query = {'is_active': True}
            if model_name:
                query['model_name'] = model_name
            
            model_data = await self.find_many('model_versions', query)
            return [ModelVersion(**data) for data in model_data]
            
        except Exception as e:
            logger.error(f"Error getting active models: {str(e)}")
            raise DatabaseError(f"Failed to get active models: {str(e)}")
    
    async def deploy_model(self, version_id: str, deployment_notes: str = "") -> ModelVersion:
        """Deploy a model version"""
        try:
            # Get model version
            model_version = await self.get_model_version(version_id)
            if not model_version:
                raise NotFoundError(f"Model version not found: {version_id}")
            
            # Deactivate other versions
            await self.update_many('model_versions', {
                'model_name': model_version.model_name,
                'is_active': True
            }, {'is_active': False})
            
            # Activate this version
            await self.update_one('model_versions', {'version_id': version_id}, {
                'is_active': True,
                'deployment_notes': deployment_notes,
                'updated_at': datetime.utcnow()
            })
            
            # Load model into memory
            await self._load_model_for_prediction(model_version)
            
            logger.info(f"Model deployed: {model_version.model_name} ({version_id})")
            return model_version
            
        except Exception as e:
            logger.error(f"Error deploying model: {str(e)}")
            raise DatabaseError(f"Failed to deploy model: {str(e)}")
    
    async def archive_model(self, version_id: str, reason: str = "") -> ModelVersion:
        """Archive a model version"""
        try:
            model_version = await self.get_model_version(version_id)
            if not model_version:
                raise NotFoundError(f"Model version not found: {version_id}")
            
            await self.update_one('model_versions', {'version_id': version_id}, {
                'is_active': False,
                'status': ModelStatus.ARCHIVED.value,
                'deployment_notes': reason,
                'updated_at': datetime.utcnow()
            })
            
            # Remove from cache
            if version_id in self._model_cache:
                del self._model_cache[version_id]
            
            logger.info(f"Model archived: {model_version.model_name} ({version_id})")
            return model_version
            
        except Exception as e:
            logger.error(f"Error archiving model: {str(e)}")
            raise DatabaseError(f"Failed to archive model: {str(e)}")
    
    # region: Model Training
    
    async def train_model(
        self,
        version_id: str,
        training_data: Union[UploadFile, List[Dict[str, Any]]],
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> ModelEvaluation:
        """Train a model version"""
        try:
            # Get model version
            model_version = await self.get_model_version(version_id)
            if not model_version:
                raise NotFoundError(f"Model version not found: {version_id}")
            
            # Create training session
            session = TrainingSession(
                session_id=self._generate_session_id(),
                model_id=model_version.model_id,
                session_type="training",
                start_time=datetime.utcnow(),
                status="running",
                progress=0.0
            )
            
            await self.insert_one('training_sessions', session.__dict__)
            
            # Process training data
            training_df = await self._process_training_data(training_data, model_version.training_config)
            
            # Perform feature engineering
            feature_engineered_data = await self._perform_feature_engineering(training_df, model_version)
            
            # Split data
            X_train, X_test, y_train, y_test = self._split_data(
                feature_engineered_data, 
                model_version.training_config.target_variable,
                model_version.training_config.train_test_split
            )
            
            # Train model
            trained_model, evaluation_metrics = await self._train_model_pipeline(
                X_train, y_train, X_test, y_test, model_version
            )
            
            # Save model
            model_path = self._model_paths / f"{model_version.version_id}.pkl"
            joblib.dump(trained_model, model_path)
            
            # Update model version
            await self.update_one('model_versions', {'version_id': version_id}, {
                'model_file_path': str(model_path),
                'training_dataset_hash': self._calculate_data_hash(training_df),
                'performance_metrics': evaluation_metrics,
                'status': ModelStatus.ACTIVE.value,
                'updated_at': datetime.utcnow()
            })
            
            # Create evaluation record
            evaluation = ModelEvaluation(
                model_id=model_version.model_id,
                model_version=version_id,
                evaluation_metrics=evaluation_metrics,
                cross_validation_scores=evaluation_metrics.get('cv_scores', []),
                confusion_matrix=evaluation_metrics.get('confusion_matrix'),
                classification_report=evaluation_metrics.get('classification_report'),
                training_time=evaluation_metrics.get('training_time', 0),
                prediction_time=evaluation_metrics.get('prediction_time', 0),
                dataset_size=len(X_train) + len(X_test),
                test_size=len(X_test),
                evaluation_timestamp=datetime.utcnow()
            )
            
            await self.insert_one('model_evaluations', evaluation.__dict__)
            
            # Update training session
            await self.update_one('training_sessions', {'session_id': session.session_id}, {
                'end_time': datetime.utcnow(),
                'status': "completed",
                'progress': 100.0
            })
            
            logger.info(f"Model training completed: {model_version.model_name} ({version_id})")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            
            # Update training session with error
            if 'session_id' in locals():
                await self.update_one('training_sessions', {'session_id': session.session_id}, {
                    'end_time': datetime.utcnow(),
                    'status': "failed",
                    'error_message': str(e),
                    'progress': session.progress
                })
            
            raise DatabaseError(f"Failed to train model: {str(e)}")
    
    # region: Prediction Generation
    
    async def make_prediction(self, request: PredictionRequest) -> PredictionResult:
        """Make a prediction using active models"""
        try:
            # Get appropriate active model
            active_models = await self.get_active_models(request.prediction_type.value)
            if not active_models:
                raise NotFoundError(f"No active models found for prediction type: {request.prediction_type}")
            
            # Use the most recently deployed model
            model_version = max(active_models, key=lambda m: m.training_timestamp)
            
            # Get model from cache
            model = self._model_cache.get(model_version.version_id)
            if not model:
                model = await self._load_model_for_prediction(model_version)
            
            # Prepare features
            X = self._prepare_prediction_features(request.features)
            
            # Make prediction
            predicted_value = model.predict([X])[0]
            confidence_score = self._calculate_prediction_confidence(model, X)
            
            # Create prediction result
            prediction_result = PredictionResult(
                request_id=self._generate_request_id(),
                student_id=request.student_id,
                course_id=request.course_id,
                prediction_type=request.prediction_type,
                predicted_value=predicted_value,
                confidence_score=confidence_score,
                prediction_interval=self._calculate_prediction_interval(model, X),
                timestamp=datetime.utcnow(),
                model_version=model_version.version_number,
                model_name=model_version.model_name,
                explanation=self._generate_prediction_explanation(request, predicted_value, confidence_score)
            )
            
            # Cache prediction result
            await self._cache_prediction_result(prediction_result)
            
            logger.info(f"Prediction made: {request.student_id} - {request.course_id} - {request.prediction_type.value}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise DatabaseError(f"Failed to make prediction: {str(e)}")
    
    async def batch_predictions(self, requests: List[PredictionRequest]) -> List[PredictionResult]:
        """Make predictions in batch"""
        try:
            # Process requests in parallel
            tasks = [self.make_prediction(request) for request in requests]
            prediction_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            results = []
            for i, result in enumerate(prediction_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch prediction {i}: {str(result)}")
                    # Create error result
                    error_result = PredictionResult(
                        request_id=self._generate_request_id(),
                        student_id=requests[i].student_id,
                        course_id=requests[i].course_id,
                        prediction_type=requests[i].prediction_type,
                        predicted_value=None,
                        confidence_score=0.0,
                        timestamp=datetime.utcnow(),
                        model_version="error",
                        model_name="error",
                        explanation=f"Prediction failed: {str(result)}"
                    )
                    results.append(error_result)
                else:
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch predictions: {str(e)}")
            raise DatabaseError(f"Failed to make batch predictions: {str(e)}")
    
    async def get_prediction_history(self, student_id: str, course_id: Optional[str] = None) -> PredictionHistory:
        """Get prediction history for a student"""
        try:
            # Query prediction database
            query = {'student_id': student_id}
            if course_id:
                query['course_id'] = course_id
            
            predictions = await self.find_many('predictions', query, sort=[('timestamp', -1)])
            
            if not predictions:
                return PredictionHistory(
                    student_id=student_id,
                    course_id=course_id,
                    prediction_requests=[],
                    actual_results=[],
                    prediction_accuracy=0.0,
                    last_prediction_date=datetime.utcnow(),
                    total_predictions=0,
                    successful_predictions=0,
                    failed_predictions=0
                )
            
            # Calculate accuracy
            successful = 0
            total = len(predictions)
            
            for pred in predictions:
                # This would compare with actual results when available
                if pred.get('predicted_value') is not None:
                    successful += 1
            
            return PredictionHistory(
                student_id=student_id,
                course_id=course_id,
                prediction_requests=[],  # Convert from dict format
                actual_results=[],
                prediction_accuracy=successful / total if total > 0 else 0.0,
                last_prediction_date=datetime.fromisoformat(predictions[0]['timestamp']),
                total_predictions=total,
                successful_predictions=successful,
                failed_predictions=total - successful
            )
            
        except Exception as e:
            logger.error(f"Error getting prediction history: {str(e)}")
            raise DatabaseError(f"Failed to get prediction history: {str(e)}")
    
    # region: Model Performance Monitoring
    
    async def monitor_model_performance(self, model_id: str) -> ModelPerformance:
        """Monitor model performance over time"""
        try:
            # Get model evaluations
            evaluations = await self.find_many('model_evaluations', {
                'model_id': model_id
            }, sort=[('evaluation_timestamp', -1)], limit=10)
            
            if not evaluations:
                raise NotFoundError(f"No evaluations found for model: {model_id}")
            
            # Calculate performance trends
            metrics = {}
            trends = {}
            
            for metric_name in ['mae', 'rmse', 'r2_score', 'accuracy']:
                values = [eval.get('evaluation_metrics', {}).get(metric_name) for eval in evaluations]
                values = [v for v in values if v is not None]
                
                if values:
                    metrics[metric_name] = values[-1]  # Latest value
                    trends[metric_name] = values
            
            # Detect drift
            drift_metrics = await self._detect_model_drift(evaluations)
            
            # Calculate performance degradation
            degradation = None
            if len(evaluations) > 1:
                latest = evaluations[0]['evaluation_metrics']
                previous = evaluations[1]['evaluation_metrics']
                if 'accuracy' in latest and 'accuracy' in previous:
                    degradation = latest['accuracy'] - previous['accuracy']
            
            return ModelPerformance(
                performance_id=self._generate_performance_id(),
                model_id=model_id,
                version=evaluations[0]['model_version'],
                evaluation_period="weekly",
                key_metrics=metrics,
                trend_analysis=trends,
                drift_detection=drift_metrics,
                performance_degradation=degradation,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error monitoring model performance: {str(e)}")
            raise DatabaseError(f"Failed to monitor model performance: {str(e)}")
    
    async def detect_model_drift(self, model_id: str) -> Dict[str, Any]:
        """Detect model drift for a specific model"""
        try:
            # Get recent predictions and actual values
            recent_predictions = await self.find_many('predictions', {
                'model_id': model_id,
                'timestamp': {'$gte': datetime.utcnow() - timedelta(days=30)}
            }, limit=100)
            
            if not recent_predictions:
                return {'drift_detected': False, 'drift_metrics': {}}
            
            # Calculate drift metrics
            drift_metrics = {
                'prediction_drift': self._calculate_prediction_drift(recent_predictions),
                'feature_drift': await self._calculate_feature_drift(model_id),
                'concept_drift': self._calculate_concept_drift(recent_predictions)
            }
            
            # Determine if drift is significant
            drift_detected = any(
                abs(metric) > 0.1 for metric in drift_metrics.values() 
                if isinstance(metric, (int, float))
            )
            
            return {
                'drift_detected': drift_detected,
                'drift_metrics': drift_metrics,
                'drift_level': 'high' if drift_detected else 'low',
                'recommended_actions': self._get_drift_recommendations(drift_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error detecting model drift: {str(e)}")
            raise DatabaseError(f"Failed to detect model drift: {str(e)}")
    
    # region: Feature Engineering
    
    async def perform_feature_engineering(
        self, 
        raw_data: Union[UploadFile, List[Dict[str, Any]]],
        config: FeatureEngineeringConfig
    ) -> pd.DataFrame:
        """Perform feature engineering on raw data"""
        try:
            # Load data
            if isinstance(raw_data, UploadFile):
                df = pd.read_csv(raw_data.file)
            else:
                df = pd.DataFrame(raw_data)
            
            # Apply feature creation rules
            for feature_name, rule in config.feature_creation_rules.items():
                df = self._create_feature(df, feature_name, rule)
            
            # Apply transformations
            for column_name, transformation in config.feature_transformation.items():
                if column_name in df.columns:
                    df[column_name] = self._transform_feature(df[column_name], transformation)
            
            # Feature selection
            if config.feature_selection:
                df = await self._select_features(df, config.feature_selection_method)
            
            # Dimensionality reduction if requested
            if config.dimensionality_reduction and config.reduction_method:
                df = self._reduce_dimensions(df, config.reduction_method, config.feature_extraction)
            
            return df
            
        except Exception as e:
            logger.error(f"Error performing feature engineering: {str(e)}")
            raise DatabaseError(f"Failed to perform feature engineering: {str(e)}")
    
    async def analyze_feature_importance(self, model_version_id: str) -> List[FeatureImportance]:
        """Analyze feature importance for a model"""
        try:
            model_version = await self.get_model_version(model_version_id)
            if not model_version:
                raise NotFoundError(f"Model version not found: {model_version_id}")
            
            # Load model
            model_path = self._model_paths / f"{model_version_id}.pkl"
            if not model_path.exists():
                raise NotFoundError(f"Model file not found: {model_path}")
            
            model = joblib.load(model_path)
            
            # Get feature importance
            importance_scores = model.feature_importances_
            feature_names = model_version.training_config.features
            
            # Create feature importance records
            importance_records = []
            for i, importance in enumerate(importance_scores):
                importance_record = FeatureImportance(
                    feature_name=feature_names[i],
                    importance_score=float(importance),
                    importance_rank=i + 1,
                    category="academic"
                )
                importance_records.append(importance_record)
            
            # Sort by importance
            importance_records.sort(key=lambda x: x.importance_score, reverse=True)
            
            # Update ranks
            for i, importance in enumerate(importance_records):
                importance.importance_rank = i + 1
            
            logger.info(f"Feature importance analyzed for model: {model_version.model_name}")
            return importance_records
            
        except Exception as e:
            logger.error(f"Error analyzing feature importance: {str(e)}")
            raise DatabaseError(f"Failed to analyze feature importance: {str(e)}")
    
    # region: Helper Methods
    
    async def _initialize_default_models(self) -> None:
        """Initialize with default models"""
        try:
            # Create default model versions
            default_models = [
                {
                    'model_name': 'Academic_Performance_Predictor',
                    'model_type': ModelType.RANDOM_FOREST,
                    'description': 'Default model for predicting student academic performance',
                    'training_config': self._default_training_config,
                    'features': ['attendance_rate', 'previous_marks', 'study_hours_per_week', 'completion_rate'],
                    'target_variable': 'final_marks',
                    'created_by': 'system'
                },
                {
                    'model_name': 'At_Risk_Student_Predictor',
                    'model_type': ModelType.RANDOM_FOREST,
                    'description': 'Model to identify at-risk students',
                    'training_config': self._default_training_config,
                    'features': ['attendance_rate', 'previous_marks', 'completion_rate', 'gpa'],
                    'target_variable': 'at_risk',
                    'created_by': 'system'
                }
            ]
            
            for model_config in default_models:
                await self.create_model_version(**model_config)
            
            logger.info("Default models initialized")
            
        except Exception as e:
            logger.error(f"Error initializing default models: {str(e)}")
    
    async def _load_model_for_prediction(self, model_version: ModelVersion) -> Any:
        """Load model into memory for prediction"""
        try:
            model_path = self._model_paths / f"{model_version.version_id}.pkl"
            
            if not model_path.exists():
                raise NotFoundError(f"Model file not found: {model_path}")
            
            model = joblib.load(model_path)
            self._model_cache[model_version.version_id] = model
            self._active_models[model_version.model_name] = model_version
            
            return model
            
        except Exception as e:
            logger.error(f"Error loading model for prediction: {str(e)}")
            raise DatabaseError(f"Failed to load model: {str(e)}")
    
    async def _process_training_data(
        self, 
        training_data: Union[UploadFile, List[Dict[str, Any]]], 
        config: ModelTrainingConfig
    ) -> pd.DataFrame:
        """Process training data"""
        try:
            # Load data
            if isinstance(training_data, UploadFile):
                df = pd.read_csv(training_data.file)
            else:
                df = pd.DataFrame(training_data)
            
            # Handle missing values
            if config.missing_values_handling == 'median':
                for col in df.select_dtypes(include=[np.number]).columns:
                    if col != config.target_variable:
                        df[col].fillna(df[col].median(), inplace=True)
            elif config.missing_values_handling == 'mean':
                for col in df.select_dtypes(include=[np.number]).columns:
                    if col != config.target_variable:
                        df[col].fillna(df[col].mean(), inplace=True)
            elif config.missing_values_handling == 'drop':
                df.dropna(inplace=True)
            
            # Remove outliers if requested
            if config.outlier_removal:
                df = self._remove_outliers(df)
            
            # Scale features if requested
            if config.scaling_method != 'none':
                df = self._scale_features(df, config.scaling_method)
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing training data: {str(e)}")
            raise DatabaseError(f"Failed to process training data: {str(e)}")
    
    async def _perform_feature_engineering(self, df: pd.DataFrame, model_version: ModelVersion) -> pd.DataFrame:
        """Perform feature engineering"""
        try:
            # Add interaction features
            if len(df.columns) > 1:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(numeric_cols) >= 2:
                    df[f"{numeric_cols[0]}_{numeric_cols[1]}_interaction"] = df[numeric_cols[0]] * df[numeric_cols[1]]
            
            # Add polynomial features
            for col in df.select_dtypes(include=[np.number]).columns:
                if col != model_version.training_config.target_variable:
                    df[f"{col}_squared"] = df[col] ** 2
                    df[f"{col}_sqrt"] = np.sqrt(df[col])
            
            # Add temporal features if timestamp column exists
            if 'timestamp' in df.columns:
                df['year'] = pd.to_datetime(df['timestamp']).dt.year
                df['month'] = pd.to_datetime(df['timestamp']).dt.month
                df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            return df
            
        except Exception as e:
            logger.error(f"Error performing feature engineering: {str(e)}")
            raise DatabaseError(f"Failed to perform feature engineering: {str(e)}")
    
    def _split_data(self, df: pd.DataFrame, target_variable: str, train_test_split: float) -> Tuple:
        """Split data into training and testing sets"""
        from sklearn.model_selection import train_test_split
        
        X = df.drop(columns=[target_variable])
        y = df[target_variable]
        
        return train_test_split(X, y, test_size=1-train_test_split, random_state=42)
    
    async def _train_model_pipeline(self, X_train, y_train, X_test, y_test, model_version: ModelVersion) -> Tuple:
        """Train the complete model pipeline"""
        try:
            import time
            from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
            from sklearn.model_selection import cross_val_score
            
            start_time = time.time()
            
            # Initialize model based on type
            if model_version.model_type == ModelType.RANDOM_FOREST:
                if model_version.training_config.target_variable in ['at_risk', 'pass_fail']:  # Classification
                    model = RandomForestClassifier(**model_version.training_config.hyperparameters)
                else:  # Regression
                    model = RandomForestRegressor(**model_version.training_config.hyperparameters)
            
            elif model_version.model_type == ModelType.GRADIENT_BOOSTING:
                from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
                
                if model_version.training_config.target_variable in ['at_risk', 'pass_fail']:  # Classification
                    model = GradientBoostingClassifier(**model_version.training_config.hyperparameters)
                else:  # Regression
                    model = GradientBoostingRegressor(**model_version.training_config.hyperparameters)
            
            else:
                raise ValidationError(f"Model type not supported: {model_version.model_type}")
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            evaluation_metrics = {}
            
            if model_version.training_config.target_variable in ['at_risk', 'pass_fail']:  # Classification
                evaluation_metrics['accuracy'] = accuracy_score(y_test, y_pred)
                evaluation_metrics['precision'] = precision_score(y_test, y_pred, average='weighted')
                evaluation_metrics['recall'] = recall_score(y_test, y_pred, average='weighted')
                evaluation_metrics['f1_score'] = f1_score(y_test, y_pred, average='weighted')
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=model_version.training_config.cross_validation_folds)
                evaluation_metrics['cv_scores'] = cv_scores.tolist()
                evaluation_metrics['cv_mean'] = cv_scores.mean()
                evaluation_metrics['cv_std'] = cv_scores.std()
            
            else:  # Regression
                evaluation_metrics['mae'] = mean_absolute_error(y_test, y_pred)
                evaluation_metrics['mse'] = mean_squared_error(y_test, y_pred)
                evaluation_metrics['rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
                evaluation_metrics['r2_score'] = r2_score(y_test, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=model_version.training_config.cross_validation_folds, scoring='r2')
                evaluation_metrics['cv_scores'] = cv_scores.tolist()
                evaluation_metrics['cv_mean'] = cv_scores.mean()
                evaluation_metrics['cv_std'] = cv_scores.std()
            
            training_time = time.time() - start_time
            
            evaluation_metrics['training_time'] = training_time
            evaluation_metrics['prediction_time'] = time.time() - start_time
            
            return model, evaluation_metrics
            
        except Exception as e:
            logger.error(f"Error training model pipeline: {str(e)}")
            raise DatabaseError(f"Failed to train model pipeline: {str(e)}")
    
    def _prepare_prediction_features(self, features: List[PredictionFeature]) -> List[float]:
        """Prepare features for prediction"""
        feature_dict = {f.name: f.value for f in features}
        
        # Ensure all required features are present
        required_features = ['attendance_rate', 'previous_marks', 'study_hours_per_week', 'completion_rate']
        for req_feature in required_features:
            if req_feature not in feature_dict:
                feature_dict[req_feature] = 0.0  # Default value
        
        # Convert to list in correct order
        ordered_features = [feature_dict[req_feature] for req_feature in required_features]
        
        return ordered_features
    
    def _calculate_prediction_confidence(self, model, X: List[float]) -> float:
        """Calculate prediction confidence"""
        try:
            # For ensemble models, use the prediction probability
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba([X])[0]
                confidence = max(probabilities)
            else:
                # For regression models, use prediction variance or proximity to training data
                confidence = 0.7  # Default confidence for regression
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.5  # Default confidence
    
    def _calculate_prediction_interval(self, model, X: List[float]) -> Optional[Tuple[float, float]]:
        """Calculate prediction interval for regression models"""
        try:
            # For regression models that support prediction intervals
            if hasattr(model, 'predict_interval'):
                intervals = model.predict_interval([X])
                return tuple(intervals[0])
            else:
                # Use standard error approximation
                prediction = model.predict([X])[0]
                std_error = 5.0  # Approximate standard error
                return (prediction - 1.96 * std_error, prediction + 1.96 * std_error)
                
        except Exception:
            return None
    
    def _generate_prediction_explanation(self, request: PredictionRequest, prediction: float, confidence: float) -> str:
        """Generate explanation for prediction"""
        try:
            explanations = {
                PredictionType.MARKS_PREDICTION: [
                    f"Based on the student's attendance rate and previous performance, predicted marks are {prediction:.1f}.",
                    f"Confidence level: {confidence:.2%}. Higher attendance and study hours typically improve predictions."
                ],
                PredictionType.GRADE_PREDICTION: [
                    f"Predicted grade: {self._marks_to_grade(prediction)}. This reflects the student's current performance trend.",
                    f"Confidence level: {confidence:.2%}. Consider improving study habits for better grades."
                ],
                PredictionType.AT_RISK_PREDICTION: [
                    f"Risk assessment: {'HIGH' if prediction > 0.7 else 'MODERATE' if prediction > 0.4 else 'LOW'}",
                    f"Based on attendance, marks, and completion patterns. Focus on attendance for improvement."
                ]
            }
            
            base_explanation = explanations.get(request.prediction_type, [
                f"Prediction: {prediction:.1f}",
                f"Confidence: {confidence:.2%}"
            ])
            
            return " ".join(base_explanation)
            
        except Exception:
            return f"Prediction: {prediction:.1f}, Confidence: {confidence:.2%}"
    
    def _marks_to_grade(self, marks: float) -> str:
        """Convert marks to letter grade"""
        if marks >= 90:
            return 'A+'
        elif marks >= 80:
            return 'A'
        elif marks >= 70:
            return 'B'
        elif marks >= 60:
            return 'C'
        elif marks >= 50:
            return 'D'
        else:
            return 'F'
    
    async def _cache_prediction_result(self, result: PredictionResult) -> None:
        """Cache prediction result"""
        try:
            cache_key = f"prediction_{result.request_id}"
            cache_data = {
                'result': result.__dict__,
                'timestamp': result.timestamp.isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=self._prediction_cache_ttl)).isoformat()
            }
            
            await self.cache.set(cache_key, cache_data, ttl=self._prediction_cache_ttl)
            
        except Exception as e:
            logger.warning(f"Failed to cache prediction result: {str(e)}")
    
    def _calculate_data_hash(self, df: pd.DataFrame) -> str:
        """Calculate hash of dataset"""
        data_str = df.to_string()
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _generate_model_id(self) -> str:
        """Generate unique model ID"""
        return f"mdl_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _generate_model_version_id(self) -> str:
        """Generate unique model version ID"""
        return f"ver_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _generate_request_id(self) -> str:
        """Generate unique prediction request ID"""
        return f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _generate_session_id(self) -> str:
        """Generate unique training session ID"""
        return f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _generate_performance_id(self) -> str:
        """Generate unique performance ID"""
        return f"perf_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _scale_features(self, df: pd.DataFrame, scaling_method: str) -> pd.DataFrame:
        """Scale features"""
        from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return df
        
        df_copy = df.copy()
        
        if scaling_method == 'standard':
            scaler = StandardScaler()
        elif scaling_method == 'minmax':
            scaler = MinMaxScaler()
        elif scaling_method == 'robust':
            scaler = RobustScaler()
        else:
            return df_copy
        
        df_copy[numeric_cols] = scaler.fit_transform(df_copy[numeric_cols])
        return df_copy
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return df
        
        df_copy = df.copy()
        
        for col in numeric_cols:
            Q1 = df_copy[col].quantile(0.25)
            Q3 = df_copy[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            df_copy = df_copy[(df_copy[col] >= lower_bound) & (df_copy[col] <= upper_bound)]
        
        return df_copy
    
    def _create_feature(self, df: pd.DataFrame, feature_name: str, rule: Dict[str, Any]) -> pd.DataFrame:
        """Create new feature based on rule"""
        try:
            if rule['type'] == 'arithmetic':
                df[feature_name] = eval(rule['formula'], {}, df.to_dict('list'))
            elif rule['type'] == 'categorical':
                df[feature_name] = df[rule['source_column']].apply(rule['mapping'])
            elif rule['type'] == 'statistical':
                if rule['function'] == 'rolling_mean':
                    df[feature_name] = df[rule['source_column']].rolling(rule['window']).mean()
            
            return df
            
        except Exception as e:
            logger.warning(f"Error creating feature {feature_name}: {str(e)}")
            return df
    
    def _transform_feature(self, series: pd.Series, transformation: str) -> pd.Series:
        """Transform a single feature"""
        try:
            if transformation == 'log':
                return np.log1p(series)
            elif transformation == 'sqrt':
                return np.sqrt(series.abs())
            elif transformation == 'square':
                return series ** 2
            elif transformation == 'normalize':
                return (series - series.mean()) / series.std()
            else:
                return series
                
        except Exception as e:
            logger.warning(f"Error transforming feature: {str(e)}")
            return series
    
    async def _select_features(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """Select features based on method"""
        from sklearn.feature_selection import SelectKBest, f_classif, f_regression, mutual_info_classif, mutual_info_regression
        
        X = df.drop(columns=['target_variable'])  # Assuming target is named 'target_variable'
        y = df['target_variable']
        
        if method == 'correlation':
            # Simple correlation-based selection
            corr_matrix = df.corr()
            high_corr_features = corr_matrix.index[abs(corr_matrix['target_variable']) > 0.5]
            return df[high_corr_features]
        
        elif method in ['mutual_info', 'mutual_info_classif', 'mutual_info_regression']:
            if method == 'mutual_info_classif':
                selector = SelectKBest(mutual_info_classif, k=10)
            else:
                selector = SelectKBest(mutual_info_regression, k=10)
            
            X_selected = selector.fit_transform(X, y)
            selected_features = X.columns[selector.get_support()]
            return df[selected_features.tolist() + ['target_variable']]
        
        elif method == 'variance_threshold':
            from sklearn.feature_selection import VarianceThreshold
            selector = VarianceThreshold(threshold=0.1)
            X_selected = selector.fit_transform(X)
            selected_features = X.columns[selector.get_support()]
            return df[selected_features.tolist() + ['target_variable']]
        
        else:
            return df
    
    def _reduce_dimensions(self, df: pd.DataFrame, method: str, config: Dict[str, Any]) -> pd.DataFrame:
        """Reduce dimensionality"""
        from sklearn.decomposition import PCA, TruncatedSVD
        
        X = df.drop(columns=['target_variable'])
        
        if method == 'pca':
            n_components = config.get('n_components', min(X.shape[1], 10))
            pca = PCA(n_components=n_components)
            X_reduced = pca.fit_transform(X)
            df_reduced = pd.DataFrame(X_reduced, columns=[f'PC_{i+1}' for i in range(n_components)])
            df_reduced['target_variable'] = df['target_variable']
            return df_reduced
        
        elif method == 'svd':
            n_components = config.get('n_components', min(X.shape[1], 10))
            svd = TruncatedSVD(n_components=n_components)
            X_reduced = svd.fit_transform(X)
            df_reduced = pd.DataFrame(X_reduced, columns=[f'SVD_{i+1}' for i in range(n_components)])
            df_reduced['target_variable'] = df['target_variable']
            return df_reduced
        
        else:
            return df
    
    def _calculate_prediction_drift(self, recent_predictions: List[Dict[str, Any]]) -> float:
        """Calculate prediction drift"""
        if len(recent_predictions) < 2:
            return 0.0
        
        # Calculate trend in prediction accuracy over time
        predictions = [p.get('predicted_value', 0) for p in recent_predictions]
        if len(predictions) > 1:
            trend = np.polyfit(range(len(predictions)), predictions, 1)[0]
            return float(trend)
        
        return 0.0
    
    async def _calculate_feature_drift(self, model_id: str) -> float:
        """Calculate feature drift"""
        # This would compare current feature distributions with training data
        # For now, return a placeholder value
        return 0.1
    
    def _calculate_concept_drift(self, recent_predictions: List[Dict[str, Any]]) -> float:
        """Calculate concept drift"""
        # This would analyze patterns in prediction errors over time
        # For now, return a placeholder value
        return 0.05
    
    def _get_drift_recommendations(self, drift_metrics: Dict[str, Any]) -> List[str]:
        """Get recommendations based on drift metrics"""
        recommendations = []
        
        if drift_metrics.get('prediction_drift', 0) > 0.2:
            recommendations.append("Retrain model with recent data")
            recommendations.append("Update feature engineering process")
        
        if drift_metrics.get('feature_drift', 0) > 0.15:
            recommendations.append("Review feature distributions")
            recommendations.append("Consider collecting more recent data")
        
        if drift_metrics.get('concept_drift', 0) > 0.1:
            recommendations.append("Investigate changing student patterns")
            recommendations.append("Update model to reflect current trends")
        
        if not recommendations:
            recommendations.append("Model performance is acceptable")
        
        return recommendations