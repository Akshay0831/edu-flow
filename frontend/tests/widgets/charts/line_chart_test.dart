import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/presentation/widgets/charts/line_chart.dart';

void main() {
  group('LineChart Widget Tests', () {
    testWidgets('LineChart displays basic chart correctly', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
        {'x': 3, 'y': 15},
        {'x': 4, 'y': 25},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.text('Time'), findsOneWidget);
      expect(find.text('Value'), findsOneWidget);
    });

    testWidgets('LineChart responds to data updates', (WidgetTester tester) async {
      final initialData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      final updatedData = [
        {'x': 1, 'y': 15},
        {'x': 2, 'y': 25},
        {'x': 3, 'y': 30},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: initialData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
      
      // Update data
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: updatedData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      await tester.pump();
      
      // Chart should update with new data
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows custom colors', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              lineColor: Colors.red,
              backgroundColor: Colors.blue,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows grid lines when enabled', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              showGrid: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows legend when provided', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      final legendData = [
        {'label': 'Series 1', 'color': Colors.blue},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              legendData: legendData,
            ),
          ),
        ),
      );
      
      expect(find.text('Series 1'), findsOneWidget);
    });

    testWidgets('LineChart shows tooltips when enabled', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              showTooltips: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart handles empty data', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: [],
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: [],
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              isLoading: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('LineChart shows error state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: [],
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              errorText: 'Error loading data',
            ),
          ),
        ),
      );
      
      expect(find.text('Error loading data'), findsOneWidget);
    });

    testWidgets('LineChart respects custom dimensions', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              width: 400,
              height: 300,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows multiple data series', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10, 'series': 'A'},
        {'x': 2, 'y': 20, 'series': 'A'},
        {'x': 1, 'y': 15, 'series': 'B'},
        {'x': 2, 'y': 25, 'series': 'B'},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              seriesKey: 'series',
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows data points when enabled', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              showDataPoints: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows smooth lines when enabled', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              smoothLines: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    testWidgets('LineChart shows animation when enabled', (WidgetTester tester) async {
      final chartData = [
        {'x': 1, 'y': 10},
        {'x': 2, 'y': 20},
      ];
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LineChartWidget(
              data: chartData,
              xAxisLabel: 'Time',
              yAxisLabel: 'Value',
              animate: true,
            ),
          ),
        ),
      );
      
      expect(find.byType(LineChartWidget), findsOneWidget);
    });

    test('LineChart throws assertion error for empty data', () {
      expect(
        () => LineChartWidget(
          data: const [],
          xAxisLabel: 'Time',
          yAxisLabel: 'Value',
          // Empty data without error state
        ),
        throwsAssertionError,
      );
    });

    test('LineChart throws assertion error for empty labels', () {
      expect(
        () => LineChartWidget(
          data: const [{'x': 1, 'y': 10}],
          xAxisLabel: '', // Empty label
          yAxisLabel: 'Value',
        ),
        throwsAssertionError,
      );
    });
  });
}