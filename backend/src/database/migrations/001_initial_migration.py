"""
Initial migration for Edu-Flow Database

This script sets up the initial database schema and indexes:
- Create collections for all entities
- Set up necessary indexes for performance
- Insert initial data if needed

Author: Edu-Flow Team
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from services.database_service import database_service
from core.logging import get_logger

logger = get_logger(__name__)

async def create_indexes():
    """Create indexes for better performance"""
    try:
        # Users collection indexes
        await database_service.db.users.create_index("email", unique=True)
        await database_service.db.users.create_index("phone")
        await database_service.db.users.create_index("created_at")
        
        # Students collection indexes
        await database_service.db.students.create_index("user_id")
        await database_service.db.students.create_index("student_id", unique=True)
        await database_service.db.students.create_index("department")
        await database_service.db.students.create_index("semester")
        await database_service.db.students.create_index("created_at")
        
        # Teachers collection indexes
        await database_service.db.teachers.create_index("user_id")
        await database_service.db.teachers.create_index("employee_id", unique=True)
        await database_service.db.teachers.create_index("department")
        await database_service.db.teachers.create_index("created_at")
        
        # Courses collection indexes
        await database_service.db.courses.create_index("code", unique=True)
        await database_service.db.courses.create_index("name")
        await database_service.db.courses.create_index("department")
        await database_service.db.courses.create_index("created_at")
        
        # Classes collection indexes
        await database_service.db.classes.create_index("course_id")
        await database_service.db.classes.create_index("teacher_id")
        await database_service.db.classes.create_index("semester")
        await database_service.db.classes.create_index("batch")
        await database_service.db.classes.create_index("created_at")
        
        # Subjects collection indexes
        await database_service.db.subjects.create_index("code", unique=True)
        await database_service.db.subjects.create_index("name")
        await database_service.db.subjects.create_index("department")
        await database_service.db.subjects.create_index("created_at")
        
        # Marks collection indexes
        await database_service.db.marks.create_index("student_id")
        await database_service.db.marks.create_index("subject_id")
        await database_service.db.marks.create_index("class_id")
        await database_service.db.marks.create_index("semester")
        await database_service.db.marks.create_index("created_at")
        
        # Feedback collection indexes
        await database_service.db.feedback.create_index("student_id")
        await database_service.db.feedback.create_index("course_id")
        await database_service.db.feedback.create_index("teacher_id")
        await database_service.db.feedback.create_index("semester")
        await database_service.db.feedback.create_index("created_at")
        
        # Departments collection indexes
        await database_service.db.departments.create_index("code", unique=True)
        await database_service.db.departments.create_index("name")
        await database_service.db.departments.create_index("created_at")
        
        # Analytics collection indexes
        await database_service.db.analytics.create_index("type")
        await database_service.db.analytics.create_index("semester")
        await database_service.db.analytics.create_index("department")
        await database_service.db.analytics.create_index("created_at")
        
        logger.info("All indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        return False

async def insert_initial_data():
    """Insert initial data if needed"""
    try:
        # Check if departments collection is empty
        existing_departments = await database_service.db.departments.count_documents({})
        if existing_departments == 0:
            # Insert initial departments
            departments = [
                {"code": "CSE", "name": "Computer Science Engineering"},
                {"code": "ECE", "name": "Electronics and Communication Engineering"},
                {"code": "ME", "name": "Mechanical Engineering"},
                {"code": "CE", "name": "Civil Engineering"},
                {"code": "EEE", "name": "Electrical and Electronics Engineering"}
            ]
            
            for dept in departments:
                await database_service.db.departments.insert_one(dept)
            
            logger.info("Initial departments inserted")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert initial data: {str(e)}")
        return False

async def run_migration():
    """Run the initial migration"""
    try:
        logger.info("Starting initial database migration...")
        
        # Connect to database
        await database_service.connect()
        
        # Create indexes
        indexes_created = await create_indexes()
        
        # Insert initial data
        initial_data_inserted = await insert_initial_data()
        
        if indexes_created and initial_data_inserted:
            logger.info("Initial migration completed successfully")
            return True
        else:
            logger.error("Initial migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(run_migration())