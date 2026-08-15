import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';

class AnalyticsDashboard extends ConsumerStatefulWidget {
  final List<Map<String, dynamic>> performanceData;
  final List<Map<String, dynamic>> enrollmentData;
  final Map<String, dynamic> summaryMetrics;
  final Function(String)? onFilterChanged;
  final List<String> availableFilters;

  const AnalyticsDashboard({
    super.key,
    required this.performanceData,
    required this.enrollmentData,
    required this.summaryMetrics,
    this.onFilterChanged,
    this.availableFilters = const ['weekly', 'monthly', 'yearly'],
  });

  @override
  ConsumerState<AnalyticsDashboard> createState() => _AnalyticsDashboardState();
}

class _AnalyticsDashboardState extends ConsumerState<AnalyticsDashboard> {
  String selectedFilter = 'weekly';
  int touchedIndex = -1;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _buildSummaryCards(),
        const SizedBox(height: 24),
        _buildFilterSection(),
        const SizedBox(height: 24),
        Expanded(
          child: Column(
            children: [
              _buildPerformanceChart(),
              const SizedBox(height: 24),
              _buildEnrollmentChart(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCards() {
    return Row(
      children: [
        Expanded(
          child: _buildSummaryCard(
            title: 'Total Students',
            value: widget.summaryMetrics['totalStudents']?.toString() ?? '0',
            icon: Icons.groups,
            color: Colors.blue,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildSummaryCard(
            title: 'Active Courses',
            value: widget.summaryMetrics['activeCourses']?.toString() ?? '0',
            icon: Icons.book,
            color: Colors.green,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildSummaryCard(
            title: 'Average Score',
            value: widget.summaryMetrics['averageScore']?.toStringAsFixed(1) ?? '0.0',
            icon: Icons.score,
            color: Colors.orange,
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 24),
                const Spacer(),
                Text(
                  title,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterSection() {
    return Row(
      children: [
        const Text(
          'Filter:',
          style: TextStyle(fontWeight: FontWeight.w500),
        ),
        const SizedBox(width: 8),
        ...widget.availableFilters.map((filter) => Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4),
          child: FilterChip(
            label: Text(filter.capitalize()),
            selected: selectedFilter == filter,
            onSelected: (selected) {
              setState(() {
                selectedFilter = filter;
              });
              if (widget.onFilterChanged != null) {
                widget.onFilterChanged!(filter);
              }
            },
          ),
        )),
      ],
    );
  }

  Widget _buildPerformanceChart() {
    if (widget.performanceData.isEmpty) {
      return const Expanded(
        child: Center(
          child: Text('No performance data available'),
        ),
      );
    }

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Performance Trends',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index >= 0 && index < widget.performanceData.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(
                                widget.performanceData[index]['label'] ?? '',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            );
                          }
                          return const Text('');
                        },
                        reservedSize: 40,
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: Theme.of(context).textTheme.bodySmall,
                          );
                        },
                        reservedSize: 40,
                      ),
                    ),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: widget.performanceData.asMap().entries.map((entry) {
                    final index = entry.key;
                    final data = entry.value;
                    return BarChartGroupData(
                      x: index,
                      barRods: [
                        BarChartRodData(
                          toY: (data['value'] ?? 0).toDouble(),
                          color: Colors.blue,
                          width: 20,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ],
                    );
                  }).toList(),
                  gridData: const FlGridData(show: false),
                ),
                duration: const Duration(milliseconds: 250),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEnrollmentChart() {
    if (widget.enrollmentData.isEmpty) {
      return const Expanded(
        child: Center(
          child: Text('No enrollment data available'),
        ),
      );
    }

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Enrollment Trends',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: LineChart(
                LineChartData(
                  alignment: LegendAlignment.end,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (value) {
                      return FlLine(
                        color: Colors.grey.withOpacity(0.2),
                        strokeWidth: 1,
                      );
                    },
                  ),
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index >= 0 && index < widget.enrollmentData.length) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 8.0),
                              child: Text(
                                widget.enrollmentData[index]['label'] ?? '',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            );
                          }
                          return const Text('');
                        },
                        reservedSize: 40,
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: Theme.of(context).textTheme.bodySmall,
                          );
                        },
                        reservedSize: 40,
                      ),
                    ),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(
                    show: false,
                    borderData: FlBorderData(
                      borderData: BorderData(
                        show: false,
                      ),
                    ),
                  ),
                  minX: 0,
                  maxX: widget.enrollmentData.length.toDouble() - 1,
                  minY: 0,
                  maxY: widget.enrollmentData.fold(0, (max, data) {
                    return max > (data['value'] ?? 0) ? max : (data['value'] ?? 0);
                  }).toDouble() * 1.2,
                  lineBarsData: [
                    LineChartBarData(
                      spots: widget.enrollmentData.asMap().entries.map((entry) {
                        final index = entry.key;
                        final data = entry.value;
                        return FlSpot(
                          index.toDouble(),
                          (data['value'] ?? 0).toDouble(),
                        );
                      }).toList(),
                      isCurved: true,
                      color: Colors.green,
                      barWidth: 2,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: Colors.green.withOpacity(0.2),
                      ),
                    ),
                  ],
                ),
                duration: const Duration(milliseconds: 250),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

extension StringExtension on String {
  String capitalize() {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }
}