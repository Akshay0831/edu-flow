import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';

class CourseService {
  final ApiClient _apiClient = ApiClient.instance;
  
  // Get all courses
  Future<List<Map<String, dynamic>>> getAllCourses() async {
    try {
      final response = await _apiClient.get(
        '/courses',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for courses list');
      }
    } catch (e) {
      throw ApiException(message: 'Get all courses failed: ${e.toString()}');
    }
  }
  
  // Get course by ID
  Future<Map<String, dynamic>> getCourseById(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get course failed: ${e.toString()}');
    }
  }
  
  // Create new course
  Future<Map<String, dynamic>> createCourse({
    required String title,
    required String code,
    required String description,
    required int credits,
    required String department,
    String? semester,
    String? academicYear,
    String? syllabus,
    String? objectives,
    String? prerequisites,
  }) async {
    try {
      final response = await _apiClient.post(
        '/courses',
        data: {
          'title': title,
          'code': code,
          'description': description,
          'credits': credits,
          'department': department,
          if (semester != null) 'semester': semester,
          if (academicYear != null) 'academic_year': academicYear,
          if (syllabus != null) 'syllabus': syllabus,
          if (objectives != null) 'objectives': objectives,
          if (prerequisites != null) 'prerequisites': prerequisites,
        },
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Create course failed: ${e.toString()}');
    }
  }
  
  // Update course
  Future<Map<String, dynamic>> updateCourse({
    required String courseId,
    String? title,
    String? code,
    String? description,
    int? credits,
    String? department,
    String? semester,
    String? academicYear,
    String? syllabus,
    String? objectives,
    String? prerequisites,
  }) async {
    try {
      final response = await _apiClient.put(
        '/courses/$courseId',
        data: {
          if (title != null) 'title': title,
          if (code != null) 'code': code,
          if (description != null) 'description': description,
          if (credits != null) 'credits': credits,
          if (department != null) 'department': department,
          if (semester != null) 'semester': semester,
          if (academicYear != null) 'academic_year': academicYear,
          if (syllabus != null) 'syllabus': syllabus,
          if (objectives != null) 'objectives': objectives,
          if (prerequisites != null) 'prerequisites': prerequisites,
        },
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Update course failed: ${e.toString()}');
    }
  }
  
  // Delete course
  Future<Map<String, dynamic>> deleteCourse(String courseId) async {
    try {
      final response = await _apiClient.delete(
        '/courses/$courseId',
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Course deleted successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Delete course failed: ${e.toString()}');
    }
  }
  
  // Get courses by department
  Future<List<Map<String, dynamic>>> getCoursesByDepartment(String department) async {
    try {
      final response = await _apiClient.get(
        '/courses?department=$department',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for courses by department');
      }
    } catch (e) {
      throw ApiException(message: 'Get courses by department failed: ${e.toString()}');
    }
  }
  
  // Get courses by semester
  Future<List<Map<String, dynamic>>> getCoursesBySemester(String semester) async {
    try {
      final response = await _apiClient.get(
        '/courses?semester=$semester',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for courses by semester');
      }
    } catch (e) {
      throw ApiException(message: 'Get courses by semester failed: ${e.toString()}');
    }
  }
  
  // Get courses by academic year
  Future<List<Map<String, dynamic>>> getCoursesByAcademicYear(String academicYear) async {
    try {
      final response = await _apiClient.get(
        '/courses?academic_year=$academicYear',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for courses by academic year');
      }
    } catch (e) {
      throw ApiException(message: 'Get courses by academic year failed: ${e.toString()}');
    }
  }
  
  // Search courses
  Future<List<Map<String, dynamic>>> searchCourses(String query) async {
    try {
      final response = await _apiClient.get(
        '/courses/search?q=$query',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for course search');
      }
    } catch (e) {
      throw ApiException(message: 'Search courses failed: ${e.toString()}');
    }
  }
  
  // Get course syllabus
  Future<Map<String, dynamic>> getCourseSyllabus(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/syllabus',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get course syllabus failed: ${e.toString()}');
    }
  }
  
  // Update course syllabus
  Future<Map<String, dynamic>> updateCourseSyllabus({
    required String courseId,
    required String syllabus,
  }) async {
    try {
      final response = await _apiClient.put(
        '/courses/$courseId/syllabus',
        data: {'syllabus': syllabus},
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Update course syllabus failed: ${e.toString()}');
    }
  }
  
  // Get course objectives
  Future<List<String>> getCourseObjectives(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/objectives',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<String>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for course objectives');
      }
    } catch (e) {
      throw ApiException(message: 'Get course objectives failed: ${e.toString()}');
    }
  }
  
  // Update course objectives
  Future<Map<String, dynamic>> updateCourseObjectives({
    required String courseId,
    required List<String> objectives,
  }) async {
    try {
      final response = await _apiClient.put(
        '/courses/$courseId/objectives',
        data: {'objectives': objectives},
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Update course objectives failed: ${e.toString()}');
    }
  }
  
  // Get course prerequisites
  Future<List<String>> getCoursePrerequisites(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/prerequisites',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<String>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for course prerequisites');
      }
    } catch (e) {
      throw ApiException(message: 'Get course prerequisites failed: ${e.toString()}');
    }
  }
  
  // Update course prerequisites
  Future<Map<String, dynamic>> updateCoursePrerequisites({
    required String courseId,
    required List<String> prerequisites,
  }) async {
    try {
      final response = await _apiClient.put(
        '/courses/$courseId/prerequisites',
        data: {'prerequisites': prerequisites},
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Update course prerequisites failed: ${e.toString()}');
    }
  }
}