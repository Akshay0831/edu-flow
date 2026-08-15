# Edu-Flow Backend Deployment Guide

This guide provides comprehensive instructions for deploying and managing the Edu-Flow backend API service.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Security Considerations](#security-considerations)
8. [Scaling and Performance](#scaling-and-performance)
9. [Troubleshooting](#troubleshooting)
10. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04/22.04, CentOS 8/9, or Windows 10/11
- **Python**: 3.11 or higher
- **Docker**: 20.10 or higher (for containerized deployment)
- **Docker Compose**: 2.0 or higher
- **Kubernetes**: 1.21 or higher (optional, for K8s deployment)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 50GB, Recommended 100GB+

### Database Requirements
- **PostgreSQL**: 14 or higher
- **MongoDB**: 5.0 or higher
- **Redis**: 6.2 or higher

### Network Requirements
- **Inbound Ports**: 8000 (API), 5432 (PostgreSQL), 27017 (MongoDB), 6379 (Redis)
- **Outbound Ports**: 443 (HTTPS), 80 (HTTP)
- **Bandwidth**: Minimum 10Mbps

## Local Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd edu-flow/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Database Setup

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres createdb eduflow_db
sudo -u postgres psql -c "CREATE USER eduflow_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE eduflow_db TO eduflow_user;"

# Install MongoDB
sudo apt-get install mongodb

# Install Redis
sudo apt-get install redis-server
```

### 3. Configure Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://eduflow_user:password@localhost:5432/eduflow_db
MONGODB_URL=mongodb://localhost:27017/eduflow
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/api.log
```

### 4. Run the Application

```bash
# Run database migrations
python -m src.core.database_migrations

# Run the application
uvicorn src.api.v1:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_user_service.py

# Run integration tests
pytest tests/integration/
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Start all services
docker-compose -f backend.docker-compose.yml up -d

# View logs
docker-compose -f backend.docker-compose.yml logs -f backend-api

# Stop all services
docker-compose -f backend.docker-compose.yml down
```

### 2. Build Docker Image Manually

```bash
# Build development image
docker build -t eduflow-backend:dev -f Dockerfile .

# Build production image
docker build --target production -t eduflow-backend:latest -f Dockerfile .

# Run container
docker run -d --name eduflow-api -p 8000:8000 \
  -e DATABASE_URL=postgresql://eduflow_user:password@host:5432/eduflow_db \
  -e MONGODB_URL=mongodb://host:27017/eduflow \
  -e REDIS_URL=redis://host:6379/0 \
  eduflow-backend:latest
```

### 3. Docker Environment Variables

```bash
# Production environment
export DATABASE_URL=postgresql://eduflow_user:password@postgres:5432/eduflow_db
export MONGODB_URL=mongodb://admin:password@mongodb:27017/eduflow
export REDIS_URL=redis://redis:6379/0
export SECRET_KEY=your-production-secret-key
export DEBUG=false
export HOST=0.0.0.0
export PORT=8000
```

## Kubernetes Deployment

### 1. Kubernetes Configuration

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: eduflow
```

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: eduflow-config
  namespace: eduflow
data:
  config.json: |
    {
      "debug": false,
      "log_level": "INFO",
      "cors_origins": ["*"],
      "jwt": {
        "secret_key": "your-secret-key",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7
      }
    }
```

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: eduflow-secrets
  namespace: eduflow
type: Opaque
data:
  database_url: cG9zdGdyZXNxbDovL2VkdWZsb3VfdXNlcjpwYXNzd29yZA@ postgres:5432/eduflow_db
  mongodb_url: bW9uZ29kYjovL2FkbWluOnBhc3N3b3JkPG1vbm9nZGJAbW9uZ29kYjo1MDAxNy8xNzAxNy9lZHVmbG91ZA==
  redis_url: cmVkaXM6Ly8xL0FHEA==
  secret_key: eW91ci1zZWNyZXQta2V5LWhlcmU=
```

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eduflow-api
  namespace: eduflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eduflow-api
  template:
    metadata:
      labels:
        app: eduflow-api
    spec:
      containers:
        - name: eduflow-api
          image: eduflow-backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: eduflow-secrets
                  key: database_url
            - name: MONGODB_URL
              valueFrom:
                secretKeyRef:
                  name: eduflow-secrets
                  key: mongodb_url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: eduflow-secrets
                  key: redis_url
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: eduflow-secrets
                  key: secret_key
            - name: DEBUG
              value: "false"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: eduflow-api-service
  namespace: eduflow
spec:
  selector:
    app: eduflow-api
  ports:
    - protocol: TCP
      port: 8000
      targetPort: 8000
  type: ClusterIP
```

### 2. Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n eduflow
kubectl get services -n eduflow

# Scale deployment
kubectl scale deployment eduflow-api --replicas=5 -n eduflow

# Rollback deployment
kubectl rollout undo deployment eduflow-api -n eduflow

# View logs
kubectl logs -f deployment/eduflow-api -n eduflow
```

## Production Deployment

### 1. Production Environment Setup

```bash
# Create production directory
sudo mkdir -p /opt/eduflow
sudo chown -R $USER:$USER /opt/eduflow

# Copy application files
cp -r /path/to/eduflow/backend/* /opt/eduflow/

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    postgresql \
    nginx \
    supervisor \
    cron

# Create systemd service
sudo tee /etc/systemd/system/eduflow-api.service <<EOF
[Unit]
Description=EduFlow API Service
After=network.target

[Service]
Type=exec
User=eduflow
WorkingDirectory=/opt/eduflow
Environment=PATH=/opt/eduflow/venv/bin
ExecStart=/opt/eduflow/venv/bin/uvicorn src.api.v1:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable eduflow-api
sudo systemctl start eduflow-api
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/eduflow
upstream eduflow_api {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name api.eduflow.com;

    # SSL termination (optional)
    # listen 443 ssl;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://eduflow_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://eduflow_api;
    }
}
```

### 3. Load Balancer Configuration (Optional)

```nginx
# /etc/nginx/sites-available/eduflow-lb
upstream eduflow_api_backend {
    server 10.0.1.1:8000;
    server 10.0.1.2:8000;
    server 10.0.1.3:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name api.eduflow.com;

    location / {
        proxy_pass http://eduflow_api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Enable keepalive
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
        proxy_buffering off;
    }
}
```

## Monitoring and Observability

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'eduflow-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 2. Grafana Dashboards

- **API Overview**: Main dashboard with request rates, response times, and error rates
- **Database Performance**: Database query performance and connection pool metrics
- **System Health**: CPU, memory, and disk usage metrics
- **User Analytics**: User activity and analytics metrics

### 3. Alerting Configuration

```yaml
# monitoring/alert_rules.yml
groups:
  - name: eduflow-alerts
    rules:
      - alert: HighAPIErrorRate
        expr: rate(api_errors_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value }} errors/second"

      - alert: SlowAPIResponse
        expr: histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API response"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: DatabaseConnectionHigh
        expr: rate(db_connections_active[5m]) > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High database connections"
          description: "Active database connections: {{ $value }}"
```

### 4. Logging Configuration

```python
# src/core/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Main application log
    app_handler = RotatingFileHandler(
        'logs/api.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(logging.Formatter(log_format))
    
    # Database log
    db_handler = RotatingFileHandler(
        'logs/database.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    db_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(db_handler)
    
    # Configure specific loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    return root_logger
```

## Security Considerations

### 1. Security Best Practices

- **Use HTTPS/TLS** for all communications
- **Implement rate limiting** to prevent DDoS attacks
- **Use JWT tokens** with proper expiration
- **Validate all inputs** to prevent injection attacks
- **Use secure password hashing**
- **Implement proper authentication and authorization**
- **Enable audit logging**
- **Regular security updates**

### 2. Database Security

```sql
-- PostgreSQL security configuration
ALTER USER eduflow_user WITH NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT ALL PRIVILEGES ON DATABASE eduflow_db TO eduflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO eduflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO eduflow_user;
```

### 3. Network Security

```bash
# Firewall configuration
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 5432/tcp # PostgreSQL (internal)
sudo ufw allow 27017/tcp # MongoDB (internal)
sudo ufw allow 6379/tcp # Redis (internal)
```

### 4. Application Security

```python
# src/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## Scaling and Performance

### 1. Horizontal Scaling

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: eduflow-api-hpa
  namespace: eduflow
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: eduflow-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 2. Database Scaling

```bash
# PostgreSQL connection pooling
sudo apt-get install pgpool2
sudo cp /etc/pgpool-II/pool_hba.conf /etc/pgpool-II/pool_hba.conf.backup

# Configure connection pooling
cat > /etc/pgpool-II/pool_hba.conf << EOF
# TYPE  DATABASE    USER        ADDRESS         METHOD
local   all         all                         trust
host    all         all         127.0.0.1/32    trust
host    all         all         ::1/128         trust
EOF

sudo systemctl restart pgpool-II
```

### 3. Caching Strategy

```python
# src/core/caching.py
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_with_ttl(ttl_seconds=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## Troubleshooting

### 1. Common Issues

**Database Connection Issues:**
```bash
# Check database connectivity
psql $DATABASE_URL

# Check database logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

**Memory Issues:**
```bash
# Check memory usage
free -h
htop

# Check application memory usage
ps aux | grep uvicorn
```

**Connection Pool Issues:**
```python
# Check database connection pool status
from src.core.database import get_db
db = next(get_db())
print(f"Active connections: {db.in_transaction}")
```

### 2. Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with debug
uvicorn src.api.v1:app --host 0.0.0.0 --port 8000 --log-level debug
```

### 3. Health Checks

```bash
# Application health check
curl http://localhost:8000/health

# Database health check
curl -f http://localhost:8000/api/health/database

# Application metrics
curl http://localhost:8000/metrics
```

## Backup and Recovery

### 1. Database Backup

```bash
# PostgreSQL backup
pg_dump -h localhost -U eduflow_user -d eduflow_db > eduflow_db_backup.sql

# MongoDB backup
mongodump --host localhost --port 27017 --db eduflow --out eduflow_backup

# Redis backup
redis-cli BGSAVE
```

### 2. Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/eduflow"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U eduflow_user -d eduflow_db > $BACKUP_DIR/eduflow_db_$DATE.sql

# MongoDB backup
mongodump --host localhost --port 27017 --db eduflow --out $BACKUP_DIR/eduflow_mongo_$DATE

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Application backup
tar -czf $BACKUP_DIR/eduflow_app_$DATE.tar.gz /opt/eduflow

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 3. Restore Procedure

```bash
# PostgreSQL restore
psql -h localhost -U eduflow_user -d eduflow_db < eduflow_db_backup.sql

# MongoDB restore
mongorestore --host localhost --port 27017 --db eduflow eduflow_backup/eduflow

# Redis restore
redis-cli BGSAVE
cp redis_backup.rdb /var/lib/redis/dump.rdb
redis-cli SHUTDOWN NOSAVE
sudo systemctl restart redis
```

### 4. Automated Backup Schedule

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
0 3 * * * find /var/backups/eduflow -name "*.sql" -mtime +7 -delete
```

## Maintenance

### 1. Regular Maintenance Tasks

```bash
# Database maintenance
sudo -u postgres vacuumdb --all --analyze

# Application maintenance
sudo systemctl restart eduflow-api

# Log rotation
sudo logrotate -f /etc/logrotate.d/eduflow
```

### 2. Updates and Patching

```bash
# System updates
sudo apt-get update
sudo apt-get upgrade

# Application updates
cd /opt/eduflow
git pull
pip install -r requirements.txt
python -m pytest
sudo systemctl restart eduflow-api
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying and managing the Edu-Flow backend API. Follow these best practices to ensure a secure, scalable, and reliable production environment.

For additional support and questions, please contact the development team.