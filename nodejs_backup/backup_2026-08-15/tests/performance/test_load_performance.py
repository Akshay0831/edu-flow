"""
Load Performance Tests

This module tests system performance under various load conditions.
It tests response times, throughput, and resource usage.

Author: Edu-Flow Team
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.services.service_container_fixed import ServiceContainer
from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.class_service import ClassService
from tests.mock_database_manager import MockDatabaseManager


class TestLoadPerformance:
    """Load performance tests for Edu-Flow backend."""
    
    @pytest.fixture(scope="class")
    async def system_services(self):
        """Create and initialize all services."""
        container = ServiceContainer()
        await container.initialize()
        yield container
        await container.dispose()
    
    @pytest.mark.asyncio
    async def test_bulk_student_creation_performance(self, system_services):
        """Test performance of bulk student creation."""
        student_service = system_services.get('student_service')
        
        # Test with different batch sizes
        batch_sizes = [10, 50, 100, 500]
        performance_results = {}
        
        for batch_size in batch_sizes:
            start_time = time.time()
            
            # Create students in batch
            student_ids = []
            for i in range(batch_size):
                student_data = {
                    'name': f'Load Test Student {i}',
                    'email': f'load.test{i}@university.edu',
                    'student_id': f'LOAD{i:03d}',
                    'department_id': 'DEPT001'
                }
                student = await student_service.create(student_data)
                student_ids.append(student['id'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            performance_results[batch_size] = {
                'duration': duration,
                'students_per_second': batch_size / duration,
                'average_time_per_student': duration / batch_size
            }
            
            # Clean up
            cleanup_tasks = []
            for student_id in student_ids:
                cleanup_tasks.append(student_service.delete(student_id))
            await asyncio.gather(*cleanup_tasks)
        
        # Performance validation
        for batch_size, results in performance_results.items():
            print(f"Batch size {batch_size}: {results['students_per_second']:.2f} students/sec")
            assert results['students_per_second'] > 10  # Should create at least 10 students per second
    
    @pytest.mark.asyncio
    async def test_bulk_course_creation_performance(self, system_services):
        """Test performance of bulk course creation."""
        course_service = system_services.get('course_service')
        
        batch_sizes = [10, 50, 100]
        performance_results = {}
        
        for batch_size in batch_sizes:
            start_time = time.time()
            
            course_ids = []
            for i in range(batch_size):
                course_data = {
                    'name': f'Load Test Course {i}',
                    'code': f'LOAD{i:03d}',
                    'credits': 3,
                    'department_id': 'DEPT001'
                }
                course = await course_service.create(course_data)
                course_ids.append(course['id'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            performance_results[batch_size] = {
                'duration': duration,
                'courses_per_second': batch_size / duration,
                'average_time_per_course': duration / batch_size
            }
            
            # Clean up
            cleanup_tasks = []
            for course_id in course_ids:
                cleanup_tasks.append(course_service.delete(course_id))
            await asyncio.gather(*cleanup_tasks)
        
        # Performance validation
        for batch_size, results in performance_results.items():
            print(f"Course batch size {batch_size}: {results['courses_per_second']:.2f} courses/sec")
            assert results['courses_per_second'] > 15  # Should create at least 15 courses per second
    
    @pytest.mark.asyncio
    async def test_concurrent_student_enrollment(self, system_services):
        """Test performance of concurrent student enrollment in classes."""
        student_service = system_services.get('student_service')
        class_service = system_services.get('class_service')
        
        # Create class
        class_data = {
            'name': 'Load Test Class',
            'subject_id': 'SUB001',
            'teacher_id': 'TCH001',
            'capacity': 100,
            'academic_year': '2023-2024'
        }
        class_obj = await class_service.create(class_data)
        class_id = class_obj['id']
        
        # Create students
        student_ids = []
        for i in range(50):
            student_data = {
                'name': f'Enrollment Test Student {i}',
                'email': f'enrollment{i}@university.edu',
                'student_id': f'ENR{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # Test concurrent enrollment
        start_time = time.time()
        
        enrollment_tasks = []
        for student_id in student_ids:
            task = class_service.enroll_student(class_id, student_id)
            enrollment_tasks.append(task)
        
        await asyncio.gather(*enrollment_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        enrollment_rate = len(student_ids) / duration
        print(f"Concurrent enrollment rate: {enrollment_rate:.2f} students/sec")
        assert enrollment_rate > 20  # Should enroll at least 20 students per second
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        cleanup_tasks.append(class_service.delete(class_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, system_services):
        """Test performance of database queries."""
        student_service = system_services.get('student_service')
        
        # Create test data
        student_ids = []
        for i in range(1000):
            student_data = {
                'name': f'Query Test Student {i}',
                'email': f'query{i}@university.edu',
                'student_id': f'QUERY{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # Test query performance
        query_times = []
        num_queries = 100
        
        for i in range(num_queries):
            start_time = time.time()
            
            # Query students by department
            students = await student_service.get_students_by_department('DEPT001')
            
            end_time = time.time()
            query_times.append(end_time - start_time)
        
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        print(f"Average query time: {avg_query_time:.4f} seconds")
        print(f"Maximum query time: {max_query_time:.4f} seconds")
        print(f"Queries per second: {1 / avg_query_time:.2f}")
        
        # Performance assertions
        assert avg_query_time < 0.1  # Average query should be under 100ms
        assert max_query_time < 0.5  # Maximum query should be under 500ms
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_statistics_calculation_performance(self, system_services):
        """Test performance of statistics calculations."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        mark_service = system_services.get('mark_service')
        
        # Create test data
        student_ids = []
        course_ids = []
        mark_ids = []
        
        # Create courses
        for i in range(50):
            course_data = {
                'name': f'Stats Course {i}',
                'code': f'STATS{i:03d}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            course = await course_service.create(course_data)
            course_ids.append(course['id'])
        
        # Create students and marks
        for i in range(100):
            student_data = {
                'name': f'Stats Student {i}',
                'email': f'stats{i}@university.edu',
                'student_id': f'STATS{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
            
            # Create marks for student
            for j in range(5):
                mark_data = {
                    'student_id': student['id'],
                    'course_id': course_ids[j % len(course_ids)],
                    'marks_obtained': 60 + (i % 40),
                    'total_marks': 100,
                    'percentage': 60 + (i % 40)
                }
                mark = await mark_service.create(mark_data)
                mark_ids.append(mark['id'])
        
        # Test statistics performance
        start_time = time.time()
        
        # Calculate various statistics
        tasks = []
        for student_id in student_ids[:20]:  # Test on subset
            tasks.append(student_service.get_student_statistics(student_id))
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        stats_per_second = 20 / duration
        print(f"Statistics calculation rate: {stats_per_second:.2f} stats/sec")
        assert stats_per_second > 5  # Should calculate at least 5 statistics per second
        
        # Clean up
        cleanup_tasks = []
        for mark_id in mark_ids:
            cleanup_tasks.append(mark_service.delete(mark_id))
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        for course_id in course_ids:
            cleanup_tasks.append(course_service.delete(course_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_api_response_time_performance(self, system_services):
        """Test API response times under load."""
        student_service = system_services.get('student_service')
        
        # Create test data
        student_ids = []
        for i in range(100):
            student_data = {
                'name': f'API Test Student {i}',
                'email': f'api{i}@university.edu',
                'student_id': f'API{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # Test API response times
        api_endpoints = [
            ('get_student', lambda: student_service.get(student_ids[0])),
            ('get_students_by_department', lambda: student_service.get_students_by_department('DEPT001')),
            ('list_students', lambda: student_service.list(limit=10)),
            ('count_students', lambda: student_service.count())
        ]
        
        response_times = {endpoint: [] for endpoint, _ in api_endpoints}
        
        for endpoint, operation in api_endpoints:
            print(f"Testing {endpoint}...")
            
            # Run operation multiple times
            for _ in range(50):
                start_time = time.time()
                await operation()
                end_time = time.time()
                response_times[endpoint].append(end_time - start_time)
        
        # Analyze response times
        for endpoint, times in response_times.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            
            print(f"{endpoint}: avg={avg_time:.4f}s, max={max_time:.4f}s, p95={p95_time:.4f}s")
            
            # Performance assertions
            assert avg_time < 0.05  # Average response time under 50ms
            assert p95_time < 0.2   # 95th percentile under 200ms
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, system_services):
        """Test memory usage during operations."""
        import psutil
        import os
        
        student_service = system_services.get('student_service')
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large amounts of data
        student_ids = []
        for i in range(1000):
            student_data = {
                'name': f'Memory Test Student {i}',
                'email': f'memory{i}@university.edu',
                'student_id': f'MEM{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # Perform operations to test memory usage
        for i in range(100):
            students = await student_service.get_students_by_department('DEPT001')
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        await asyncio.gather(*cleanup_tasks)
        
        # Wait for garbage collection
        await asyncio.sleep(1)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_growth = peak_memory - initial_memory
        memory_cleanup_efficiency = (peak_memory - final_memory) / memory_growth
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Peak memory: {peak_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        print(f"Cleanup efficiency: {memory_cleanup_efficiency:.2%}")
        
        # Memory usage assertions
        assert memory_growth < 100  # Memory growth should be less than 100MB
        assert memory_cleanup_efficiency > 0.8  # Should clean up at least 80% of memory
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, system_services):
        """Test database connection pool performance."""
        student_service = system_services.get('student_service')
        
        # Simulate high concurrent database operations
        start_time = time.time()
        
        # Create many concurrent operations
        concurrent_tasks = []
        for i in range(100):
            task = student_service.create({
                'name': f'Pool Test Student {i}',
                'email': f'pool{i}@university.edu',
                'student_id': f'POOL{i:03d}',
                'department_id': 'DEPT001'
            })
            concurrent_tasks.append(task)
        
        await asyncio.gather(*concurrent_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        operations_per_second = 100 / duration
        print(f"Database pool performance: {operations_per_second:.2f} ops/sec")
        assert operations_per_second > 10  # Should handle at least 10 operations per second
        
        # Clean up all created students
        cleanup_tasks = []
        for i in range(100):
            task = student_service.get(f'POOL{i:03d}')
            cleanup_tasks.append(task)
        
        students = await asyncio.gather(*cleanup_tasks)
        
        for student in students:
            if student:
                cleanup_tasks.append(student_service.delete(student['id']))
        
        await asyncio.gather(*cleanup_tasks)