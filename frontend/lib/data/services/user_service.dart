import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';
import 'package:edu_flow/data/models/user_model.dart';

class UserService {
  final ApiClient _apiClient = ApiClient.instance;
  
  // Get all users
  Future<List<UserModel>> getAllUsers() async {
    try {
      final response = await _apiClient.get(
        '/users',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((userJson) => UserModel.fromJson(userJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for users list');
      }
    } catch (e) {
      throw ApiException(message: 'Get all users failed: ${e.toString()}');
    }
  }
  
  // Get user by ID
  Future<UserModel> getUserById(String userId) async {
    try {
      final response = await _apiClient.get(
        '/users/$userId',
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Get user failed: ${e.toString()}');
    }
  }
  
  // Create new user
  Future<UserModel> createUser({
    required String email,
    required String password,
    required String name,
    required String role,
    String? phone,
    String? avatar,
  }) async {
    try {
      final response = await _apiClient.post(
        '/users',
        data: {
          'email': email,
          'password': password,
          'name': name,
          'role': role,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Create user failed: ${e.toString()}');
    }
  }
  
  // Update user
  Future<UserModel> updateUser({
    required String userId,
    String? name,
    String? email,
    String? phone,
    String? avatar,
    String? role,
  }) async {
    try {
      final response = await _apiClient.put(
        '/users/$userId',
        data: {
          if (name != null) 'name': name,
          if (email != null) 'email': email,
          if (phone != null) 'phone': phone,
          if (avatar != null) 'avatar': avatar,
          if (role != null) 'role': role,
        },
        isAuthRequired: true,
      );
      
      return UserModel.fromJson(response['data']);
    } catch (e) {
      throw ApiException(message: 'Update user failed: ${e.toString()}');
    }
  }
  
  // Delete user
  Future<Map<String, dynamic>> deleteUser(String userId) async {
    try {
      final response = await _apiClient.delete(
        '/users/$userId',
        isAuthRequired: true,
      );
      
      return {
        'success': response['success'] ?? true,
        'message': response['message'] ?? 'User deleted successfully',
      };
    } catch (e) {
      throw ApiException(message: 'Delete user failed: ${e.toString()}');
    }
  }
  
  // Get users by role
  Future<List<UserModel>> getUsersByRole(String role) async {
    try {
      final response = await _apiClient.get(
        '/users?role=$role',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((userJson) => UserModel.fromJson(userJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for users by role');
      }
    } catch (e) {
      throw ApiException(message: 'Get users by role failed: ${e.toString()}');
    }
  }
  
  // Search users
  Future<List<UserModel>> searchUsers(String query) async {
    try {
      final response = await _apiClient.get(
        '/users/search?q=$query',
        isAuthRequired: true,
      );
      
      if (response['data'] is List) {
        return (response['data'] as List)
            .map((userJson) => UserModel.fromJson(userJson))
            .toList();
      } else {
        throw ApiException(message: 'Invalid response format for user search');
      }
    } catch (e) {
      throw ApiException(message: 'Search users failed: ${e.toString()}');
    }
  }
}