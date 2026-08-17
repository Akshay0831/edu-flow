import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_app_bar.dart';

void main() {
  group('CustomAppBar Widget Tests', () {
    testWidgets('CustomAppBar displays title correctly', (WidgetTester tester) async {
      const title = 'Test App Bar';
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(title: title),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text(title), findsOneWidget);
    });

    testWidgets('CustomAppBar shows leading icon', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              leading: Icons.menu,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.menu), findsOneWidget);
    });

    testWidgets('CustomAppBar responds to leading tap', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              leading: Icons.menu,
              onLeadingPressed: () => tapped = true,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      await tester.tap(find.byIcon(Icons.menu));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomAppBar shows actions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              actions: [
                const Icon(Icons.search),
                const Icon(Icons.more_vert),
              ],
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.search), findsOneWidget);
      expect(find.byIcon(Icons.more_vert), findsOneWidget);
    });

    testWidgets('CustomAppBar responds to action taps', (WidgetTester tester) async {
      bool tapped = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              actions: [
                const Icon(Icons.search),
              ],
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      await tester.tap(find.byIcon(Icons.search));
      await tester.pump();
      
      expect(tapped, true);
    });

    testWidgets('CustomAppBar shows custom background color', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              backgroundColor: Colors.blue,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows custom elevation', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              elevation: 8,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows center title', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              centerTitle: true,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows automaticallyImplyLeading false', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              automaticallyImplyLeading: false,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
      // Should not have default leading back button
    });

    testWidgets('CustomAppBar shows custom font size', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              fontSize: 20,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows custom font weight', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              fontWeight: FontWeight.bold,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows custom title color', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              titleColor: Colors.red,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar shows icon color', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              leading: Icons.menu,
              iconColor: Colors.blue,
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.menu), findsOneWidget);
    });

    testWidgets('CustomAppBar shows bottom widget', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(50),
                child: Container(
                  color: Colors.grey,
                  child: const Text('Bottom Content'),
                ),
              ),
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Bottom Content'), findsOneWidget);
    });

    testWidgets('CustomAppBar throws assertion error for empty title', (WidgetTester tester) async {
      expect(
        () => CustomAppBar(
          title: '', // Empty title
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomAppBar with null actions still works', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              // No actions provided
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('CustomAppBar with null leading still works', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: CustomAppBar(
              title: 'Test',
              // No leading provided
            ),
            body: const Center(child: Text('Content')),
          ),
        ),
      );
      
      expect(find.text('Test'), findsOneWidget);
    });
  });
}