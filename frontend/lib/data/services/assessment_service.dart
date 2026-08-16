import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/assessment_model.dart';

class AssessmentService {
  final ApiClient _apiClient;
  
  AssessmentService([ApiClient? apiClient]) : _apiClient = apiClient ?? ApiClient.instance;
  AssessmentService.internal(this._apiClient);
  
  // Get all assessments
  Future<List<AssessmentModel>> getAllAssessments({String? courseId, String? teacherId}) async {
    try {
      Map<String, String> params = {};
      if (courseId != null) params['course_id'] = courseId;
      if (teacherId != null) params['teacher_id'] = teacherId;
      
      final response = await _apiClient.get(
        '/assessments',
        isAuthRequired: true,
        queryParams: params.isNotEmpty ? params : null,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((assessmentJson) => AssessmentModel.fromJson(assessmentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for assessments list');
      }
    } catch (e) {
      throw ApiException(message: 'Get all assessments failed: ${e.toString()}');
    }
  }
  
  // Get assessment by ID
  Future<AssessmentModel> getAssessmentById(String assessmentId) async {
    try {
      final response = await _apiClient.get(
        '/assessments/$assessmentId',
        isAuthRequired: true,
      );
      
      return AssessmentModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get assessment failed: ${e.toString()}');
    }
  }
  
  // Create new assessment
  Future<AssessmentModel> createAssessment(AssessmentModel assessment) async {
    try {
      final response = await _apiClient.post(
        '/assessments',
        isAuthRequired: true,
        data: assessment.toJson(),
      );
      
      return AssessmentModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Create assessment failed: ${e.toString()}');
    }
  }
  
  // Update assessment
  Future<AssessmentModel> updateAssessment(String assessmentId, AssessmentModel assessment) async {
    try {
      final response = await _apiClient.put(
        '/assessments/$assessmentId',
        isAuthRequired: true,
        data: assessment.toJson(),
      );
      
      return AssessmentModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Update assessment failed: ${e.toString()}');
    }
  }
  
  // Delete assessment
  Future<void> deleteAssessment(String assessmentId) async {
    try {
      await _apiClient.delete(
        '/assessments/$assessmentId',
        isAuthRequired: true,
      );
    } catch (e) {
      throw ApiException(message: 'Delete assessment failed: ${e.toString()}');
    }
  }
  
  // Batch create assessments
  Future<List<AssessmentModel>> createBatchAssessments(List<AssessmentModel> assessments) async {
    try {
      final response = await _apiClient.post(
        '/assessments/batch',
        isAuthRequired: true,
        data: {
          'assessments': assessments.map((a) => a.toJson()).toList(),
        },
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((assessmentJson) => AssessmentModel.fromJson(assessmentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for batch assessments');
      }
    } catch (e) {
      throw ApiException(message: 'Batch create assessments failed: ${e.toString()}');
    }
  }
  
  // Batch update assessments
  Future<void> updateBatchAssessments(Map<String, AssessmentModel> assessments) async {
    try {
      final data = assessments.entries.map((entry) => {
        'id': entry.key,
        'assessment': entry.value.toJson(),
      }).toList();
      
      await _apiClient.put(
        '/assessments/batch',
        isAuthRequired: true,
        data: {'assessments': data},
      );
    } catch (e) {
      throw ApiException(message: 'Batch update assessments failed: ${e.toString()}');
    }
  }
  
  // Get assessments by student ID
  Future<List<AssessmentModel>> getAssessmentsByStudent(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/assessments',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((assessmentJson) => AssessmentModel.fromJson(assessmentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for student assessments');
      }
    } catch (e) {
      throw ApiException(message: 'Get student assessments failed: ${e.toString()}');
    }
  }
  
  // Get assessments by course ID
  Future<List<AssessmentModel>> getAssessmentsByCourse(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/assessments',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((assessmentJson) => AssessmentModel.fromJson(assessmentJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for course assessments');
      }
    } catch (e) {
      throw ApiException(message: 'Get course assessments failed: ${e.toString()}');
    }
  }
  
  // Submit grade for assessment
  Future<AssessmentSubmission> submitGrade(String assessmentId, String studentId, double marks, {String? feedback}) async {
    try {
      final response = await _apiClient.post(
        '/assessments/$assessmentId/grades',
        isAuthRequired: true,
        data: {
          'student_id': studentId,
          'marks': marks,
          'feedback': feedback,
        },
      );
      
      return AssessmentSubmission.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Submit grade failed: ${e.toString()}');
    }
  }
  
  // Submit batch grades
  Future<void> submitBatchGrades(List<Map<String, dynamic>> grades) async {
    try {
      await _apiClient.post(
        '/assessments/batch-grades',
        isAuthRequired: true,
        data: {'grades': grades},
      );
    } catch (e) {
      throw ApiException(message: 'Submit batch grades failed: ${e.toString()}');
    }
  }
  
  // Calculate student grades
  Future<GradeCalculation> calculateStudentGrades(String studentId) async {
    try {
      final response = await _apiClient.get(
        '/students/$studentId/grades/calculate',
        isAuthRequired: true,
      );
      
      return GradeCalculation.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Calculate student grades failed: ${e.toString()}');
    }
  }
  
  // Calculate course grades
  Future<Map<String, GradeCalculation>> calculateCourseGrades(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/grades/calculate',
        isAuthRequired: true,
      );
      
      if (response['data'] is Map) {
        return (response['data'] as Map).map((key, value) => 
          MapEntry(key.toString(), GradeCalculation.fromJson(value))
        );
      } else {
        throw ApiException(message: 'Invalid response format for course grades');
      }
    } catch (e) {
      throw ApiException(message: 'Calculate course grades failed: ${e.toString()}');
    }
  }
  
  // Get grade statistics for course
  Future<Map<String, dynamic>> getGradeStatistics(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/grades/statistics',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get grade statistics failed: ${e.toString()}');
    }
  }
}