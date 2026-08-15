import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BarChart extends ConsumerWidget {
  final String title;
  final List<Map<String, dynamic>> data;
  final String yAxisLabel;
  final Color? barColor;
  final double height;
  final double width;

  const BarChart({
    super.key,
    required this.title,
    required this.data,
    required this.yAxisLabel,
    this.barColor,
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

    final maxValue = data.fold(0, (max, item) => (item['value'] as num).compareTo(max) > 0 ? (item['value'] as num) : max);
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
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const SizedBox(width: 40),
                  Expanded(
                    child: Row(
                      children: data.asMap().entries.map((entry) {
                        final index = entry.key;
                        final item = entry.value;
                        final value = item['value'] as num;
                        final label = item['label'] as String;
                        final barHeight = maxValue > 0 ? (value / maxValue) * 140 : 0;

                        return Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                Container(
                                  width: double.infinity,
                                  height: barHeight,
                                  decoration: BoxDecoration(
                                    color: effectiveBarColor,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  label,
                                  style: Theme.of(context).textTheme.bodySmall,
                                  textAlign: TextAlign.center,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  value.toString(),
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: effectiveBarColor,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 4),
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