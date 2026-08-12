import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:edu_flow/config/app_config.dart';
import 'package:edu_flow/core/exceptions/api_exceptions.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  static ApiClient get instance => _instance;
  
  ApiClient._internal();
  
  final AppConfig _config = AppConfig.instance;
  final http.Client _client = http.Client();
  
  // Request timeout
  static const Duration _timeout = Duration(seconds: 30);
  
  // Headers for all requests
  Map<String, String> _getHeaders({bool isAuthRequired = false}) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'EduFlow-Flutter/${_config.appVersion}',
    };
    
    if (isAuthRequired) {
      // Add authorization header if available
      final token = _getAuthToken();
      if (token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    
    return headers;
  }
  
  // Get authentication token from storage
  String _getAuthToken() {
    // This should be implemented with secure storage
    return ''; // Return empty for now, implement actual token retrieval
  }
  
  // Save authentication token
  void _saveAuthToken(String token) {
    // This should be implemented with secure storage
    // For now, just store in memory
  }
  
  // Generic GET request
  Future<Map<String, dynamic>> get(
    String endpoint, {
    bool isAuthRequired = true,
    Map<String, String>? queryParams,
  }) async {
    try {
      final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
      
      if (queryParams != null) {
        url.queryParameters.addAll(queryParams);
      }
      
      final response = await _client.get(
        url,
        headers: _getHeaders(isAuthRequired: isAuthRequired),
        timeout: _timeout,
      );
      
      return _handleResponse(response);
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Network error: ${e.message}',
        statusCode: -1,
      );
    } catch (e) {
      throw ApiException(
        message: 'Request failed: $e',
        statusCode: -1,
      );
    }
  }
  
  // Generic POST request
  Future<Map<String, dynamic>> post(
    String endpoint, {
    required Map<String, dynamic> data,
    bool isAuthRequired = true,
  }) async {
    try {
      final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
      
      final response = await _client.post(
        url,
        headers: _getHeaders(isAuthRequired: isAuthRequired),
        body: jsonEncode(data),
        timeout: _timeout,
      );
      
      return _handleResponse(response);
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Network error: ${e.message}',
        statusCode: -1,
      );
    } catch (e) {
      throw ApiException(
        message: 'Request failed: $e',
        statusCode: -1,
      );
    }
  }
  
  // Generic PUT request
  Future<Map<String, dynamic>> put(
    String endpoint, {
    required Map<String, dynamic> data,
    bool isAuthRequired = true,
  }) async {
    try {
      final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
      
      final response = await _client.put(
        url,
        headers: _getHeaders(isAuthRequired: isAuthRequired),
        body: jsonEncode(data),
        timeout: _timeout,
      );
      
      return _handleResponse(response);
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Network error: ${e.message}',
        statusCode: -1,
      );
    } catch (e) {
      throw ApiException(
        message: 'Request failed: $e',
        statusCode: -1,
      );
    }
  }
  
  // Generic DELETE request
  Future<Map<String, dynamic>> delete(
    String endpoint, {
    bool isAuthRequired = true,
  }) async {
    try {
      final url = Uri.parse('${_config.apiBaseUrl}${_config.apiVersion}$endpoint');
      
      final response = await _client.delete(
        url,
        headers: _getHeaders(isAuthRequired: isAuthRequired),
        timeout: _timeout,
      );
      
      return _handleResponse(response);
    } on http.ClientException catch (e) {
      throw ApiException(
        message: 'Network error: ${e.message}',
        statusCode: -1,
      );
    } catch (e) {
      throw ApiException(
        message: 'Request failed: $e',
        statusCode: -1,
      );
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
        headers: _getHeaders(isAuthRequired: isAuthRequired),
        timeout: _timeout,
      );
      
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
}