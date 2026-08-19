# Edu-Flow Frontend

Flutter application in `lib/` with web support.

## Run

```bash
cd frontend
flutter pub get
flutter run -d chrome --web-port 8080
```

The web app uses `frontend/.env`; local development uses `API_BASE_URL=http://localhost:8001`.

## Test and Build

```bash
cd frontend
flutter analyze
flutter test
flutter build web --release
```

## Deployment

Use the repository-level Compose deployment:

```bash
docker compose -f docker-compose.yml up --build -d frontend
```

The frontend is exposed on host port `8080`.