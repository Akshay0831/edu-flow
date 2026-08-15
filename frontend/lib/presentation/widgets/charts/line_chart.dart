import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LineChart extends ConsumerWidget {
  final String title;
  final List<Map<String, dynamic>> data;
  final String xAxisLabel;
  final String yAxisLabel;
  final Color? lineColor;
  final double height;
  final double width;

  const LineChart({
    super.key,
    required this.title,
    required this.data,
    required this.xAxisLabel,
    required this.yAxisLabel,
    this.lineColor,
    this.height = 200,
    this.width = double.infinity,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (data.isEmpty || data.length < 2) {
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

    final maxValue = data.fold(0, (max, item) => (item['value'] as num).compareTo(max) > 0 ? (item['value'] as num) : max);
    final minValue = data.fold(double.infinity, (min, item) => (item['value'] as num).compareTo(min) < 0 ? (item['value'] as num) : min);
    final valueRange = maxValue - minValue;
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
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: CustomPaint(
                painter: _LineChartPainter(
                  data: data,
                  minValue: minValue,
                  valueRange: valueRange,
                  lineColor: effectiveLineColor,
                ),
                child: Container(
                  decoration: const BoxDecoration(
                    border: Border(
                      left: BorderSide(color: Colors.grey),
                      bottom: BorderSide(color: Colors.grey),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  xAxisLabel,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                Text(
                  yAxisLabel,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
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

  _LineChartPainter({
    required this.data,
    required this.minValue,
    required this.valueRange,
    required this.lineColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.length < 2) return;

    final padding = 20.0;
    final chartWidth = size.width - 2 * padding;
    final chartHeight = size.height - 2 * padding;

    // Draw grid lines
    final gridPaint = Paint()
      ..color = Colors.grey.withOpacity(0.3)
      ..style = PaintingStyle.stroke;

    for (int i = 0; i <= 5; i++) {
      final y = padding + (chartHeight * i / 5);
      canvas.drawLine(
        Offset(padding, y),
        Offset(size.width - padding, y),
        gridPaint,
      );
    }

    // Draw data line
    final linePaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    final points = <Offset>[];

    for (int i = 0; i < data.length; i++) {
      final value = data[i]['value'] as num;
      final x = padding + (chartWidth * i / (data.length - 1));
      final y = padding + chartHeight - ((value - minValue) / valueRange * chartHeight);
      points.add(Offset(x, y));
    }

    canvas.drawPoints(
      PointMode.polygon,
      points,
      linePaint,
    );

    // Draw data points
    final pointPaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.fill;

    for (int i = 0; i < points.length; i++) {
      canvas.drawCircle(points[i], 5, pointPaint);
    }

    // Draw labels
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    // X-axis labels
    for (int i = 0; i < data.length; i++) {
      final label = data[i]['label'] as String;
      textPainter.text = TextSpan(
        text: label,
        style: TextStyle(color: Colors.grey[700], fontSize: 10),
      );
      textPainter.layout();
      
      final x = padding + (chartWidth * i / (data.length - 1));
      textPainter.paint(
        canvas,
        Offset(x - textPainter.width / 2, size.height - 5),
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}