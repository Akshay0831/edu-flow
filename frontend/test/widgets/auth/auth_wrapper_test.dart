import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/auth/auth_wrapper.dart';
import 'package:provider/provider.dart';

class AuthNotifier extends ChangeNotifier {
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;

  void setUser(User? user) {
    _currentUser = user;
    notifyListeners();
  }

  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void setError(String? error) {
    _error = error;
    notifyListeners();
  }
}

class User {
  final String id;
  final String name;
  final String email;

  User({
    required this.id,
    required this.name,
    required this.email,
  });
}

class MockAuthNotifier extends AuthNotifier {}

class MockUser extends User {
  MockUser() : super(id: '1', name: 'Test User', email: 'test@example.com');
}

void main() {
  group('AuthWrapper Widget Tests', () {
    late MockAuthNotifier mockAuthNotifier;
    
    setUp(() {
      mockAuthNotifier = MockAuthNotifier();
    });

    testWidgets('AuthWrapper shows login screen when user is not authenticated', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show login screen when user is null
      expect(find.text('Login Screen'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
    });

    testWidgets('AuthWrapper shows protected content when user is authenticated', (WidgetTester tester) async {
      final mockUser = MockUser();
      mockAuthNotifier.setUser(mockUser);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show protected content when user is not null
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Login Screen'), findsNothing);
    });

    testWidgets('AuthWrapper shows loading state when auth status is loading', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              loadingWidget: Text('Loading...'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show loading widget
      expect(find.text('Loading...'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      expect(find.text('Login Screen'), findsNothing);
    });

    testWidgets('AuthWrapper shows custom loading widget', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      mockAuthNotifier.setLoading(true);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              loadingWidget: CircularProgressIndicator(),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show custom loading widget
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('AuthWrapper shows custom login screen', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Custom Login Screen'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Custom Login Screen'), findsOneWidget);
    });

    testWidgets('AuthWrapper shows custom error widget', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      mockAuthNotifier.setError('Authentication error');
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              errorWidget: Text('Error occurred'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      // Should show error widget
      expect(find.text('Error occurred'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      expect(find.text('Login Screen'), findsNothing);
    });

    testWidgets('AuthWrapper redirects to custom login route when onAuthRequired is called', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      
      await tester.pumpWidget(
        MaterialApp(
          routes: {
            '/login': (context) => const Text('Login Route'),
            '/': (context) => const AuthWrapper(
              loginScreen: Text('Login Screen'),
              child: Text('Protected Content'),
            ),
          },
        ),
      );
      
      expect(find.text('Protected Content'), findsOneWidget);
      
      // Simulate auth required
      await tester.pump();
      await tester.tap(find.byType(IconButton));
      await tester.pump();
      
      expect(find.text('Login Route'), findsOneWidget);
    });
  });
}

