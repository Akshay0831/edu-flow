FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY models/ ./models/
COPY routes/ ./routes/
COPY config/ ./config/
COPY db/ ./db/

# Create logs directory
RUN mkdir -p logs/ai-services/api logs/ai-services/audit logs/ai-services/errors logs/ai-services/performance \
    logs/auth-gateway/api logs/auth-gateway/audit logs/auth-gateway/errors logs/auth-gateway/performance \
    logs/backend/api logs/backend/audit logs/backend/errors logs/backend/performance \
    logs/database/api logs/database/audit logs/database/errors logs/database/performance \
    logs/frontend/api logs/frontend/audit logs/frontend/errors logs/frontend/performance \
    logs/performance logs/security

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]