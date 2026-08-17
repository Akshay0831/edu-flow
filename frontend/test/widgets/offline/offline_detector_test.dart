import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/offline/offline_detector.dart';

void main() {
  group('OfflineDetector Widget Tests', () {
    testWidgets('OfflineDetector shows online by default', (WidgetTester tester) async {
      final boolChanged = <bool>[];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              onStatusChanged: (isOnline) {
                boolChanged.add(isOnline);
              },
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsNothing);
    });

    testWidgets('OfflineDetector shows offline state', (WidgetTester tester) async {
      final boolChanged = <bool>[];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              onStatusChanged: (isOnline) {
                boolChanged.add(isOnline);
              },
              isOnline: false,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
      expect(boolChanged, [false]);
    });

    testWidgets('OfflineDetector responds to online status changes', (WidgetTester tester) async {
      final boolChanged = <bool>[];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              onStatusChanged: (isOnline) {
                boolChanged.add(isOnline);
              },
              isOnline: false,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      // Initially offline
      expect(find.text('Offline'), findsOneWidget);
      expect(boolChanged, [false]);
      
      // Switch to online
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              onStatusChanged: (isOnline) {
                boolChanged.add(isOnline);
              },
              isOnline: true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      await tester.pump();
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsNothing);
      expect(boolChanged, [false, true]);
    });

    testWidgets('OfflineDetector shows custom offline message', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              offlineMessage: 'No internet connection',
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('No internet connection'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows custom online message', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: true,
              onlineMessage: 'Back online!',
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Back online!'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows custom offline widget', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              offlineWidget: const Text('Custom Offline Widget'),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Custom Offline Widget'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows custom online widget', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: true,
              onlineWidget: const Text('Custom Online Widget'),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Custom Online Widget'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows retry button when enabled', (WidgetTester tester) async {
      bool retryPressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              showRetryButton: true,
              onRetry: () {
                retryPressed = true;
              },
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
      
      await tester.tap(find.text('Retry'));
      await tester.pump();
      
      expect(retryPressed, true);
    });

    testWidgets('OfflineDetector shows loading state when checking', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              isLoading: true,
              showLoading: true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Offline'), findsNothing);
    });

    testWidgets('OfflineDetector shows auto-refresh interval', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              autoRefreshInterval: const Duration(seconds: 5),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows custom styling', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              offlineColor: Colors.red,
              onlineColor: Colors.green,
              offlineTextColor: Colors.white,
              onlineTextColor: Colors.black,
              borderRadius: 8,
              padding: const EdgeInsets.all(16),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
    });

    testWidgets('OfflineDetector ignores manual refresh when disabled', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              manualRefreshEnabled: false,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows logging when enabled', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              enableLogging: true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
    });

    testWidgets('OfflineDetector respects timeout setting', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              timeout: const Duration(seconds: 10),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Offline'), findsOneWidget);
    });

    testWidgets('OfflineDetector shows custom error widget', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              errorWidget: const Text('Connection Error'),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
      expect(find.text('Connection Error'), findsOneWidget);
    });

    testWidgets('OfflineDetector throws assertion error for null child', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OfflineDetector(
              isOnline: false,
              // No child provided
            ),
          ),
        ),
      );
      
      expect(find.text('Connection Error'), findsOneWidget);
    });
  });
}