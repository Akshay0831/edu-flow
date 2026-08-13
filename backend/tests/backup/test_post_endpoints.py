
from src.core.exceptions import ValidationError, AuthenticationError, NotFoundError
"""
Test POST endpoints for data creation
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_post_endpoints():
    try:
        import httpx
        import time
        import json
        
        print("🔍 Testing POST endpoints...")
        
        # Wait for server to start
        print("1. Waiting for server to start...")
        time.sleep(3)
        
        # Test POST /api/v1/database/departments
        print("2. Testing POST /api/v1/database/departments...")
        async with httpx.AsyncClient() as client:
            new_department = {
                "department_id": "DEPT_BIO",
                "name": "Biotechnology",
                "code": "BIO",
                "description": "Department of Biotechnology",
                "head_of_department": "Dr. Emily Chen",
                "contact_email": "bio@eduflow.com",
                "contact_phone": "+1-555-0105"
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/database/departments",
                    json=new_department,
                    timeout=10.0
                )
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"   ✅ Success! Created department: {data.get('department_id')}")
                else:
                    print(f"   ❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ HTTP Error: {e}")
                
            # Test POST /api/v1/database/courses
            print("3. Testing POST /api/v1/database/courses...")
            new_course = {
                "course_id": "COURSE002",
                "title": "Advanced Biotechnology",
                "code": "BIO201",
                "department_id": "DEPT_BIO",
                "level": "advanced",
                "credits": 4.0,
                "credit_type": "regular",
                "description": "Advanced concepts in biotechnology",
                "prerequisites": ["BIO101"],
                "corequisites": [],
                "learning_objectives": "Advanced biotechnology skills",
                "assessment_methods": "Research project and exams",
                "duration_weeks": 16,
                "typical_semesters": ["spring"],
                "status": "active"
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/database/courses",
                    json=new_course,
                    timeout=10.0
                )
                print(f"   Status Code: {response.status_code}")
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"   ✅ Success! Created course: {data.get('title')}")
                else:
                    print(f"   ❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ HTTP Error: {e}")
                
    except Exception as e:
        print(f"❌ Main Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_post_endpoints())