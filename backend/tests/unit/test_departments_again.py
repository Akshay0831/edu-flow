from src.core.test_validation_system import TestValidationSystem, assert_response_format, assert_error, assert_success
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Test the departments endpoint again after fixing database connection
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_departments():
    try:
        import httpx
        
        print("🔍 Testing departments endpoint...")
        
        # Test with HTTPX
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/database/departments")
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Found {data.get('count', 0)} departments")
                print(f"Message: {data.get('message', 'No message')}")
                if data.get('departments'):
                    print("First department:", data['departments'][0])
            else:
                print(f"❌ Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Wait a bit for server to start
    import time
    time.sleep(2)
    asyncio.run(test_departments())