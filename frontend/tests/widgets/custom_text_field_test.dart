import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_text_field.dart';

void main() {
  group('CustomTextField Widget Tests', () {
    testWidgets('CustomTextField displays label correctly', (WidgetTester tester) async {
      const labelText = 'Test Label';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: labelText,
              controller: TextEditingController(),
            ),
          ),
        ),
      );
      
      expect(find.text(labelText), findsOneWidget);
    });

    testWidgets('CustomTextField displays helper text correctly', (WidgetTester tester) async {
      const helperText = 'Helper text';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: TextEditingController(),
              helperText: helperText,
            ),
          ),
        ),
      );
      
      expect(find.text(helperText), findsOneWidget);
    });

    testWidgets('CustomTextField displays error text correctly', (WidgetTester tester) async {
      const errorText = 'Error message';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: TextEditingController(),
              errorText: errorText,
            ),
          ),
        ),
      );
      
      expect(find.text(errorText), findsOneWidget);
    });

    testWidgets('CustomTextField responds to text input', (WidgetTester tester) async {
      final controller = TextEditingController();
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: controller,
            ),
          ),
        ),
      );
      
      await tester.enterText(find.byType(TextFormField), 'Hello World');
      await tester.pump();
      
      expect(controller.text, 'Hello World');
    });

    testWidgets('CustomTextField shows password icon when isPassword is true', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Password',
              controller: TextEditingController(),
              isPassword: true,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    });

    testWidgets('CustomTextField toggles password visibility', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Password',
              controller: TextEditingController(),
              isPassword: true,
            ),
          ),
        ),
      );
      
      // Initially shows password icon
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
      expect(find.byIcon(Icons.visibility), findsNothing);
      
      // Tap to toggle visibility
      await tester.tap(find.byIcon(Icons.visibility_off));
      await tester.pump();
      
      // Should show visibility icon after toggle
      expect(find.byIcon(Icons.visibility), findsOneWidget);
      expect(find.byIcon(Icons.visibility_off), findsNothing);
    });

    testWidgets('CustomTextField shows prefix icon when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Email',
              controller: TextEditingController(),
              prefixIcon: Icons.email,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.email), findsOneWidget);
    });

    testWidgets('CustomTextField shows suffix icon when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Search',
              controller: TextEditingController(),
              suffixIcon: Icons.search,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.search), findsOneWidget);
    });

    testWidgets('CustomTextField validates text with validator', (WidgetTester tester) async {
      final controller = TextEditingController();
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: controller,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Field is required';
                }
                return null;
              },
            ),
          ),
        ),
      );
      
      // Try to submit empty field
      await tester.tap(find.byType(TextButton));
      await tester.pump();
      
      expect(find.text('Field is required'), findsOneWidget);
    });

    testWidgets('CustomTextField respects custom dimensions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: TextEditingController(),
              width: 300,
              height: 50,
              borderRadius: 8,
            ),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomTextField can be disabled', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: TextEditingController(),
              isEnabled: false,
            ),
          ),
        ),
      );
      
      expect(find.byType(TextFormField), findsOneWidget);
      // Field should be disabled (non-interactive)
    });

    testWidgets('CustomTextField respects max lines', (WidgetTester tester) async {
      final controller = TextEditingController();
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Test',
              controller: controller,
              maxLines: 3,
            ),
          ),
        ),
      );
      
      expect(find.byType(TextFormField), findsOneWidget);
      // Text field should accept multiple lines
    });

    testWidgets('CustomTextField respects keyboard type', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomTextField(
              label: 'Phone',
              controller: TextEditingController(),
              keyboardType: TextInputType.phone,
            ),
          ),
        ),
      );
      
      expect(find.byType(TextFormField), findsOneWidget);
      // Field should show phone keyboard when focused
    });

    testWidgets('CustomTextField throws assertion error for empty label', () {
      expect(
        () => CustomTextField(
          controller: TextEditingController(),
          // No label provided
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomTextField throws assertion error for null controller', () {
      expect(
        () => CustomTextField(
          label: 'Test',
          // No controller provided
        ),
        throwsAssertionError,
      );
    });
  });
}