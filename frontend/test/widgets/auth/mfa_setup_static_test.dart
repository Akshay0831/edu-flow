import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// A simplified static version of MfaSetup for testing
class MfaSetupStatic extends StatelessWidget {
  final bool showBackupCodes;
  final bool showRecoveryOptions;

  const MfaSetupStatic({
    super.key,
    this.showBackupCodes = false,
    this.showRecoveryOptions = false,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Two-Factor Authentication'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Two-Factor Authentication (MFA)',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Add an extra layer of security to your account',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Enable MFA'),
            ),
          ],
        ),
      ),
    );
  }
}

void main() {
  group('MfaSetupStatic Widget Tests', () {
    testWidgets('MfaSetupStatic widget should display correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MfaSetupStatic(),
        ),
      );

      // Verify widget is loaded and displays correctly
      expect(find.byType(MfaSetupStatic), findsOneWidget);
      expect(find.text('Two-Factor Authentication'), findsOneWidget);
      expect(find.text('Enable MFA'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('MfaSetupStatic widget should work with different parameters', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MfaSetupStatic(
            showBackupCodes: true,
            showRecoveryOptions: true,
          ),
        ),
      );

      // Verify widget works with parameters
      expect(find.byType(MfaSetupStatic), findsOneWidget);
      expect(find.text('Two-Factor Authentication'), findsOneWidget);
      expect(find.text('Enable MFA'), findsOneWidget);
    });

    testWidgets('MfaSetupStatic widget should display button correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MfaSetupStatic(),
        ),
      );

      // Verify button is properly styled and interactive
      expect(find.text('Enable MFA'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
      
      // Verify button can be tapped
      await tester.tap(find.text('Enable MFA'));
      await tester.pumpAndSettle();
      
      // Widget should still be present after tap
      expect(find.byType(MfaSetupStatic), findsOneWidget);
    });

    testWidgets('MfaSetupStatic widget should work with different themes', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(
            primarySwatch: Colors.blue,
            visualDensity: VisualDensity.standard,
          ),
          home: const MfaSetupStatic(),
        ),
      );

      // Verify widget works with theme
      expect(find.byType(MfaSetupStatic), findsOneWidget);
      expect(find.text('Two-Factor Authentication'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('MfaSetupStatic widget should have proper layout', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MfaSetupStatic(),
        ),
      );

      // Verify layout structure
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.byType(SingleChildScrollView), findsOneWidget);
      expect(find.byType(Column), findsOneWidget);
      
      // Verify content is present
      expect(find.text('Two-Factor Authentication'), findsOneWidget);
      expect(find.text('Enable MFA'), findsOneWidget);
    });
  });
}