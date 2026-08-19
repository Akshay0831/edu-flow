import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/user_model.dart';

class TeacherService {
  final ApiClient _apiClient = ApiClient.instance;
  
  // Get all teachers
  Future<List<UserModel>> getAllTeachers() async {
    try {
      final response = await _apiClient.get(
        '/teachers',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((teacherJson) => UserModel.fromJson(teacherJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teachers list');
      }
    } catch (e) {
      throw ApiException(message: 'Get all teachers failed: ${e.toString()}');
    }
  }
  
  // Get teacher by ID
  Future<UserModel> getTeacherById(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId',
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get teacher failed: ${e.toString()}');
    }
  }
  
  // Get teacher profile with additional details
  Future<Map<String, dynamic>> getTeacherProfile(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId/profile',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get teacher profile failed: ${e.toString()}');
    }
  }
  
  // Create new teacher
  Future<UserModel> createTeacher({
    required String email,
    required String password,
    required String name,
    String? phone,
    String? avatar,
    String? teacherId, // Optional teacher ID number
    String? department,
    String? designation,
    String? specialization,
  }) async {
    try {
      final response = await _apiClient.post(
        '/teachers',
        data: {
          'email': email,
          'password': password,
          'name': name,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
          if (teacherId != null) 'teacher_id': teacherId,
          if (department != null) 'department': department,
          if (designation != null) 'designation': designation,
          if (specialization != null) 'specialization': specialization,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Create teacher failed: ${e.toString()}');
    }
  }
  
  // Update teacher
  Future<UserModel> updateTeacher({
    required String teacherId,
    String? name,
    String? email,
    String? phone,
    String? avatar,
    String? department,
    String? designation,
    String? specialization,
  }) async {
    try {
      final response = await _apiClient.put(
        '/teachers/$teacherId',
        data: {
          if (name != null) 'name': name,
          if (email != null) 'email': email,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
          if (department != null) 'department': department,
          if (designation != null) 'designation': designation,
          if (specialization != null) 'specialization': specialization,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Update teacher failed: ${e.toString()}');
    }
  }
  
  // Delete teacher
  Future<Map<String, dynamic>> deleteTeacher(String teacherId) async {
    try {
      final response = await _apiClient.delete(
        '/teachers/$teacherId',
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Teacher deleted successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Delete teacher failed: ${e.toString()}');
    }
  }
  
  // Get teachers by department
  Future<List<UserModel>> getTeachersByDepartment(String department) async {
    try {
      final response = await _apiClient.get(
        '/teachers?department=$department',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((teacherJson) => UserModel.fromJson(teacherJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teachers by department');
      }
    } catch (e) {
      throw ApiException(message: 'Get teachers by department failed: ${e.toString()}');
    }
  }
  
  // Get teachers by designation
  Future<List<UserModel>> getTeachersByDesignation(String designation) async {
    try {
      final response = await _apiClient.get(
        '/teachers?designation=$designation',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((teacherJson) => UserModel.fromJson(teacherJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teachers by designation');
      }
    } catch (e) {
      throw ApiException(message: 'Get teachers by designation failed: ${e.toString()}');
    }
  }
  
  // Search teachers
  Future<List<UserModel>> searchTeachers(String query) async {
    try {
      final response = await _apiClient.get(
        '/teachers/search?q=$query',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((teacherJson) => UserModel.fromJson(teacherJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teacher search');
      }
    } catch (e) {
      throw ApiException(message: 'Search teachers failed: ${e.toString()}');
    }
  }
  
  // Get teacher assigned courses
  Future<List<Map<String, dynamic>>> getTeacherCourses(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId/courses',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return List<Map<String, dynamic>>.from(response['data']);
      } else {
        throw ApiException(message: 'Invalid response format for teacher courses');
      }
    } catch (e) {
      throw ApiException(message: 'Get teacher courses failed: ${e.toString()}');
    }
  }
  
  // Assign course to teacher
  Future<Map<String, dynamic>> assignCourseToTeacher({
    required String teacherId,
    required String courseId,
  }) async {
    try {
      final response = await _apiClient.post(
        '/teachers/$teacherId/courses',
        data: {'course_id': courseId},
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Course assigned successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Assign course to teacher failed: ${e.toString()}');
    }
  }
  
  // Remove course from teacher
  Future<Map<String, dynamic>> removeCourseFromTeacher({
    required String teacherId,
    required String courseId,
  }) async {
    try {
      final response = await _apiClient.delete(
        '/teachers/$teacherId/courses/$courseId',
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Course removed successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Remove course from teacher failed: ${e.toString()}');
    }
  }
}