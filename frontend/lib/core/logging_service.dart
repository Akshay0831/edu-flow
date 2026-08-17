import 'dart:developer' as developer;
import 'package:flutter/foundation.dart';

/// Comprehensive logging service for the Flutter application
class LoggingService {
  static final LoggingService _instance = LoggingService._internal();
  factory LoggingService() => _instance;
  
  LoggingService._internal();
  
  /// Logging levels
  static const String debugLevel = 'DEBUG';
  static const String infoLevel = 'INFO';
  static const String warningLevel = 'WARNING';
  static const String errorLevel = 'ERROR';
  static const String criticalLevel = 'CRITICAL';
  
  /// Initialize logging configuration
  void initialize({
    String level = infoLevel,
    bool enableConsoleLogs = true,
    bool enableFileLogs = false,
    bool enablePerformanceTracking = false,
  }) {
    _log('Logging initialized with level: $level', infoLevel);
    
    // Configure performance tracking
    if (enablePerformanceTracking) {
      _enablePerformanceTracking();
    }
  }
  
  /// Internal log method
  void _log(String message, String level) {
    final timestamp = DateTime.now().toIso8601String();
    final logEntry = {
      'timestamp': timestamp,
      'level': level,
      'message': message,
    };
    
    // Log based on platform and configuration
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: message,
    );
  }
  
  /// General logging method
  void log(String message, {
    String level = infoLevel,
    dynamic error,
    StackTrace? stackTrace,
    Map<String, dynamic>? extra,
    String? tag,
  }) {
    final timestamp = DateTime.now().toIso8601String();
    final logEntry = {
      'timestamp': timestamp,
      'level': level,
      'message': message,
      'tag': tag,
      'error': error?.toString(),
      'stack_trace': stackTrace?.toString(),
      'extra': extra,
    };
    
    // Format log message
    final formattedMessage = _formatMessage(
      message: message,
      level: level,
      tag: tag,
      extra: extra,
    );
    
    // Log based on platform and configuration
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// Debug logging
  void debug(String message, {String? tag, Map<String, dynamic>? extra}) {
    log(message, level: debugLevel, tag: tag, extra: extra);
  }
  
  /// Info logging
  void info(String message, {String? tag, Map<String, dynamic>? extra}) {
    log(message, level: infoLevel, tag: tag, extra: extra);
  }
  
  /// Warning logging
  void warning(String message, {String? tag, Map<String, dynamic>? extra}) {
    log(message, level: warningLevel, tag: tag, extra: extra);
  }
  
  /// Error logging
  void error(String message, {
    dynamic error,
    StackTrace? stackTrace,
    String? tag,
    Map<String, dynamic>? extra,
  }) {
    log(message, level: errorLevel, error: error, stackTrace: stackTrace, tag: tag, extra: extra);
  }
  
  /// Critical logging
  void critical(String message, {
    dynamic error,
    StackTrace? stackTrace,
    String? tag,
    Map<String, dynamic>? extra,
  }) {
    log(message, level: criticalLevel, error: error, stackTrace: stackTrace, tag: tag, extra: extra);
  }
  
  /// Network logging
  void network(String endpoint, {
    String method = 'GET',
    Map<String, dynamic>? request,
    Map<String, dynamic>? response,
    int? statusCode,
    String? statusMessage,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'NETWORK',
      'endpoint': endpoint,
      'method': method,
      'request': request,
      'response': response,
      'status_code': statusCode,
      'status_message': statusMessage,
      'tag': tag,
    };
    
    final formattedMessage = '[$method] $endpoint - ${statusCode ?? 'N/A'}: ${statusMessage ?? ''}';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// UI Event logging
  void uiEvent(String component, String event, {
    Map<String, dynamic>? data,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'UI_EVENT',
      'component': component,
      'event': event,
      'data': data,
      'tag': tag,
    };
    
    final formattedMessage = 'UI Event: $component.$event';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// Performance tracking
  void performance(String operation, {
    DateTime? startTime,
    DateTime? endTime,
    Map<String, dynamic>? metrics,
    String level = infoLevel,
    String? tag,
  }) {
    final duration = startTime != null && endTime != null
        ? endTime.difference(startTime).inMilliseconds
        : null;
    
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'PERFORMANCE',
      'operation': operation,
      'duration_ms': duration,
      'start_time': startTime?.toIso8601String(),
      'end_time': endTime?.toIso8601String(),
      'metrics': metrics,
      'tag': tag,
    };
    
    final formattedMessage = 'Performance: $operation - ${duration ?? 'N/A'}ms';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// User action logging
  void userAction(String action, {
    String? userId,
    String? screen,
    Map<String, dynamic>? data,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'USER_ACTION',
      'action': action,
      'user_id': userId,
      'screen': screen,
      'data': data,
      'tag': tag,
    };
    
    final formattedMessage = 'User Action: $action${userId != null ? ' by $userId' : ''}';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// API request logging
  void apiRequest(String endpoint, {
    String method = 'GET',
    Map<String, dynamic>? headers,
    dynamic body,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'API_REQUEST',
      'endpoint': endpoint,
      'method': method,
      'headers': headers,
      'body': body,
      'tag': tag,
    };
    
    final formattedMessage = 'API Request: $method $endpoint';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// API response logging
  void apiResponse(String endpoint, {
    required int statusCode,
    String? statusMessage,
    dynamic data,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'API_RESPONSE',
      'endpoint': endpoint,
      'status_code': statusCode,
      'status_message': statusMessage,
      'data': data,
      'tag': tag,
    };
    
    final formattedMessage = 'API Response: $endpoint - $statusCode: ${statusMessage ?? ''}';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// Database operation logging
  void dbOperation(String operation, {
    String? collection,
    String? documentId,
    dynamic data,
    dynamic result,
    String level = infoLevel,
    String? tag,
  }) {
    final logEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'level': level,
      'type': 'DATABASE',
      'operation': operation,
      'collection': collection,
      'document_id': documentId,
      'data': data,
      'result': result,
      'tag': tag,
    };
    
    final formattedMessage = 'Database: $operation${collection != null ? ' on $collection' : ''}';
    
    _logToAppropriateDestination(
      logEntry: logEntry,
      formattedMessage: formattedMessage,
    );
  }
  
  /// Format log message
  String _formatMessage({
    required String message,
    required String level,
    String? tag,
    Map<String, dynamic>? extra,
  }) {
    final buffer = StringBuffer();
    
    // Level color coding for console output
    const levelColors = {
      debugLevel: '\x1B[36m',    // Cyan
      infoLevel: '\x1B[32m',     // Green
      warningLevel: '\x1B[33m',  // Yellow
      errorLevel: '\x1B[31m',    // Red
      criticalLevel: '\x1B[35m', // Magenta
    };
    
    final color = levelColors[level] ?? '\x1B[0m';
    const reset = '\x1B[0m';
    
    buffer.write('$color[$level]$reset');
    
    if (tag != null) {
      buffer.write(' [$tag]');
    }
    
    buffer.write(': $message');
    
    if (extra != null && extra.isNotEmpty) {
      buffer.write(' | Extra: $extra');
    }
    
    return buffer.toString();
  }
  
  /// Log to appropriate destination based on platform and configuration
  void _logToAppropriateDestination({
    required Map<String, dynamic> logEntry,
    required String formattedMessage,
  }) {
    // Always log to console in debug mode
    if (kDebugMode) {
      developer.log(formattedMessage, name: 'edu_flow');
    }
    
    // Platform-specific logging
    if (kIsWeb) {
      _logToWeb(logEntry);
    } else {
      _logToNative(logEntry);
    }
    
    // TODO: Implement file logging for mobile/desktop platforms
    // TODO: Implement external logging service integration
  }
  
  /// Web-specific logging
  void _logToWeb(Map<String, dynamic> logEntry) {
    // Use standard debugPrint for web platform
    final level = logEntry['level'];
    final message = logEntry['message'];
    debugPrint('[$level] $message - $logEntry');
  }
  
  /// Native platform logging (iOS, Android, Desktop)
  void _logToNative(Map<String, dynamic> logEntry) {
    // Use native logging mechanisms
    final level = logEntry['level'];
    final message = logEntry['message'];
    
    switch (level) {
      case debugLevel:
        debugPrint('[DEBUG] $message');
        break;
      case infoLevel:
        debugPrint('[INFO] $message');
        break;
      case warningLevel:
        debugPrint('[WARNING] $message');
        break;
      case errorLevel:
        debugPrint('[ERROR] $message');
        break;
      case criticalLevel:
        debugPrint('[CRITICAL] $message');
        break;
    }
  }
  
  /// Enable performance tracking
  void _enablePerformanceTracking() {
    // TODO: Implement performance tracking using Flutter's Performance API
    // Track frame drops, UI jank, memory usage, etc.
  }
  
  /// Create a logger with specific tag
  Logger withTag(String tag) {
    return _LoggerImpl(this, tag);
  }
  
  /// Get log history (simplified version)
  List<Map<String, dynamic>> getLogHistory() {
    // TODO: Implement log history retrieval from local storage
    return [];
  }
  
  /// Clear log history
  void clearLogHistory() {
    // TODO: Implement log history clearing
  }
}

/// Logger interface for tagged logging
abstract class Logger {
  void d(String message, {Map<String, dynamic>? extra});
  void i(String message, {Map<String, dynamic>? extra});
  void w(String message, {Map<String, dynamic>? extra});
  void e(String message, {dynamic error, StackTrace? stackTrace, Map<String, dynamic>? extra});
  void c(String message, {dynamic error, StackTrace? stackTrace, Map<String, dynamic>? extra});
  void network(String endpoint, {String method = 'GET', Map<String, dynamic>? request, Map<String, dynamic>? response, int? statusCode, String? statusMessage});
  void uiEvent(String component, String event, {Map<String, dynamic>? data});
  void performance(String operation, {DateTime? startTime, DateTime? endTime, Map<String, dynamic>? metrics});
  void userAction(String action, {String? userId, String? screen, Map<String, dynamic>? data});
  void apiRequest(String endpoint, {String method = 'GET', Map<String, dynamic>? headers, dynamic body});
  void apiResponse(String endpoint, {required int statusCode, String? statusMessage, dynamic data});
  void dbOperation(String operation, {String? collection, String? documentId, dynamic data, dynamic result});
}

/// Logger implementation
class _LoggerImpl implements Logger {
  final LoggingService _service;
  final String _tag;
  
  _LoggerImpl(this._service, this._tag);
  
  @override
  void d(String message, {Map<String, dynamic>? extra}) {
    _service.debug(message, tag: _tag, extra: extra);
  }
  
  @override
  void i(String message, {Map<String, dynamic>? extra}) {
    _service.info(message, tag: _tag, extra: extra);
  }
  
  @override
  void w(String message, {Map<String, dynamic>? extra}) {
    _service.warning(message, tag: _tag, extra: extra);
  }
  
  @override
  void e(String message, {dynamic error, StackTrace? stackTrace, Map<String, dynamic>? extra}) {
    _service.error(message, error: error, stackTrace: stackTrace, tag: _tag, extra: extra);
  }
  
  @override
  void c(String message, {dynamic error, StackTrace? stackTrace, Map<String, dynamic>? extra}) {
    _service.critical(message, error: error, stackTrace: stackTrace, tag: _tag, extra: extra);
  }
  
  @override
  void network(String endpoint, {String method = 'GET', Map<String, dynamic>? request, Map<String, dynamic>? response, int? statusCode, String? statusMessage}) {
    _service.network(endpoint, method: method, request: request, response: response, statusCode: statusCode, statusMessage: statusMessage, tag: _tag);
  }
  
  @override
  void uiEvent(String component, String event, {Map<String, dynamic>? data}) {
    _service.uiEvent(component, event, data: data, tag: _tag);
  }
  
  @override
  void performance(String operation, {DateTime? startTime, DateTime? endTime, Map<String, dynamic>? metrics}) {
    _service.performance(operation, startTime: startTime, endTime: endTime, metrics: metrics, tag: _tag);
  }
  
  @override
  void userAction(String action, {String? userId, String? screen, Map<String, dynamic>? data}) {
    _service.userAction(action, userId: userId, screen: screen, data: data, tag: _tag);
  }
  
  @override
  void apiRequest(String endpoint, {String method = 'GET', Map<String, dynamic>? headers, dynamic body}) {
    _service.apiRequest(endpoint, method: method, headers: headers, body: body, tag: _tag);
  }
  
  @override
  void apiResponse(String endpoint, {required int statusCode, String? statusMessage, dynamic data}) {
    _service.apiResponse(endpoint, statusCode: statusCode, statusMessage: statusMessage, data: data, tag: _tag);
  }
  
  @override
  void dbOperation(String operation, {String? collection, String? documentId, dynamic data, dynamic result}) {
    _service.dbOperation(operation, collection: collection, documentId: documentId, data: data, result: result, tag: _tag);
  }
}