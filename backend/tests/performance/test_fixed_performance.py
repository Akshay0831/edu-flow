"""
Fixed Performance Tests

This module provides basic performance tests that properly handle async operations.
It tests database mock performance and basic operations.

Author: Edu-Flow Team
"""

import pytest
import time
import asyncio
from tests.mock_database_manager import MockDatabaseManager


class TestFixedPerformance:
    """Fixed performance tests for Edu-Flow backend."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database instance."""
        return MockDatabaseManager()
    
    @pytest.mark.asyncio
    async def test_database_creation_performance(self, mock_db):
        """Test database creation performance."""
        start_time = time.time()
        
        # Create 100 students
        tasks = []
        for i in range(100):
            student_data = {
                'name': f'Performance Test Student {i}',
                'email': f'perf{i}@university.edu',
                'student_id': f'PERF{i:03d}',
                'department_id': 'DEPT001'
            }
            tasks.append(mock_db.create_student(student_data))
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time
        
        operations_per_second = 100 / duration
        print(f"Database creation performance: {operations_per_second:.2f} ops/sec")
        
        # Should handle at least 50 operations per second
        assert operations_per_second > 50
        
        # Clean up
        cleanup_tasks = []
        for i in range(100):
            student_id = f'PERF{i:03d}'
            cleanup_tasks.append(mock_db.get_student_by_id(student_id))
        
        students = await asyncio.gather(*cleanup_tasks)
        
        for student in students:
            if student:
                cleanup_tasks.append(mock_db.delete('students', student['id']))
        
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, mock_db):
        """Test database query performance."""
        # Create test data first
        for i in range(50):
            student_data = {
                'name': f'Query Test Student {i}',
                'email': f'query{i}@university.edu',
                'student_id': f'QUERY{i:03d}',
                'department_id': 'DEPT001'
            }
            await mock_db.create_student(student_data)
        
        # Test query performance
        start_time = time.time()
        
        # Query all students
        students = await mock_db.get_all('students', skip=0, limit=50)
        
        end_time = time.time()
        duration = end_time - start_time
        
        queries_per_second = 1 / duration
        print(f"Database query performance: {queries_per_second:.2f} queries/sec")
        
        # Should handle at least 100 queries per second
        assert queries_per_second > 100
        
        # Clean up
        cleanup_tasks = []
        for student in students:
            if student:
                cleanup_tasks.append(mock_db.delete('students', student['id']))
        
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_update_performance(self, mock_db):
        """Test database update performance."""
        # Create test data first
        student_id = None
        for i in range(10):
            student_data = {
                'name': f'Update Test Student {i}',
                'email': f'update{i}@university.edu',
                'student_id': f'UPDATE{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await mock_db.create_student(student_data)
            student_id = student['id']
        
        # Test update performance
        start_time = time.time()
        
        # Update student 10 times
        for i in range(10):
            update_data = {
                'name': f'Updated Student {i}',
                'email': f'updated{i}@university.edu'
            }
            await mock_db.update('students', student_id, update_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        updates_per_second = 10 / duration
        print(f"Database update performance: {updates_per_second:.2f} updates/sec")
        
        # Should handle at least 50 updates per second
        assert updates_per_second > 50
        
        # Clean up
        await mock_db.delete('students', student_id)
    
    @pytest.mark.asyncio
    async def test_database_bulk_operations(self, mock_db):
        """Test database bulk operations performance."""
        start_time = time.time()
        
        # Create 200 bulk operations
        for i in range(200):
            if i % 4 == 0:
                # Student creation
                student_data = {
                    'name': f'Bulk Student {i}',
                    'email': f'bulk{i}@university.edu',
                    'student_id': f'BULK{i:03d}',
                    'department_id': 'DEPT001'
                }
                await mock_db.create_student(student_data)
            elif i % 4 == 1:
                # Course creation
                course_data = {
                    'name': f'Bulk Course {i}',
                    'code': f'BC{i:03d}',
                    'description': f'Bulk course {i}',
                    'credits': 3,
                    'department_id': 'DEPT001'
                }
                await mock_db.create_course(course_data)
            elif i % 4 == 2:
                # Teacher creation
                teacher_data = {
                    'name': f'Bulk Teacher {i}',
                    'email': f'bulk_teacher{i}@university.edu',
                    'teacher_id': f'BT{i:03d}',
                    'phone': '+1234567890',
                    'address': '123 Campus St',
                    'gender': 'M',
                    'birth_date': '1980-01-01',
                    'hire_date': '2020-01-01',
                    'department_id': 'DEPT001',
                    'specialization': 'Computer Science'
                }
                await mock_db.create_teacher(teacher_data)
            else:
                # Mark creation
                # First need to get a student and course
                students = await mock_db.get_all('students', skip=0, limit=1)
                courses = await mock_db.get_all('courses', skip=0, limit=1)
                
                if students and courses:
                    mark_data = {
                        'student_id': students[0]['id'],
                        'course_id': courses[0]['id'],
                        'exam_name': 'Bulk Test',
                        'marks_obtained': 75,
                        'total_marks': 100,
                        'percentage': 75.0
                    }
                    await mock_db.create_mark(mark_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        operations_per_second = 200 / duration
        print(f"Database bulk operations performance: {operations_per_second:.2f} ops/sec")
        
        # Should handle at least 20 operations per second for bulk
        assert operations_per_second > 20
        
        # Clean up all created entities
        cleanup_tasks = []
        for entity_type in ['students', 'courses', 'teachers', 'marks']:
            entities = await mock_db.get_all(entity_type)
            for entity in entities:
                if entity:
                    cleanup_tasks.append(mock_db.delete(entity_type, entity['id']))
        
        # Run all cleanup tasks
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_concurrent_operations(self, mock_db):
        """Test database concurrent operations performance."""
        async def create_student_task(mock_db, start_idx, count):
            """Task to create multiple students."""
            for i in range(count):
                student_data = {
                    'name': f'Concurrent Student {start_idx + i}',
                    'email': f'concurrent{start_idx + i}@university.edu',
                    'student_id': f'CONC{start_idx + i:03d}',
                    'department_id': 'DEPT001'
                }
                await mock_db.create_student(student_data)
        
        async def query_students_task(mock_db, count):
            """Task to query students."""
            for i in range(count):
                await mock_db.get_students_by_department('DEPT001')
        
        # Create concurrent tasks
        start_time = time.time()
        
        tasks = []
        for i in range(10):
            # Create 10 concurrent student creation tasks
            task = create_student_task(mock_db, i * 10, 10)
            tasks.append(task)
        
        # Create 5 concurrent query tasks
        for i in range(5):
            task = query_students_task(mock_db, 10)
            tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_operations = 150  # 100 creations + 50 queries
        operations_per_second = total_operations / duration
        print(f"Database concurrent operations performance: {operations_per_second:.2f} ops/sec")
        
        # Should handle at least 30 operations per second for concurrent
        assert operations_per_second > 30
        
        # Clean up
        cleanup_tasks = []
        for i in range(100):
            student_id = f'CONC{i:03d}'
            cleanup_tasks.append(mock_db.get_student_by_id(student_id))
        
        students = await asyncio.gather(*cleanup_tasks)
        
        for student in students:
            if student:
                cleanup_tasks.append(mock_db.delete('students', student['id']))
        
        await asyncio.gather(*cleanup_tasks)