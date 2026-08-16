import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/auth/mfa_setup.dart';

void main() {
  group('MfaSetup Basic Widget Tests', () {
    testWidgets('MfaSetup widget should be created', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Center(
              child: MfaSetup(showBackupCodes: true),
            ),
          ),
        ),
      );

      // Verify the widget is created (this should work without async operations)
      expect(find.byType(MfaSetup), findsOneWidget);
    });

    testWidgets('MfaSetup widget should have proper structure', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Center(
              child: MfaSetup(showBackupCodes: false),
            ),
          ),
        ),
      );

      // Verify the basic structure
      expect(find.byType(MfaSetup), findsOneWidget);
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byType(Center), findsOneWidget);
    });

    testWidgets('MfaSetup widget should accept parameters', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Center(
              child: MfaSetup(
                showBackupCodes: true,
                showRecoveryOptions: true,
              ),
            ),
          ),
        ),
      );

      // Verify the widget is created with parameters
      expect(find.byType(MfaSetup), findsOneWidget);
    });

    testWidgets('MfaSetup widget should work with different themes', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(
            primarySwatch: Colors.red,
            visualDensity: VisualDensity.standard,
          ),
          home: const Scaffold(
            body: Center(
              child: MfaSetup(),
            ),
          ),
        ),
      );

      // Verify the widget works with theme
      expect(find.byType(MfaSetup), findsOneWidget);
    });
  });
}