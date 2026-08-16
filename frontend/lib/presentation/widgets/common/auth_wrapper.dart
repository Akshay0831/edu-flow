import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:edu_flow/data/services/auth_state_service.dart';
import 'package:edu_flow/data/services/auth_service.dart';
import 'loading_indicator.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

class AuthWrapper extends ConsumerWidget {
  final Widget? authenticatedChild;
  final Widget? child;
  final Widget? loginScreen;
  final Widget? loadingScreen;
  final Widget? loadingWidget;
  final Widget? errorWidget;
  final Widget? unauthenticatedChild;
  final List<String>? roles;
  final String? redirectTo;
  final bool showLoadingIndicator;

  const AuthWrapper({
    super.key,
    this.authenticatedChild,
    this.child,
    this.loginScreen,
    this.loadingScreen,
    this.loadingWidget,
    this.errorWidget,
    this.unauthenticatedChild,
    this.roles,
    this.redirectTo,
    this.showLoadingIndicator = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateServiceProvider);
    final effectiveChild = authenticatedChild ?? child ?? const SizedBox.shrink();

    if (authState.isLoading && showLoadingIndicator) {
      return loadingWidget ??
          loadingScreen ??
          const Scaffold(
            body: Center(
              child: LoadingIndicator(message: 'Authenticating...'),
            ),
          );
    }

    if (authState.isAuthenticated) {
      if (roles != null && roles!.isNotEmpty) {
        final userRole = authState.userRole?.toLowerCase() ?? '';
        final hasRole = roles!.any((r) => r.toLowerCase() == userRole);
        if (!hasRole) {
          return const Scaffold(
            body: Center(
              child: Text(
                'Access Denied',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          );
        }
      }
      return effectiveChild;
    }

    if (loginScreen != null) {
      return loginScreen!;
    }

    if (unauthenticatedChild != null) {
      return unauthenticatedChild!;
    }

    if (redirectTo != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.go(redirectTo!);
      });
      return const SizedBox.shrink();
    }

    return const Scaffold(
      body: Center(
        child: Text(
          'Please authenticate to continue',
          style: TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}

class ProtectedRoute extends StatelessWidget {
  final Widget child;
  final String? redirectTo;
  final bool requireAuth;

  const ProtectedRoute({
    super.key,
    required this.child,
    this.redirectTo = '/login',
    this.requireAuth = true,
  });

  @override
  Widget build(BuildContext context) {
    return AuthWrapper(
      redirectTo: requireAuth ? redirectTo : null,
      authenticatedChild: child,
    );
  }
}