import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'index.dart';
import '../charts/analytics_dashboard.dart';

class ComponentsDemoScreen extends ConsumerStatefulWidget {
  const ComponentsDemoScreen({super.key});

  @override
  ConsumerState<ComponentsDemoScreen> createState() => _ComponentsDemoScreenState();
}

class _ComponentsDemoScreenState extends ConsumerState<ComponentsDemoScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 5,
      vsync: this,
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: 'Components Demo',
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: 'Basic Components'),
            Tab(text: 'Authentication'),
            Tab(text: 'Charts'),
            Tab(text: 'Utilities'),
            Tab(text: 'App Structure'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildBasicComponentsTab(),
          _buildAuthComponentsTab(),
          _buildChartsTab(),
          _buildUtilitiesTab(),
          _buildAppStructureTab(),
        ],
      ),
    );
  }

  Widget _buildBasicComponentsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Basic UI Components',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Custom Button
          const Text('Custom Button', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              CustomButton(
                text: 'Primary',
                onPressed: () => CustomSnackBar.showSuccess(context: context, message: 'Primary button clicked'),
              ),
              CustomButton(
                text: 'Outlined',
                isOutlined: true,
                onPressed: () => CustomSnackBar.showInfo(context: context, message: 'Outlined button clicked'),
              ),
              CustomButton(
                text: 'Disabled',
                isDisabled: true,
                onPressed: () {},
              ),
              CustomButton(
                text: 'Loading',
                isLoading: true,
                onPressed: () {},
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          // Custom Card
          const Text('Custom Card', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          CustomCard(
            backgroundColor: Colors.blue[50],
            hasBorder: true,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'This is a custom card with various customization options.',
                style: TextStyle(fontSize: 16),
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Custom Text Field
          const Text('Custom Text Field', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          CustomTextField(
            labelText: 'Name',
            hintText: 'Enter your name',
            prefixIcon: Icons.person,
            onChanged: (value) => print('Name: $value'),
          ),
          
          const SizedBox(height: 24),
          
          // Custom List Tile
          const Text('Custom List Tile', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Column(
            children: [
              CustomListTile(
                title: 'Dashboard',
                subtitle: 'View your dashboard',
                leading: const Icon(Icons.dashboard),
                onTap: () => CustomSnackBar.showSuccess(context: context, message: 'Dashboard tapped'),
              ),
              CustomListTile(
                title: 'Settings',
                subtitle: 'Configure app settings',
                leading: const Icon(Icons.settings),
                isSelected: true,
                onTap: () => CustomSnackBar.showSuccess(context: context, message: 'Settings tapped'),
              ),
              CustomListTile(
                title: 'Profile',
                subtitle: 'Manage your profile',
                leading: const Icon(Icons.person),
                onTap: () => CustomSnackBar.showSuccess(context: context, message: 'Profile tapped'),
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          // Loading Indicator
          const Text('Loading Indicator', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const LoadingIndicator(message: 'Loading...'),
        ],
      ),
    );
  }

  Widget _buildAuthComponentsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Authentication Components',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Auth Wrapper
          const Text('Auth Wrapper', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Auth Wrapper provides authentication state management and role-based access control.',
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Password Strength Indicator
          const Text('Password Strength Indicator', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const PasswordStrengthIndicator(
            password: 'Password123!',
            label: 'Password Strength',
            showDetailedScore: true,
          ),
          
          const SizedBox(height: 24),
          
          // Password Generator
          const Text('Password Generator', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const PasswordGenerator(),
          
          const SizedBox(height: 24),
          
          // Multi-factor Auth
          const Text('Multi-factor Authentication', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Multi-factor authentication provides enhanced security with various verification methods.',
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Social Auth Buttons
          const Text('Social Authentication', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          SocialAuthButtons(
            onGoogleSignIn: () => CustomSnackBar.showSuccess(context: context, message: 'Google sign in clicked'),
            onAppleSignIn: () => CustomSnackBar.showSuccess(context: context, message: 'Apple sign in clicked'),
          ),
          
          const SizedBox(height: 24),
          
          // Biometric Auth
          const Text('Biometric Authentication', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const BiometricAuthButton(
            onAuthenticate: null,
          ),
        ],
      ),
    );
  }

  Widget _buildChartsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Data Visualization',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Analytics Dashboard
          const Text('Analytics Dashboard', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          AnalyticsDashboard(
            performanceData: const [
              {'label': 'Jan', 'value': 65},
              {'label': 'Feb', 'value': 78},
              {'label': 'Mar', 'value': 85},
              {'label': 'Apr', 'value': 92},
              {'label': 'May', 'value': 88},
            ],
            enrollmentData: const [
              {'label': 'Jan', 'value': 120},
              {'label': 'Feb', 'value': 135},
              {'label': 'Mar', 'value': 150},
              {'label': 'Apr', 'value': 165},
              {'label': 'May', 'value': 180},
            ],
            summaryMetrics: const {
              'totalStudents': 1250,
              'activeCourses': 45,
              'averageScore': 78.5,
            },
            availableFilters: const ['weekly', 'monthly', 'yearly'],
            onFilterChanged: (filter) => CustomSnackBar.showInfo(context: context, message: 'Filter changed to $filter'),
          ),
        ],
      ),
    );
  }

  Widget _buildUtilitiesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Utility Components',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Custom Alert Dialog
          const Text('Custom Alert Dialog', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: () {
              CustomAlertDialog.show(
                context: context,
                title: 'Confirm Action',
                content: 'Are you sure you want to perform this action?',
                confirmText: 'Confirm',
                cancelText: 'Cancel',
                isDestructiveAction: true,
                onConfirm: () => CustomSnackBar.showSuccess(context: context, message: 'Action confirmed'),
              );
            },
            child: const Text('Show Dialog'),
          ),
          
          const SizedBox(height: 24),
          
          // Custom Snackbar
          const Text('Custom Snackbar', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Column(
            children: [
              ElevatedButton(
                onPressed: () => CustomSnackBar.showSuccess(context: context, message: 'Success message'),
                child: const Text('Show Success'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => CustomSnackBar.showError(context: context, message: 'Error message'),
                child: const Text('Show Error'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => CustomSnackBar.showInfo(context: context, message: 'Info message'),
                child: const Text('Show Info'),
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          // Offline Support
          const Text('Offline Support', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const OfflineSupportIndicator(
            message: 'You are offline. Changes will be synced when online.',
            child: Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('Content with offline support'),
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Performance Monitor
          const Text('Performance Monitor', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const PerformanceMonitor(
            enabled: true,
            screenName: 'Demo Screen',
            child: Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('Performance monitoring enabled'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppStructureTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Application Structure',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Application Wrapper
          const Text('Application Wrapper', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Application Wrapper provides the main app structure with navigation, drawer, and bottom navigation.',
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Dashboard Screen Wrapper
          const Text('Dashboard Screen Wrapper', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Dashboard Screen Wrapper includes quick actions and sync functionality.',
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Usage Examples
          const Text('Usage Examples', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          ExpansionTile(
            title: const Text('How to use components'),
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '1. Import components:',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      color: Colors.grey[200],
                      child: const Text(
                        "import 'package:edu_flow/presentation/widgets/common/index.dart';",
                        style: TextStyle(fontFamily: 'monospace'),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '2. Use components in your widgets:',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      color: Colors.grey[200],
                      child: const Text(
                        "CustomButton(\n"
                        "  text: 'Click me',\n"
                        "  onPressed: () {\n"
                        "    CustomSnackBar.showSuccess(context, message: 'Clicked!');\n"
                        "  },\n"
                        ")",
                        style: TextStyle(fontFamily: 'monospace'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}