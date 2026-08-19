# Frontend

Flutter application in `lib/` with web support.

## Install and Run

```bash
cd frontend
flutter pub get
flutter run -d chrome --web-port 8080
```

Local API configuration is in `frontend/.env`:

```env
API_BASE_URL=http://localhost:8001/api/v1
```

Frontend: `http://localhost:8080`.

## Analyze, Test, Build

```bash
cd frontend
flutter analyze
flutter test
flutter build web --release
```

## Docker

Use the repository-level Compose deployment:

```bash
docker compose -f docker-compose.yml up --build -d frontend
```

Docker maps the frontend to host port `8080`.