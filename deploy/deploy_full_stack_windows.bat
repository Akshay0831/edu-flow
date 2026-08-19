@echo off
setlocal enabledelayedexpansion

REM Edu-Flow Full Stack Deployment Script (Windows)
REM This script deploys both backend and frontend services

echo 🚀 Starting Edu-Flow Full Stack Deployment...

REM Configuration
set BACKEND_PORT=8001
set FRONTEND_PORT=8080
set BACKEND_NAME=edu-flow-backend
set FRONTEND_NAME=edu-flow-frontend
set DB_HOST=%DB_HOST:-localhost%
set DB_PORT=%DB_PORT:-5432%
set DB_NAME=%DB_NAME:-edu_flow%
set DB_USER=%DB_USER:-postgres%
set DB_PASSWORD=%DB_PASSWORD:-password%

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if required ports are available
netstat -ano | findstr ":%BACKEND_PORT%" >nul
if %ERRORLEVEL% EQU 0 (
    echo [ERROR] Port %BACKEND_PORT% is already in use. Please free up this port or configure a different port.
    pause
    exit /b 1
)

netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %ERRORLEVEL% EQU 0 (
    echo [ERROR] Port %FRONTEND_PORT% is already in use. Please free up this port or configure a different port.
    pause
    exit /b 1
)

echo [STEP] Checking port availability...

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "frontend\build" mkdir frontend\build

REM Build and deploy backend
echo [STEP] Deploying backend...
cd backend

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating backend .env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql+asyncpg://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%
        echo REDIS_URL=redis://%DB_HOST%:%DB_PORT%:-6379%/0
        echo.
        echo # Security Configuration
        echo SECRET_KEY=%SECRET_KEY:-your-secret-key-here%
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo REFRESH_TOKEN_EXPIRE_DAYS=7
        echo.
        echo # API Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=%BACKEND_PORT%
        echo DEBUG=false
        echo.
        echo # CORS Configuration
        echo ALLOWED_ORIGINS=["http://localhost:%FRONTEND_PORT%", "http://localhost:3000", "http://localhost:8080"]
        echo.
        echo # Email Configuration ^(if needed^)
        echo SMTP_HOST=%SMTP_HOST:-smtp.gmail.com%
        echo SMTP_PORT=%SMTP_PORT:-587%
        echo SMTP_USER=%SMTP_USER:-%
        echo SMTP_PASSWORD=%SMTP_PASSWORD:-%
        echo FROM_EMAIL=%FROM_EMAIL:-noreply@edu-flow.com%
        echo.
        echo # Logging Configuration
        echo LOG_LEVEL=INFO
        echo LOG_FILE=logs/edu_flow.log
    ) > .env
)

REM Build backend image
echo [INFO] Building backend Docker image...
docker build -t %BACKEND_NAME%:latest .

REM Stop existing backend container
docker ps -q -f name=%BACKEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Stopping existing backend container...
    docker stop %BACKEND_NAME%
)

REM Remove existing backend container
docker ps -aq -f name=%BACKEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Removing existing backend container...
    docker rm %BACKEND_NAME%
)

REM Deploy backend
echo [INFO] Starting backend service...
docker run -d ^
    --name %BACKEND_NAME% ^
    --restart unless-stopped ^
    -p %BACKEND_PORT%:8001 ^
    -v "%cd%\logs:/app/logs" ^
    -v "%cd%\data:/app/data" ^
    -v "%cd%\uploads:/app/uploads" ^
    -e DATABASE_URL="postgresql+asyncpg://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%" ^
    -e REDIS_URL="redis://%DB_HOST%:%DB_PORT%:-6379%/0" ^
    -e SECRET_KEY=%SECRET_KEY:-your-secret-key-here% ^
    -e ACCESS_TOKEN_EXPIRE_MINUTES=30 ^
    -e REFRESH_TOKEN_EXPIRE_DAYS=7 ^
    -e API_HOST=0.0.0.0 ^
    -e API_PORT=8001 ^
    -e DEBUG=false ^
    -e LOG_LEVEL=INFO ^
    -e LOG_FILE=/app/logs/edu_flow.log ^
    %BACKEND_NAME%:latest

cd ..

REM Build and deploy frontend
echo [STEP] Deploying frontend...
cd frontend

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating frontend .env file...
    (
        echo # API Configuration
        echo API_BASE_URL=http://%DB_HOST%:%BACKEND_PORT%
        echo API_TIMEOUT=30
        echo.
        echo # App Configuration
        echo APP_NAME=Edu-Flow
        echo APP_VERSION=1.0.0
        echo DEBUG=false
        echo.
        echo # Firebase Configuration ^(if needed^)
        echo FIREBASE_API_KEY=%FIREBASE_API_KEY:-%
        echo FIREBASE_AUTH_DOMAIN=%FIREBASE_AUTH_DOMAIN:-%
        echo FIREBASE_PROJECT_ID=%FIREBASE_PROJECT_ID:-%
        echo FIREBASE_STORAGE_BUCKET=%FIREBASE_STORAGE_BUCKET:-%
        echo FIREBASE_MESSAGING_SENDER_ID=%FIREBASE_MESSAGING_SENDER_ID:-%
        echo FIREBASE_APP_ID=%FIREBASE_APP_ID:-%
        echo.
        echo # CDN Configuration ^(if needed^)
        echo CDN_URL=%CDN_URL:-%
        echo CDN_ENABLED=%CDN_ENABLED:-false%
        echo.
        echo # Analytics Configuration ^(if needed^)
        echo ANALYTICS_ENABLED=%ANALYTICS_ENABLED:-false%
        echo ANALYTICS_ID=%ANALYTICS_ID:-%
    ) > .env
)

REM Build Flutter web application
echo [INFO] Building Flutter web application...
flutter clean
flutter pub get
flutter build web --release --web-renderer canvaskit

REM Build frontend image
echo [INFO] Building frontend Docker image...
docker build -t %FRONTEND_NAME%:latest .

REM Stop existing frontend container
docker ps -q -f name=%FRONTEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Stopping existing frontend container...
    docker stop %FRONTEND_NAME%
)

REM Remove existing frontend container
docker ps -aq -f name=%FRONTEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Removing existing frontend container...
    docker rm %FRONTEND_NAME%
)

REM Deploy frontend
echo [INFO] Starting frontend service...
docker run -d ^
    --name %FRONTEND_NAME% ^
    --restart unless-stopped ^
    -p %FRONTEND_PORT%:80 ^
    -v "%cd%\build\web:/usr/share/nginx/html" ^
    -v "%cd%\logs:/var/log/nginx" ^
    -e API_BASE_URL=http://%DB_HOST%:%BACKEND_PORT% ^
    -e APP_NAME=Edu-Flow ^
    -e APP_VERSION=1.0.0 ^
    -e DEBUG=false ^
    nginx:alpine

cd ..

REM Wait for services to start
echo [STEP] Waiting for services to start...
timeout /t 15 /nobreak >nul

REM Check if services are running
echo [STEP] Checking service status...

REM Check backend
docker ps -q -f name=%BACKEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend is running on port %BACKEND_PORT%
    
    REM Check backend health
    curl -f http://localhost:%BACKEND_PORT%/health >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Backend health check passed
    ) else (
        echo ⚠️ Backend health check failed
    )
    
    REM Check backend API docs
    curl -f http://localhost:%BACKEND_PORT%/docs >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Backend API documentation is accessible
    ) else (
        echo ⚠️ Backend API documentation not accessible
    )
) else (
    echo ❌ Backend failed to start
    pause
    exit /b 1
)

REM Check frontend
docker ps -q -f name=%FRONTEND_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Frontend is running on port %FRONTEND_PORT%
    
    REM Check frontend accessibility
    curl -f http://localhost:%FRONTEND_PORT% >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Frontend is accessible
    ) else (
        echo ⚠️ Frontend not accessible yet
    )
) else (
    echo ❌ Frontend failed to start
    pause
    exit /b 1
)

REM Run smoke tests
echo [STEP] Running smoke tests...
echo [INFO] Testing backend API connectivity...
curl -f http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend API connectivity test passed
) else (
    echo ⚠️ Backend API connectivity test failed
)

echo [INFO] Testing frontend connectivity...
curl -f http://localhost:%FRONTEND_PORT% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Frontend connectivity test passed
) else (
    echo ⚠️ Frontend connectivity test failed
)

REM Create admin user
echo [STEP] Creating admin user...
set ADMIN_CREATED=false
set BACKEND_URL=http://localhost:%BACKEND_PORT%

REM Try to create admin user
curl -X POST "%BACKEND_URL%/api/v1/auth/register" ^
    -H "Content-Type: application/json" ^
    -d "{\"email\": \"admin@example.com\", \"password\": \"Admin123!\", \"name\": \"Administrator\", \"role\": \"admin\"}" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set ADMIN_CREATED=true
)

if "%ADMIN_CREATED%"=="true" (
    echo ✅ Admin user created ^(admin@example.com / Admin123!^)
) else (
    echo ⚠️ Admin user creation failed ^(might already exist^)
)

REM Print deployment summary
echo.
echo 🎉 Deployment completed successfully!
echo ============================================
echo 🌐 Frontend URL: http://localhost:%FRONTEND_PORT%
echo 🔗 Backend URL: http://localhost:%BACKEND_PORT%
echo 📚 Backend API Docs: http://localhost:%BACKEND_PORT%/docs
echo 🏥 Health Check: http://localhost:%BACKEND_PORT%/health
echo.
echo 🔧 Default Admin Account:
echo    Email: admin@example.com
echo    Password: Admin123!
echo.
echo 📋 Management Commands:
echo    - View backend logs: docker logs -f %BACKEND_NAME%
echo    - View frontend logs: docker logs -f %FRONTEND_NAME%
echo    - Stop backend: docker stop %BACKEND_NAME%
echo    - Stop frontend: docker stop %FRONTEND_NAME%
echo    - Restart backend: docker restart %BACKEND_NAME%
echo    - Restart frontend: docker restart %FRONTEND_NAME%
echo.
echo 🔗 Database Configuration:
echo    Host: %DB_HOST%:%DB_PORT%
echo    Database: %DB_NAME%
echo    User: %DB_USER%
echo.
echo 📊 Monitoring:
echo    - Docker status: docker ps -a
echo    - System resources: docker stats
echo    - Container logs: docker logs [container_name]
echo.
echo 🚀 Next Steps:
echo    1. Open http://localhost:%FRONTEND_PORT% to access the application
echo    2. Use the admin credentials to log in
echo    3. Explore the API documentation at http://localhost:%BACKEND_PORT%/docs
echo    4. Monitor the logs for any issues
echo.
pause