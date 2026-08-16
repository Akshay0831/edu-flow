import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/auth/mfa_setup.dart';
import 'package:mockito/mockito.dart';

class MockAuthNotifier extends Mock implements AuthNotifier {
  @override
  bool get isMfaEnabled => _isMfaEnabled;
  bool _isMfaEnabled = false;
  
  @override
  Future<void> enableMfa(String code) async {}
  @override
  Future<void> disableMfa(String password) async {}
  
  void setMfaEnabled(bool enabled) {
    _isMfaEnabled = enabled;
    notifyListeners();
  }
}

class MockAuthServiceProvider extends Mock implements AuthServiceProvider {
  @override
  AuthNotifier get notifier => MockAuthNotifier();
}

void main() {
  group('MfaSetup Widget Tests', () {
    late MockAuthNotifier mockAuthNotifier;
    late MockAuthServiceProvider mockServiceProvider;
    
    setUp(() {
      mockAuthNotifier = MockAuthNotifier();
      mockServiceProvider = MockAuthServiceProvider();
    });

    testWidgets('MfaSetup shows setup screen when MFA is disabled', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      expect(find.text('Enable Two-Factor Authentication'), findsOneWidget);
      expect(find.text('Scan QR Code'), findsOneWidget);
      expect(find.text('Setup with Code'), findsOneWidget);
    });

    testWidgets('MfaSetup shows disable screen when MFA is enabled', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      expect(find.text('Disable Two-Factor Authentication'), findsOneWidget);
      expect(find.text('Confirm with Password'), findsOneWidget);
    });

    testWidgets('MfaSetup responds to QR code setup selection', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.tap(find.text('Scan QR Code'));
      await tester.pump();
      
      expect(find.text('QR Code Setup'), findsOneWidget);
      expect(find.text('Setup with Code'), findsNothing);
    });

    testWidgets('MfaSetup responds to code setup selection', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.tap(find.text('Setup with Code'));
      await tester.pump();
      
      expect(find.text('Setup with Code'), findsOneWidget);
      expect(find.text('QR Code Setup'), findsNothing);
    });

    testWidgets('MfaSetup validates MFA code format', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      // Switch to code setup for testing
      await tester.tap(find.text('Setup with Code'));
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField), '12345'); // Invalid format
      await tester.pump();
      
      await tester.tap(find.text('Enable MFA'));
      await tester.pump();
      
      // Should show error for invalid code format
      expect(find.text('Please enter a valid MFA code'), findsOneWidget);
    });

    testWidgets('MfaSetup validates MFA code length', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      // Switch to code setup for testing
      await tester.tap(find.text('Setup with Code'));
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField), '123'); // Too short
      await tester.pump();
      
      await tester.tap(find.text('Enable MFA'));
      await tester.pump();
      
      // Should show error for code too short
      expect(find.text('MFA code must be 6 digits'), findsOneWidget);
    });

    testWidgets('MfaSetup shows loading state during setup', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      // Switch to code setup for testing
      await tester.tap(find.text('Setup with Code'));
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField), '123456');
      
      // Simulate loading state
      await tester.tap(find.text('Enable MFA'));
      await tester.pump();
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Enable MFA'), findsNothing);
    });

    testWidgets('MfaSetup shows success message on successful setup', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      // Switch to code setup for testing
      await tester.tap(find.text('Setup with Code'));
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField), '123456');
      
      // Simulate successful setup
      await tester.tap(find.text('Enable MFA'));
      await tester.pump();
      
      // Should show success message
      expect(find.text('MFA enabled successfully'), findsOneWidget);
    });

    testWidgets('MfaSetup validates password for disabling', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField), 'wrong-password');
      await tester.pump();
      
      await tester.tap(find.text('Disable MFA'));
      await tester.pump();
      
      // Should show error for wrong password
      expect(find.text('Incorrect password'), findsOneWidget);
    });

    testWidgets('MfaSetup shows loading state during disabling', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField), 'correct-password');
      
      // Simulate loading state
      await tester.tap(find.text('Disable MFA'));
      await tester.pump();
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Disable MFA'), findsNothing);
    });

    testWidgets('MfaSetup shows success message on successful disabling', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField), 'correct-password');
      
      // Simulate successful disabling
      await tester.tap(find.text('Disable MFA'));
      await tester.pump();
      
      // Should show success message
      expect(find.text('MFA disabled successfully'), findsOneWidget);
    });

    testWidgets('MfaSetup shows backup codes when MFA is enabled', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(showBackupCodes: true),
          ),
        ),
      );
      
      expect(find.text('Backup Codes'), findsOneWidget);
      expect(find.text('Save these codes'), findsOneWidget);
    });

    testWidgets('MfaSetup allows copying backup codes', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(showBackupCodes: true),
          ),
        ),
      );
      
      await tester.tap(find.text('Copy Codes'));
      await tester.pump();
      
      // Should copy codes to clipboard
      // This would depend on your clipboard implementation
    });

    testWidgets('MfaSetup shows recovery options when needed', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(showRecoveryOptions: true),
          ),
        ),
      );
      
      expect(find.text('Lost Authenticator?'), findsOneWidget);
      expect(find.text('Use Backup Codes'), findsOneWidget);
    });

    testWidgets('MfaSetup handles recovery code input', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(showRecoveryOptions: true),
          ),
        ),
      );
      
      await tester.tap(find.text('Use Backup Codes'));
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField), 'backup123');
      await tester.pump();
      
      await tester.tap(find.text('Verify'));
      await tester.pump();
      
      // Should handle recovery code verification
      // This would depend on your recovery code implementation
    });

    testWidgets('MfaSetup shows help information', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      expect(find.text('What is 2FA?'), findsOneWidget);
      expect(find.text('How to set up'), findsOneWidget);
    });

    testWidgets('MfaSetup responds to help taps', (WidgetTester tester) async {
      mockAuthNotifier.setMfaEnabled(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const MfaSetup(),
          ),
        ),
      );
      
      await tester.tap(find.text('What is 2FA?'));
      await tester.pump();
      
      // Should show help information
      // This would depend on your help implementation
    });
  });
}