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
        // Save authentication tokens and user info
        await _apiClient._saveAuthToken(response['access_token'], refreshToken: response['refresh_token']);
        await _apiClient._saveUserRole(user.role);
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
      throw ApiException(message: 'Registration failed: ${e.toString()}');
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
        // Save authentication tokens and user info
        await _apiClient._saveAuthToken(response['access_token'], refreshToken: response['refresh_token']);
        await _apiClient._saveUserRole(user.role);
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
      throw ApiException(message: 'Login failed: ${e.toString()}');
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
      throw ApiException(message: 'Forgot password failed: ${e.toString()}');
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
      throw ApiException(message: 'Reset password failed: ${e.toString()}');
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
      throw ApiException(message: 'Change password failed: ${e.toString()}');
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
      throw ApiException(message: 'Get current user failed: ${e.toString()}');
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
      throw ApiException(message: 'Update user profile failed: ${e.toString()}');
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
      throw ApiException(message: 'Token refresh failed: ${e.toString()}');
    }
  }
  
  // Check if user is authenticated
  Future<bool> isAuthenticated() async {
    return await _apiClient.isAuthenticated();
  }
  
  // Get user role
  Future<String> getUserRole() async {
    return await _apiClient.getUserRole();
  }
  
  // Logout user with proper cleanup
  Future<void> logout() async {
    try {
      // Call API logout if needed
      await _apiClient.post('/auth/logout', data: {}, isAuthRequired: true);
    } catch (e) {
      // Ignore errors if logout API call fails, just proceed with token cleanup
    } finally {
      // Always clear tokens
      await _apiClient._clearAuthTokens();
    }
  }
}