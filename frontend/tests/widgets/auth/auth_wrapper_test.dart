import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/auth/auth_wrapper.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

// Mock classes for testing
class MockAuthNotifier extends Mock implements AuthNotifier {
  @override
  User? get currentUser => _currentUser;
  User? _currentUser;

  void setUser(User? user) {
    _currentUser = user;
    notifyListeners();
  }
}

class MockUser extends Mock implements User {}

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
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
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
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
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
      (mockAuthNotifier as Mock).mockStatus = AuthStatus.loading;
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
              loadingWidget: Text('Loading...'),
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
      (mockAuthNotifier as Mock).mockStatus = AuthStatus.loading;
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
              loadingWidget: CircularProgressIndicator(),
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
              child: Text('Protected Content'),
              loginScreen: Text('Custom Login Screen'),
            ),
          ),
        ),
      );
      
      expect(find.text('Custom Login Screen'), findsOneWidget);
    });

    testWidgets('AuthWrapper shows custom error widget', (WidgetTester tester) async {
      mockAuthNotifier.setUser(null);
      (mockAuthNotifier as Mock).mockError = 'Authentication error';
      
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthNotifier>(
            create: (_) => mockAuthNotifier,
            child: const AuthWrapper(
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
              errorWidget: Text('Error occurred'),
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
              child: Text('Protected Content'),
              loginScreen: Text('Login Screen'),
            ),
          },
        ),
      );
      
      expect(find.text('Protected Content'), findsOneWidget);
      
      // Simulate auth required
      await tester.pumpNamed('/login');
      
      expect(find.text('Login Route'), findsOneWidget);
    });
  });
}

// Extension to mock auth status
extension MockAuthNotifier on MockAuthNotifier {
  AuthStatus get mockStatus {
    // This is a workaround for testing purposes
    throw UnimplementedError();
  }
  
  void set mockStatus(AuthStatus status) {
    // This is a workaround for testing purposes
    throw UnimplementedError();
  }
  
  String? get mockError => null;
  
  void set mockError(String? error) {
    // This is a workaround for testing purposes
    throw UnimplementedError();
  }
}