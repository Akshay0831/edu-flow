import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BarChart extends ConsumerWidget {
  final String title;
  final List<Map<String, dynamic>> data;
  final String? xAxisLabel;
  final String? yAxisLabel;
  final Color? barColor;
  final double height;
  final double width;
  final bool showGrid;
  final bool showTooltip;

  const BarChart({
    super.key,
    this.title = '',
    required this.data,
    this.xAxisLabel,
    this.yAxisLabel,
    this.barColor,
    this.height = 200,
    this.width = double.infinity,
    this.showGrid = true,
    this.showTooltip = true,
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

    final double maxValue = data.fold<double>(
      0.0,
      (max, item) {
        final val = ((item['value'] ?? 0) as num).toDouble();
        return val > max ? val : max;
      },
    );
    final effectiveBarColor = barColor ?? Theme.of(context).primaryColor;

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
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: data.map((item) {
                  final val = ((item['value'] ?? 0) as num).toDouble();
                  final itemHeight = maxValue > 0
                      ? (val / maxValue) * (height - (title.isNotEmpty ? 100 : 70))
                      : 0.0;
                  final color = item['color'] as Color? ?? effectiveBarColor;

                  return Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Tooltip(
                          message: '${item['label'] ?? ''}: ${item['value'] ?? ''}',
                          child: Container(
                            height: itemHeight.clamp(4.0, height),
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            decoration: BoxDecoration(
                              color: color,
                              borderRadius: const BorderRadius.vertical(
                                top: Radius.circular(4),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          item['label']?.toString() ?? '',
                          style: Theme.of(context).textTheme.bodySmall,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  );
                }).toList(),
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

typedef BarChartWidget = BarChart;