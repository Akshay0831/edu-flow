import 'dart:ui';
import 'package:flutter/material.dart' hide PointMode;
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LineChart extends ConsumerWidget {
  final String title;
  final List<Map<String, dynamic>> data;
  final String? xAxisLabel;
  final String? yAxisLabel;
  final Color? lineColor;
  final double height;
  final double width;
  final bool showGrid;
  final bool showPoints;

  const LineChart({
    super.key,
    this.title = '',
    required this.data,
    this.xAxisLabel,
    this.yAxisLabel,
    this.lineColor,
    this.height = 200,
    this.width = double.infinity,
    this.showGrid = true,
    this.showPoints = true,
  })  : assert(data.isNotEmpty, 'data cannot be empty'),
        assert(xAxisLabel == null || xAxisLabel.length > 0, 'xAxisLabel cannot be empty'),
        assert(yAxisLabel == null || yAxisLabel.length > 0, 'yAxisLabel cannot be empty');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (data.isEmpty) {
      return Card(
        elevation: 4,
        child: Container(
          width: width,
          height: height,
          padding: const EdgeInsets.all(16),
          child: const Center(
            child: Text('Not enough data to display chart'),
          ),
        ),
      );
    }

    final double maxValue = data.fold<double>(
      double.negativeInfinity,
      (max, item) {
        final val = ((item['value'] ?? item['y'] ?? 0) as num).toDouble();
        return val > max ? val : max;
      },
    );
    final double minValue = data.fold<double>(
      double.infinity,
      (min, item) {
        final val = ((item['value'] ?? item['y'] ?? 0) as num).toDouble();
        return val < min ? val : min;
      },
    );
    final double valueRange = (maxValue - minValue) == 0 ? 1.0 : (maxValue - minValue);
    final effectiveLineColor = lineColor ?? Theme.of(context).primaryColor;

    return Card(
      elevation: 4,
      child: Container(
        width: width,
        height: height,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (title.isNotEmpty)
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            if (title.isNotEmpty) const SizedBox(height: 16),
            if (yAxisLabel != null && yAxisLabel!.isNotEmpty)
              Text(
                yAxisLabel!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
              ),
            const SizedBox(height: 8),
            Expanded(
              child: CustomPaint(
                size: Size.infinite,
                painter: _LineChartPainter(
                  data: data,
                  minValue: minValue,
                  valueRange: valueRange,
                  lineColor: effectiveLineColor,
                  showGrid: showGrid,
                  showPoints: showPoints,
                ),
              ),
            ),
            if (xAxisLabel != null && xAxisLabel!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Center(
                  child: Text(
                    xAxisLabel!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _LineChartPainter extends CustomPainter {
  final List<Map<String, dynamic>> data;
  final double minValue;
  final double valueRange;
  final Color lineColor;
  final bool showGrid;
  final bool showPoints;

  _LineChartPainter({
    required this.data,
    required this.minValue,
    required this.valueRange,
    required this.lineColor,
    required this.showGrid,
    required this.showPoints,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final paint = Paint()
      ..color = lineColor
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final points = <Offset>[];
    final double stepX = data.length > 1 ? size.width / (data.length - 1) : size.width;

    for (int i = 0; i < data.length; i++) {
      final val = ((data[i]['value'] ?? data[i]['y'] ?? 0) as num).toDouble();
      final x = i * stepX;
      final y = size.height - ((val - minValue) / valueRange) * size.height;
      points.add(Offset(x, y.clamp(0.0, size.height)));
    }

    if (points.length > 1) {
      final path = Path();
      path.moveTo(points[0].dx, points[0].dy);
      for (int i = 1; i < points.length; i++) {
        path.lineTo(points[i].dx, points[i].dy);
      }
      canvas.drawPath(path, paint);
    } else if (points.length == 1) {
      canvas.drawCircle(points[0], 4, paint);
    }

    if (showPoints) {
      final pointPaint = Paint()
        ..color = lineColor
        ..style = PaintingStyle.fill;
      for (final pt in points) {
        canvas.drawCircle(pt, 3.5, pointPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) => true;
}

typedef LineChartWidget = LineChart;