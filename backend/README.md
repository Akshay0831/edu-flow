# Edu-Flow Backend

FastAPI service in `src/main.py`.

## Run

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=src python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

The active health endpoint is `/health`; API docs are at `/docs`. Local development uses the SQLite configuration in the application startup path.

## Test

```bash
cd backend
PYTHONPATH=src python -m pytest
```

## Deployment

Use the repository-level Compose deployment:

```bash
docker compose -f docker-compose.yml up --build -d backend
```

The Compose backend is exposed on host port `8000`. Local development uses `8001`.