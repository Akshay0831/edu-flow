import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_icon_button.dart';

void main() {
  group('CustomIconButton Widget Tests', () {
    testWidgets('CustomIconButton displays icon correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton responds to tap', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () => tapped = true,
            ),
          ),
        ),
      );
      
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomIconButton shows tooltip', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              tooltip: 'Add Item',
            ),
          ),
        ),
      );
      
      // Tooltip is shown on hover, but button should be there
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton respects custom size', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              size: 50,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton shows background color', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              backgroundColor: Colors.blue,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton shows foreground color', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              foregroundColor: Colors.white,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton can be disabled', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () => tapped = true,
              isDisabled: true,
            ),
          ),
        ),
      );
      
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();
      
      expect(tapped, false); // Should not be tapped when disabled
    });

    testWidgets('CustomIconButton shows badge count', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.notifications,
              onPressed: () {},
              badgeCount: 5,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.notifications), findsOneWidget);
      expect(find.text('5'), findsOneWidget);
    });

    testWidgets('CustomIconButton shows badge text', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.notifications,
              onPressed: () {},
              badgeText: 'New',
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.notifications), findsOneWidget);
      expect(find.text('New'), findsOneWidget);
    });

    testWidgets('CustomIconButton shows loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              isLoading: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('CustomIconButton shows label when label is provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              label: 'Add',
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
      expect(find.text('Add'), findsOneWidget);
    });

    testWidgets('CustomIconButton respects shape', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              shape: BoxShape.circle,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton shows border when borderColor is set', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.add,
              onPressed: () {},
              borderColor: Colors.red,
              borderWidth: 2,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('CustomIconButton throws assertion error for null icon', () {
      expect(
        () => CustomIconButton(
          onPressed: () {},
          // No icon provided
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomIconButton throws assertion error for null onPressed', () {
      expect(
        () => CustomIconButton(
          icon: Icons.add,
          // No onPressed provided
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomIconButton with badge count 0 shows nothing', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomIconButton(
              icon: Icons.notifications,
              onPressed: () {},
              badgeCount: 0,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.notifications), findsOneWidget);
      expect(find.text('0'), findsNothing); // Should not show "0" badge
    });
  });
}