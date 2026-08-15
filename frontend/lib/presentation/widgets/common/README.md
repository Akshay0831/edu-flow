# EduFlow Flutter Components Library

A comprehensive collection of reusable Flutter widgets designed for the EduFlow education management system.

## Overview

This library provides a wide range of pre-built, customizable components that follow Material Design guidelines and best practices. All components are designed to be:

- **Consistent**: Uniform design language across the application
- **Customizable**: Configurable properties for different use cases
- **Accessible**: Built with accessibility in mind
- **Testable**: Easy to unit and integration test
- **Performance-Optimized**: Efficient rendering and state management

## Quick Start

### Installation

The components are included in the EduFlow Flutter project. No additional installation is required.

### Basic Usage

```dart
import 'package:edu_flow/presentation/widgets/common/index.dart';

// Basic button
CustomButton(
  text: 'Click Me',
  onPressed: () {
    CustomSnackBar.showSuccess(context, message: 'Button clicked!');
  },
)

// Form field with validation
CustomTextField(
  labelText: 'Email',
  hintText: 'Enter your email',
  validator: (value) {
    if (value == null || value.isEmpty) {
      return 'Please enter your email';
    }
    return null;
  },
)

// Alert dialog
CustomAlertDialog.show(
  context: context,
  title: 'Confirm Action',
  content: 'Are you sure?',
  onConfirm: () {
    // Handle confirmation
  },
)
```

## Component Categories

### 1. Basic UI Components

#### CustomButton
A versatile button component with various styles and states.

```dart
CustomButton(
  text: 'Primary Button',
  onPressed: () {},
  isLoading: false,
  isOutlined: false,
  isDisabled: false,
  icon: Icons.add,
  width: double.infinity,
  height: 48,
  borderRadius: 8,
)
```

#### CustomTextField
A customizable text field with validation and various input types.

```dart
CustomTextField(
  labelText: 'Full Name',
  hintText: 'Enter your full name',
  prefixIcon: Icons.person,
  suffixIcon: Icons.clear,
  obscureText: false,
  keyboardType: TextInputType.name,
  validator: (value) => value?.isNotEmpty == null ? 'Required' : null,
)
```

#### CustomCard
A card component with customizable appearance and interactions.

```dart
CustomCard(
  child: Column(
    children: [
      Text('Card Title'),
      Text('Card Content'),
    ],
  ),
  onTap: () {},
  hasBorder: true,
  elevation: 4,
  borderRadius: 12,
)
```

#### CustomListTile
A customizable list item for navigation and selections.

```dart
CustomListTile(
  title: 'Dashboard',
  subtitle: 'View analytics and reports',
  leading: Icon(Icons.dashboard),
  trailing: Icon(Icons.arrow_forward_ios),
  onTap: () {},
  isSelected: true,
)
```

#### CustomAppBar
A customizable app bar with various features.

```dart
CustomAppBar(
  title: 'App Title',
  actions: [
    IconButton(icon: Icons.search, onPressed: () {}),
    IconButton(icon: Icons.notifications, onPressed: () {}),
  ],
  centerTitle: true,
  elevation: 2,
)
```

#### CustomAlertDialog
A customizable alert dialog component.

```dart
CustomAlertDialog.show(
  context: context,
  title: 'Delete Item',
  content: 'This action cannot be undone.',
  confirmText: 'Delete',
  cancelText: 'Cancel',
  isDestructiveAction: true,
  onConfirm: () {},
)
```

#### CustomSnackBar
A customizable snackbar for notifications.

```dart
CustomSnackBar.showSuccess(
  context: context,
  message: 'Operation completed successfully',
  actionLabel: 'Undo',
  onAction: () {},
)
```

#### LoadingIndicator
Loading indicator with optional message.

```dart
LoadingIndicator(
  message: 'Loading...',
  size: 32,
  strokeWidth: 3,
)
```

### 2. Authentication Components

#### AuthWrapper
Authentication state management wrapper.

```dart
AuthWrapper(
  authenticatedChild: DashboardScreen(),
  redirectTo: '/login',
)
```

#### ProtectedRoute
Route with authentication requirements.

```dart
ProtectedRoute(
  child: DashboardScreen(),
  redirectTo: '/login',
  requireAuth: true,
)
```

#### RoleBasedRoute
Route with role-based access control.

```dart
RoleBasedRoute(
  child: AdminScreen(),
  allowedRoles: ['admin'],
  redirectTo: '/unauthorized',
)
```

#### MultiFactorAuthScreen
Multi-factor authentication interface.

```dart
MultiFactorAuthScreen(
  email: 'user@example.com',
  password: 'password123',
  role: 'student',
)
```

#### PasswordStrengthIndicator
Real-time password strength evaluation.

```dart
PasswordStrengthIndicator(
  password: 'Password123!',
  label: 'Password Strength',
  showDetailedScore: true,
)
```

#### PasswordGenerator
Secure password generator with customizable criteria.

```dart
PasswordGenerator(
  length: 12,
  includeUppercase: true,
  includeLowercase: true,
  includeNumbers: true,
  includeSymbols: true,
  onPasswordGenerated: (password) {
    // Handle generated password
  },
)
```

#### SocialAuthButtons
Social media authentication buttons.

```dart
SocialAuthButtons(
  onGoogleSignIn: () {},
  onAppleSignIn: () {},
  onMicrosoftSignIn: () {},
)
```

### 3. Data Visualization Components

#### AnalyticsDashboard
Comprehensive analytics dashboard with charts and metrics.

```dart
AnalyticsDashboard(
  performanceData: [
    {'label': 'Jan', 'value': 65},
    {'label': 'Feb', 'value': 78},
  ],
  enrollmentData: [
    {'label': 'Jan', 'value': 120},
    {'label': 'Feb', 'value': 135},
  ],
  summaryMetrics: {
    'totalStudents': 1250,
    'activeCourses': 45,
    'averageScore': 78.5,
  },
  availableFilters: ['weekly', 'monthly', 'yearly'],
  onFilterChanged: (filter) {},
)
```

### 4. Utility Components

#### OfflineSupportManager
Offline state management and synchronization.

```dart
OfflineSupportIndicator(
  message: 'You are offline. Changes will be synced when online.',
  child: ContentWidget(),
)
```

#### SyncButton
Manual sync trigger for offline data.

```dart
SyncButton(
  onSync: () async {
    // Perform sync operation
  },
  successMessage: 'Sync completed',
)
```

#### PerformanceMonitor
Performance monitoring and analytics.

```dart
PerformanceMonitor(
  enabled: true,
  screenName: 'Dashboard',
  child: ContentWidget(),
)
```

### 5. Application Structure Components

#### ApplicationWrapper
Main application wrapper with navigation and branding.

```dart
ApplicationWrapper(
  child: DashboardScreen(),
)
```

#### DashboardScreenWrapper
Dashboard-specific wrapper with quick actions.

```dart
DashboardScreenWrapper(
  child: DashboardContent(),
)
```

## Advanced Features

### Customization

All components support extensive customization through their properties:

```dart
CustomButton(
  text: 'Custom Button',
  onPressed: () {},
  backgroundColor: Colors.blue[600],
  textColor: Colors.white,
  borderRadius: 12,
  height: 56,
  icon: Icons.custom_icon,
  iconPosition: IconPosition.leading,
)
```

### Theming

Components integrate with Flutter's theme system:

```dart
Theme(
  data: ThemeData(
    primaryColor: Colors.blue,
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.blue[600],
      ),
    ),
  ),
  child: CustomButton(
    text: 'Themed Button',
    onPressed: () {},
  ),
)
```

### Responsive Design

Components are designed to work with different screen sizes:

```dart
LayoutBuilder(
  builder: (context, constraints) {
    return CustomCard(
      width: constraints.maxWidth * 0.8,
      child: Content(),
    );
  },
)
```

## Testing

### Unit Testing

```dart
testWidgets('CustomButton responds to tap', (WidgetTester tester) async {
  bool tapped = false;
  
  await tester.pumpWidget(
    MaterialApp(
      home: CustomButton(
        text: 'Test',
        onPressed: () => tapped = true,
      ),
    ),
  );
  
  await tester.tap(find.text('Test'));
  await tester.pump();
  
  expect(tapped, true);
});
```

### Widget Testing

```dart
testWidgets('CustomTextField validation', (WidgetTester tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: CustomTextField(
        labelText: 'Test',
        validator: (value) => value?.isNotEmpty == null ? 'Required' : null,
      ),
    ),
  );
  
  await tester.enterText(find.byType(TextField), '');
  await tester.tap(find.text('Submit'));
  await tester.pump();
  
  expect(find.text('Required'), findsOneWidget);
});
```

## Performance Considerations

- **Minimal Rebuilds**: Components use const constructors where possible
- **Efficient State Management**: Leveraging Riverpod for reactive state
- **Lazy Loading**: Heavy components load on demand
- **Caching**: Image and data caching for better performance

## Contributing

To add new components:

1. Follow the existing structure and naming conventions
2. Include comprehensive documentation
3. Provide examples and usage patterns
4. Add unit tests
5. Ensure accessibility compliance
6. Review design guidelines for consistency

## Dependencies

- flutter: SDK dependency
- flutter_riverpod: State management
- go_router: Navigation
- fl_chart: Data visualization
- connectivity_plus: Offline detection
- shared_preferences: Local storage

## Future Enhancements

- Dark mode support
- Internationalization
- Advanced animations
- Custom theme system
- Component documentation generator

## Support

For issues and questions:
- Check the project documentation
- Review existing examples
- Create detailed bug reports
- Suggest improvements through project issues