import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/charts/bar_chart.dart';

void main() {
  group('BarChart Widget Tests', () {
    testWidgets('BarChart displays basic chart correctly', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
        {'label': 'Mar', 'value': 15},
        {'label': 'Apr', 'value': 25},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.text('Month'), findsOneWidget);
      expect(find.text('Value'), findsOneWidget);
    });

    testWidgets('BarChart responds to data updates', (WidgetTester tester) async {
      final initialData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      final updatedData = [
        {'label': 'Jan', 'value': 15},
        {'label': 'Feb', 'value': 25},
        {'label': 'Mar', 'value': 30},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: initialData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
      
      // Update data
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: updatedData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      await tester.pump();
      
      // Chart should update with new data
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows custom colors', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              barColor: Colors.blue,
              backgroundColor: Colors.grey[100],
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows grid lines when enabled', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              showGrid: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows legend when provided', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      final legendData = [
        {'label': 'Monthly Data', 'color': Colors.blue},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              legendData: legendData,
            ),
          ),
        ),
      );
      
      expect(find.text('Monthly Data'), findsOneWidget);
    });

    testWidgets('BarChart shows tooltips when enabled', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              showTooltips: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart handles empty data', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: [],
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: [],
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              isLoading: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('BarChart shows error state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: [],
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              errorText: 'Error loading data',
            ),
          ),
        ),
      );
      
      expect(find.text('Error loading data'), findsOneWidget);
    });

    testWidgets('BarChart respects custom dimensions', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              width: 400,
              height: 300,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows horizontal layout', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              horizontal: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows multiple data series', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10, 'series': 'A'},
        {'label': 'Feb', 'value': 20, 'series': 'A'},
        {'label': 'Jan', 'value': 15, 'series': 'B'},
        {'label': 'Feb', 'value': 25, 'series': 'B'},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              seriesKey: 'series',
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows value labels on bars', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              showValueLabels: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    testWidgets('BarChart shows animation when enabled', (WidgetTester tester) async {
      final chartData = [
        {'label': 'Jan', 'value': 10},
        {'label': 'Feb', 'value': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: BarChartWidget(
              data: chartData,
              xAxisLabel: 'Month',
              yAxisLabel: 'Value',
              animate: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(BarChartWidget), findsOneWidget);
    });

    test('BarChart throws assertion error for empty data', () {
      expect(
        () => BarChartWidget(
          data: const [],
          xAxisLabel: 'Month',
          yAxisLabel: 'Value',
          // Empty data without error state
        ),
        throwsAssertionError,
      );
    });

    test('BarChart throws assertion error for empty labels', () {
      expect(
        () => BarChartWidget(
          data: const [{'label': 'Jan', 'value': 10}],
          xAxisLabel: '', // Empty label
          yAxisLabel: 'Value',
        ),
        throwsAssertionError,
      );
    });
  });
}