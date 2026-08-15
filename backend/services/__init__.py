"""
Rust AI Services for Edu-Flow

This package provides AI services using Rust and Candle ML framework.
All services are implemented in Rust for performance and security.
"""

from .src.ai_services import (
    StudentFeatures,
    StudentPerformanceModel,
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
