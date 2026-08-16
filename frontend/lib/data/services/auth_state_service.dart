import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';

class AuthState {
  final bool isAuthenticated;
  final String? token;
  final String? refreshToken;
  final String? userRole;
  final String? userId;
  final String? userName;
  final String? userEmail;
  final DateTime? lastUpdated;

  const AuthState({
    this.isAuthenticated = false,
    this.token,
    this.refreshToken,
    this.userRole,
    this.userId,
    this.userName,
    this.userEmail,
    this.lastUpdated,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    String? token,
    String? refreshToken,
    String? userRole,
    String? userId,
    String? userName,
    String? userEmail,
    DateTime? lastUpdated,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      token: token ?? this.token,
      refreshToken: refreshToken ?? this.refreshToken,
      userRole: userRole ?? this.userRole,
      userId: userId ?? this.userId,
      userName: userName ?? this.userName,
      userEmail: userEmail ?? this.userEmail,
      lastUpdated: lastUpdated ?? DateTime.now(),
    );
  }

  AuthState reset() {
    return const AuthState(
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      userRole: null,
      userId: null,
      userName: null,
      userEmail: null,
    );
  }

  // Role-based access control getters
  bool get isAdmin => userRole?.toLowerCase() == 'admin';
  bool get isTeacher => userRole?.toLowerCase() == 'teacher';
  bool get isStudent => userRole?.toLowerCase() == 'student';
}

class AuthStateService extends StateNotifier<AuthState> {
  AuthStateService() : super(const AuthState());
  final ApiClient _apiClient = ApiClient.instance;

  // Initialize auth state from secure storage
  Future<void> initialize() async {
    try {
      final isAuthenticated = await _apiClient.isAuthenticated();
      final userRole = await _apiClient.getUserRole();
      
      if (isAuthenticated && userRole.isNotEmpty) {
        state = state.copyWith(
          isAuthenticated: true,
          userRole: userRole,
          lastUpdated: DateTime.now(),
        );
      }
    } catch (e) {
      // If initialization fails, reset state
      state = state.reset();
    }
  }

  // Update authentication state
  Future<void> updateAuthState({
    String? token,
    String? refreshToken,
    String? userRole,
    String? userId,
    String? userName,
    String? userEmail,
  }) async {
    state = state.copyWith(
      isAuthenticated: token != null && token.isNotEmpty && userRole != null && userRole.isNotEmpty,
      token: token,
      refreshToken: refreshToken,
      userRole: userRole,
      userId: userId,
      userName: userName,
      userEmail: userEmail,
      lastUpdated: DateTime.now(),
    );
  }

  // Clear authentication state
  Future<void> clearAuthState() async {
    try {
      await _apiClient.clearAuthTokens();
    } catch (e) {
      // Ignore errors during clear
    }
    state = state.reset();
  }

  // Get current user role
  String? getCurrentUserRole() {
    return state.userRole;
  }

  // Check if user has specific role
  bool hasRole(String requiredRole) {
    return state.userRole == requiredRole;
  }

  // Check if user is admin
  bool get isAdmin => hasRole('admin');

  // Check if user is teacher
  bool get isTeacher => hasRole('teacher');

  // Check if user is student
  bool get isStudent => hasRole('student');

  // Get user ID
  String? getUserId() {
    return state.userId;
  }

  // Get user name
  String? getUserName() {
    return state.userName;
  }

  // Get user email
  String? getUserEmail() {
    return state.userEmail;
  }

  // Check if authenticated
  bool get isAuthenticated => state.isAuthenticated;

  // Get token (for API calls)
  Future<String?> getAuthToken() async {
    return await _apiClient.getAuthToken();
  }

  // Refresh token
  Future<void> refreshToken() async {
    try {
      await _apiClient.refreshAccessToken();
      // Update state with new tokens (API client already saved them)
      final newToken = await _apiClient.getAuthToken();
      final newRefreshToken = await _apiClient.getRefreshToken();
      final userRole = await _apiClient.getUserRole();
      
      state = state.copyWith(
        token: newToken,
        refreshToken: newRefreshToken,
        userRole: userRole,
        lastUpdated: DateTime.now(),
      );
    } catch (e) {
      // If refresh fails, clear state
      await clearAuthState();
      throw ApiException(message: 'Token refresh failed: ${e.toString()}');
    }
  }
}

// Create providers for dependency injection
final authStateServiceProvider = StateNotifierProvider<AuthStateService, AuthState>((ref) {
  return AuthStateService();
});

// Provider for checking authentication
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authStateServiceProvider).isAuthenticated;
});

// Provider for user role
final userRoleProvider = Provider<String?>((ref) {
  return ref.watch(authStateServiceProvider).userRole;
});

// Provider for checking admin role
final isAdminProvider = Provider<bool>((ref) {
  return ref.watch(authStateServiceProvider).isAdmin;
});

// Provider for checking teacher role
final isTeacherProvider = Provider<bool>((ref) {
  return ref.watch(authStateServiceProvider).isTeacher;
});

// Provider for checking student role
final isStudentProvider = Provider<bool>((ref) {
  return ref.watch(authStateServiceProvider).isStudent;
});

// Provider for user ID
final userIdProvider = Provider<String?>((ref) {
  return ref.watch(authStateServiceProvider).userId;
});

// Provider for user name
final userNameProvider = Provider<String?>((ref) {
  return ref.watch(authStateServiceProvider).userName;
});

// Provider for user email
final userEmailProvider = Provider<String?>((ref) {
  return ref.watch(authStateServiceProvider).userEmail;
});