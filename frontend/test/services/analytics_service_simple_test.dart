import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/data/services/analytics_service.dart';

void main() {
  group('AnalyticsService', () {
    late AnalyticsService analyticsService;

    setUp(() {
      analyticsService = AnalyticsService();
    });

    test('creates service successfully', () {
      expect(analyticsService, isA<AnalyticsService>());
    });

    // Skip the test with actual API call for now
    test('getDashboardData requires API connectivity', () async {
      // This test would require actual API connection or more complex mocking
      // For now, just test that the method exists
      expect(analyticsService.getDashboardData, isA<Function>());
    });
  });
}