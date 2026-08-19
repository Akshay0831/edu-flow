# Edu-Flow

FastAPI backend, Flutter frontend, and optional Rust services for an education management system.

## Requirements

- Python 3.13 or compatible Python 3.8+
- Flutter SDK
- Docker Desktop for container deployment

## Local Start

Backend:

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=src python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

Frontend:

```bash
cd frontend
flutter pub get
flutter run -d chrome --web-port 8080
```

- Frontend: `http://localhost:8080`
- API: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`
- Health: `http://localhost:8001/health`

## Docker Start

```bash
docker compose up --build -d
```

Docker maps the backend to host port `8000` and the frontend to `8080`.

Stop the stack with `docker compose down`.

The scripts in `deploy/` are convenience wrappers around Compose.

## Tests

```bash
cd backend
PYTHONPATH=src python -m pytest
```

Frontend tests run with `flutter test` from `frontend`.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for component commands.

## License

MIT. See [LICENSE](LICENSE).