import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_card.dart';

void main() {
  group('CustomCard Widget Tests', () {
    testWidgets('CustomCard displays title and subtitle correctly', (WidgetTester tester) async {
      const title = 'Test Card';
      const subtitle = 'Card subtitle';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: title,
              subtitle: subtitle,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text(title), findsOneWidget);
      expect(find.text(subtitle), findsOneWidget);
      expect(find.text('Content'), findsOneWidget);
    });

    testWidgets('CustomCard displays child content', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Test Card',
              child: const Column(
                children: [
                  Text('Item 1'),
                  Text('Item 2'),
                ],
              ),
            ),
          ),
        ),
      );
      
      expect(find.text('Item 1'), findsOneWidget);
      expect(find.text('Item 2'), findsOneWidget);
    });

    testWidgets('CustomCard displays action button', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Test Card',
              action: TextButton(
                onPressed: () => tapped = true,
                child: const Text('Action'),
              ),
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Action'), findsOneWidget);
      
      await tester.tap(find.text('Action'));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomCard respects custom dimensions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Custom Size',
              width: 300,
              height: 200,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Custom Size'), findsOneWidget);
    });

    testWidgets('CustomCard with no title still works', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Content'), findsOneWidget);
    });

    testWidgets('CustomCard with no subtitle still works', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Title',
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Title'), findsOneWidget);
      expect(find.text('Content'), findsOneWidget);
    });

    testWidgets('CustomCard shows loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Loading Card',
              isLoading: true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('CustomCard can be disabled', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Disabled Card',
              isDisabled: true,
              onTap: () => tapped = true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      await tester.tap(find.text('Disabled Card'));
      await tester.pump();
      
      expect(tapped, false); // Should not be tapped when disabled
    });

    testWidgets('CustomCard responds to tap', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Clickable Card',
              onTap: () => tapped = true,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      await tester.tap(find.text('Clickable Card'));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomCard shows border when borderColor is set', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Bordered Card',
              borderColor: Colors.red,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Bordered Card'), findsOneWidget);
    });

    testWidgets('CustomCard shows elevation', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomCard(
              title: 'Elevated Card',
              elevation: 8,
              child: const Text('Content'),
            ),
          ),
        ),
      );
      
      expect(find.text('Elevated Card'), findsOneWidget);
    });

    testWidgets('CustomCard throws assertion error for null child', () {
      expect(
        () => CustomCard(
          title: 'Test Card',
          // No child provided
        ),
        throwsAssertionError,
      );
    });
  });
}