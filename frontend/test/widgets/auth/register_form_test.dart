import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/auth/register_form.dart';
import 'package:mockito/mockito.dart';

class MockAuthNotifier extends Mock implements AuthNotifier {
  @override
  Future<void> register(String email, String password, String name, String? role) async {}
  
  @override
  bool get isLoading => _isLoading;
  bool _isLoading = false;
  
  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }
}

class MockAuthServiceProvider extends Mock implements AuthServiceProvider {
  @override
  AuthNotifier get notifier => MockAuthNotifier();
}

void main() {
  group('RegisterForm Widget Tests', () {
    late MockAuthNotifier mockAuthNotifier;
    late MockAuthServiceProvider mockServiceProvider;
    
    setUp(() {
      mockAuthNotifier = MockAuthNotifier();
      mockServiceProvider = MockAuthServiceProvider();
    });

    testWidgets('RegisterForm displays form fields correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      expect(find.text('Create Account'), findsOneWidget);
      expect(find.text('Name'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Confirm Password'), findsOneWidget);
      expect(find.text('Sign Up'), findsOneWidget);
    });

    testWidgets('RegisterForm responds to text input', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[3], 'password123');
      await tester.pump();
      
      expect(find.text('John Doe'), findsOneWidget);
      expect(find.text('john@example.com'), findsOneWidget);
      expect(find.text('password123'), findsNWidgets(2));
    });

    testWidgets('RegisterForm validates name field', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'J'); // Too short
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for name too short
      expect(find.text('Name must be at least 2 characters'), findsOneWidget);
    });

    testWidgets('RegisterForm validates email format', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'invalid-email');
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for invalid email format
      expect(find.text('Please enter a valid email address'), findsOneWidget);
    });

    testWidgets('RegisterForm validates password strength', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.enterText(find.byType(TextFormField)[2], '123'); // Too short
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for password too short
      expect(find.text('Password must be at least 6 characters'), findsOneWidget);
    });

    testWidgets('RegisterForm validates password match', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.enterText(find.byType(TextFormField)[3], 'differentpassword');
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for password mismatch
      expect(find.text('Passwords do not match'), findsOneWidget);
    });

    testWidgets('RegisterForm shows loading state', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Sign Up'), findsNothing);
    });

    testWidgets('RegisterForm disables form when loading', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      // Should not respond to taps when loading
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Still should show loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('RegisterForm shows error message on registration failure', (WidgetTester tester) async {
      mockAuthNotifier.setLoading(false);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.enterText(find.byType(TextFormField)[3], 'password123');
      await tester.pump();
      
      // Simulate registration error
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error message
      expect(find.text('Registration failed. Please try again.'), findsOneWidget);
    });

    testWidgets('RegisterForm shows role selection when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(showRoleSelection: true),
          ),
        ),
      );
      
      expect(find.text('Role'), findsOneWidget);
      expect(find.text('Student'), findsOneWidget);
      expect(find.text('Teacher'), findsOneWidget);
      expect(find.text('Admin'), findsOneWidget);
    });

    testWidgets('RegisterForm validates role selection', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(showRoleSelection: true),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.enterText(find.byType(TextFormField)[3], 'password123');
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for role not selected
      expect(find.text('Please select a role'), findsOneWidget);
    });

    testWidgets('RegisterForm shows terms and conditions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(showTerms: true),
          ),
        ),
      );
      
      expect(find.text('I agree to the Terms and Conditions'), findsOneWidget);
      expect(find.text('Sign Up'), findsOneWidget);
    });

    testWidgets('RegisterForm validates terms acceptance', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(showTerms: true),
          ),
        ),
      );
      
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.enterText(find.byType(TextFormField)[3], 'password123');
      await tester.pump();
      
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Should show error for terms not accepted
      expect(find.text('You must accept the terms and conditions'), findsOneWidget);
    });

    testWidgets('RegisterForm shows login link', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      expect(find.text('Already have an account?'), findsOneWidget);
      expect(find.text('Log in'), findsOneWidget);
    });

    testWidgets('RegisterForm navigates to login', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      await tester.tap(find.text('Log in'));
      await tester.pump();
      
      // Should navigate to login screen
      // This would depend on your routing setup
    });
  });
}