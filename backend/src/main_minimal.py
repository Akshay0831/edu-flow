"""
FastAPI Application for Edu-Flow Backend - Minimal Version

This module initializes a minimal FastAPI application to test basic functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Edu-Flow API",
    description="Education Management System API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Edu-Flow API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/auth_register")
async def auth_register():
    return {"message": "Registration endpoint - not implemented yet"}

@app.get("/api/v1/auth_login")
async def auth_login():
    return {"message": "Login endpoint - not implemented yet"}

@app.get("/api/v1/users")
async def users_list():
    return {"message": "Users list endpoint - not implemented yet"}