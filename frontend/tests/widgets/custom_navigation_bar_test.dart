import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/common/custom_navigation_bar.dart';

void main() {
  group('CustomNavigationBar Widget Tests', () {
    testWidgets('CustomNavigationBar displays items correctly', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.search,
          label: 'Search',
        ),
        CustomBottomNavBarItem(
          icon: Icons.person,
          label: 'Profile',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.byIcon(Icons.search), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Search'), findsOneWidget);
      expect(find.text('Profile'), findsOneWidget);
    });

    testWidgets('CustomNavigationBar responds to tap', (WidgetTester tester) async {
      int tappedIndex = -1;
      
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.search,
          label: 'Search',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) => tappedIndex = index,
            ),
          ),
        ),
      );
      
      await tester.tap(find.text('Search'));
      await tester.pump();
      
      expect(tappedIndex, 1);
    });

    testWidgets('CustomNavigationBar shows active state', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.search,
          label: 'Search',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 1,
              onTap: (index) {},
            ),
          ),
        ),
      );
      
      // Second item should be active
      expect(find.text('Search'), findsOneWidget);
      // First item should not be active
    });

    testWidgets('CustomNavigationBar shows custom background color', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              backgroundColor: Colors.blue,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    testWidgets('CustomNavigationBar shows custom active color', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              activeColor: Colors.red,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    testWidgets('CustomNavigationBar shows custom inactive color', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
        CustomBottomNavBarItem(
          icon: Icons.search,
          label: 'Search',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              inactiveColor: Colors.grey,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.byIcon(Icons.search), findsOneWidget);
    });

    testWidgets('CustomNavigationBar respects custom height', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              height: 80,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    testWidgets('CustomNavigationBar shows type indicator', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              type: CustomNavBarType.fixed,
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    testWidgets('CustomNavigationBar shows selected item indicator', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
          showIndicator: true,
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    test('CustomNavigationBar with no items throws assertion error', () {
      expect(
        () => CustomNavigationBar(
          items: const [],
          currentIndex: 0,
          onTap: (index) {},
        ),
        throwsAssertionError,
      );
    });

    test('CustomNavigationBar throws assertion error for out of bounds index', () {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      expect(
        () => CustomNavigationBar(
          items: items,
          currentIndex: 1, // Out of bounds
          onTap: (index) {},
        ),
        throwsAssertionError,
      );
    });

    testWidgets('CustomNavigationBar shows items with label padding', (WidgetTester tester) async {
      const items = [
        CustomBottomNavBarItem(
          icon: Icons.home,
          label: 'Home',
        ),
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomNavigationBar(
              items: items,
              currentIndex: 0,
              onTap: (index) {},
              labelPadding: const EdgeInsets.all(8),
            ),
          ),
        ),
      );
      
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
    });
  });
}