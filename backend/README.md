# Backend

FastAPI service in `src/main.py`.

## Install and Run

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=src python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

Local database: SQLite (`edu_flow.db`).

- API: `http://localhost:8001`
- Docs: `http://localhost:8001/docs`
- Health: `http://localhost:8001/health`

## Test

```bash
cd backend
PYTHONPATH=src python -m pytest
```

Focused database tests:

```bash
PYTHONPATH=src python -m pytest tests/test_database_manager.py -q
```

## Docker

Use the repository-level Compose deployment:

```bash
docker compose -f docker-compose.yml up --build -d backend
```

Docker maps the backend to host port `8000`.