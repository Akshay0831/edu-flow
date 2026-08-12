import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/user_model.dart';

class AuthService {
  final ApiClient _apiClient = ApiClient.instance;
  
  // User registration
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String name,
    required String role,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/register',
        data: {
          'email': email,
          'password': password,
          'name': name,
          'role': role,
        },
        isAuthRequired: false,
      );
      
      // Extract tokens and user data
      final user = response['data'] != null 
          ? UserModel.fromJson(response['data'])
          : null;
      
      if (user != null && response['access_token'] != null) {
        // Save authentication token
        _apiClient._saveAuthToken(response['access_token']);
      }
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Registration successful',
        'user': user,
        'access_token': response['access_token'],
        'refresh_token': response['refresh_token'],
        'token_type': response['token_type'] ?? 'bearer',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // User login
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
        isAuthRequired: false,
      );
      
      // Extract tokens and user data
      final user = response['data'] != null 
          ? UserModel.fromJson(response['data'])
          : null;
      
      if (user != null && response['access_token'] != null) {
        // Save authentication token
        _apiClient._saveAuthToken(response['access_token']);
      }
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Login successful',
        'user': user,
        'access_token': response['access_token'],
        'refresh_token': response['refresh_token'],
        'token_type': response['token_type'] ?? 'bearer',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Forgot password
  Future<Map<String, dynamic>> forgotPassword({
    required String email,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/forgot-password',
        data: {
          'email': email,
        },
        isAuthRequired: false,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Password reset email sent',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Reset password
  Future<Map<String, dynamic>> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/reset-password',
        data: {
          'token': token,
          'password': newPassword,
        },
        isAuthRequired: false,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Password reset successful',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Change password
  Future<Map<String, dynamic>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/change-password',
        data: {
          'current_password': currentPassword,
          'new_password': newPassword,
        },
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Password changed successfully',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Get current user profile
  Future<UserModel> getCurrentUser() async {
    try {
      final response = await _apiClient.get(
        '/auth/profile',
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Update user profile
  Future<UserModel> updateUserProfile({
    required String userId,
    String? name,
    String? email,
    String? phone,
    String? avatar,
  }) async {
    try {
      final response = await _apiClient.put(
        '/users/$userId',
        data: {
          if (name != null) 'name': name,
          if (email != null) 'email': email,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Logout
  Future<Map<String, dynamic>> logout() async {
    try {
      // Clear authentication token
      _apiClient._saveAuthToken('');
      
      return {
        'success': true,
        'message': 'Logout successful',
      };
    } catch (e) {
      // Even if logout fails, clear the token
      _apiClient._saveAuthToken('');
      throw ApiException.fromError(e);
    }
  }
  
  // Refresh access token
  Future<Map<String, dynamic>> refreshToken({
    required String refreshToken,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/refresh-token',
        data: {
          'refresh_token': refreshToken,
        },
        isAuthRequired: false,
      );
      
      // Save new authentication token
      _apiClient._saveAuthToken(response['access_token']);
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'Token refreshed successfully',
        'access_token': response['access_token'],
        'refresh_token': response['refresh_token'],
        'token_type': response['token_type'] ?? 'bearer',
      };
    } catch (e) {
      throw ApiException.fromError(e);
    }
  }
  
  // Check if user is authenticated
  bool isAuthenticated() {
    final token = _apiClient._getAuthToken();
    return token.isNotEmpty;
  }
}