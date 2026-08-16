import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/data/services/assessment_service.dart';

void main() {
  group('AssessmentService', () {
    late AssessmentService assessmentService;

    setUp(() {
      assessmentService = AssessmentService();
    });

    test('creates service successfully', () {
      expect(assessmentService, isA<AssessmentService>());
    });

    // Skip the test with actual API call for now
    test('getAllAssessments method exists', () {
      expect(assessmentService.getAllAssessments, isA<Function>());
    });
  });
}