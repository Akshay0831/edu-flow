import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:edu_flow/config/app_config.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  static ApiClient get instance => _instance;
  
  ApiClient._internal();
  
  final AppConfig _config = AppConfig.instance;
  final http.Client _client = http.Client();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  
  // Request timeout
  static const Duration _timeout = Duration(seconds: 30);
  
  // Token management
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userRoleKey = 'user_role';
  static const String _userIdKey = 'user_id';
  
  // Get headers for requests
  Future<Map<String, String>> _getHeaders({bool isAuthRequired = false}) async {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'EduFlow-Flutter/${_config.appVersion}',
    };
    
    if (isAuthRequired) {
      final token = await _getAuthToken();
      if (token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    
    return headers;
  }
  
  // Get authentication token from secure storage
  Future<String> _getAuthToken() async {
    try {
      return await _secureStorage.read(key: _accessTokenKey) ?? '';
    } catch (e) {
      return '';
    }
  }
  
  // Get refresh token from secure storage
  Future<String> _getRefreshToken() async {
    try {
      return await _secureStorage.read(key: _refreshTokenKey) ?? '';
    } catch (e) {
      return '';
    }
  }
  
  // Save authentication tokens to secure storage
  Future<void> saveAuthToken(String accessToken, {String? refreshToken}) async {
    try {
      await _secureStorage.write(key: _accessTokenKey, value: accessToken);
      if (refreshToken != null) {
        await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
      }
    } catch (e) {
      throw ApiException(message: 'Failed to save auth token: $e');
    }
  }
  
  // Save user role to secure storage
  Future<void> saveUserRole(String role) async {
    try {
      await _secureStorage.write(key: _userRoleKey, value: role);
    } catch (e) {
      throw ApiException(message: 'Failed to save user role: $e');
    }
  }
  
  // Get user role from secure storage
  Future<String> _getUserRole() async {
    try {
      return await _secureStorage.read(key: _userRoleKey) ?? '';
    } catch (e) {
      return '';
    }
  }
  
  // Refresh access token
  Future<String> _refreshAccessToken() async {
    try {
      final refreshToken = await _getRefreshToken();
      if (refreshToken.isEmpty) {
        throw ApiException(message: 'No refresh token available');
      }
      
      final response = await _client.post(
        Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}/auth/refresh'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({'refresh_token': refreshToken}),
      ).timeout(_timeout);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final newAccessToken = data['access_token'];
        final newRefreshToken = data['refresh_token'];
        
        if (newAccessToken != null) {
          await saveAuthToken(newAccessToken, refreshToken: newRefreshToken);
          return newAccessToken;
        }
        
        throw ApiException(message: 'Failed to refresh token: No access token returned');
      } else {
        throw ApiException(message: 'Token refresh failed', statusCode: response.statusCode);
      }
    } catch (e) {
      // If refresh fails, clear stored tokens and throw
      await _clearAuthTokens();
      throw ApiException(message: 'Token refresh failed: ${e.toString()}');
    }
  }
  
  // Clear authentication tokens
  Future<void> clearAuthTokens() async {
    try {
      await _secureStorage.delete(key: _accessTokenKey);
      await _secureStorage.delete(key: _refreshTokenKey);
      await _secureStorage.delete(key: _userRoleKey);
      await _secureStorage.delete(key: _userIdKey);
    } catch (e) {
      throw ApiException(message: 'Failed to clear auth tokens: $e');
    }
  }
  
  // Private clear authentication tokens (for internal use)
  Future<void> _clearAuthTokens() async {
    try {
      await _secureStorage.delete(key: _accessTokenKey);
      await _secureStorage.delete(key: _refreshTokenKey);
      await _secureStorage.delete(key: _userRoleKey);
      await _secureStorage.delete(key: _userIdKey);
    } catch (e) {
      throw ApiException(message: 'Failed to clear auth tokens: $e');
    }
  }
  
  // Generic GET request with automatic token refresh
  Future<Map<String, dynamic>> get(
    String endpoint, {
    bool isAuthRequired = true,
    Map<String, String>? queryParams,
  }) async {
    return _makeRequest(
      'GET',
      endpoint,
      isAuthRequired: isAuthRequired,
      queryParams: queryParams,
    );
  }
  
  // Generic POST request with automatic token refresh
  Future<Map<String, dynamic>> post(
    String endpoint, {
    required Map<String, dynamic> data,
    bool isAuthRequired = true,
  }) async {
    return _makeRequest(
      'POST',
      endpoint,
      data: data,
      isAuthRequired: isAuthRequired,
    );
  }
  
  // Generic PUT request with automatic token refresh
  Future<Map<String, dynamic>> put(
    String endpoint, {
    required Map<String, dynamic> data,
    bool isAuthRequired = true,
  }) async {
    return _makeRequest(
      'PUT',
      endpoint,
      data: data,
      isAuthRequired: isAuthRequired,
    );
  }
  
  // Generic DELETE request with automatic token refresh
  Future<Map<String, dynamic>> delete(
    String endpoint, {
    bool isAuthRequired = true,
  }) async {
    return _makeRequest(
      'DELETE',
      endpoint,
      isAuthRequired: isAuthRequired,
    );
  }
  
  // Make request with automatic token refresh
  Future<Map<String, dynamic>> _makeRequest(
    String method,
    String endpoint, {
    required bool isAuthRequired,
    Map<String, dynamic>? data,
    Map<String, String>? queryParams,
  }) async {
    int retryCount = 0;
    const int maxRetries = 1;
    
    while (true) {
      try {
        final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
        
        if (queryParams != null) {
          url.queryParameters.addAll(queryParams);
        }
        
        http.Response response;
        
        switch (method.toUpperCase()) {
          case 'GET':
            response = await _client.get(
              url,
              headers: await _getHeaders(isAuthRequired: isAuthRequired),
            ).timeout(_timeout);
            break;
          case 'POST':
            response = await _client.post(
              url,
              headers: await _getHeaders(isAuthRequired: isAuthRequired),
              body: jsonEncode(data),
            ).timeout(_timeout);
            break;
          case 'PUT':
            response = await _client.put(
              url,
              headers: await _getHeaders(isAuthRequired: isAuthRequired),
              body: jsonEncode(data),
            ).timeout(_timeout);
            break;
          case 'DELETE':
            response = await _client.delete(
              url,
              headers: await _getHeaders(isAuthRequired: isAuthRequired),
            ).timeout(_timeout);
            break;
          default:
            throw ApiException(message: 'Unsupported HTTP method: $method');
        }
        
        return _handleResponse(response);
        
      } on ApiException catch (e) {
        if (e.statusCode == 401 && isAuthRequired && retryCount < maxRetries) {
          // Try to refresh token and retry once
          retryCount++;
          await _refreshAccessToken();
        } else {
          rethrow;
        }
      } catch (e) {
        if (retryCount < maxRetries) {
          retryCount++;
        } else {
          throw ApiException(
            message: 'Request failed: ${e.toString()}',
            statusCode: -1,
          );
        }
      }
    }
  }
  
  // Handle API response
  Map<String, dynamic> _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    final responseBody = utf8.decode(response.bodyBytes);
    
    if (statusCode >= 200 && statusCode < 300) {
      try {
        final json = jsonDecode(responseBody);
        
        // Check for standard API response format
        if (json is Map<String, dynamic>) {
          return json;
        } else {
          return {'success': true, 'data': json};
        }
      } catch (e) {
        return {
          'success': true,
          'data': responseBody,
          'raw_response': responseBody,
        };
      }
    } else {
      try {
        final errorJson = jsonDecode(responseBody);
        throw ApiException(
          message: errorJson['message'] ?? 'Request failed with status $statusCode',
          statusCode: statusCode,
          errorDetails: errorJson,
          errorCode: errorJson['error'],
        );
      } catch (e) {
        throw ApiException(
          message: 'Request failed with status $statusCode: $responseBody',
          statusCode: statusCode,
        );
      }
    }
  }
  
  // Upload file with multipart
  Future<Map<String, dynamic>> uploadFile(
    String endpoint, {
    required String filePath,
    required String fieldName,
    Map<String, String>? additionalData,
    bool isAuthRequired = true,
  }) async {
    // Implement file upload functionality
    // This would use the http package with multipart requests
    throw UnimplementedError('File upload not implemented yet');
  }
  
  // Download file
  Future<http.Response> downloadFile(
    String endpoint, {
    bool isAuthRequired = true,
  }) async {
    try {
      final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
      
      final response = await _client.get(
        url,
        headers: await _getHeaders(isAuthRequired: isAuthRequired),
      ).timeout(_timeout);
      
      return response;
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Network error: ${e.message}',
        statusCode: -1,
      );
    } catch (e) {
      throw ApiException(
        message: 'Download failed: $e',
        statusCode: -1,
      );
    }
  }
  
  // Clean up resources
  void dispose() {
    _client.close();
  }
  
  // Check if user is authenticated
  Future<bool> isAuthenticated() async {
    try {
      final token = await _getAuthToken();
      final role = await _getUserRole();
      return token.isNotEmpty && role.isNotEmpty;
    } catch (e) {
      return false;
    }
  }
  
  // Get current user role
  Future<String> getUserRole() async {
    return await _getUserRole();
  }
  
  // Logout user
  Future<void> logout() async {
    try {
      await _clearAuthTokens();
      // Optionally notify other parts of the app about logout
    } catch (e) {
      throw ApiException(message: 'Logout failed: $e');
    }
  }
  
  // Public getters for token management (for auth state service)
  Future<String> getAuthToken() async {
    return await _getAuthToken();
  }
  
  Future<String> getRefreshToken() async {
    return await _getRefreshToken();
  }
  
  Future<void> refreshAccessToken() async {
    await _refreshAccessToken();
  }
}