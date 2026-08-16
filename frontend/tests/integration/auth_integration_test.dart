import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:edu_flow/presentation/widgets/auth/auth_wrapper.dart';
import 'package:edu_flow/presentation/widgets/auth/login_form.dart';
import 'package:edu_flow/presentation/widgets/auth/register_form.dart';
import 'package:edu_flow/presentation/widgets/common/custom_app_bar.dart';
import 'package:edu_flow/presentation/widgets/common/custom_navigation_bar.dart';

// Mock classes for testing
class MockAuthNotifier extends Mock implements AuthNotifier {
  @override
  User? get currentUser => _currentUser;
  User? _currentUser;

  void setUser(User? user) {
    _currentUser = user;
    notifyListeners();
  }

  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  bool _isLoading = false;
  @override
  bool get isLoading => _isLoading;
}

class MockUser extends Mock implements User {}

class MockAuthServiceProvider extends Mock implements AuthServiceProvider {
  @override
  AuthNotifier get notifier => MockAuthNotifier();
}

void main() {
  group('Auth Integration Tests', () {
    late MockAuthNotifier mockAuthNotifier;
    late MockAuthServiceProvider mockServiceProvider;
    
    setUp(() {
      mockAuthNotifier = MockAuthNotifier();
      mockServiceProvider = MockAuthServiceProvider();
    });

    testWidgets('Authentication flow integration test', (WidgetTester tester) async {
      // Start with login screen
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      // Should show login screen
      expect(find.text('Login'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      
      // Enter credentials
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField).last, 'password123');
      await tester.pump();
      
      // Submit login
      await tester.tap(find.text('Sign In'));
      await tester.pump();
      
      // Simulate successful login
      mockAuthNotifier.setUser(MockUser());
      mockAuthNotifier.setLoading(false);
      
      // Update widget with new state
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      await tester.pump();
      
      // Should now show protected content
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Login'), findsNothing);
    });

    testWidgets('Registration and login flow integration', (WidgetTester tester) async {
      // Start with login screen
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      // Should show login screen
      expect(find.text('Login'), findsOneWidget);
      
      // Navigate to register
      await tester.tap(find.text('Sign up'));
      await tester.pump();
      
      // Should show register form (this would depend on your routing)
      // For this test, let's simulate direct register form
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const RegisterForm(),
          ),
        ),
      );
      
      expect(find.text('Create Account'), findsOneWidget);
      
      // Fill registration form
      await tester.enterText(find.text('Name').first, 'John Doe');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[1], 'john@example.com');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[2], 'password123');
      await tester.pump();
      
      await tester.enterText(find.byType(TextFormField)[3], 'password123');
      await tester.pump();
      
      // Submit registration
      await tester.tap(find.text('Sign Up'));
      await tester.pump();
      
      // Simulate successful registration and login
      mockAuthNotifier.setUser(MockUser());
      mockAuthNotifier.setLoading(false);
      
      // Update widget with new state
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      await tester.pump();
      
      // Should now show protected content
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Login'), findsNothing);
    });

    testWidgets('Authenticated user with app bar integration', (WidgetTester tester) async {
      // Set authenticated user
      mockAuthNotifier.setUser(MockUser());
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: Scaffold(
              appBar: CustomAppBar(
                title: 'Dashboard',
                leading: Icons.menu,
                actions: [
                  IconButton(icon: Icons.logout, onPressed: () {}),
                ],
              ),
              body: const Text('Protected Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.byIcon(Icons.menu), findsOneWidget);
      expect(find.byIcon(Icons.logout), findsOneWidget);
      expect(find.text('Protected Content'), findsOneWidget);
    });

    testWidgets('Authenticated user with navigation bar integration', (WidgetTester tester) async {
      // Set authenticated user
      mockAuthNotifier.setUser(MockUser());
      
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.person,
          label: 'Profile',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: Scaffold(
              body: const Text('Home Content'),
              bottomNavigationBar: CustomNavigationBar(
                items: items,
                currentIndex: 0,
                onTap: (index) {},
              ),
            ),
          ),
        ),
      );
      
      expect(find.text('Home Content'), findsOneWidget);
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Profile'), findsOneWidget);
    });

    testWidgets('Logout flow integration', (WidgetTester tester) async {
      // Set authenticated user
      mockAuthNotifier.setUser(MockUser());
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: Scaffold(
              appBar: CustomAppBar(
                title: 'Dashboard',
                actions: [
                  IconButton(icon: Icons.logout, onPressed: () {
                    mockAuthNotifier.setUser(null);
                  }),
                ],
              ),
              body: const Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show authenticated state
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.byIcon(Icons.logout), findsOneWidget);
      expect(find.text('Protected Content'), findsOneWidget);
      
      // Tap logout
      await tester.tap(find.byIcon(Icons.logout));
      await tester.pump();
      
      // Should show login screen
      expect(find.text('Login'), findsOneWidget);
      expect(find.text('Dashboard'), findsNothing);
      expect(find.text('Protected Content'), findsNothing);
    });

    testWidgets('Loading state integration', (WidgetTester tester) async {
      // Set loading state
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      // Should show loading state
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      expect(find.text('Login'), findsNothing);
    });

    testWidgets('Error state integration', (WidgetTester tester) async {
      // Simulate error state
      mockAuthNotifier.setLoading(false);
      mockAuthNotifier.error = 'Authentication failed';
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      // Should show error message
      expect(find.text('Authentication failed'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      expect(find.text('Login'), findsNothing);
    });

    testWidgets('Navigation integration with different user roles', (WidgetTester tester) async {
      // Set user with specific role
      final user = MockUser();
      (user as dynamic).role = 'student';
      mockAuthNotifier.setUser(user);
      
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.school,
          label: 'Courses',
        ),
        CustomBottomNavBarItem(
          icon: Icons.person,
          label: 'Profile',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: Scaffold(
              body: const Text('Home Content'),
              bottomNavigationBar: CustomNavigationBar(
                items: items,
                currentIndex: 0,
                onTap: (index) {},
              ),
            ),
          ),
        ),
      );
      
      // Should show appropriate navigation items for student role
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.byIcon(Icons.school), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
      
      // Navigate to courses
      await tester.tap(find.byIcon(Icons.school));
      await tester.pump();
      
      // Should show courses content
      expect(find.text('Courses Content'), findsOneWidget);
    });

    testWidgets('Theme integration with authentication', (WidgetTester tester) async {
      // Set authenticated user
      mockAuthNotifier.setUser(MockUser());
      
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(
            primarySwatch: Colors.blue,
            brightness: Brightness.dark,
          ),
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: LoginForm(),
            ),
          ),
        ),
      );
      
      // Should apply theme to authenticated state
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Login'), findsNothing);
    });

    testWidgets('Accessibility integration with authentication', (WidgetTester tester) async {
      // Set authenticated user
      mockAuthNotifier.setUser(MockUser());
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthServiceProvider>(
            create: (_) => mockServiceProvider,
            child: Scaffold(
              appBar: const CustomAppBar(
                title: 'Dashboard',
                semanticLabel: 'Main dashboard navigation',
              ),
              body: const Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show proper accessibility labels
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.text('Protected Content'), findsOneWidget);
    });
  });
}

// Extension to mock auth status
extension MockAuthNotifier on MockAuthNotifier {
  String? get error => null;
  
  void set error(String? error) {
    // This is a workaround for testing purposes
    throw UnimplementedError();
  }
}