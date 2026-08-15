import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/analytics_model.dart';

class AnalyticsService {
  final ApiClient _apiClient;
  
  AnalyticsService._internal(this._apiClient);
  
  factory AnalyticsService() {
    return AnalyticsService._internal(ApiClient.instance);
  }
  
  // Student analytics
  Future<StudentPerformance> getStudentPerformance(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/performance',
        isAuthRequired: true,
      );
      
      return StudentPerformance.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get student performance failed: ${e.toString()}');
    }
  }
  
  // Get student progress for multiple courses
  Future<List<CourseProgress>> getStudentProgress(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/progress',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((progressJson) => CourseProgress.fromJson(progressJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for student progress');
      }
    } catch (e) {
      throw ApiException(message: 'Get student progress failed: ${e.toString()}');
    }
  }
  
  // Get student attendance
  Future<Map<String, dynamic>> getStudentAttendance(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/attendance',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get student attendance failed: ${e.toString()}');
    }
  }
  
  // Class analytics
  Future<ClassPerformance> getClassPerformance(String classId) async {
    try {
      final response = await _apiClient.get(
        '/classes/$classId/performance',
        isAuthRequired: true,
      );
      
      return ClassPerformance.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get class performance failed: ${e.toString()}');
    }
  }
  
  // Get class students with performance data
  Future<List<StudentPerformance>> getClassStudents(String classId) async {
    try {
      final response = await _apiClient.get(
        '/classes/$classId/students',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((studentJson) => StudentPerformance.fromJson(studentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for class students');
      }
    } catch (e) {
      throw ApiException(message: 'Get class students failed: ${e.toString()}');
    }
  }
  
  // Course analytics
  Future<CourseAnalytics> getCourseAnalytics(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/analytics',
        isAuthRequired: true,
      );
      
      return CourseAnalytics.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get course analytics failed: ${e.toString()}');
    }
  }
  
  // Get course enrollment trends
  Future<List<EnrollmentTrend>> getEnrollmentTrends(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/enrollment-trends',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((trendJson) => EnrollmentTrend.fromJson(trendJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for enrollment trends');
      }
    } catch (e) {
      throw ApiException(message: 'Get enrollment trends failed: ${e.toString()}');
    }
  }
  
  // Teacher analytics
  Future<TeacherPerformance> getTeacherPerformance(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId/performance',
        isAuthRequired: true,
      );
      
      return TeacherPerformance.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get teacher performance failed: ${e.toString()}');
    }
  }
  
  // Get teacher courses with analytics
  Future<List<CourseAnalytics>> getTeacherCourses(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId/courses',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((courseJson) => CourseAnalytics.fromJson(courseJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teacher courses');
      }
    } catch (e) {
      throw ApiException(message: 'Get teacher courses failed: ${e.toString()}');
    }
  }
  
  // Get teacher effectiveness metrics
  Future<Map<String, dynamic>> getTeacherEffectivenessMetrics(String teacherId) async {
    try {
      final response = await _apiClient.get(
        '/teachers/$teacherId/effectiveness',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get teacher effectiveness metrics failed: ${e.toString()}');
    }
  }
  
  // Department analytics
  Future<Map<String, dynamic>> getDepartmentAnalytics(String departmentId) async {
    try {
      final response = await _apiClient.get(
        '/departments/$departmentId/analytics',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get department analytics failed: ${e.toString()}');
    }
  }
  
  // Get institutional analytics (admin only)
  Future<Map<String, dynamic>> getInstitutionalAnalytics() async {
    try {
      final response = await _apiClient.get(
        '/analytics/institution',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get institutional analytics failed: ${e.toString()}');
    }
  }
  
  // Get dashboard data for different roles
  Future<Map<String, dynamic>> getDashboardData(String role) async {
    try {
      Map<String, String> params = {'role': role};
      final response = await _apiClient.get(
        '/analytics/dashboard',
        isAuthRequired: true,
        queryParams: params,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get dashboard data failed: ${e.toString()}');
    }
  }
  
  // Generate performance report
  Future<Map<String, dynamic>> generatePerformanceReport({
    String? studentId,
    String? courseId,
    String? classId,
    String? teacherId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final params = <String, String>{};
      
      if (studentId != null) params['student_id'] = studentId;
      if (courseId != null) params['course_id'] = courseId;
      if (classId != null) params['class_id'] = classId;
      if (teacherId != null) params['teacher_id'] = teacherId;
      if (startDate != null) params['start_date'] = startDate.toIso8601String();
      if (endDate != null) params['end_date'] = endDate.toIso8601String();
      
      final response = await _apiClient.post(
        '/analytics/performance-report',
        isAuthRequired: true,
        data: params.isNotEmpty ? <String, dynamic>{...params} : const {},
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Generate performance report failed: ${e.toString()}');
    }
  }
  
  // Export analytics data
  Future<String> exportAnalyticsData({
    String? format,
    String? studentId,
    String? courseId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final params = <String, String>{};
      
      if (format != null) params['format'] = format;
      if (studentId != null) params['student_id'] = studentId;
      if (courseId != null) params['course_id'] = courseId;
      if (startDate != null) params['start_date'] = startDate.toIso8601String();
      if (endDate != null) params['end_date'] = endDate.toIso8601String();
      
      final response = await _apiClient.get(
        '/analytics/export',
        isAuthRequired: true,
        queryParams: params.isNotEmpty ? params : null,
      );
      
      return response['data']?['export_url'] ?? '';
    } catch (e) {
      throw ApiException(message: 'Export analytics data failed: ${e.toString()}');
    }
  }
}