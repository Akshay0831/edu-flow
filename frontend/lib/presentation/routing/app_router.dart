import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';
import 'package:edu_flow/core/theme/app_theme.dart';
import 'package:edu_flow/presentation/screens/auth/login_screen.dart';
import 'package:edu_flow/presentation/screens/auth/register_screen.dart';
import 'package:edu_flow/presentation/screens/auth/forgot_password_screen.dart';
import 'package:edu_flow/presentation/screens/dashboard/dashboard_screen.dart';
import 'package:edu_flow/presentation/screens/profile/profile_screen.dart';
import 'package:edu_flow/presentation/screens/courses/courses_screen.dart';
import 'package:edu_flow/presentation/screens/courses/course_details_screen.dart';
import 'package:edu_flow/presentation/screens/students/students_screen.dart';
import 'package:edu_flow/presentation/screens/students/student_details_screen.dart';
import 'package:edu_flow/presentation/screens/teachers/teachers_screen.dart';
import 'package:edu_flow/presentation/screens/teachers/teacher_details_screen.dart';
import 'package:edu_flow/presentation/screens/assessments/assessments_screen.dart';
import 'package:edu_flow/presentation/screens/assessments/assessment_details_screen.dart';
import 'package:edu_flow/presentation/screens/settings/settings_screen.dart';
import 'package:edu_flow/presentation/screens/splash/splash_screen.dart';

class AppRouter {
  late final GoRouter router;

  AppRouter() {
    router = GoRouter(
      initialLocation: '/splash',
      routes: [
        // Splash screen
        GoRoute(
          path: '/splash',
          builder: (context, state) => const SplashScreen(),
        ),
        
        // Auth routes
        GoRoute(
          path: '/login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/register',
          builder: (context, state) => const RegisterScreen(),
        ),
        GoRoute(
          path: '/forgot-password',
          builder: (context, state) => const ForgotPasswordScreen(),
        ),
        
        // Main app routes
        ShellRoute(
          builder: (context, state, child) => MainWrapper(child: child),
          routes: [
            // Dashboard
            GoRoute(
              path: '/dashboard',
              builder: (context, state) => const DashboardScreen(),
            ),
            
            // Profile
            GoRoute(
              path: '/profile',
              builder: (context, state) => const ProfileScreen(),
            ),
            
            // Courses
            GoRoute(
              path: '/courses',
              builder: (context, state) => const CoursesScreen(),
            ),
            GoRoute(
              path: '/courses/:id',
              builder: (context, state) => CourseDetailsScreen(
                courseId: state.pathParameters['id']!,
              ),
            ),
            
            // Students
            GoRoute(
              path: '/students',
              builder: (context, state) => const StudentsScreen(),
            ),
            GoRoute(
              path: '/students/:id',
              builder: (context, state) => StudentDetailsScreen(
                studentId: state.pathParameters['id']!,
              ),
            ),
            
            // Teachers
            GoRoute(
              path: '/teachers',
              builder: (context, state) => const TeachersScreen(),
            ),
            GoRoute(
              path: '/teachers/:id',
              builder: (context, state) => TeacherDetailsScreen(
                teacherId: state.pathParameters['id']!,
              ),
            ),
            
            // Assessments
            GoRoute(
              path: '/assessments',
              builder: (context, state) => const AssessmentsScreen(),
            ),
            GoRoute(
              path: '/assessments/:id',
              builder: (context, state) => AssessmentDetailsScreen(
                assessmentId: state.pathParameters['id']!,
              ),
            ),
            
            // Settings
            GoRoute(
              path: '/settings',
              builder: (context, state) => const SettingsScreen(),
            ),
          ],
        ),
      ],
      errorBuilder: (context, state) => ErrorScreen(
        error: state.error,
      ),
    );
  }
}

class MainWrapper extends StatelessWidget {
  final Widget child;
  
  const MainWrapper({super.key, required this.child});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _getCurrentIndex(context),
        onTap: (index) {
          _navigateToIndex(context, index);
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.book),
            label: 'Courses',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.people),
            label: 'Students',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
  
  int _getCurrentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    
    if (location.contains('/dashboard')) return 0;
    if (location.contains('/courses')) return 1;
    if (location.contains('/students')) return 2;
    if (location.contains('/profile')) return 3;
    
    return 0;
  }
  
  void _navigateToIndex(BuildContext context, int index) {
    switch (index) {
      case 0:
        GoRouter.of(context).go('/dashboard');
        break;
      case 1:
        GoRouter.of(context).go('/courses');
        break;
      case 2:
        GoRouter.of(context).go('/students');
        break;
      case 3:
        GoRouter.of(context).go('/profile');
        break;
    }
  }
}

class ErrorScreen extends StatelessWidget {
  final Exception? error;
  
  const ErrorScreen({super.key, this.error});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Error'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: AppTheme.errorColor,
            ),
            const SizedBox(height: 16),
            const Text(
              'Something went wrong',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            if (error != null)
              Text(
                error.toString(),
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                GoRouter.of(context).go('/dashboard');
              },
              child: const Text('Go to Dashboard'),
            ),
          ],
        ),
      ),
    );
  }
}