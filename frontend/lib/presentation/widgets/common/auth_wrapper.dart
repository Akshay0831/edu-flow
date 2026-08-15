import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/services/auth_service.dart';
import 'loading_indicator.dart';

class AuthWrapper extends ConsumerWidget {
  final Widget authenticatedChild;
  final String? redirectTo;
  final bool showLoadingIndicator;

  const AuthWrapper({
    super.key,
    required this.authenticatedChild,
    this.redirectTo,
    this.showLoadingIndicator = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);

    return authState.when(
      loading: () {
        if (showLoadingIndicator) {
          return Scaffold(
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const LoadingIndicator(message: 'Checking authentication...'),
                  const SizedBox(height: 16),
                  Text(
                    'Please wait',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          );
        }
        return const SizedBox.shrink();
      },
      authenticated: (user) {
        return authenticatedChild;
      },
      unauthenticated: () {
        if (redirectTo != null) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            context.go(redirectTo!);
          });
          return const SizedBox.shrink();
        }
        return const Center(
          child: Text(
            'Please authenticate to continue',
            style: TextStyle(fontSize: 18),
          ),
        );
      },
      error: (error) {
        return Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, color: Colors.red, size: 48),
                const SizedBox(height: 16),
                Text(
                  'Authentication Error',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 8),
                Text(
                  error.toString(),
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {
                    ref.read(authServiceProvider).signOut();
                  },
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        );
      },
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
      authenticatedChild: child,
      redirectTo: requireAuth ? redirectTo : null,
      showLoadingIndicator: true,
    );
  }
}

class RoleBasedRoute extends StatelessWidget {
  final Widget child;
  final List<String> allowedRoles;
  final String redirectTo;
  final Widget? unauthorizedChild;

  const RoleBasedRoute({
    super.key,
    required this.child,
    required this.allowedRoles,
    this.redirectTo = '/unauthorized',
    this.unauthorizedChild,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, child) {
        final authState = ref.watch(authStateProvider);

        return authState.when(
          loading: () => const LoadingIndicator(message: 'Loading...'),
          authenticated: (user) {
            if (allowedRoles.contains(user.role)) {
              return child!;
            }
            return unauthorizedChild ?? _buildUnauthorizedPage(context);
          },
          unauthenticated: () => AuthWrapper(
            authenticatedChild: _buildUnauthorizedPage(context),
            redirectTo: '/login',
          ),
          error: (error) => _buildErrorPage(context, error),
        );
      },
      child: child,
    );
  }

  Widget _buildUnauthorizedPage(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Access Denied'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.lock_outlined, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Access Denied',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'You do not have permission to access this resource.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Go Back'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorPage(BuildContext context, dynamic error) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Error'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Error Loading Page',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              error.toString(),
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Go Back'),
            ),
          ],
        ),
      ),
    );
  }
}