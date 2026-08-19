import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:developer' as developer;
import 'dart:io';

/// Central error handling service for comprehensive error logging and management
class ErrorHandlingService {
  static final ErrorHandlingService _instance = ErrorHandlingService._internal();
  factory ErrorHandlingService() => _instance;
  
  ErrorHandlingService._internal();

  static const int _maxStoredErrors = 100;
  final List<Map<String, dynamic>> _storedErrors = [];
  
  /// Global error handler for Flutter framework errors
  void handleFlutterError(FlutterErrorDetails details) {
    final error = details.exception;
    final stackTrace = details.stack as StackTrace;
    
    // Log error with comprehensive details
    _logError(
      exception: error,
      stackTrace: stackTrace,
      context: 'Flutter Framework Error',
      level: 'CRITICAL',
      additionalInfo: {
        'library': details.library,
        'widget': details.toString(),
      },
    );
  }
  
  /// Handle platform-specific errors (iOS, Android, Web, Desktop)
  void handlePlatformError(dynamic error, StackTrace stackTrace, {String context = 'Platform Error'}) {
    _logError(
      exception: error,
      stackTrace: stackTrace,
      context: context,
      level: 'ERROR',
      additionalInfo: {
        'platform': kIsWeb ? 'Web' : Platform.operatingSystem,
        'platformVersion': Platform.operatingSystemVersion,
      },
    );
  }
  
  /// Handle network-related errors
  void handleNetworkError(dynamic error, String endpoint, {String method = 'GET', Map<String, dynamic>? params}) {
    _logError(
      exception: error,
      stackTrace: StackTrace.current,
      context: 'Network Error',
      level: 'WARNING',
      additionalInfo: {
        'endpoint': endpoint,
        'method': method,
        'hasParams': params != null,
        'errorType': error.runtimeType.toString(),
      },
    );
  }
  
  /// Handle API response errors
  void handleApiError(int statusCode, String message, {String? endpoint, dynamic responseData}) {
    _logError(
      exception: message,
      stackTrace: StackTrace.current,
      context: 'API Error',
      level: statusCode >= 500 ? 'ERROR' : 'WARNING',
      additionalInfo: {
        'statusCode': statusCode,
        'endpoint': endpoint,
        'responseData': responseData,
      },
    );
  }
  
  /// Handle database-related errors
  void handleDatabaseError(String operation, dynamic error, {String? collection, String? documentId}) {
    _logError(
      exception: error,
      stackTrace: StackTrace.current,
      context: 'Database Error',
      level: 'ERROR',
      additionalInfo: {
        'operation': operation,
        'collection': collection,
        'documentId': documentId,
        'errorType': error.runtimeType.toString(),
      },
    );
  }
  
  /// Handle authentication/authorization errors
  void handleAuthError(String type, String message, {String? userId, String? action}) {
    _logError(
      exception: message,
      stackTrace: StackTrace.current,
      context: 'Authentication Error',
      level: type == 'session_expired' ? 'WARNING' : 'ERROR',
      additionalInfo: {
        'auth_type': type,
        'user_id': userId,
        'action': action,
      },
    );
  }
  
  /// Handle state management errors (Riverpod, Provider, etc.)
  void handleStateError(String providerName, dynamic error, {String? state, String? action}) {
    _logError(
      exception: error,
      stackTrace: StackTrace.current,
      context: 'State Management Error',
      level: 'ERROR',
      additionalInfo: {
        'provider': providerName,
        'state': state,
        'action': action,
      },
    );
  }
  
  /// Handle UI-related errors
  void handleUIError(String component, dynamic error, {String? action, Map<String, dynamic>? context}) {
    _logError(
      exception: error,
      stackTrace: StackTrace.current,
      context: 'UI Error',
      level: 'WARNING',
      additionalInfo: {
        'component': component,
        'action': action,
        'context': context,
      },
    );
  }
  
  /// Handle business logic errors
  void handleBusinessLogicError(String operation, String message, {String? userId, Map<String, dynamic>? data}) {
    _logError(
      exception: message,
      stackTrace: StackTrace.current,
      context: 'Business Logic Error',
      level: 'WARNING',
      additionalInfo: {
        'operation': operation,
        'user_id': userId,
        'data': data,
      },
    );
  }
  
  /// General error logging method
  void _logError({
    required dynamic exception,
    required StackTrace stackTrace,
    required String context,
    required String level,
    Map<String, dynamic>? additionalInfo,
  }) {
    final errorData = {
      'timestamp': DateTime.now().toIso8601String(),
      'context': context,
      'level': level,
      'exception_type': exception.runtimeType.toString(),
      'exception_message': exception.toString(),
      'stack_trace': stackTrace.toString(),
      'additional_info': additionalInfo ?? {},
    };
    
    // Log to console in development
    if (kDebugMode) {
      print('\n[ERROR] $context ($level):');
      print('Exception: ${exception.runtimeType} - ${exception.toString()}');
      print('Stack Trace:');
      print(stackTrace.toString());
      if (additionalInfo != null && additionalInfo.isNotEmpty) {
        print('Additional Info: $additionalInfo');
      }
      print(List.filled(50, '=').join());
    }
    
    _sendToExternalLoggingService(errorData);
    
    // Store in local storage for debugging
    _storeErrorLocally(errorData);
  }
  
  /// Send error details to the configured platform logger.
  void _sendToExternalLoggingService(Map<String, dynamic> errorData) {
    developer.log(
      errorData['exception_message'] as String,
      name: 'edu_flow.error.${errorData['level']}',
      error: errorData['exception_type'],
      stackTrace: StackTrace.fromString(errorData['stack_trace'] as String),
    );
  }
  
  /// Store error locally for debugging
  void _storeErrorLocally(Map<String, dynamic> errorData) {
    _storedErrors.add(Map<String, dynamic>.from(errorData));
    if (_storedErrors.length > _maxStoredErrors) {
      _storedErrors.removeAt(0);
    }
  }
}

/// Global error handler initialization
void initializeErrorHandling() {
  // Handle Flutter framework errors
  FlutterError.onError = (details) {
    ErrorHandlingService().handleFlutterError(details);
  };
  
  // Handle uncaught async errors
  PlatformDispatcher.instance.onError = (error, stackTrace) {
    ErrorHandlingService().handlePlatformError(error, stackTrace);
    return true; // Error handled
  };
}

/// Widget for catching and handling errors in the widget tree
class ErrorBoundary extends StatefulWidget {
  final Widget child;
  final Function(FlutterErrorDetails)? onError;
  
  const ErrorBoundary({
    super.key,
    required this.child,
    this.onError,
  });
  
  @override
  ErrorBoundaryState createState() => ErrorBoundaryState();
}

class ErrorBoundaryState extends State<ErrorBoundary> {
  bool _hasError = false;
  
  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return const Center(child: Text('An error occurred'));
    }
    return widget.child;
  }
  
  @override
  void initState() {
    super.initState();
    // Add error handling to the widget tree
    _bindErrorHandling();
  }
  
  void _bindErrorHandling() {
    // Bind error handlers at the widget level
  }
  
  void handleError(FlutterErrorDetails details) {
    setState(() {
      _hasError = true;
    });
    
    ErrorHandlingService().handleFlutterError(details);
    
    if (widget.onError != null) {
      widget.onError!(details);
    }
  }
}