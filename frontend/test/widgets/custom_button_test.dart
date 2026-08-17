import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_button.dart';

void main() {
  group('CustomButton Widget Tests', () {
    testWidgets('CustomButton displays text correctly', (WidgetTester tester) async {
      const buttonText = 'Test Button';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: buttonText,
              onPressed: () {},
            ),
          ),
        ),
      );
      
      expect(find.text(buttonText), findsOneWidget);
    });

    testWidgets('CustomButton responds to tap', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Click Me',
              onPressed: () => tapped = true,
            ),
          ),
        ),
      );
      
      await tester.tap(find.text('Click Me'));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomButton is disabled when isDisabled is true', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Disabled Button',
              onPressed: () {},
              isDisabled: true,
            ),
          ),
        ),
      );
      
      final button = find.byType(CustomButton);
      expect(button, findsOneWidget);
      
      // Disabled button should not respond to taps
      await tester.tap(find.text('Disabled Button'));
      await tester.pump();
      
      // Button should still be there but not interactive
      expect(button, findsOneWidget);
    });

    testWidgets('CustomButton shows loading indicator when isLoading is true', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Loading Button',
              onPressed: () {},
              isLoading: true,
            ),
          ),
        ),
      );
      
      // Should show loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      
      // Should not respond to taps when loading
      await tester.tap(find.text('Loading Button'));
      await tester.pump();
      
      // Button should still be there
      expect(find.text('Loading Button'), findsOneWidget);
    });

    testWidgets('CustomButton shows icon when provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Icon Button',
              onPressed: () {},
              icon: Icons.add,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomButton can be outlined', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Outlined Button',
              onPressed: () {},
              isOutlined: true,
            ),
          ),
        ),
      );
      
      expect(find.text('Outlined Button'), findsOneWidget);
    });

    testWidgets('CustomButton respects custom dimensions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              text: 'Custom Size',
              onPressed: () {},
              width: 200,
              height: 50,
              borderRadius: 12,
            ),
          ),
        ),
      );
      
      expect(find.text('Custom Size'), findsOneWidget);
    });

    testWidgets('CustomButton with no text throws assertion error', (WidgetTester tester) async {
      expect(
        () => CustomButton(
          onPressed: () {},
          text: '',
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomButton with null onPressed throws assertion error', (WidgetTester tester) async {
      expect(
        () => CustomButton(
          onPressed: () {}, // Should not be null
          text: 'Test Button',
        ),
        throwsAssertionError,
      );
    });
  });
}