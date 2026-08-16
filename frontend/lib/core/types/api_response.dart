// API Response Types

class ApiResponse<T> {
  final bool success;
  final String? message;
  final T? data;
  final int? statusCode;
  final Map<String, dynamic>? metadata;
  final DateTime? timestamp;

  ApiResponse({
    required this.success,
    this.message,
    this.data,
    this.statusCode,
    this.metadata,
    this.timestamp,
  });

  factory ApiResponse.success({
    T? data,
    String? message,
    Map<String, dynamic>? metadata,
  }) {
    return ApiResponse<T>(
      success: true,
      data: data,
      message: message ?? 'Operation successful',
      metadata: metadata,
      timestamp: DateTime.now(),
    );
  }

  factory ApiResponse.error({
    required String message,
    int? statusCode,
    Map<String, dynamic>? errorDetails,
    Map<String, dynamic>? metadata,
  }) {
    return ApiResponse<T>(
      success: false,
      message: message,
      statusCode: statusCode,
      metadata: {
        'error': errorDetails,
        ...?metadata,
      },
      timestamp: DateTime.now(),
    );
  }

  factory ApiResponse.fromMap(Map<String, dynamic> map) {
    return ApiResponse<T>(
      success: map['success'] ?? false,
      message: map['message'],
      data: map['data'] != null ? _parseData(map['data']) : null,
      statusCode: map['status_code'],
      metadata: map['metadata'],
      timestamp: map['timestamp'] != null 
          ? DateTime.parse(map['timestamp'])
          : null,
    );
  }

  T? _parseData(dynamic data) {
    // This would be more sophisticated in a real app
    // For now, we'll just return the data as-is
    return data as T?;
  }

  Map<String, dynamic> toMap() {
    return {
      'success': success,
      'message': message,
      'data': data,
      'status_code': statusCode,
      'metadata': metadata,
      'timestamp': timestamp?.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'ApiResponse(success: $success, message: $message, data: $data, statusCode: $statusCode)';
  }
}

// Paginated Response Type
class PaginatedApiResponse<T> {
  final List<T> items;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;
  final bool hasNext;
  final bool hasPrevious;
  final Map<String, dynamic>? metadata;

  PaginatedApiResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
    required this.hasNext,
    required this.hasPrevious,
    this.metadata,
  });

  factory PaginatedApiResponse.fromMap(Map<String, dynamic> map, T Function(dynamic) parser) {
    return PaginatedApiResponse<T>(
      items: (map['items'] as List).map((item) => parser(item)).toList(),
      total: map['total'] ?? 0,
      page: map['page'] ?? 1,
      pageSize: map['page_size'] ?? 10,
      totalPages: map['total_pages'] ?? 1,
      hasNext: map['has_next'] ?? false,
      hasPrevious: map['has_previous'] ?? false,
      metadata: map['metadata'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'items': items,
      'total': total,
      'page': page,
      'page_size': pageSize,
      'total_pages': totalPages,
      'has_next': hasNext,
      'has_previous': hasPrevious,
      'metadata': metadata,
    };
  }
}

// API Error Types
class ApiError {
  final String code;
  final String message;
  final int? statusCode;
  final Map<String, dynamic>? details;
  final DateTime timestamp;

  ApiError({
    required this.code,
    required this.message,
    this.statusCode,
    this.details,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory ApiError.fromMap(Map<String, dynamic> map) {
    return ApiError(
      code: map['error'] ?? 'UNKNOWN_ERROR',
      message: map['message'] ?? 'An error occurred',
      statusCode: map['status_code'],
      details: map['details'],
      timestamp: map['timestamp'] != null 
          ? DateTime.parse(map['timestamp'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'error': code,
      'message': message,
      'status_code': statusCode,
      'details': details,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'ApiError(code: $code, message: $message, statusCode: $statusCode)';
  }
}

// Common API Response Extensions
extension ApiResponseExtensions on ApiResponse {
  bool get isSuccessful => success;
  bool get hasError => !success;
  bool get hasData => data != null;
  bool get hasMessage => message != null && message!.isNotEmpty;
}

// Common Error Codes
class ApiErrorCodes {
  static const String unauthorized = 'UNAUTHORIZED';
  static const String forbidden = 'FORBIDDEN';
  static const String notFound = 'NOT_FOUND';
  static const String validationError = 'VALIDATION_ERROR';
  static const String serverError = 'SERVER_ERROR';
  static const String networkError = 'NETWORK_ERROR';
  static const String timeoutError = 'TIMEOUT_ERROR';
  static const String rateLimitExceeded = 'RATE_LIMIT_EXCEEDED';
  static const String invalidToken = 'INVALID_TOKEN';
  static const String tokenExpired = 'TOKEN_EXPIRED';
  static const String insufficientPermissions = 'INSUFFICIENT_PERMISSIONS';
  static const String resourceNotFound = 'RESOURCE_NOT_FOUND';
  static const String duplicateResource = 'DUPLICATE_RESOURCE';
  static const String constraintViolation = 'CONSTRAINT_VIOLATION';
  static const String databaseError = 'DATABASE_ERROR';
}