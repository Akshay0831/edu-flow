
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Test simple endpoint to see if FastAPI is working
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_simple_endpoint():
    try:
        import httpx
        import time
        
        print("🔍 Testing simple endpoint...")
        
        # Wait for server to start
        print("1. Waiting for server to start...")
        time.sleep(3)
        
        # Test health endpoint
        print("2. Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/health", timeout=10.0)
                print(f"Health Status Code: {response.status_code}")
                print(f"Health Response: {response.text}")
                
            except Exception as e:
                print(f"❌ Health Error: {e}")
                
        # Test info endpoint
        print("3. Testing info endpoint...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/api/v1/info", timeout=10.0)
                print(f"Info Status Code: {response.status_code}")
                print(f"Info Response: {response.text}")
                
            except Exception as e:
                print(f"❌ Info Error: {e}")
                
    except Exception as e:
        print(f"❌ Main Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_endpoint())