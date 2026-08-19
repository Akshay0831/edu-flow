import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:edu_flow/presentation/widgets/auth/login_form.dart';

// Mock classes
class MockAuthNotifier extends ChangeNotifier {
  bool _isLoading = false;
  
  bool get isLoading => _isLoading;
  
  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }
  
  Future<void> login(String email, String password, {bool rememberMe = false}) async {
    setLoading(true);
    await Future.delayed(const Duration(milliseconds: 500));
    setLoading(false);
  }
}

class MockAuthServiceProvider extends ChangeNotifier {
  MockAuthNotifier get notifier => MockAuthNotifier();
}

void main() {
  group('LoginForm Widget Tests', () {
    late MockAuthNotifier mockAuthNotifier;
    late MockAuthServiceProvider mockServiceProvider;
    
    setUp(() {
      mockAuthNotifier = MockAuthNotifier();
      mockServiceProvider = MockAuthServiceProvider();
    });

    testWidgets('LoginForm displays form fields correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      expect(find.text('Login'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Remember me'), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });

    testWidgets('LoginForm responds to text input', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField).last, 'password123');
      await tester.pump();
      
      expect(find.text('test@example.com'), findsOneWidget);
      expect(find.text('password123'), findsOneWidget);
    });

    testWidgets('LoginForm validates email format', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField).first, 'invalid-email');
      await tester.pump();
      
      await tester.tap(find.text('Sign In'));
      await tester.pump();
      
      // Should show error for invalid email format
      expect(find.text('Please enter a valid email address'), findsOneWidget);
    });

    testWidgets('LoginForm validates password length', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField).last, '123'); // Too short
      await tester.pump();
      
      await tester.tap(find.text('Sign In'));
      await tester.pump();
      
      // Should show error for password too short
      expect(find.text('Password must be at least 6 characters'), findsOneWidget);
    });

    testWidgets('LoginForm shows loading state', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Sign In'), findsNothing);
    });

    testWidgets('LoginForm disables form when loading', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      // Should not respond to taps when loading
      await tester.tap(find.text('Sign In'));
      await tester.pump();
      
      // Still should show loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('LoginForm toggles remember me checkbox', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      expect(find.byType(Checkbox).first, findsOneWidget);
      
      // Initially not checked
      expect(tester.widget<Checkbox>(find.byType(Checkbox).first).value, false);
      
      // Tap to check
      await tester.tap(find.byType(Checkbox).first);
      await tester.pump();
      
      expect(tester.widget<Checkbox>(find.byType(Checkbox).first).value, true);
    });

    testWidgets('LoginForm shows error message on login failure', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.enterText(find.byType(TextFormField).last, 'password123');
      await tester.pump();
      
      // Simulate login error
      await tester.tap(find.text('Sign In'));
      await tester.pump();
      
      // Should show error message
      expect(find.text('Invalid email or password'), findsOneWidget);
    });

    testWidgets('LoginForm navigates to forgot password', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.tap(find.text('Forgot password?'));
      await tester.pump();
      
      // Should navigate to forgot password screen
      // This would depend on your routing setup
    });

    testWidgets('LoginForm shows sign up link', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      expect(find.text('Don\'t have an account?'), findsOneWidget);
      expect(find.text('Sign up'), findsOneWidget);
    });

    testWidgets('LoginForm navigates to sign up', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(),
          ),
        ),
      );
      
      await tester.tap(find.text('Sign up'));
      await tester.pump();
      
      // Should navigate to sign up screen
      // This would depend on your routing setup
    });

    testWidgets('LoginForm shows social login options', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(showSocialLogin: true),
          ),
        ),
      );
      
      expect(find.text('Or continue with'), findsOneWidget);
      expect(find.text('Google'), findsOneWidget);
      expect(find.text('Facebook'), findsOneWidget);
    });

    testWidgets('LoginForm responds to social login taps', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<MockAuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const LoginForm(showSocialLogin: true),
          ),
        ),
      );
      
      await tester.tap(find.text('Google'));
      await tester.pump();
      
      // Should handle Google login
      // This would depend on your Google sign-in implementation
      
      await tester.tap(find.text('Facebook'));
      await tester.pump();
      
      // Should handle Facebook login
      // This would depend on your Facebook sign-in implementation
    });
  });
}