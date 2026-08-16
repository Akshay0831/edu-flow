import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'bar_chart.dart';
import 'line_chart.dart';

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

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildSummaryCards(),
          const SizedBox(height: 24),
          _buildFilterSection(),
          const SizedBox(height: 24),
          _buildPerformanceChart(),
          const SizedBox(height: 24),
          _buildEnrollmentChart(),
        ],
      ),
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
            value: (widget.summaryMetrics['averageScore'] is num)
                ? (widget.summaryMetrics['averageScore'] as num).toStringAsFixed(1)
                : widget.summaryMetrics['averageScore']?.toString() ?? '0.0',
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
      return const SizedBox(
        height: 200,
        child: Center(
          child: Text('No performance data available'),
        ),
      );
    }

    return BarChart(
      title: 'Performance Trends',
      data: widget.performanceData,
      yAxisLabel: 'Score',
      height: 250,
    );
  }

  Widget _buildEnrollmentChart() {
    if (widget.enrollmentData.isEmpty) {
      return const SizedBox(
        height: 200,
        child: Center(
          child: Text('No enrollment data available'),
        ),
      );
    }

    return LineChart(
      title: 'Enrollment Trends',
      data: widget.enrollmentData,
      xAxisLabel: 'Period',
      yAxisLabel: 'Students',
      lineColor: Colors.green,
      height: 250,
    );
  }
}

extension StringExtension on String {
  String capitalize() {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }
}