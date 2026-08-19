import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/test/helpers/test_helpers.dart';
import 'package:edu_flow/data/services/analytics_service.dart';
import 'package:edu_flow/data/models/analytics_model.dart';

// Mock classes
class MockApiClient extends Mock implements ApiClient {}

void main() {
  group('AnalyticsService', () {
    late AnalyticsService analyticsService;
    late MockApiClient mockApiClient;

    setUp(() {
      mockApiClient = MockApiClient();
      analyticsService = AnalyticsService();
    });

    group('getStudentPerformance', () {
      test('returns student performance when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/students/student1/performance',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'student_id': 'student1',
            'name': 'John Doe',
            'overall_score': 85.5,
            'attendance_rate': 95.0,
            'total_assessments': 10,
            'completed_assessments': 9,
            'average_grade': 82.0,
            'course_progress': [
              {
                'course_id': 'course1',
                'title': 'Mathematics',
                'completion_percentage': 90.0,
                'average_grade': 85.0,
                'enrolled_students': 30,
                'completed_students': 27,
                'start_date': '2023-01-01T00:00:00Z',
                'end_date': '2023-12-31T23:59:59Z',
                'top_performers': [],
              },
            ],
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final performance = await analyticsService.getStudentPerformance('student1');

        expect(performance, isA<StudentPerformance>());
        expect(performance.studentId, 'student1');
        expect(performance.name, 'John Doe');
        expect(performance.overallScore, 85.5);
        expect(performance.attendanceRate, 95.0);
        expect(performance.totalAssessments, 10);
        expect(performance.completedAssessments, 9);
      });
    });

    group('getCourseAnalytics', () {
      test('returns course analytics when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/courses/course1/analytics',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'course_id': 'course1',
            'title': 'Mathematics',
            'average_grade': 78.5,
            'completion_rate': 85.0,
            'enrolled_students': 30,
            'completed_students': 26,
            'enrollment_trends': [
              {
                'date': '2023-01-01T00:00:00Z',
                'new_enrollments': 10,
                'dropouts': 2,
                'active_students': 8,
              },
            ],
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final analytics = await analyticsService.getCourseAnalytics('course1');

        expect(analytics, isA<CourseAnalytics>());
        expect(analytics.courseId, 'course1');
        expect(analytics.title, 'Mathematics');
        expect(analytics.averageGrade, 78.5);
        expect(analytics.completionRate, 85.0);
        expect(analytics.enrolledStudents, 30);
        expect(analytics.completedStudents, 26);
      });
    });

    group('getTeacherPerformance', () {
      test('returns teacher performance when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/teachers/teacher1/performance',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'teacher_id': 'teacher1',
            'name': 'Jane Smith',
            'average_student_score': 82.5,
            'course_completion_rate': 90.0,
            'total_courses': 5,
            'total_students': 120,
            'course_analytics': [
              {
                'course_id': 'course1',
                'title': 'Mathematics',
                'average_grade': 80.0,
                'completion_rate': 88.0,
                'enrolled_students': 30,
                'completed_students': 26,
                'enrollment_trends': [],
              },
            ],
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final performance = await analyticsService.getTeacherPerformance('teacher1');

        expect(performance, isA<TeacherPerformance>());
        expect(performance.teacherId, 'teacher1');
        expect(performance.name, 'Jane Smith');
        expect(performance.averageStudentScore, 82.5);
        expect(performance.courseCompletionRate, 90.0);
        expect(performance.totalCourses, 5);
        expect(performance.totalStudents, 120);
      });
    });

    group('getStudentProgress', () {
      test('returns student progress when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/students/student1/progress',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': [
            {
              'course_id': 'course1',
              'title': 'Mathematics',
              'completion_percentage': 90.0,
              'average_grade': 85.0,
              'enrolled_students': 30,
              'completed_students': 27,
              'start_date': '2023-01-01T00:00:00Z',
              'end_date': '2023-12-31T23:59:59Z',
              'top_performers': [],
            },
          ],
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final progress = await analyticsService.getStudentProgress('student1');

        expect(progress, isA<List<CourseProgress>>());
        expect(progress.length, 1);
        expect(progress[0].courseId, 'course1');
        expect(progress[0].title, 'Mathematics');
        expect(progress[0].completionPercentage, 90.0);
      });
    });

    group('getDashboardData', () {
      test('returns dashboard data when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/analytics/dashboard',
          isAuthRequired: true,
          params: {'role': 'admin'},
        )).thenAnswer((_) async => {
          'data': {
            'total_students': 1000,
            'total_teachers': 50,
            'active_courses': 25,
            'completion_rate': 85.0,
            'recent_activity': [
              {'description': 'New student enrolled', 'time': '2 hours ago'},
              {'description': 'Course completed', 'time': '5 hours ago'},
            ],
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final dashboardData = await analyticsService.getDashboardData('admin');

        expect(dashboardData, isA<Map<String, dynamic>>());
        expect(dashboardData['total_students'], 1000);
        expect(dashboardData['total_teachers'], 50);
        expect(dashboardData['active_courses'], 25);
        expect(dashboardData['completion_rate'], 85.0);
      });
    });

    group('generatePerformanceReport', () {
      test('generates performance report when API call is successful', () async {
        // Mock API response
        when(mockApiClient.post(
          '/analytics/performance-report',
          isAuthRequired: true,
          data: {
            'student_id': 'student1',
            'course_id': 'course1',
            'start_date': '2023-01-01T00:00:00Z',
            'end_date': '2023-12-31T23:59:59Z',
          },
        )).thenAnswer((_) async => {
          'data': {
            'report_id': 'report1',
            'generated_at': '2023-12-31T23:59:59Z',
            'student_performance': {
              'student_id': 'student1',
              'name': 'John Doe',
              'overall_score': 85.5,
            },
            'recommendations': ['Focus on mathematics'],
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final startDate = DateTime(2023, 1, 1);
        final endDate = DateTime(2023, 12, 31);

        final report = await analyticsService.generatePerformanceReport(
          studentId: 'student1',
          courseId: 'course1',
          startDate: startDate,
          endDate: endDate,
        );

        expect(report, isA<Map<String, dynamic>>());
        expect(report['report_id'], 'report1');
        expect(report['generated_at'], isA<String>);
      });
    });

    group('exportAnalyticsData', () {
      test('exports analytics data when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/analytics/export',
          isAuthRequired: true,
          params: {
            'format': 'csv',
            'student_id': 'student1',
            'course_id': 'course1',
            'start_date': '2023-01-01T00:00:00Z',
            'end_date': '2023-12-31T23:59:59Z',
          },
        )).thenAnswer((_) async => {
          'data': {
            'export_url': 'https://example.com/analytics_export.csv',
          },
        });

        // Mock the ApiClient.instance
        ApiClientTestHelper.testInstance = mockApiClient;

        final startDate = DateTime(2023, 1, 1);
        final endDate = DateTime(2023, 12, 31);

        final exportUrl = await analyticsService.exportAnalyticsData(
          format: 'csv',
          studentId: 'student1',
          courseId: 'course1',
          startDate: startDate,
          endDate: endDate,
        );

        expect(exportUrl, 'https://example.com/analytics_export.csv');
      });
    });
  });
}