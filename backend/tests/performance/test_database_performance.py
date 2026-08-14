"""
Database Performance Tests

This module tests database-specific performance aspects including
query optimization, indexing, and database connection handling.

Author: Edu-Flow Team
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, date
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.services.service_container_fixed import ServiceContainer
from src.infrastructure.services.student_service import StudentService
from src.infrastructure.services.teacher_service import TeacherService
from src.infrastructure.services.course_service import CourseService
from src.infrastructure.services.class_service import ClassService
from src.infrastructure.services.mark_service import MarkService
from tests.mock_database_manager import MockDatabaseManager


class TestDatabasePerformance:
    """Database performance tests for Edu-Flow backend."""
    
@pytest.fixture(scope="class")
    def system_services(self):
        """Create and initialize all services."""
        container = ServiceContainer()
        # Initialize synchronously for simplicity
        container.initialize_sync()
        yield container
        container.dispose_sync()

    @pytest.mark.asyncio
    async def test_database_index_performance(self, system_services):
        
        # Create test data
        student_ids = []
        course_ids = []
        
        # Create students
        for i in range(1000):
            student_data = {
                'name': f'Index Test Student {i}',
                'email': f'index{i}@university.edu',
                'student_id': f'IDX{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
        
        # Create courses
        for i in range(100):
            course_data = {
                'name': f'Index Test Course {i}',
                'code': f'IDX{i:03d}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            course = await course_service.create(course_data)
            course_ids.append(course['id'])
        
        # Test indexed vs non-indexed queries
        indexed_times = []
        non_indexed_times = []
        
        # Test indexed query (student by ID - should be fast)
        for i in range(100):
            start_time = time.time()
            await student_service.get(student_ids[i % len(student_ids)])
            end_time = time.time()
            indexed_times.append(end_time - start_time)
        
        # Test non-indexed query (would need to be simulated)
        for i in range(100):
            start_time = time.time()
            await student_service.get_students_by_department('DEPT001')
            end_time = time.time()
            non_indexed_times.append(end_time - start_time)
        
        indexed_avg = statistics.mean(indexed_times)
        non_indexed_avg = statistics.mean(non_indexed_times)
        
        print(f"Indexed query avg time: {indexed_avg:.6f}s")
        print(f"Non-indexed query avg time: {non_indexed_avg:.6f}s")
        print(f"Index improvement ratio: {non_indexed_avg / indexed_avg:.2f}x")
        
        # Index performance assertion
        assert indexed_avg < non_indexed_avg  # Indexed queries should be faster
        assert indexed_avg < 0.01  # Indexed queries under 10ms
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        for course_id in course_ids:
            cleanup_tasks.append(course_service.delete(course_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, system_services):
        """Test database connection pool performance."""
        student_service = system_services.get('student_service')
        
        # Simulate many concurrent database operations
        start_time = time.time()
        
        # Create many concurrent operations to test connection pooling
        concurrent_operations = []
        for i in range(200):
            operation = student_service.create({
                'name': f'Pool Test Student {i}',
                'email': f'pool{i}@university.edu',
                'student_id': f'POOL{i:03d}',
                'department_id': 'DEPT001'
            })
            concurrent_operations.append(operation)
        
        await asyncio.gather(*concurrent_operations)
        
        end_time = time.time()
        duration = end_time - start_time
        
        operations_per_second = 200 / duration
        print(f"Connection pool performance: {operations_per_second:.2f} ops/sec")
        assert operations_per_second > 15  # Should handle at least 15 operations per second
        
        # Clean up
        cleanup_tasks = []
        for i in range(200):
            task = student_service.get(f'POOL{i:03d}')
            cleanup_tasks.append(task)
        
        students = await asyncio.gather(*cleanup_tasks)
        
        for student in students:
            if student:
                cleanup_tasks.append(student_service.delete(student['id']))
        
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_transaction_performance(self, system_services):
        """Test database transaction performance."""
        student_service = system_services.get('student_service')
        mark_service = system_services.get('mark_service')
        
        # Create test data
        student_id = None
        mark_ids = []
        
        # Create student
        student_data = {
            'name': 'Transaction Test Student',
            'email': 'transaction@university.edu',
            'student_id': 'TRANSACTION001',
            'department_id': 'DEPT001'
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # Test transaction performance
        transaction_times = []
        
        for i in range(100):
            start_time = time.time()
            
            # Create multiple related marks in a transaction (simulated)
            for j in range(5):
                mark_data = {
                    'student_id': student_id,
                    'course_id': f'COURSE{i:03d}',
                    'marks_obtained': 60 + (i % 40),
                    'total_marks': 100,
                    'percentage': 60 + (i % 40)
                }
                mark = await mark_service.create(mark_data)
                mark_ids.append(mark['id'])
            
            end_time = time.time()
            transaction_times.append(end_time - start_time)
        
        avg_transaction_time = statistics.mean(transaction_times)
        transactions_per_second = 100 / sum(transaction_times)
        
        print(f"Average transaction time: {avg_transaction_time:.6f}s")
        print(f"Transactions per second: {transactions_per_second:.2f}")
        assert transactions_per_second > 10  # Should handle at least 10 transactions per second
        
        # Clean up
        cleanup_tasks = []
        for mark_id in mark_ids:
            cleanup_tasks.append(mark_service.delete(mark_id))
        cleanup_tasks.append(student_service.delete(student_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_query_optimization(self, system_services):
        """Test query optimization techniques."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        mark_service = system_services.get('mark_service')
        
        # Create complex test data with relationships
        student_ids = []
        course_ids = []
        mark_ids = []
        
        # Create courses
        for i in range(50):
            course_data = {
                'name': f'Optimized Course {i}',
                'code': f'OPT{i:03d}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            course = await course_service.create(course_data)
            course_ids.append(course['id'])
        
        # Create students with marks
        for i in range(200):
            student_data = {
                'name': f'Optimized Student {i}',
                'email': f'optimized{i}@university.edu',
                'student_id': f'OPT{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
            
            # Create marks for student
            for j in range(3):
                mark_data = {
                    'student_id': student['id'],
                    'course_id': course_ids[j % len(course_ids)],
                    'marks_obtained': 70 + (i % 30),
                    'total_marks': 100,
                    'percentage': 70 + (i % 30)
                }
                mark = await mark_service.create(mark_data)
                mark_ids.append(mark['id'])
        
        # Test optimized queries
        optimized_times = []
        
        # Test join-like queries (students with their marks)
        for i in range(50):
            start_time = time.time()
            # This simulates a join operation between students and their marks
            students = await student_service.get_students_by_department('DEPT001')
            marks = await mark_service.get_student_marks(students[i % len(students)]['id'])
            end_time = time.time()
            optimized_times.append(end_time - start_time)
        
        avg_optimized_time = statistics.mean(optimized_times)
        
        print(f"Optimized query avg time: {avg_optimized_time:.6f}s")
        print(f"Optimized queries per second: {1 / avg_optimized_time:.2f}")
        assert avg_optimized_time < 0.05  # Optimized queries under 50ms
        
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
    async def test_database_batch_operations(self, system_services):
        """Test database batch operation performance."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # Test batch creation performance
        batch_sizes = [10, 50, 100, 500]
        batch_results = {}
        
        for batch_size in batch_sizes:
            start_time = time.time()
            
            # Create batch of students
            student_ids = []
            for i in range(batch_size):
                student_data = {
                    'name': f'Batch Student {i}',
                    'email': f'batch{i}@university.edu',
                    'student_id': f'BATCH{i:03d}',
                    'department_id': 'DEPT001'
                }
                student = await student_service.create(student_data)
                student_ids.append(student['id'])
            
            end_time = time.time()
            duration = end_time - start_time
            
            batch_results[batch_size] = {
                'duration': duration,
                'operations_per_second': batch_size / duration,
                'average_time_per_operation': duration / batch_size
            }
            
            # Clean up batch
            cleanup_tasks = []
            for student_id in student_ids:
                cleanup_tasks.append(student_service.delete(student_id))
            await asyncio.gather(*cleanup_tasks)
        
        # Analyze batch performance
        for batch_size, results in batch_results.items():
            print(f"Batch size {batch_size}: {results['operations_per_second']:.2f} ops/sec")
            assert results['operations_per_second'] > 20  # Should handle at least 20 operations per second
    
    @pytest.mark.asyncio
    async def test_database_caching_performance(self, system_services):
        """Test database query caching performance."""
        student_service = system_services.get('student_service')
        
        # Create test data
        student_id = None
        
        # Create student
        student_data = {
            'name': 'Cache Test Student',
            'email': 'cache@university.edu',
            'student_id': 'CACHE001',
            'department_id': 'DEPT001'
        }
        student = await student_service.create(student_data)
        student_id = student['id']
        
        # Test cache performance - first call (cold cache)
        start_time = time.time()
        await student_service.get(student_id)
        cold_cache_time = time.time() - start_time
        
        # Test cache performance - subsequent calls (warm cache)
        warm_cache_times = []
        for i in range(100):
            start_time = time.time()
            await student_service.get(student_id)
            warm_cache_times.append(time.time() - start_time)
        
        avg_warm_cache_time = statistics.mean(warm_cache_times)
        cache_speedup = cold_cache_time / avg_warm_cache_time
        
        print(f"Cold cache time: {cold_cache_time:.6f}s")
        print(f"Warm cache avg time: {avg_warm_cache_time:.6f}s")
        print(f"Cache speedup: {cache_speedup:.2f}x")
        
        # Cache performance assertion
        assert cache_speedup > 2  # Cache should be at least 2x faster
        assert avg_warm_cache_time < 0.01  # Warm cache under 10ms
        
        # Clean up
        await student_service.delete(student_id)
    
    @pytest.mark.asyncio
    async def test_database_concurrent_queries(self, system_services):
        """Test performance of concurrent database queries."""
        student_service = system_services.get('student_service')
        course_service = system_services.get('course_service')
        
        # Create test data
        student_ids = []
        course_ids = []
        
        # Create test data
        for i in range(100):
            student_data = {
                'name': f'Concurrent Student {i}',
                'email': f'concurrent{i}@university.edu',
                'student_id': f'CON{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_ids.append(student['id'])
            
            course_data = {
                'name': f'Concurrent Course {i}',
                'code': f'CON{i:03d}',
                'credits': 3,
                'department_id': 'DEPT001'
            }
            course = await course_service.create(course_data)
            course_ids.append(course['id'])
        
        # Test concurrent query performance
        start_time = time.time()
        
        # Run many concurrent queries
        query_tasks = []
        for i in range(200):
            if i % 2 == 0:
                # Student query
                task = student_service.get(student_ids[i % len(student_ids)])
            else:
                # Course query
                task = course_service.get(course_ids[i % len(course_ids)])
            query_tasks.append(task)
        
        await asyncio.gather(*query_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        queries_per_second = 200 / duration
        avg_query_time = duration / 200
        
        print(f"Concurrent queries: 200")
        print(f"Total time: {duration:.4f}s")
        print(f"Average query time: {avg_query_time:.6f}s")
        print(f"Queries per second: {queries_per_second:.2f}")
        assert queries_per_second > 25  # Should handle at least 25 concurrent queries per second
        
        # Clean up
        cleanup_tasks = []
        for student_id in student_ids:
            cleanup_tasks.append(student_service.delete(student_id))
        for course_id in course_ids:
            cleanup_tasks.append(course_service.delete(course_id))
        await asyncio.gather(*cleanup_tasks)
    
    @pytest.mark.asyncio
    async def test_database_write_performance(self, system_services):
        """Test database write performance."""
        student_service = system_services.get('student_service')
        mark_service = system_services.get('mark_service')
        
        # Test write performance
        write_times = []
        
        # Create many write operations
        for i in range(500):
            start_time = time.time()
            
            # Create student
            student_data = {
                'name': f'Write Test Student {i}',
                'email': f'write{i}@university.edu',
                'student_id': f'WRITE{i:03d}',
                'department_id': 'DEPT001'
            }
            student = await student_service.create(student_data)
            student_id = student['id']
            
            # Create mark
            mark_data = {
                'student_id': student_id,
                'course_id': f'COURSE{i:03d}',
                'marks_obtained': 80,
                'total_marks': 100,
                'percentage': 80.0
            }
            mark = await mark_service.create(mark_data)
            
            end_time = time.time()
            write_times.append(end_time - start_time)
            
            # Clean up immediately
            await student_service.delete(student_id)
            await mark_service.delete(mark['id'])
        
        avg_write_time = statistics.mean(write_times)
        writes_per_second = 500 / sum(write_times)
        
        print(f"Average write time: {avg_write_time:.6f}s")
        print(f"Writes per second: {writes_per_second:.2f}")
        assert writes_per_second > 10  # Should handle at least 10 writes per second