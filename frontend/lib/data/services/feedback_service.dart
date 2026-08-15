import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/feedback_model.dart';

class FeedbackService {
  final ApiClient _apiClient;
  
  FeedbackService._internal(this._apiClient);
  
  factory FeedbackService() {
    return FeedbackService._internal(ApiClient.instance);
  }
  
  // Submit feedback
  Future<Feedback> submitFeedback(Feedback feedback) async {
    try {
      final response = await _apiClient.post(
        '/feedback',
        isAuthRequired: true,
        data: feedback.toJson(),
      );
      
      return Feedback.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Submit feedback failed: ${e.toString()}');
    }
  }
  
  // Get feedback by ID
  Future<Feedback> getFeedbackById(String feedbackId) async {
    try {
      final response = await _apiClient.get(
        '/feedback/$feedbackId',
        isAuthRequired: true,
      );
      
      return Feedback.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get feedback failed: ${e.toString()}');
    }
  }
  
  // Get student feedback
  Future<List<Feedback>> getStudentFeedback(String studentId, {String? courseId}) async {
    try {
      final params = <String, String>{};
      if (courseId != null) params['course_id'] = courseId;
      
      final response = await _apiClient.get(
        '/students/$studentId/feedback',
        isAuthRequired: true,
        queryParams: params.isNotEmpty ? params : null,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((feedbackJson) => Feedback.fromJson(feedbackJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for student feedback');
      }
    } catch (e) {
      throw ApiException(message: 'Get student feedback failed: ${e.toString()}');
    }
  }
  
  // Get teacher feedback
  Future<List<Feedback>> getTeacherFeedback(String teacherId, {String? courseId}) async {
    try {
      final params = <String, String>{};
      if (courseId != null) params['course_id'] = courseId;
      
      final response = await _apiClient.get(
        '/teachers/$teacherId/feedback',
        isAuthRequired: true,
        queryParams: params.isNotEmpty ? params : null,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((feedbackJson) => Feedback.fromJson(feedbackJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for teacher feedback');
      }
    } catch (e) {
      throw ApiException(message: 'Get teacher feedback failed: ${e.toString()}');
    }
  }
  
  // Get course feedback
  Future<List<Feedback>> getCourseFeedback(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((feedbackJson) => Feedback.fromJson(feedbackJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for course feedback');
      }
    } catch (e) {
      throw ApiException(message: 'Get course feedback failed: ${e.toString()}');
    }
  }
  
  // Get feedback summary for course
  Future<FeedbackSummary> getFeedbackSummary(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback/summary',
        isAuthRequired: true,
      );
      
      return FeedbackSummary.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get feedback summary failed: ${e.toString()}');
    }
  }
  
  // Analyze feedback sentiment
  Future<SentimentAnalysis> analyzeFeedbackSentiment(String feedbackId) async {
    try {
      final response = await _apiClient.post(
        '/feedback/$feedbackId/analyze',
        isAuthRequired: true,
        data: {},
      );
      
      return SentimentAnalysis.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Analyze feedback sentiment failed: ${e.toString()}');
    }
  }
  
  // Generate feedback report
  Future<FeedbackReport> generateFeedbackReport(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback/report',
        isAuthRequired: true,
      );
      
      return FeedbackReport.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Generate feedback report failed: ${e.toString()}');
    }
  }
  
  // Get action items from feedback
  Future<List<ActionItem>> getActionItems(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback/action-items',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((itemJson) => ActionItem.fromJson(itemJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for action items');
      }
    } catch (e) {
      throw ApiException(message: 'Get action items failed: ${e.toString()}');
    }
  }
  
  // Create action item from feedback
  Future<ActionItem> createActionItem(ActionItem actionItem) async {
    try {
      final response = await _apiClient.post(
        '/feedback/action-items',
        isAuthRequired: true,
        data: actionItem.toJson(),
      );
      
      return ActionItem.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Create action item failed: ${e.toString()}');
    }
  }
  
  // Update action item
  Future<ActionItem> updateActionItem(String actionItemId, ActionItem actionItem) async {
    try {
      final response = await _apiClient.put(
        '/feedback/action-items/$actionItemId',
        isAuthRequired: true,
        data: actionItem.toJson(),
      );
      
      return ActionItem.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Update action item failed: ${e.toString()}');
    }
  }
  
  // Complete action item
  Future<void> completeActionItem(String actionItemId) async {
    try {
      await _apiClient.put(
        '/feedback/action-items/$actionItemId/complete',
        isAuthRequired: true,
        data: {},
      );
    } catch (e) {
      throw ApiException(message: 'Complete action item failed: ${e.toString()}');
    }
  }
  
  // Get feedback trends over time
  Future<Map<String, dynamic>> getFeedbackTrends(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback/trends',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get feedback trends failed: ${e.toString()}');
    }
  }
  
  // Get feedback statistics
  Future<Map<String, dynamic>> getFeedbackStatistics(String courseId) async {
    try {
      final response = await _apiClient.get(
        '/courses/$courseId/feedback/statistics',
        isAuthRequired: true,
      );
      
      return response['data'] ?? {};
    } catch (e) {
      throw ApiException(message: 'Get feedback statistics failed: ${e.toString()}');
    }
  }
  
  // Export feedback data
  Future<String> exportFeedbackData({
    String? courseId,
    String? format,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final params = <String, String>{};
      
      if (courseId != null) params['course_id'] = courseId;
      if (format != null) params['format'] = format;
      if (startDate != null) params['start_date'] = startDate.toIso8601String();
      if (endDate != null) params['end_date'] = endDate.toIso8601String();
      
      final response = await _apiClient.get(
        '/feedback/export',
        isAuthRequired: true,
        queryParams: params.isNotEmpty ? params : null,
      );
      
      return response['data']?['export_url'] ?? '';
    } catch (e) {
      throw ApiException(message: 'Export feedback data failed: ${e.toString()}');
    }
  }
}