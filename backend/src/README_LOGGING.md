# Edu-Flow Unified Logging System

## Overview

The Edu-Flow Unified Logging System provides comprehensive logging capabilities for the entire Edu-Flow application stack, including:
- **Backend**: Python FastAPI/Flask services
- **Frontend**: Flutter client applications
- **Auth Gateway**: Modular authentication system
- **AI Services**: Rust microservices for AI/ML features
- **Database**: PostgreSQL and MongoDB operations

## Features

### Core Features
- **Unified Architecture**: Single logging system across all components
- **Component Separation**: Separate log files and directories for each component
- **Rotating Files**: Automatic log rotation with size limits
- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **Performance Monitoring**: Automatic tracking of API performance and database operations
- **Security Logging**: Comprehensive security event tracking
- **Audit Trails**: Complete audit trails for compliance and debugging
- **Auto-cleanup**: Automatic cleanup of old log files based on retention policies

### Log Types
1. **Component Logs**: General application logs for each component
2. **Error Logs**: Separate error logs with JSON formatting for structured analysis
3. **Audit Logs**: Security and compliance logs with time-based rotation
4. **Performance Logs**: Performance metrics and API call tracking
5. **Security Logs**: Security events and authentication attempts

## Directory Structure

```
logs/
├── backend/
│   ├── backend.log              # General backend logs
│   ├── backend_error.log        # Backend error logs (JSON format)
│   ├── backend_audit.log        # Backend audit logs (daily rotation)
│   ├── errors/                  # Error log archives
│   ├── audit/                   # Audit log archives
│   ├── performance/             # Performance log archives
│   └── api/                     # API log archives
├── frontend/
│   ├── frontend.log              # General frontend logs
│   ├── frontend_error.log        # Frontend error logs (JSON format)
│   ├── frontend_audit.log        # Frontend audit logs (daily rotation)
│   └── [subdirectories...]
├── auth-gateway/
│   ├── auth-gateway.log         # General auth gateway logs
│   ├── auth-gateway_error.log    # Auth gateway error logs (JSON format)
│   ├── auth-gateway_audit.log    # Auth gateway audit logs (daily rotation)
│   └── [subdirectories...]
├── ai-services/
│   ├── ai-services.log          # General AI services logs
│   ├── ai-services_error.log     # AI services error logs (JSON format)
│   ├── ai-services_audit.log     # AI services audit logs (daily rotation)
│   └── [subdirectories...]
└── database/
    ├── database.log              # General database logs
    ├── database_error.log        # Database error logs (JSON format)
    ├── database_audit.log        # Database audit logs (daily rotation)
    └── [subdirectories...]
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development, testing, production) | development |
| `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| `LOG_ROTATION_SIZE` | Log rotation size in bytes | 10MB |
| `LOG_BACKUP_COUNT` | Number of backup log files to keep | 10 |
| `LOG_CLEANUP_DAYS` | Number of days to keep log files | 30 |
| `SENTRY_DSN` | Sentry DSN for error tracking | - |
| `ELASTICSEARCH_HOST` | Elasticsearch host | - |
| `FLUENTD_HOST` | Fluentd host | - |

### Logging Levels

- **DEBUG**: Detailed information for development
- **INFO**: General information about application operation
- **WARNING**: Warning messages that indicate potential issues
- **ERROR**: Error messages that indicate problems
- **CRITICAL**: Critical errors that require immediate attention

## Usage

### Basic Usage

```python
from src.config.logging import get_logger

# Get a logger for a specific component
logger = get_logger('backend')

# Log messages
logger.info("Application started successfully")
logger.error("Database connection failed", db_host="localhost", db_port=5432)
logger.warning("Rate limit approaching", current_rate=95, max_rate=100)
logger.debug("Detailed debugging information")
```

### With Context

```python
from src.config.logging import get_logger

logger = get_logger('backend')

# Log with additional context
logger.info("User created account", 
           user_id="user123", 
           email="user@example.com",
           ip_address="192.168.1.1")
```

### Audit Logging

```python
from src.config.logging import get_logger

logger = get_logger('auth-gateway')

# Log audit events
logger.audit(
    action="user_login",
    user="user123",
    resource="auth_service",
    details={"method": "jwt", "ip": "192.168.1.1"}
)
```

### Security Logging

```python
from src.config.logging import get_logger

logger = get_logger('security')

# Log security events
logger.security_event(
    event_type="unauthorized_access",
    severity="HIGH",
    details={"user_id": "user123", "resource": "admin_panel"}
)
```

### Performance Logging

```python
from src.core.logging_utils import log_performance_metric

# Log performance metrics
log_performance_metric(
    metric_name="api_response_time",
    value=0.5,
    unit="seconds",
    tags={"endpoint": "/api/users", "method": "GET"}
)
```

## Decorators

### Function Call Logging

```python
from src.core.logging_utils import log_function_call

@log_function_call('backend')
def process_user_data(user_id):
    # Function logic here
    pass
```

### API Request Logging

```python
from src.core.logging_utils import log_api_request

@log_api_request('backend')
def get_users():
    # API logic here
    pass
```

### Database Operation Logging

```python
from src.core.logging_utils import log_database_operation

@log_database_operation('select', 'users')
def get_user_by_id(user_id):
    # Database logic here
    pass
```

## FastAPI Integration

### Basic Setup

```python
from src.core.logging_integration import create_fastapi_app

# Create FastAPI app with logging
app = create_fastapi_app(
    app_name="Edu-Flow",
    environment="production"
)

# Add logging routes
from src.core.logging_integration import add_logging_routes
add_logging_routes(app)
```

### Middleware Usage

```python
from src.core.logging_middleware import LoggingMiddleware

# Add logging middleware
app.add_middleware(LoggingMiddleware)
```

## Flask Integration

### Basic Setup

```python
from src.core.flask_logging_integration import create_flask_app

# Create Flask app with logging
app = create_flask_app(
    app_name="Edu-Flow",
    environment="production"
)
```

### Middleware Usage

```python
from src.core.flask_logging_integration import FlaskLoggingMiddleware

# Add logging middleware
FlaskLoggingMiddleware(app)
```

## Log Analysis

### Log Formats

1. **Standard Format**
   ```
   2024-01-01 12:00:00 - edu-flow-backend - INFO - User created account
   ```

2. **JSON Format (Errors & Security)**
   ```json
   {
     "timestamp": "2024-01-01T12:00:00.000Z",
     "level": "ERROR",
     "logger": "edu-flow-backend",
     "message": "Database connection failed",
     "error": "Connection refused",
     "exception": "...",
     "context": {
       "db_host": "localhost",
       "db_port": 5432
     }
   }
   ```

### Log Rotation

- **Size-based rotation**: Files are rotated when they reach the specified size (default: 10MB)
- **Time-based rotation**: Audit logs are rotated daily
- **Backup retention**: Number of backup files to keep (default: 10)
- **Auto-cleanup**: Old log files are automatically cleaned up based on retention policy

### Performance Considerations

- **Async logging**: All logging operations are non-blocking
- **Buffering**: Log writes are batched for better performance
- **Memory usage**: Log rotation prevents unlimited memory growth
- **Disk space**: Automatic cleanup prevents disk space issues

## Monitoring and Alerting

### Built-in Metrics

1. **API Performance**
   - Request duration
   - Response status codes
   - Request rate
   - Error rate

2. **System Performance**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

3. **Security Metrics**
   - Authentication attempts
   - Authorization failures
   - Security events
   - Suspicious activities

### Integration Options

1. **Sentry**: Error tracking and alerting
2. **Elasticsearch**: Log aggregation and analysis
3. **Fluentd**: Log forwarding and processing
4. **Prometheus**: Metrics collection and monitoring
5. **Grafana**: Visualization and dashboards

## Best Practices

1. **Log Level Usage**
   - Use DEBUG for development troubleshooting
   - Use INFO for normal operation tracking
   - Use WARNING for potential issues
   - Use ERROR for actual problems
   - Use CRITICAL for system-threatening issues

2. **Context Information**
   - Always include relevant context in logs
   - Use structured data for complex information
   - Avoid logging sensitive data (passwords, tokens, etc.)

3. **Performance Considerations**
   - Keep log messages concise
   - Avoid logging in hot paths (frequently called functions)
   - Use appropriate log levels to reduce log volume

4. **Security Considerations**
   - Log security events with appropriate severity levels
   - Include IP addresses and user agents for security events
   - Use audit logs for compliance requirements

5. **Log Management**
   - Regularly rotate and archive logs
   - Implement log retention policies
   - Monitor log sizes and disk usage
   - Test log retrieval and analysis

## Troubleshooting

### Common Issues

1. **Log files not created**
   - Check permissions on logs directory
   - Verify disk space availability
   - Check environment configuration

2. **Logging too verbose**
   - Adjust log levels for production
   - Use appropriate context filtering
   - Implement log sampling for high-volume events

3. **Performance issues**
   - Check log rotation settings
   - Verify buffer configuration
   - Monitor disk I/O performance

### Debug Mode

Enable debug mode for detailed logging:

```python
import os
os.environ['ENVIRONMENT'] = 'development'
os.environ['LOG_LEVEL'] = 'DEBUG'
```

## Migration Guide

### From Legacy Logging

1. **Replace basic logging calls**
   ```python
   # Before
   import logging
   logging.info("Message")
   
   # After
   from src.config.logging import get_logger
   logger = get_logger('backend')
   logger.info("Message")
   ```

2. **Add context information**
   ```python
   # Before
   logger.info("User login")
   
   # After
   logger.info("User login", user_id="user123", ip="192.168.1.1")
   ```

3. **Use appropriate log types**
   ```python
   # Before
   logger.error("Security event")
   
   # After
   logger.security_event("unauthorized_access", "HIGH", details={...})
   ```

### Configuration Migration

1. **Update requirements.txt**
   - Add new logging dependencies
   - Remove conflicting logging libraries

2. **Update application startup**
   - Initialize logging system early
   - Set up middleware and decorators

3. **Update log analysis tools**
   - Configure new log formats
   - Update parsing rules for JSON logs

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the best practices guide
3. Enable debug mode for detailed information
4. Contact the development team for support

---

*This logging system is designed to scale with the Edu-Flow application and provide comprehensive monitoring capabilities across all components of the system.*