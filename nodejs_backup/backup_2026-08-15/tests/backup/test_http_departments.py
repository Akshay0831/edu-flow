
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Test departments endpoint with HTTP to see what's actually happening
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_http_departments():
    try:
        import httpx
        import time
        
        print("🔍 Testing departments endpoint with HTTP...")
        
        # Wait for server to start
        print("1. Waiting for server to start...")
        time.sleep(3)
        
        # Test with HTTPX
        print("2. Testing with HTTPX...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/api/v1/database/departments", timeout=10.0)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found {data.get('count', 0)} departments")
                    print(f"Message: {data.get('message', 'No message')}")
                else:
                    print(f"❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ HTTP Error: {e}")
                
    except Exception as e:
        print(f"❌ Main Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_http_departments())