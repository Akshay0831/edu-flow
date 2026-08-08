import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json

class UnifiedLogger:
    """
    Unified logging system for Edu-Flow with rotating files, auto-cleanup,
    and support for different components (frontend, backend, microservices).
    
    Features:
    - Separate log files for different components
    - Rotating file handlers with size limits
    - Time-based rotation for daily logs
    - Automatic cleanup of old log files
    - Structured logging with JSON format
    - Console and file output
    - Component-specific log levels
    """
    
    _instances: Dict[str, 'UnifiedLogger'] = {}
    _log_levels = {
        'development': logging.DEBUG,
        'testing': logging.INFO,
        'production': logging.WARNING
    }
    
    def __new__(cls, component: str, environment: str = 'development'):
        # Check if instance already exists and environment matches
        if component in cls._instances:
            existing_instance = cls._instances[component]
            # Only recreate if environment is different
            if hasattr(existing_instance, '_environment') and existing_instance._environment == environment:
                return existing_instance
        
        # Force re-initialization if environment changes or instance doesn't exist
        if component in cls._instances:
            old_instance = cls._instances[component]
            # Close all handlers to free file handles
            for handler in old_instance.logger.handlers[:]:
                old_instance.logger.removeHandler(handler)
                handler.close()
        
        cls._instances[component] = super(UnifiedLogger, cls).__new__(cls)
        cls._instances[component]._initialize(component, environment)
        return cls._instances[component]
    
    def _initialize(self, component: str, environment: str):
        """Initialize the logger with component-specific configuration"""
        self.component = component
        self.environment = environment
        self.log_level = self._log_levels.get(environment, logging.INFO)        
        # Store environment for later reference
        self._environment = environment        
        # Create logs directory structure
        self.base_logs_dir = Path("logs")
        self.component_logs_dir = self.base_logs_dir / component
        
        # Create directories if they don't exist
        self.component_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up the logger
        self.logger = logging.getLogger(f"edu-flow-{component}")
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set up formatters
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        self.json_formatter = JSONFormatter()
        
        # Add handlers
        self._add_console_handler()
        self._add_component_handler()
        self._add_error_handler()
        self._add_audit_handler()
    
    def _add_console_handler(self):
        """Add console handler for development and testing"""
        if self.environment in ['development', 'testing']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self.console_formatter)
            self.logger.addHandler(console_handler)
    
    def _add_component_handler(self):
        """Add rotating file handler for component-specific logs"""
        log_file = self.component_logs_dir / f"{self.component}.log"
        
        component_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        component_handler.setLevel(self.log_level)
        component_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(component_handler)
        
        # Clean up old log files (older than 30 days)
        self._cleanup_old_logs()
    
    def _add_error_handler(self):
        """Add separate handler for error logs"""
        error_log_file = self.component_logs_dir / f"{self.component}_error.log"
        
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.json_formatter)
        self.logger.addHandler(error_handler)
    
    def _add_audit_handler(self):
        """Add separate handler for audit logs (auth, security, critical operations)"""
        audit_log_file = self.component_logs_dir / f"{self.component}_audit.log"
        
        audit_handler = TimedRotatingFileHandler(
            audit_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(self.json_formatter)
        self.logger.addHandler(audit_handler)
    
    def _cleanup_old_logs(self):
        """Clean up log files older than 30 days"""
        try:
            cutoff_time = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 days
            
            for log_file in self.component_logs_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.debug(f"Cleaned up old log file: {log_file}")
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self.logger.info(message, extra={'context': kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context"""
        self.logger.error(message, extra={'context': kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self.logger.warning(message, extra={'context': kwargs})
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self.logger.debug(message, extra={'context': kwargs})
    
    def audit(self, action: str, user: str, resource: str, details: Dict[str, Any] = None):
        """Log audit event for security and compliance"""
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user,
            'resource': resource,
            'component': self.component,
            'environment': self.environment
        }
        
        if details:
            audit_data.update(details)
        
        self.logger.info(f"AUDIT: {json.dumps(audit_data)}", extra={'audit': True})
    
    def security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log security events with severity levels"""
        security_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'component': self.component,
            'details': details
        }
        
        if severity.upper() in ['CRITICAL', 'HIGH']:
            self.logger.error(f"SECURITY: {json.dumps(security_data)}", extra={'security': True})
        else:
            self.logger.warning(f"SECURITY: {json.dumps(security_data)}", extra={'security': True})
    
    def api_request(self, method: str, endpoint: str, status_code: int, duration: float, user: str = None):
        """Log API requests with performance metrics"""
        api_data = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'user': user,
            'component': self.component
        }
        
        self.logger.info(f"API: {json.dumps(api_data)}", extra={'api': True})
    
    def database_operation(self, operation: str, collection: str, duration: float, record_count: int = 0):
        """Log database operations with performance metrics"""
        db_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'collection': collection,
            'duration_ms': round(duration * 1000, 2),
            'record_count': record_count,
            'component': self.component
        }
        
        self.logger.info(f"DATABASE: {json.dumps(db_data)}", extra={'database': True})
    
    def ai_service_request(self, service: str, model: str, input_size: int, output_size: int, duration: float):
        """Log AI service requests with performance metrics"""
        ai_data = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'model': model,
            'input_size': input_size,
            'output_size': output_size,
            'duration_ms': round(duration * 1000, 2),
            'component': self.component
        }
        
        self.logger.info(f"AI: {json.dumps(ai_data)}", extra={'ai': True})


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'component': getattr(record, 'component', 'unknown')
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        # Add audit data
        if hasattr(record, 'audit'):
            log_entry['audit'] = True
        
        # Add security data
        if hasattr(record, 'security'):
            log_entry['security'] = True
        
        # Add API data
        if hasattr(record, 'api'):
            log_entry['api'] = True
        
        # Add database data
        if hasattr(record, 'database'):
            log_entry['database'] = True
        
        # Add AI data
        if hasattr(record, 'ai'):
            log_entry['ai'] = True
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


# Global logger instances for different components
def get_logger(component: str = 'backend', environment: str = None) -> UnifiedLogger:
    """Get or create a logger instance for a specific component"""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    return UnifiedLogger(component, environment)

def reset_loggers():
    """Reset all logger instances (useful for testing)"""
    for instance in UnifiedLogger._instances.values():
        for handler in instance.logger.handlers[:]:
            instance.logger.removeHandler(handler)
            handler.close()
    UnifiedLogger._instances.clear()


# Configuration for different environments
LOGGING_CONFIG = {
    'development': {
        'level': 'DEBUG',
        'console': True,
        'files': True,
        'rotation_size': '10MB',
        'backup_count': 10,
        'cleanup_days': 30
    },
    'testing': {
        'level': 'INFO',
        'console': True,
        'files': True,
        'rotation_size': '5MB',
        'backup_count': 5,
        'cleanup_days': 7
    },
    'production': {
        'level': 'WARNING',
        'console': False,
        'files': True,
        'rotation_size': '20MB',
        'backup_count': 20,
        'cleanup_days': 90
    }
}

# Export functions
__all__ = ['UnifiedLogger', 'get_logger', 'get_component_logger', 'LOGGING_CONFIG']

def get_component_logger(component: str, environment: str = 'development') -> 'UnifiedLogger':
    """Get logger for a specific component (alias for get_logger)"""
    return get_logger(component, environment)