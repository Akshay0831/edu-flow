import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/user_model.dart';

class StudentService {
  final ApiClient _apiClient = ApiClient.instance;
  
  // Get all students
  Future<List<UserModel>> getAllStudents() async {
    try {
      final response = await _apiClient.get(
        '/students',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => UserModel.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for students list');
      }
    } catch (e) {
      throw ApiException(message: 'Get all students failed: ${e.toString()}');
    }
  }
  
  // Get student by ID
  Future<UserModel> getStudentById(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId',
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get student failed: ${e.toString()}');
    }
  }
  
  // Get student profile with additional details
  Future<Map<String, dynamic>> getStudentProfile(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/profile',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get student profile failed: ${e.toString()}');
    }
  }
  
  // Create new student
  Future<UserModel> createStudent({
    required String email,
    required String password,
    required String name,
    String? phone,
    String? avatar,
    String? studentId, // Optional student ID number
    String? department,
    String? program,
    String? year,
  }) async {
    try {
      final response = await _apiClient.post(
        '/students',
        data: {
          'email': email,
          'password': password,
          'name': name,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
          if (studentId != null) 'student_id': studentId,
          if (department != null) 'department': department,
          if (program != null) 'program': program,
          if (year != null) 'year': year,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Create student failed: ${e.toString()}');
    }
  }
  
  // Update student
  Future<UserModel> updateStudent({
    required String studentId,
    String? name,
    String? email,
    String? phone,
    String? avatar,
    String? department,
    String? program,
    String? year,
  }) async {
    try {
      final response = await _apiClient.put(
        '/students/$studentId',
        data: {
          if (name != null) 'name': name,
          if (email != null) 'email': email,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
          if (department != null) 'department': department,
          if (program != null) 'program': program,
          if (year != null) 'year': year,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Update student failed: ${e.toString()}');
    }
  }
  
  // Delete student
  Future<Map<String, dynamic>> deleteStudent(String studentId) async {
    try {
      final response = await _apiClient.delete(
        '/students/$studentId',
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Student deleted successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Delete student failed: ${e.toString()}');
    }
  }
  
  // Get students by department
  Future<List<UserModel>> getStudentsByDepartment(String department) async {
    try {
      final response = await _apiClient.get(
        '/students?department=$department',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => UserModel.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for students by department');
      }
    } catch (e) {
      throw ApiException(message: 'Get students by department failed: ${e.toString()}');
    }
  }
  
  // Get students by program
  Future<List<UserModel>> getStudentsByProgram(String program) async {
    try {
      final response = await _apiClient.get(
        '/students?program=$program',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => UserModel.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for students by program');
      }
    } catch (e) {
      throw ApiException(message: 'Get students by program failed: ${e.toString()}');
    }
  }
  
  // Get students by year
  Future<List<UserModel>> getStudentsByYear(String year) async {
    try {
      final response = await _apiClient.get(
        '/students?year=$year',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => UserModel.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for students by year');
      }
    } catch (e) {
      throw ApiException(message: 'Get students by year failed: ${e.toString()}');
    }
  }
  
  // Search students
  Future<List<UserModel>> searchStudents(String query) async {
    try {
      final response = await _apiClient.get(
        '/students/search?q=$query',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => UserModel.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for student search');
      }
    } catch (e) {
      throw ApiException(message: 'Search students failed: ${e.toString()}');
    }
  }
}