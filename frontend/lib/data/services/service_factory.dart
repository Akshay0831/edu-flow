import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:edu_flow/data/api/api_client.dart';
import 'package:edu_flow/data/services/auth_service.dart';
import 'package:edu_flow/data/services/user_service.dart';
import 'package:edu_flow/data/services/student_service.dart';
import 'package:edu_flow/data/services/teacher_service.dart';
import 'package:edu_flow/data/services/course_service.dart';
import 'package:edu_flow/data/services/auth_state_service.dart';

// Create service providers using Riverpod for dependency injection

// Authentication Service
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

// User Service
final userServiceProvider = Provider<UserService>((ref) {
  return UserService();
});

// Student Service
final studentServiceProvider = Provider<StudentService>((ref) {
  return StudentService();
});

// Teacher Service
final teacherServiceProvider = Provider<TeacherService>((ref) {
  return TeacherService();
});

// Course Service
final courseServiceProvider = Provider<CourseService>((ref) {
  return CourseService();
});

// API Client Singleton
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient.instance;
});

// Service Factory for accessing all services
class ServiceFactory {
  final Ref ref;

  ServiceFactory(this.ref);

  // Get authentication service
  AuthService get auth => ref.read(authServiceProvider);

  // Get user service
  UserService get users => ref.read(userServiceProvider);

  // Get student service
  StudentService get students => ref.read(studentServiceProvider);

  // Get teacher service
  TeacherService get teachers => ref.read(teacherServiceProvider);

  // Get course service
  CourseService get courses => ref.read(courseServiceProvider);

  // Get API client
  ApiClient get api => ref.read(apiClientProvider);

  // Get auth state service
  AuthStateService get authState => ref.read(authStateServiceProvider.notifier);

  // Initialize all services
  Future<void> initialize() async {
    // Initialize auth state
    await ref.read(authStateServiceProvider.notifier).initialize();
  }

  // Clear all auth-related data
  Future<void> clearAuth() async {
    await ref.read(authStateServiceProvider.notifier).clearAuthState();
  }
}

// Service Factory Provider
final serviceFactoryProvider = Provider<ServiceFactory>((ref) {
  return ServiceFactory(ref);
});

// Convenience provider for accessing the service factory
final servicesProvider = Provider<ServiceFactory>((ref) {
  return ServiceFactory(ref);
});

// Auto-dispose providers for services that need to be recreated
final autoDisposeAuthServiceProvider = AutoDisposeProvider<AuthService>((ref) {
  return AuthService();
});

final autoDisposeUserServiceProvider = AutoDisposeProvider<UserService>((ref) {
  return UserService();
});

final autoDisposeStudentServiceProvider = AutoDisposeProvider<StudentService>((ref) {
  return StudentService();
});

final autoDisposeTeacherServiceProvider = AutoDisposeProvider<TeacherService>((ref) {
  return TeacherService();
});

final autoDisposeCourseServiceProvider = AutoDisposeProvider<CourseService>((ref) {
  return CourseService();
});

// Cache providers for frequently accessed data
final cachedUsersProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final userService = ref.read(userServiceProvider);
  try {
    return await userService.getAllUsers().then((users) => 
      users.map((user) => user.toJson()).toList());
  } catch (e) {
    throw Exception('Failed to load users: $e');
  }
});

final cachedStudentsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final studentService = ref.read(studentServiceProvider);
  try {
    return await studentService.getAllStudents().then((students) => 
      students.map((student) => student.toJson()).toList());
  } catch (e) {
    throw Exception('Failed to load students: $e');
  }
});

final cachedTeachersProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final teacherService = ref.read(teacherServiceProvider);
  try {
    return await teacherService.getAllTeachers().then((teachers) => 
      teachers.map((teacher) => teacher.toJson()).toList());
  } catch (e) {
    throw Exception('Failed to load teachers: $e');
  }
});

final cachedCoursesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final courseService = ref.read(courseServiceProvider);
  try {
    return await courseService.getAllCourses();
  } catch (e) {
    throw Exception('Failed to load courses: $e');
  }
});

// Invalidate cache providers
final invalidateCacheProvider = Provider((ref) {
  return () {
    ref.invalidate(cachedUsersProvider);
    ref.invalidate(cachedStudentsProvider);
    ref.invalidate(cachedTeachersProvider);
    ref.invalidate(cachedCoursesProvider);
  };
});

// Service utilities
class ServiceUtils {
  static String generateEndpoint(String base, String path, {Map<String, String>? params}) {
    final buffer = StringBuffer(base);
    if (path.startsWith('/')) {
      buffer.write(path);
    } else {
      buffer.write('/$path');
    }
    
    if (params != null && params.isNotEmpty) {
      buffer.write('?');
      buffer.write(params.entries.map((e) => '${e.key}=${e.value}').join('&'));
    }
    
    return buffer.toString();
  }

  static Map<String, dynamic> sanitizeForApi(Map<String, dynamic> data) {
    final sanitized = <String, dynamic>{};
    
    data.forEach((key, value) {
      if (value != null && value != '') {
        sanitized[key] = value;
      }
    });
    
    return sanitized;
  }

  static Map<String, String> buildQueryParams({
    String? search,
    String? role,
    String? department,
    String? semester,
    String? academicYear,
    String? program,
    String? year,
    int? page,
    int? pageSize,
    String? sortBy,
    String? sortOrder,
  }) {
    final params = <String, String>{};
    
    if (search != null && search.isNotEmpty) {
      params['q'] = search;
    }
    if (role != null && role.isNotEmpty) {
      params['role'] = role;
    }
    if (department != null && department.isNotEmpty) {
      params['department'] = department;
    }
    if (semester != null && semester.isNotEmpty) {
      params['semester'] = semester;
    }
    if (academicYear != null && academicYear.isNotEmpty) {
      params['academic_year'] = academicYear;
    }
    if (program != null && program.isNotEmpty) {
      params['program'] = program;
    }
    if (year != null && year.isNotEmpty) {
      params['year'] = year;
    }
    if (page != null) {
      params['page'] = page.toString();
    }
    if (pageSize != null) {
      params['page_size'] = pageSize.toString();
    }
    if (sortBy != null && sortBy.isNotEmpty) {
      params['sort_by'] = sortBy;
    }
    if (sortOrder != null && sortOrder.isNotEmpty) {
      params['sort_order'] = sortOrder;
    }
    
    return params;
  }
}