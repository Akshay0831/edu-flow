# Edu-Flow

Edu-Flow is an education management application with a FastAPI backend, Flutter frontend, and optional Rust services.

## Run Locally

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

Open `http://localhost:8080`. The API is at `http://localhost:8001`; documentation is at `/docs`.

## Docker Deployment

```bash
docker compose up --build -d
```

Compose exposes the backend on port `8000` and the frontend on port `8080`. Local development uses backend port `8001`.

Windows:

```bat
deploy\deploy_full_stack_windows.bat
```

Linux/macOS:

```bash
./deploy/deploy_full_stack.sh
```

## Tests

```bash
cd backend
PYTHONPATH=src python -m pytest
```

Frontend tests run with `flutter test` from `frontend`.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for component details. This repository does not currently include a `LICENSE` file.