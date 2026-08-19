import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/data/services/assessment_service.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/assessment_model.dart';

// Mock classes
class MockApiClient extends Mock implements ApiClient {}

void main() {
  group('AssessmentService', () {
    late AssessmentService assessmentService;
    late MockApiClient mockApiClient;

    setUp(() {
      mockApiClient = MockApiClient();
      assessmentService = AssessmentService.internal(mockApiClient);
    });

    group('getAllAssessments', () {
      test('returns list of assessments when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/assessments',
          isAuthRequired: true,
          queryParams: null,
        )).thenAnswer((_) async => {
          'data': [
            {
              'id': '1',
              'title': 'Math Test',
              'description': 'Basic math assessment',
              'max_marks': 100,
              'course_id': 'course1',
              'teacher_id': 'teacher1',
              'due_date': '2023-12-31T23:59:59Z',
              'created_at': '2023-12-01T10:00:00Z',
              'updated_at': '2023-12-01T10:00:00Z',
            },
            {
              'id': '2',
              'title': 'Science Quiz',
              'description': 'Science knowledge quiz',
              'max_marks': 50,
              'course_id': 'course2',
              'teacher_id': 'teacher2',
              'due_date': '2023-12-31T23:59:59Z',
              'created_at': '2023-12-01T10:00:00Z',
              'updated_at': '2023-12-01T10:00:00Z',
            },
          ],
        });

        final assessments = await assessmentService.getAllAssessments();

        expect(assessments, isA<List<AssessmentModel>>());
        expect(assessments.length, 2);
        expect(assessments[0].title, 'Math Test');
        expect(assessments[1].title, 'Science Quiz');
      });

      test('throws ApiException when API response is invalid', () async {
        // Mock invalid API response
        when(mockApiClient.get(
          '/assessments',
          isAuthRequired: true,
          queryParams: null,
        )).thenAnswer((_) async => {
          'data': 'invalid_response',
        });

        expect(
          () async => await assessmentService.getAllAssessments(),
          throwsA(isA<ApiException>()),
        );
      });

      test('throws ApiException when API call fails', () async {
        // Mock API failure
        when(mockApiClient.get(
          '/assessments',
          isAuthRequired: true,
          queryParams: null,
        )).thenThrow(Exception('Network error'));

        expect(
          () async => await assessmentService.getAllAssessments(),
          throwsA(isA<ApiException>()),
        );
      });
    });

    group('getAssessmentById', () {
      test('returns assessment when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/assessments/1',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'id': '1',
            'title': 'Math Test',
            'description': 'Basic math assessment',
            'max_marks': 100,
            'course_id': 'course1',
            'teacher_id': 'teacher1',
            'due_date': '2023-12-31T23:59:59Z',
            'created_at': '2023-12-01T10:00:00Z',
            'updated_at': '2023-12-01T10:00:00Z',
          },
        });

        // Mock the ApiClient.instance
        final assessment = await assessmentService.getAssessmentById('1');

        expect(assessment, isA<AssessmentModel>());
        expect(assessment.id, '1');
        expect(assessment.title, 'Math Test');
      });
    });

    group('createAssessment', () {
      test('creates assessment when API call is successful', () async {
        final assessment = AssessmentModel(
          id: '1',
          title: 'New Test',
          description: 'New assessment description',
          maxMarks: 100,
          courseId: 'course1',
          teacherId: 'teacher1',
          dueDate: DateTime.now(),
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );

        // Mock API response
        when(mockApiClient.post(
          '/assessments',
          isAuthRequired: true,
          data: assessment.toJson(),
        )).thenAnswer((_) async => {
          'data': {
            'id': '1',
            'title': 'New Test',
            'description': 'New assessment description',
            'max_marks': 100,
            'course_id': 'course1',
            'teacher_id': 'teacher1',
            'due_date': assessment.dueDate.toIso8601String(),
            'created_at': assessment.createdAt.toIso8601String(),
            'updated_at': assessment.updatedAt.toIso8601String(),
          },
        });

        // Mock the ApiClient.instance
        final createdAssessment = await assessmentService.createAssessment(assessment);

        expect(createdAssessment, isA<AssessmentModel>());
        expect(createdAssessment.id, '1');
        expect(createdAssessment.title, 'New Test');
      });
    });

    group('submitGrade', () {
      test('submits grade when API call is successful', () async {
        // Mock API response
        when(mockApiClient.post(
          '/assessments/1/grades',
          isAuthRequired: true,
          data: {
            'student_id': 'student1',
            'marks': 85,
            'feedback': 'Good work',
          },
        )).thenAnswer((_) async => {
          'data': {
            'id': '1',
            'assessment_id': '1',
            'student_id': 'student1',
            'marks': 85,
            'feedback': 'Good work',
            'status': 'graded',
            'submitted_at': DateTime.now().toIso8601String(),
            'graded_at': DateTime.now().toIso8601String(),
          },
        });

        final submission = await assessmentService.submitGrade(
          '1',
          'student1',
          85,
          feedback: 'Good work',
        );

        expect(submission, isA<AssessmentSubmission>());
        expect(submission.id, '1');
        expect(submission.marks, 85);
        expect(submission.feedback, 'Good work');
      });
    });

    group('calculateStudentGrades', () {
      test('calculates student grades when API call is successful', () async {
        // Mock API response
        when(mockApiClient.get(
          '/students/student1/grades/calculate',
          isAuthRequired: true,
        )).thenAnswer((_) async => {
          'data': {
            'student_id': 'student1',
            'course_id': 'course1',
            'assessment_grades': [
              {
                'assessment_id': '1',
                'title': 'Math Test',
                'marks': 85,
                'max_marks': 100,
                'percentage': 85,
                'grade': 'A',
                'graded_at': DateTime.now().toIso8601String(),
              },
            ],
            'total_score': 85,
            'final_grade': 'A',
            'percentage': 85,
            'letter_grade': 'A',
          },
        });

        // Mock the ApiClient.instance
        final gradeCalculation = await assessmentService.calculateStudentGrades('student1');

        expect(gradeCalculation, isA<GradeCalculation>());
        expect(gradeCalculation.studentId, 'student1');
        expect(gradeCalculation.finalGrade, 'A');
        expect(gradeCalculation.percentage, 85);
      });
    });
  });
}