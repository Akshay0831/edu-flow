@echo off
REM Development Environment Setup Script
REM For Edu-Flow Migration Project

echo Setting up development environment for Edu-Flow...

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r backend\src\requirements.txt

REM Install Rust toolchain (for future phases)
echo Installing Rust toolchain...
curl -sSf https://win.rustup.rs/ | sh -s -- -y
call %USERPROFILE%\.cargo\env

REM Install Flutter SDK
echo Installing Flutter SDK...
git clone https://github.com/flutter/flutter.git -b stable %USERPROFILE%\flutter
set PATH=%PATH%;%USERPROFILE%\flutter\bin
flutter doctor

REM Install Node.js dependencies
echo Installing Node.js dependencies...
cd frontend
npm install
cd ..

REM Set up MongoDB and Redis services
echo Setting up database services...
REM Add commands to start MongoDB and Redis
REM These can be: docker-compose up -d or service commands

echo Environment setup completed!
echo.
echo Next steps:
echo 1. Configure environment variables in backend\src\.env
echo 2. Set up database connections
echo 3. Run backend tests: python -m pytest backend\tests\
echo 4. Start development server: cd backend && uvicorn src.main:app --reload

pause