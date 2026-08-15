# Rust AI Services Implementation

## Overview

This package provides comprehensive AI services for Edu-Flow using a modular, config-based architecture:
- **Configuration Management**: Centralized, environment-driven configuration
- **Service Registry**: Service discovery and lifecycle management
- **Course Recommendations**: Intelligent course suggestions based on student data
- **Knowledge Search**: Semantic search and knowledge graph traversal
- **Adaptive Learning**: Personalized learning paths and content adaptation
- **Integration Layer**: Python-Rust service communication
- **Monitoring**: Prometheus metrics, health checks, and observability
- **Service Container**: Centralized service management

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Service Container                    │
│  - Manages all services                                 │
│  - Handles initialization and lifecycle                 │
│  - Provides statistics and health checks               │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼────────┐ ┌───────▼────────┐
│ Course         │ │ Knowledge     │ │ Adaptive       │
│ Recommendation │ │ Search        │ │ Learning       │
│ Service        │ │ Service       │ │ Service        │
└────────────────┘ └───────────────┘ └────────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼────────┐ ┌───────▼────────┐
│ Integration    │ │ Monitoring    │ │ Service        │
│ Layer          │ │ System        │ │ Registry       │
└────────────────┘ └───────────────┘ └────────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
┌──────────────────────────▼───────────────────────────┐
│                   Configuration                       │
│  - Environment variables                              │
│  - JSON config files                                  │
│  - Service-specific settings                          │
└───────────────────────────────────────────────────────┘
```

## Features

### 1. Configuration Management
- Centralized configuration via JSON files
- Environment variable support
- Service-specific configurations
- Model configurations
- Database and cache configurations
- Easy to adapt and extend

### 2. Service Registry
- Service discovery and registration
- Health checking
- Load balancing support
- Graceful degradation
- Fault tolerance

### 3. AI Services

#### Course Recommendation Service
- Collaborative filtering-based recommendations
- Personalized course suggestions
- Prerequisite checking
- Difficulty level adaptation
- 20+ API endpoints

#### Knowledge Search Service
- Semantic search capabilities
- Knowledge graph traversal
- Multi-source aggregation
- Context-aware results
- Hybrid search (keyword + semantic)

#### Adaptive Learning Service
- Personalized content delivery
- Adaptive difficulty adjustment
- Real-time feedback
- Learning path optimization
- Skill mastery tracking

### 4. Integration Layer
- REST API communication (Python ↔ Rust)
- Request/response caching
- Retry logic with exponential backoff
- Error handling and logging
- Distributed tracing support

### 5. Monitoring & Observability
- Prometheus metrics collection
- Service health checks
- Request latency tracking
- Error rate monitoring
- Cache performance tracking
- System-wide metrics

## Installation

1. Ensure dependencies are installed:
```bash
pip install pydantic aiohttp prometheus_client
```

2. Configure services:
```bash
cp src/services/rust_ai_services/rust_ai_config.example.json src/services/rust_ai_services/rust_ai_config.json
```

3. Set environment variables:
```bash
export DB_PASSWORD="your_password"
export RUST_AI_SERVICES_ENABLED="true"
```

4. Start the application:
```bash
python -m uvicorn src.main:app --reload
```

## API Endpoints

### Rust AI Services

#### Health Check
```
GET /rust-ai/health
```
Check health of all Rust AI services.

#### Service Health
```
GET /rust-ai/services/{service_name}
```
Check health of a specific service.

#### Statistics
```
GET /rust-ai/stats
```
Get statistics about Rust AI services.

### SEE Prediction Service (Python)
- `/api/v1/see-prediction/models` - GET/POST
- `/api/v1/see-prediction/predictions` - POST
- `/api/v1/see-prediction/features/engineer` - POST
- And 17 more endpoints

### Advanced Analytics Service (Python)
- `/api/v1/analytics/query/execute` - POST
- `/api/v1/analytics/students/{student_id}/performance` - GET
- `/api/v1/analytics/dashboards` - POST
- And 15 more endpoints

## Configuration

### Example Configuration

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "username": "postgres",
    "password": "your_password",
    "database": "edu_flow"
  },
  "cache": {
    "backend": "redis",
    "host": "localhost",
    "port": 6379
  },
  "models": {
    "course_recommendation": {
      "model_type": "collaborative_filtering",
      "model_path": "models/course_recommendation.pt",
      "framework": "candle",
      "device": "cpu"
    }
  },
  "services": {
    "course_recommendation": {
      "service_name": "course_recommendation",
      "service_type": "ai_service",
      "api_endpoint": "http://localhost:8002",
      "enable_metrics": true
    }
  }
}
```

## Usage Examples

### Get Course Recommendations

```python
from src.services.rust_ai_services import get_container

async def get_recommendations():
    container = get_container()
    # Get course recommendation service
    service = await container.get_service("course_recommendation")
    
    if service:
        from src.services.rust_ai_services import StudentProfile
        student_profile = StudentProfile(
            student_id="stu_123",
            name="John Doe",
            current_program="Computer Science",
            current_semester=3,
            gpa=3.5,
            interests=["AI", "Machine Learning"],
            strengths=["Programming", "Problem Solving"],
            preferred_learning_style="visual",
            career_goals=["ML Engineer"]
        )
        
        result = await service.get_recommendations(
            student_profile=student_profile,
            semester=4,
            limit=5
        )
        
        return result
```

### Search Knowledge Base

```python
from src.services.rust_ai_services import get_container, SearchQuery

async def search_knowledge():
    container = get_container()
    service = await container.get_service("knowledge_search")
    
    if service:
        query = SearchQuery(
            query="machine learning algorithms",
            search_type="semantic",
            limit=10
        )
        
        results = await service.search(query)
        return results
```

### Adaptive Learning Session

```python
from src.services.rust_ai_services import get_container, LearningSession

async def start_adaptive_session():
    container = get_container()
    service = await container.get_service("adaptive_learning")
    
    if service:
        session = await service.start_session(
            student_id="stu_123",
            content_id="lesson_1",
            content_type="lesson"
        )
        
        return session
```

### Check Service Health

```python
from src.services.rust_ai_services import get_container

async def check_health():
    container = get_container()
    health = await container.check_all_services_health()
    return health
```

## Design Principles

1. **Modularity**: Each service is independent and can be developed/tested separately
2. **Configurability**: All settings externalized via configuration files and environment variables
3. **Extensibility**: Easy to add new services without modifying existing code
4. **Observability**: Comprehensive monitoring and logging throughout
5. **Fault Tolerance**: Graceful degradation and retry logic
6. **Performance**: Async/await patterns, caching, and efficient communication

## Testing

Run service health checks:
```bash
curl http://localhost:8000/rust-ai/health
```

Get service statistics:
```bash
curl http://localhost:8000/rust-ai/stats
```

## Monitoring

Access Prometheus metrics at:
```
http://localhost:8000/metrics
```

Access API documentation at:
```
http://localhost:8000/docs
```

## Troubleshooting

### Services Not Loading
1. Check configuration file exists and is valid
2. Verify environment variables are set correctly
3. Ensure Rust AI services are compiled and running
4. Check application logs for errors

### High Latency
1. Check Redis cache connection
2. Verify model loading is complete
3. Monitor Prometheus metrics for bottlenecks

### Service Disconnections
1. Verify network connectivity
2. Check service health endpoints
3. Review integration layer logs

## Contributing

1. Add new service in appropriate file
2. Register service in ServiceContainer
3. Add configuration examples
4. Update documentation
5. Add unit tests

## License

Edu-Flow Team

## Support

For issues and questions, please open an issue on GitHub or contact the development team.
