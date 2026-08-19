import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'common/index.dart';

class ApplicationWrapper extends StatelessWidget {
  final Widget child;

  const ApplicationWrapper({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'EduFlow',
        hasBackButton: false,
      ),
      body: PerformanceMonitor(
        enabled: true,
        screenName: 'Application',
        child: OfflineSupportIndicator(
          message: 'You are offline. Changes will be synced when online.',
          child: child,
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          CustomSnackBar.showSuccess(
            context: context,
            message: 'Action completed successfully',
          );
        },
        child: const Icon(Icons.add),
      ),
      drawer: _buildDrawer(context),
      bottomNavigationBar: _buildBottomNavigationBar(context),
    );
  }

  Drawer _buildDrawer(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const CircleAvatar(
                  radius: 32,
                  backgroundColor: Colors.white,
                  child: Icon(Icons.person, size: 40),
                ),
                const SizedBox(height: 16),
                Text(
                  'John Doe',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'john.doe@example.com',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white70,
                  ),
                ),
              ],
            ),
          ),
          _buildDrawerItem(
            icon: Icons.dashboard,
            title: 'Dashboard',
            onTap: () => context.go('/dashboard'),
          ),
          _buildDrawerItem(
            icon: Icons.book,
            title: 'Courses',
            onTap: () => context.go('/courses'),
          ),
          _buildDrawerItem(
            icon: Icons.people,
            title: 'Students',
            onTap: () => context.go('/students'),
          ),
          _buildDrawerItem(
            icon: Icons.assessment,
            title: 'Analytics',
            onTap: () => context.go('/analytics'),
          ),
          _buildDrawerItem(
            icon: Icons.settings,
            title: 'Settings',
            onTap: () => context.go('/settings'),
          ),
          const Divider(),
          _buildDrawerItem(
            icon: Icons.exit_to_app,
            title: 'Logout',
            onTap: () => _handleLogout(context),
          ),
        ],
      ),
    );
  }

  Widget _buildDrawerItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      onTap: onTap,
    );
  }

  void _handleLogout(BuildContext context) {
    CustomAlertDialog.show(
      context: context,
      title: 'Confirm Logout',
      content: 'Are you sure you want to logout?',
      confirmText: 'Logout',
      cancelText: 'Cancel',
      isDestructiveAction: true,
      onConfirm: () {
        CustomSnackBar.showSuccess(
          context: context,
          message: 'Logged out successfully',
        );
        context.go('/login');
      },
    );
  }

  BottomNavigationBar _buildBottomNavigationBar(BuildContext context) {
    return BottomNavigationBar(
      type: BottomNavigationBarType.fixed,
      items: const [
        BottomNavigationBarItem(
          icon: Icon(Icons.home),
          label: 'Home',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.search),
          label: 'Search',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.notifications),
          label: 'Notifications',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person),
          label: 'Profile',
        ),
      ],
      currentIndex: 0,
      onTap: (index) {
        switch (index) {
          case 0:
            context.go('/dashboard');
            break;
          case 1:
            context.go('/search');
            break;
          case 2:
            context.go('/notifications');
            break;
          case 3:
            context.go('/profile');
            break;
        }
      },
    );
  }
}

class DashboardScreenWrapper extends StatelessWidget {
  final Widget child;

  const DashboardScreenWrapper({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Dashboard',
      ),
      body: Column(
        children: [
          Expanded(
            child: child,
          ),
          _buildQuickActions(context),
        ],
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildQuickActionCard(
                icon: Icons.add,
                title: 'Add Course',
                onTap: () => context.go('/courses/new'),
                color: Colors.blue,
              ),
              _buildQuickActionCard(
                icon: Icons.upload_file,
                title: 'Upload Material',
                onTap: () => CustomSnackBar.showInfo(
                  context: context,
                  message: 'Upload feature coming soon',
                ),
                color: Colors.green,
              ),
              _buildQuickActionCard(
                icon: Icons.assessment,
                title: 'View Reports',
                onTap: () => context.go('/reports'),
                color: Colors.orange,
              ),
            ],
          ),
          const SizedBox(height: 16),
          SyncButton(
            onSync: () async {
              // This is safe because the BuildContext is not being used across widget rebuilds
              await Future.delayed(const Duration(seconds: 2));
            },
            successMessage: 'Data synced successfully',
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionCard({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    required Color color,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              title,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}