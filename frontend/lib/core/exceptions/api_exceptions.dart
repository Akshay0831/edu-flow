import 'dart:io';

class ApiException implements Exception {
  final String message;
  final int statusCode;
  final Map<String, dynamic>? errorDetails;
  final String? errorCode;
  
  ApiException({
    required this.message,
    this.statusCode = 500,
    this.errorDetails,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'ApiException: $message';
  }
  
  factory ApiException.fromResponse(HttpResponse response) {
    return ApiException(
      message: response.message,
      statusCode: response.statusCode,
      errorDetails: response.errorDetails,
    );
  }
}

class NetworkException implements Exception {
  final String message;
  final int? statusCode;
  
  NetworkException({
    required this.message,
    this.statusCode,
  });
  
  @override
  String toString() => 'NetworkException: $message';
}

class TimeoutException implements Exception {
  final String message;
  final Duration? timeoutDuration;
  
  TimeoutException({
    required this.message,
    this.timeoutDuration,
  });
  
  @override
  String toString() {
    if (timeoutDuration != null) {
      return 'TimeoutException: $message (after ${timeoutDuration!.inSeconds}s)';
    }
    return 'TimeoutException: $message';
  }
}

class AuthenticationException implements Exception {
  final String message;
  final String? errorCode;
  
  AuthenticationException({
    required this.message,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'AuthenticationException: $message';
  }
}

class AuthorizationException implements Exception {
  final String message;
  final String? errorCode;
  
  AuthorizationException({
    required this.message,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'AuthorizationException: $message';
  }
}

class ValidationException implements Exception {
  final String message;
  final Map<String, dynamic>? validationErrors;
  final String? errorCode;
  
  ValidationException({
    required this.message,
    this.validationErrors,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'ValidationException: $message';
  }
}

class NotFoundException implements Exception {
  final String message;
  final String? resourceType;
  final String? resourceId;
  final String? errorCode;
  
  NotFoundException({
    required this.message,
    this.resourceType,
    this.resourceId,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'NotFoundException: $message';
  }
}

class ServerException implements Exception {
  final String message;
  final int? statusCode;
  final String? errorCode;
  
  ServerException({
    required this.message,
    this.statusCode,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'ServerException: $message';
  }
}

class ConnectionException implements Exception {
  final String message;
  final String? endpoint;
  
  ConnectionException({
    required this.message,
    this.endpoint,
  });
  
  @override
  String toString() {
    if (endpoint != null) {
      return 'ConnectionException: $message (endpoint: $endpoint)';
    }
    return 'ConnectionException: $message';
  }
}

class DataFormatException implements Exception {
  final String message;
  final String? rawResponse;
  
  DataFormatException({
    required this.message,
    this.rawResponse,
  });
  
  @override
  String toString() {
    if (rawResponse != null) {
      return 'DataFormatException: $message\nRaw: $rawResponse';
    }
    return 'DataFormatException: $message';
  }
}

class RateLimitException implements Exception {
  final String message;
  final int? retryAfter;
  final String? errorCode;
  
  RateLimitException({
    required this.message,
    this.retryAfter,
    this.errorCode,
  });
  
  @override
  String toString() {
    if (errorCode != null) {
      return '[$errorCode] $message';
    }
    return 'RateLimitException: $message';
  }
}

class ApiExceptionHelper {
  static ApiException fromError(dynamic error) {
    if (error is ApiException) {
      return error;
    } else if (error is NetworkException) {
      return ApiException(
        message: error.message,
        statusCode: error.statusCode ?? -1,
        errorCode: 'NETWORK_ERROR',
      );
    } else if (error is TimeoutException) {
      return ApiException(
        message: error.message,
        statusCode: -1,
        errorCode: 'TIMEOUT',
      );
    } else if (error is AuthenticationException) {
      return ApiException(
        message: error.message,
        statusCode: 401,
        errorCode: error.errorCode ?? 'AUTH_ERROR',
      );
    } else if (error is AuthorizationException) {
      return ApiException(
        message: error.message,
        statusCode: 403,
        errorCode: error.errorCode ?? 'AUTH_ERROR',
      );
    } else if (error is ValidationException) {
      return ApiException(
        message: error.message,
        statusCode: 400,
        errorCode: error.errorCode ?? 'VALIDATION_ERROR',
      );
    } else if (error is NotFoundException) {
      return ApiException(
        message: error.message,
        statusCode: 404,
        errorCode: error.errorCode ?? 'NOT_FOUND',
      );
    } else if (error is ServerException) {
      return ApiException(
        message: error.message,
        statusCode: error.statusCode ?? 500,
        errorCode: error.errorCode ?? 'SERVER_ERROR',
      );
    } else if (error is ConnectionException) {
      return ApiException(
        message: error.message,
        statusCode: -1,
        errorCode: 'CONNECTION_ERROR',
      );
    } else if (error is DataFormatException) {
      return ApiException(
        message: error.message,
        statusCode: -1,
        errorCode: 'DATA_FORMAT_ERROR',
      );
    } else if (error is RateLimitException) {
      return ApiException(
        message: error.message,
        statusCode: 429,
        errorCode: error.errorCode ?? 'RATE_LIMIT',
      );
    } else {
      return ApiException(
        message: 'Unknown error: $error',
        statusCode: -1,
        errorCode: 'UNKNOWN_ERROR',
      );
    }
  }
}

class HttpResponse {
  final int statusCode;
  final String message;
  final Map<String, dynamic>? errorDetails;
  final String? rawResponse;
  
  HttpResponse({
    required this.statusCode,
    required this.message,
    this.errorDetails,
    this.rawResponse,
  });
}