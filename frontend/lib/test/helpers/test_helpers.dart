/// Test helpers for mocking and testing utilities

import '../../data/api/api_client.dart';

/// Test helper class for managing ApiClient instances during tests
class ApiClientTestHelper {
  static ApiClient? _testInstance;
  
  /// Get the current test instance if set, otherwise return the real instance
  static ApiClient get instance {
    return _testInstance ?? ApiClient.instance;
  }
  
  /// Set a test instance (for mocking)
  static set testInstance(ApiClient? instance) {
    _testInstance = instance;
  }
  
  /// Clear the test instance and return to the real instance
  static void clearTestInstance() {
    _testInstance = null;
  }
}