import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/data/services/feedback_service.dart';
import 'package:edu_flow/data/models/feedback_model.dart';

// Mock classes
class MockApiClient extends Mock implements ApiClient {}

void main() {
  group('FeedbackService', () {
    late FeedbackService feedbackService;
    late MockApiClient mockApiClient;

    setUp(() {
      mockApiClient = MockApiClient();
      feedbackService = FeedbackService();
    });

    group('submitFeedback', () {
      test('submits feedback when API call is successful', () async {
        final feedback = Feedback(
          id: '1',
          courseId: 'course1',
          studentId: 'student1',
          teacherId: 'teacher1',
          type: 'student_feedback',
          rating: '5',
          comment: 'Excellent course',
          tags: ['helpful', 'engaging'],
          submittedAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        // Mock API response
        when(mockApiClient.post(
          '/feedback',
          isAuthRequired: true,
          data: feedback.toJson(),
        )).thenAnswer((_) async => {
          'data': {
            'id': '1',
            'course_id': 'course1',
            'student_id': 'student1',
            'teacher_id': 'teacher1',
            'type': 'student_feedback',
            'rating': '5',
            'comment': 'Excellent course',
            'tags': ['helpful', 'engaging'],
            'submitted_at': feedback.submittedAt.toIso8601String(),
            'updated_at': feedback.updatedAt.toIso8601String(),
          },
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final submittedFeedback = await feedbackService.submitFeedback(feedback);

        expect(submittedFeedback, isA<Feedback>());
        expect(submittedFeedback.id, '1');
        expect(submittedFeedback.courseId, 'course1');
        expect(submittedFeedback.studentId, 'student1');
        expect(submittedFeedback.teacherId, 'teacher1');
        expect(submittedFeedback.type, 'student_feedback');
        expect(submittedFeedback.rating, '5');
        expect(submittedFeedback.comment, 'Excellent course');
        expect(submittedFeedback.tags, ['helpful', 'engaging']);
      });
    });

    group('getStudentFeedback', () {
      test('returns student feedback when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/students/student1/feedback',
          isAuthRequired: true,
          params: {'course_id': 'course1'},
        )).thenAnswer((_) async => {
          'data': [
            {
              'id': '1',
              'course_id': 'course1',
              'student_id': 'student1',
              'teacher_id': 'teacher1',
              'type': 'student_feedback',
              'rating': '5',
              'comment': 'Excellent course',
              'tags': ['helpful', 'engaging'],
              'submitted_at': DateTime.now().toIso8601String(),
              'updated_at': DateTime.now().toIso8601String(),
            },
          ],
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final feedbacks = await feedbackService.getStudentFeedback('student1', courseId: 'course1');

        expect(feedbacks, isA<List<Feedback>>());
        expect(feedbacks.length, 1);
        expect(feedbacks[0].id, '1');
        expect(feedbacks[0].studentId, 'student1');
        expect(feedbacks[0].rating, '5');
      });
    });

    group('getFeedbackSummary', () {
      test('returns feedback summary when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/courses/course1/feedback/summary',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'course_id': 'course1',
            'average_rating': 4.5,
            'total_feedbacks': 25,
            'rating_distribution': {
              '5': 15,
              '4': 8,
              '3': 2,
              '2': 0,
              '1': 0,
            },
            'common_tags': ['helpful', 'engaging', 'clear'],
            'positive_comments': ['Great course!', 'Very informative'],
            'negative_comments': ['Needs more examples'],
            'last_updated': DateTime.now().toIso8601String(),
          },
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final summary = await feedbackService.getFeedbackSummary('course1');

        expect(summary, isA<FeedbackSummary>());
        expect(summary.courseId, 'course1');
        expect(summary.averageRating, 4.5);
        expect(summary.totalFeedbacks, 25);
        expect(summary.ratingDistribution, {
          '5': 15,
          '4': 8,
          '3': 2,
          '2': 0,
          '1': 0,
        });
        expect(summary.commonTags, ['helpful', 'engaging', 'clear']);
      });
    });

    group('analyzeFeedbackSentiment', () {
      test('analyzes feedback sentiment when API call is successful', () async {
        // Mock API response
        when(mockApiClient.post(
          '/feedback/1/analyze',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'feedback_id': '1',
            'sentiment': 'positive',
            'confidence': 0.95,
            'emotion_scores': {
              'joy': 0.8,
              'trust': 0.6,
              'fear': 0.1,
            },
            'keywords': ['excellent', 'helpful', 'clear'],
            'suggestions': ['Continue current teaching style'],
            'analyzed_at': DateTime.now().toIso8601String(),
          },
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final analysis = await feedbackService.analyzeFeedbackSentiment('1');

        expect(analysis, isA<SentimentAnalysis>());
        expect(analysis.feedbackId, '1');
        expect(analysis.sentiment, 'positive');
        expect(analysis.confidence, 0.95);
        expect(analysis.emotionScores, {
          'joy': 0.8,
          'trust': 0.6,
          'fear': 0.1,
        });
        expect(analysis.keywords, ['excellent', 'helpful', 'clear']);
      });
    });

    group('generateFeedbackReport', () {
      test('generates feedback report when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/courses/course1/feedback/report',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'course_id': 'course1',
            'title': 'Course Feedback Report',
            'generated_at': DateTime.now().toIso8601String(),
            'summary': {
              'average_rating': 4.5,
              'total_feedbacks': 25,
              'rating_distribution': {
                '5': 15,
                '4': 8,
                '3': 2,
                '2': 0,
                '1': 0,
              },
            },
            'feedbacks': [
              {
                'id': '1',
                'course_id': 'course1',
                'student_id': 'student1',
                'teacher_id': 'teacher1',
                'type': 'student_feedback',
                'rating': '5',
                'comment': 'Excellent course',
                'tags': ['helpful', 'engaging'],
                'submitted_at': DateTime.now().toIso8601String(),
                'updated_at': DateTime.now().toIso8601String(),
              },
            ],
            'action_items': [
              {
                'id': '1',
                'title': 'Improve examples',
                'description': 'Add more practical examples',
                'priority': 'medium',
                'assignee_id': 'teacher1',
                'assignee_name': 'John Doe',
                'due_date': DateTime.now().add(const Duration(days: 7)).toIso8601String(),
                'status': 'pending',
                'created_at': DateTime.now().toIso8601String(),
                'updated_at': DateTime.now().toIso8601String(),
              },
            ],
            'recommendations': ['Continue current teaching style'],
          },
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final report = await feedbackService.generateFeedbackReport('course1');

        expect(report, isA<FeedbackReport>());
        expect(report.courseId, 'course1');
        expect(report.title, 'Course Feedback Report');
        expect(report.summary.averageRating, 4.5);
        expect(report.feedbacks.length, 1);
        expect(report.actionItems.length, 1);
        expect(report.recommendations, ['Continue current teaching style']);
      });
    });

    group('getActionItems', () {
      test('returns action items when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/courses/course1/feedback/action-items',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': [
            {
              'id': '1',
              'title': 'Improve examples',
              'description': 'Add more practical examples',
              'priority': 'medium',
              'assignee_id': 'teacher1',
              'assignee_name': 'John Doe',
              'due_date': DateTime.now().add(const Duration(days: 7)).toIso8601String(),
              'status': 'pending',
              'created_at': DateTime.now().toIso8601String(),
              'updated_at': DateTime.now().toIso8601String(),
            },
          ],
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final actionItems = await feedbackService.getActionItems('course1');

        expect(actionItems, isA<List<ActionItem>>());
        expect(actionItems.length, 1);
        expect(actionItems[0].id, '1');
        expect(actionItems[0].title, 'Improve examples');
        expect(actionItems[0].priority, 'medium');
        expect(actionItems[0].assigneeId, 'teacher1');
      });
    });

    group('exportFeedbackData', () {
      test('exports feedback data when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/feedback/export',
          isAuthRequired: true,
          params: {
            'course_id': 'course1',
            'format': 'csv',
            'start_date': '2023-01-01T00:00:00Z',
            'end_date': '2023-12-31T23:59:59Z',
          },
        )).thenAnswer((_) async => {
          'data': {
            'export_url': 'https://example.com/feedback_export.csv',
          },
        });

        // Mock the ApiClient.instance
        ApiClient.instance = mockApiClient;

        final startDate = DateTime(2023, 1, 1);
        final endDate = DateTime(2023, 12, 31);

        final exportUrl = await feedbackService.exportFeedbackData(
          courseId: 'course1',
          format: 'csv',
          startDate: startDate,
          endDate: endDate,
        );

        expect(exportUrl, 'https://example.com/feedback_export.csv');
      });
    });
  });
}