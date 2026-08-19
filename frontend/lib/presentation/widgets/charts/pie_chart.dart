import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PieChart extends ConsumerWidget {
  final String title;
  final List<Map<String, dynamic>> data;
  final List<Color>? colors;
  final double height;
  final double width;

  const PieChart({
    super.key,
    required this.title,
    required this.data,
    this.colors,
    this.height = 200,
    this.width = double.infinity,
  });

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
            child: Text('No data available'),
          ),
        ),
      );
    }

    final double total = data.fold<double>(
      0.0,
      (sum, item) => sum + (item['value'] as num).toDouble(),
    );
    final effectiveColors = colors ?? _getDefaultColors(data.length);
    final double size = width < 200 ? width : 200;

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
            Row(
              children: [
                SizedBox(
                  width: size,
                  height: size,
                  child: CustomPaint(
                    painter: _PieChartPainter(
                      data: data,
                      colors: effectiveColors,
                      total: total,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: data.map((item) {
                      final label = item['label'] as String;
                      final value = item['value'] as num;
                      final percentage = total > 0 ? (value.toDouble() / total) * 100 : 0;
                      final color = effectiveColors[data.indexOf(item) % effectiveColors.length];

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(
                                    color: color,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  label,
                                  style: Theme.of(context).textTheme.bodySmall,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                            Text(
                              '${percentage.toStringAsFixed(1)}%',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  List<Color> _getDefaultColors(int count) {
    const defaultColors = [
      Colors.blue,
      Colors.green,
      Colors.orange,
      Colors.red,
      Colors.purple,
      Colors.teal,
      Colors.amber,
      Colors.pink,
    ];

    if (count <= defaultColors.length) {
      return defaultColors.sublist(0, count);
    }

    final colors = List<Color>.from(defaultColors);
    for (int i = defaultColors.length; i < count; i++) {
      final hue = (360.0 / count) * i;
      colors.add(HSLColor.fromAHSL(1.0, hue, 0.7, 0.5).toColor());
    }

    return colors;
  }
}

class _PieChartPainter extends CustomPainter {
  final List<Map<String, dynamic>> data;
  final List<Color> colors;
  final double total;

  _PieChartPainter({
    required this.data,
    required this.colors,
    required this.total,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 10;

    if (total == 0) {
      canvas.drawCircle(center, radius, Paint()..color = Colors.grey[300]!);
      return;
    }

    double startAngle = -90 * (pi / 180);

    for (int i = 0; i < data.length; i++) {
      final value = (data[i]['value'] as num).toDouble();
      final sweepAngle = (value / total) * 2 * pi;

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepAngle,
        false,
        Paint()
          ..color = colors[i % colors.length]
          ..style = PaintingStyle.fill,
      );

      if (value / total > 0.05) {
        final percentageAngle = startAngle + sweepAngle / 2;
        final textRadius = radius * 0.7;
        final textX = center.dx + textRadius * cos(percentageAngle);
        final textY = center.dy + textRadius * sin(percentageAngle);

        final textPainter = TextPainter(
          text: TextSpan(
            text: '${((value / total) * 100).toStringAsFixed(0)}%',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          textDirection: TextDirection.ltr,
        );

        textPainter.layout();
        textPainter.paint(
          canvas,
          Offset(textX - textPainter.width / 2, textY - textPainter.height / 2),
        );
      }

      startAngle += sweepAngle;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}