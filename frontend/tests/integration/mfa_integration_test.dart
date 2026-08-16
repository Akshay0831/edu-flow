import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:edu_flow/presentation/widgets/auth/mfa_setup.dart';
import 'mocks.mockito.dart';

void main() {
  group('MFA Integration Tests', () {
    late MockAuthService mockAuthService;

    setUp(() {
      mockAuthService = MockAuthService();
    });

    testWidgets('MfaSetup widget should load and display correctly', (WidgetTester tester) async {
      // Mock initial state
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

      // Wait for loading to complete
      await tester.pumpAndSettle();

      // Verify widget is loaded
      expect(find.byType(MfaSetup), findsOneWidget);
      expect(find.text('Two-Factor Authentication (MFA)'), findsOneWidget);
    });

    testWidgets('MFA should be enabled successfully', (WidgetTester tester) async {
      // Mock MFA disabled initially
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

      // Tap Enable MFA button
      await tester.tap(find.text('Enable MFA'));
      await tester.pumpAndSettle();

      // Verify setup options appear
      expect(find.text('Choose Setup Method'), findsOneWidget);
      
      // Tap QR Code Setup
      await tester.tap(find.text('QR Code Setup'));
      await tester.pumpAndSettle();

      // Verify QR code setup screen
      expect(find.text('QR Code Setup'), findsOneWidget);
      expect(find.text('Enter verification code'), findsOneWidget);

      // Enter verification code and verify
      await tester.enterText(find.byType(TextFormField), '123456');
      await tester.tap(find.text('Verify & Save'));
      await tester.pumpAndSettle();

      // Verify success message
      expect(find.text('MFA Enabled Successfully'), findsOneWidget);
    });

    testWidgets('MFA should be disabled successfully', (WidgetTester tester) async {
      // Mock MFA enabled initially
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

      // Tap Disable MFA button
      await tester.tap(find.text('Disable MFA'));
      await tester.pumpAndSettle();

      // Verify confirmation dialog
      expect(find.text('Disable MFA?'), findsOneWidget);
      expect(find.text('Are you sure you want to disable two-factor authentication?'), findsOneWidget);

      // Confirm disable
      await tester.tap(find.text('Disable MFA'));
      await tester.pumpAndSettle();

      // Verify success message
      expect(find.text('MFA Disabled Successfully'), findsOneWidget);
    });

    testWidgets('Error handling should work correctly', (WidgetTester tester) async {
      // Mock error case
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

      // Attempt to enable MFA and verify error handling
      await tester.tap(find.text('Enable MFA'));
      await tester.pumpAndSettle();

      // Verify error message is shown
      expect(find.text('Failed to enable MFA'), findsOneWidget);
    });

    testWidgets('Loading states should be handled correctly', (WidgetTester tester) async {
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

      // Verify loading indicator is shown initially
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      
      // Wait for loading to complete
      await tester.pumpAndSettle();
      
      // Verify loading indicator is replaced with content
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });
  });
}