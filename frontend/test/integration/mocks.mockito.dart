// Mock implementation of AuthService interface
class MockAuthService {
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String name,
    required String role,
  }) async {
    return {
      'success': true,
      'message': 'Registration successful',
      'user': null,
      'access_token': 'mock_token',
      'refresh_token': 'mock_refresh_token',
      'token_type': 'bearer',
    };
  }
  
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    return {
      'success': true,
      'message': 'Login successful',
      'user': null,
      'access_token': 'mock_token',
      'refresh_token': 'mock_refresh_token',
      'token_type': 'bearer',
    };
  }
}