"""
Logging configuration setup for Edu-Flow application.
This module provides easy configuration and initialization of the logging system.
"""

import os
import sys
from typing import Dict, Any
from pathlib import Path

from .logging import get_logger, LOGGING_CONFIG

class LoggingConfig:
    """Centralized logging configuration manager"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.config = LOGGING_CONFIG.get(self.environment, LOGGING_CONFIG['development'])
        
        # Create logs directory structure
        self._setup_log_directories()
        
        # Initialize loggers for different components
        self.loggers = {}
        self._initialize_loggers()
    
    def _setup_log_directories(self):
        """Create the directory structure for logs"""
        logs_dir = Path("logs")
        
        # Component directories
        components = ['backend', 'frontend', 'auth-gateway', 'ai-services', 'database']
        
        for component in components:
            component_dir = logs_dir / component
            component_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different log types
            subdirs = ['errors', 'audit', 'performance', 'api']
            for subdir in subdirs:
                subdir_path = component_dir / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
    
    def _initialize_loggers(self):
        """Initialize loggers for different components"""
        # Core application loggers
        self.loggers['backend'] = get_logger('backend', self.environment)
        self.loggers['frontend'] = get_logger('frontend', self.environment)
        self.loggers['auth-gateway'] = get_logger('auth-gateway', self.environment)
        
        # Service loggers
        self.loggers['ai-services'] = get_logger('ai-services', self.environment)
        self.loggers['database'] = get_logger('database', self.environment)
        
        # Specialized loggers
        self.loggers['performance'] = get_logger('performance', self.environment)
        self.loggers['security'] = get_logger('security', self.environment)
    
    def get_logger(self, component: str) -> 'UnifiedLogger':
        """Get logger for a specific component"""
        if component not in self.loggers:
            self.loggers[component] = get_logger(component, self.environment)
        return self.loggers[component]
    
    def configure_fluentd(self, host: str = 'localhost', port: int = 24224):
        """Configure fluentd integration for log forwarding"""
        try:
            import fluent
            from fluent import handler
            
            fluent_handler = handler.FluentHandler(
                'edu-flow',
                host=host,
                port=port
            )
            
            # Add fluentd handler to all loggers
            for logger in self.loggers.values():
                if hasattr(logger, 'logger'):
                    logger.logger.addHandler(fluent_handler)
                    
        except ImportError:
            # fluentd not available, skip configuration
            pass
    
    def configure_sentry(self, dsn: str = None):
        """Configure Sentry integration for error tracking"""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_dsn = dsn or os.getenv('SENTRY_DSN')
            if sentry_dsn:
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR # Send errors as events
                )
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[sentry_logging],
                    traces_sample_rate=0.2,
                    environment=self.environment
                )
                
                # Add sentry handler to error loggers
                error_loggers = ['backend', 'frontend', 'auth-gateway']
                for component in error_loggers:
                    if component in self.loggers:
                        # Note: This would need additional implementation in the UnifiedLogger
                        pass
                        
        except ImportError:
            # sentry-sdk not available, skip configuration
            pass
    
    def configure_elasticsearch(self, hosts: list = None, index: str = 'edu-flow-logs'):
        """Configure Elasticsearch integration for log storage and analysis"""
        try:
            import elasticsearch
            from elasticsearch.handlers import logging
            
            es_hosts = hosts or [os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')]
            
            # Elasticsearch handler would need to be implemented
            # This is a placeholder for future implementation
            
        except ImportError:
            # elasticsearch not available, skip configuration
            pass


def setup_logging(environment: str = None) -> LoggingConfig:
    """
    Setup logging configuration for the application.
    
    Args:
        environment: Environment (development, testing, production)
        
    Returns:
        LoggingConfig instance
    """
    return LoggingConfig(environment)


def get_component_logger(component: str, environment: str = None) -> 'UnifiedLogger':
    """
    Get a logger for a specific component.
    
    Args:
        component: Component name (backend, frontend, auth-gateway, etc.)
        environment: Environment (development, testing, production)
        
    Returns:
        UnifiedLogger instance
    """
    config = setup_logging(environment)
    return config.get_logger(component)