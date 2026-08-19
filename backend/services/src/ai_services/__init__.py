"""
AI Services for Edu-Flow

This module contains Rust AI service implementations using Candle ML framework.
"""

from .models import (
    StudentFeatures,
    StudentPerformanceModel,
)

from .performance_prediction import (
    PerformancePrediction,
    PerformanceMetrics,
    PerformancePredictionService,
)

__all__ = [
    "StudentFeatures",
    "StudentPerformanceModel",
    "PerformancePrediction",
    "PerformanceMetrics",
    "PerformancePredictionService",
]
