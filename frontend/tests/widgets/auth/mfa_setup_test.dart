import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:edu_flow/data/services/auth_service.dart';
import 'package:edu_flow/presentation/widgets/auth/mfa_setup.dart';
import 'package:edu_flow/data/models/user_model.dart';

// Mock classes
class MockAuthService extends Mock with ChangeNotifier implements AuthService {}

class MockUser extends Mock implements UserModel {}

void main() {
  group('MfaSetup Widget Tests', () {
    late MockAuthService mockAuthService;

    setUp(() {
      mockAuthService = MockAuthService();
    });

    group('Widget Initialization', () {
      testWidgets('MfaSetup widget should display correctly when MFA is disabled', (WidgetTester tester) async {
        // Mock initial state - MFA disabled
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Verify widget displays correctly when MFA is disabled
        expect(find.text('Two-Factor Authentication (MFA)'), findsOneWidget);
        expect(find.byType(ElevatedButton), findsOneWidget);
        expect(find.text('Enable MFA'), findsOneWidget);
      });

      testWidgets('MfaSetup widget should display correctly when MFA is enabled', (WidgetTester tester) async {
        // Mock initial state - MFA enabled
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => true);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Verify widget displays correctly when MFA is enabled
        expect(find.text('Two-Factor Authentication (MFA)'), findsOneWidget);
        expect(find.byType(ElevatedButton), findsOneWidget);
        expect(find.text('Disable MFA'), findsOneWidget);
      });

      testWidgets('MfaSetup widget should show loading state during initialization', (WidgetTester tester) async {
        // Mock loading state
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async {
          await Future.delayed(const Duration(milliseconds: 100));
          return false;
        });
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        // Verify loading state is shown
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
        
        await tester.pumpAndSettle();
        
        // Verify loading state is replaced with actual content
        expect(find.byType(CircularProgressIndicator), findsNothing);
        expect(find.byType(ElevatedButton), findsOneWidget);
      });
    });

    group('MFA Enable Flow', () {
      testWidgets('Enable MFA flow should show QR code setup option', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.enableMfa()).thenAnswer((_) async => {
          'success': true,
          'qr_code_url': 'otpauth://totp/Test:test?secret=ABC123',
          'backup_codes': ['code1', 'code2', 'code3']
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Click Enable MFA button
        await tester.tap(find.text('Enable MFA'));
        await tester.pumpAndSettle();

        // Verify setup options are shown
        expect(find.text('Choose Setup Method'), findsOneWidget);
        expect(find.text('QR Code Setup'), findsOneWidget);
        expect(find.text('Manual Setup'), findsOneWidget);
      });

      testWidgets('QR Code setup should show QR code and verification', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.enableMfa()).thenAnswer((_) async => {
          'success': true,
          'qr_code_url': 'otpauth://totp/Test:test?secret=ABC123',
          'backup_codes': ['code1', 'code2', 'code3']
        });
        when(mockAuthService.verifyMfaToken('123456')).thenAnswer((_) async => {
          'success': true,
          'message': 'MFA verification successful'
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to QR Code setup
        await tester.tap(find.text('Enable MFA'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('QR Code Setup'));
        await tester.pumpAndSettle();

        // Verify QR code setup screen
        expect(find.text('QR Code Setup'), findsOneWidget);
        expect(find.text('Scan this QR code with your authenticator app'), findsOneWidget);
        expect(find.byType(TextFormField), findsOneWidget);
        expect(find.text('Enter verification code'), findsOneWidget);
        expect(find.text('Verify & Save'), findsOneWidget);

        // Enter verification code
        await tester.enterText(find.byType(TextFormField), '123456');
        await tester.tap(find.text('Verify & Save'));
        await tester.pumpAndSettle();

        // Verify success message
        expect(find.text('MFA Enabled Successfully'), findsOneWidget);
        expect(find.text('Backup Codes'), findsOneWidget);
        expect(find.text('Save these codes somewhere safe'), findsOneWidget);
      });

      testWidgets('Manual setup should show secret key and verification', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.enableMfa()).thenAnswer((_) async => {
          'success': true,
          'qr_code_url': 'otpauth://totp/Test:test?secret=ABC123',
          'backup_codes': ['code1', 'code2', 'code3']
        });
        when(mockAuthService.verifyMfaToken('123456')).thenAnswer((_) async => {
          'success': true,
          'message': 'MFA verification successful'
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to Manual setup
        await tester.tap(find.text('Enable MFA'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Manual Setup'));
        await tester.pumpAndSettle();

        // Verify manual setup screen
        expect(find.text('Manual Setup'), findsOneWidget);
        expect(find.text('Enter this secret key in your authenticator app'), findsOneWidget);
        expect(find.byType(TextFormField), findsOneWidget);
        expect(find.text('Enter verification code'), findsOneWidget);
        expect(find.text('Verify & Save'), findsOneWidget);
      });
    });

    group('MFA Disable Flow', () {
      testWidgets('Disable MFA should show confirmation dialog', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => true);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.disableMfa()).thenAnswer((_) async => {
          'success': true,
          'message': 'MFA disabled successfully'
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Click Disable MFA button
        await tester.tap(find.text('Disable MFA'));
        await tester.pumpAndSettle();

        // Verify confirmation dialog
        expect(find.text('Disable MFA?'), findsOneWidget);
        expect(find.text('Are you sure you want to disable two-factor authentication?'), findsOneWidget);
        expect(find.text('Cancel'), findsOneWidget);
        expect(find.text('Disable MFA'), findsOneWidget);
      });

      testWidgets('Disable MFA should complete successfully when confirmed', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => true);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.disableMfa()).thenAnswer((_) async => {
          'success': true,
          'message': 'MFA disabled successfully'
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Start disable process
        await tester.tap(find.text('Disable MFA'));
        await tester.pumpAndSettle();

        // Confirm disable
        await tester.tap(find.text('Disable MFA'));
        await tester.pumpAndSettle();

        // Verify success message
        expect(find.text('MFA Disabled Successfully'), findsOneWidget);
        expect(find.text('Two-factor authentication has been disabled'), findsOneWidget);
      });
    });

    group('Recovery Code Flow', () {
      testWidgets('Recovery code flow should work correctly', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => true);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.generateBackupCodes()).thenAnswer((_) async => {
          'success': true,
          'backup_codes': ['new1', 'new2', 'new3', 'new4', 'new5', 'new6', 'new7', 'new8', 'new9', 'new10']
        });
        when(mockAuthService.verifyRecoveryCode('new1')).thenAnswer((_) async => {
          'success': true,
          'message': 'Recovery code verified successfully'
        });

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Access recovery codes
        await tester.tap(find.byIcon(Icons.key));
        await tester.pumpAndSettle();

        // Verify recovery codes screen
        expect(find.text('Recovery Codes'), findsOneWidget);
        expect(find.text('Save these codes somewhere safe'), findsOneWidget);
        expect(find.byType(ElevatedButton), findsOneWidget);
        expect(find.text('Generate New Recovery Codes'), findsOneWidget);

        // Test verification flow
        await tester.enterText(find.byType(TextFormField), 'new1');
        await tester.tap(find.text('Verify'));
        await tester.pumpAndSettle();

        // Verify success message
        expect(find.text('Recovery code verified successfully'), findsOneWidget);
      });
    });

    group('Error Handling', () {
      testWidgets('Should handle API errors gracefully', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.enableMfa()).thenThrow(Exception('Failed to enable MFA'));

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Attempt to enable MFA
        await tester.tap(find.text('Enable MFA'));
        await tester.pumpAndSettle();

        // Verify error message is shown
        expect(find.text('Failed to enable MFA'), findsOneWidget);
      });

      testWidgets('Should handle network errors gracefully', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');
        when(mockAuthService.enableMfa()).thenThrow(Exception('Network error'));

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Attempt to enable MFA
        await tester.tap(find.text('Enable MFA'));
        await tester.pumpAndSettle();

        // Verify error message is shown
        expect(find.text('Network error'), findsOneWidget);
      });
    });

    group('Accessibility', () {
      testWidgets('All interactive elements should be accessible', (WidgetTester tester) async {
        when(mockAuthService.checkMfaStatus()).thenAnswer((_) async => false);
        when(mockAuthService.getUserRole()).thenAnswer((_) async => 'student');

        await tester.pumpWidget(
          MaterialApp(
            home: ChangeNotifierProvider.value(
              value: mockAuthService,
              child: const MfaSetup(),
            ),
          ),
        );

        await tester.pumpAndSettle();

        // Verify all interactive elements have proper semantics
        expect(tester.getSemantics(find.byType(ElevatedButton)), isNotNull);
        expect(tester.getSemantics(find.byType(TextFormField)), isNotNull);
        expect(tester.getSemantics(find.text('Enable MFA')), isNotNull);
        expect(tester.getSemantics(find.text('Two-Factor Authentication (MFA)')), isNotNull);
      });
    });
  });
}