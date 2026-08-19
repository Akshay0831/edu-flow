import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static AppConfig? _instance;
  static AppConfig get instance => _instance ??= AppConfig._internal();
  
  AppConfig._internal();

  String get apiBaseUrl {
    return dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000';
  }

  String get apiVersion {
    return dotenv.env['API_VERSION'] ?? '/api/v1';
  }

  String get authEndpoint {
    return '$apiBaseUrl$apiVersion/auth';
  }

  String get usersEndpoint {
    return '$apiBaseUrl$apiVersion/users';
  }

  String get studentsEndpoint {
    return '$apiBaseUrl$apiVersion/students';
  }

  String get teachersEndpoint {
    return '$apiBaseUrl$apiVersion/teachers';
  }

  String get coursesEndpoint {
    return '$apiBaseUrl$apiVersion/courses';
  }

  String get assessmentsEndpoint {
    return '$apiBaseUrl$apiVersion/assessments';
  }

  String get analyticsEndpoint {
    return '$apiBaseUrl$apiVersion/analytics';
  }

  bool get enableAnalytics {
    return dotenv.env['ENABLE_ANALYTICS']?.toLowerCase() == 'true';
  }

  bool get enableCrashReporting {
    return dotenv.env['ENABLE_CRASH_REPORTING']?.toLowerCase() == 'true';
  }

  String get appVersion {
    return dotenv.env['APP_VERSION'] ?? '1.0.0';
  }

  String get environment {
    return dotenv.env['ENVIRONMENT'] ?? 'development';
  }

  bool get isDevelopment {
    return environment == 'development';
  }

  bool get isProduction {
    return environment == 'production';
  }

  int get maxCacheSize {
    return int.parse(dotenv.env['MAX_CACHE_SIZE'] ?? '100');
  }

  Duration get cacheExpiry {
    final hours = int.parse(dotenv.env['CACHE_EXPIRY_HOURS'] ?? '24');
    return Duration(hours: hours);
  }

  String get defaultLanguage {
    return dotenv.env['DEFAULT_LANGUAGE'] ?? 'en';
  }

  String get defaultCountry {
    return dotenv.env['DEFAULT_COUNTRY'] ?? 'US';
  }

  List<String> get supportedLanguages {
    return dotenv.env['SUPPORTED_LANGUAGES']?.split(',') ?? ['en', 'es', 'fr', 'de', 'zh'];
  }

  bool get enableNotifications {
    return dotenv.env['ENABLE_NOTIFICATIONS']?.toLowerCase() == 'true';
  }

  String get notificationChannel {
    return dotenv.env['NOTIFICATION_CHANNEL'] ?? 'edu_flow';
  }

  int get maxImageSize {
    return int.parse(dotenv.env['MAX_IMAGE_SIZE'] ?? '5242880'); // 5MB
  }

  List<String> get supportedImageFormats {
    return dotenv.env['SUPPORTED_IMAGE_FORMATS']?.split(',') ?? ['jpg', 'jpeg', 'png', 'gif'];
  }

  int get maxFileSize {
    return int.parse(dotenv.env['MAX_FILE_SIZE'] ?? '10485760'); // 10MB
  }

  List<String> get supportedFileFormats {
    return dotenv.env['SUPPORTED_FILE_FORMATS']?.split(',') ?? ['pdf', 'doc', 'docx', 'txt'];
  }

  Duration get requestTimeout {
    final seconds = int.parse(dotenv.env['REQUEST_TIMEOUT_SECONDS'] ?? '30');
    return Duration(seconds: seconds);
  }

  int get maxRetryAttempts {
    return int.parse(dotenv.env['MAX_RETRY_ATTEMPTS'] ?? '3');
  }

  Duration get retryDelay {
    final seconds = int.parse(dotenv.env['RETRY_DELAY_SECONDS'] ?? '1');
    return Duration(seconds: seconds);
  }
}