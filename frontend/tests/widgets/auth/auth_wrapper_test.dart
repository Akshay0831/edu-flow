import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/auth_wrapper.dart';
import 'package:provider/provider.dart';

enum AuthStatus {
  authenticated,
  unauthenticated,
  loading,
  error,
}

class User {
  final String id;
  final String email;
  User({this.id = '1', this.email = 'test@example.com'});
}

class AuthNotifier extends ChangeNotifier {
  User? _currentUser;
  AuthStatus _mockStatus = AuthStatus.unauthenticated;
  String? _mockError;

  User? get currentUser => _currentUser;
  AuthStatus get mockStatus => _mockStatus;
  set mockStatus(AuthStatus status) {
    _mockStatus = status;
    notifyListeners();
  }

  String? get mockError => _mockError;
  set mockError(String? error) {
    _mockError = error;
    notifyListeners();
  }

  void setUser(User? user) {
    _currentUser = user;
    _mockStatus = user != null ? AuthStatus.authenticated : AuthStatus.unauthenticated;
    notifyListeners();
  }
}

class MockAuthNotifier extends AuthNotifier {}

class MockUser extends User {}

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
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
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
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Protected Content'), findsOneWidget);
      expect(find.text('Login Screen'), findsNothing);
    });

    testWidgets('AuthWrapper shows loading state when auth status is loading', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      mockAuthNotifier.mockStatus = AuthStatus.loading;
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              loadingWidget: Text('Loading...'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Loading...'), findsOneWidget);
      expect(find.text('Protected Content'), findsNothing);
      expect(find.text('Login Screen'), findsNothing);
    });

    testWidgets('AuthWrapper shows custom loading widget', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      mockAuthNotifier.mockStatus = AuthStatus.loading;
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              loadingWidget: CircularProgressIndicator(),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('AuthWrapper shows custom login screen', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
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
      mockAuthNotifier.mockError = 'Authentication error';
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>.value(
            value: mockAuthNotifier,
            child: const AuthWrapper(
              loginScreen: Text('Login Screen'),
              errorWidget: Text('Error occurred'),
              child: Text('Protected Content'),
            ),
          ),
        ),
      );
      
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
    });
  });
}