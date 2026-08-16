import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PerformanceMonitor extends StatefulWidget {
  final Widget child;
  final bool enabled;
  final String? screenName;

  const PerformanceMonitor({
    super.key,
    required this.child,
    this.enabled = true,
    this.screenName,
  });

  @override
  State<PerformanceMonitor> createState() => _PerformanceMonitorState();
}

class _PerformanceMonitorState extends State<PerformanceMonitor> {
  late final DateTime _startTime;
  int _frameCount = 0;
  double _fps = 0.0;
  bool _showDebugPanel = false;

  @override
  void initState() {
    super.initState();
    _startTime = DateTime.now();
    _startFrameMonitoring();
  }

  void _startFrameMonitoring() {
    if (!widget.enabled) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updatePerformanceMetrics();
    });
  }

  void _updatePerformanceMetrics() {
    if (!widget.enabled) return;

    final now = DateTime.now();
    final duration = now.difference(_startTime).inMilliseconds;
    
    if (duration > 0) {
      setState(() {
        _fps = _frameCount / (duration / 1000.0);
      });
    }

    _frameCount++;

    if (mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _updatePerformanceMetrics();
      });
    }
  }

  void _toggleDebugPanel() {
    setState(() {
      _showDebugPanel = !_showDebugPanel;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) {
      return widget.child;
    }

    return Stack(
      children: [
        widget.child,
        if (_showDebugPanel)
          _buildDebugPanel(),
        Positioned(
          bottom: 16,
          right: 16,
          child: FloatingActionButton(
            onPressed: _toggleDebugPanel,
            backgroundColor: Colors.black.withOpacity(0.7),
            mini: true,
            child: Icon(
              _showDebugPanel ? Icons.visibility_off : Icons.visibility,
              color: Colors.white,
              size: 16,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDebugPanel() {
    return Positioned(
      top: 16,
      right: 16,
      child: Container(
        width: 200,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.8),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.speed, color: Colors.white, size: 16),
                const SizedBox(width: 8),
                Text(
                  'Performance',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: _toggleDebugPanel,
                  icon: const Icon(Icons.close, color: Colors.white, size: 16),
                  padding: EdgeInsets.zero,
                ),
              ],
            ),
            const Divider(color: Colors.white24),
            _buildMetricItem('Screen', widget.screenName ?? 'Unknown'),
            _buildMetricItem('FPS', '${_fps}'),
            _buildMetricItem('Frame Count', '$_frameCount'),
            _buildMetricItem('Memory', _getMemoryUsage()),
            _buildMetricItem('Platform', '${Theme.of(context).platform}'),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  String _getMemoryUsage() {
    final memoryUsage = (MemoryInfo.getCurrentUsage() / (1024 * 1024)).toStringAsFixed(1);
    return '${memoryUsage} MB';
  }

  @override
  void dispose() {
    super.dispose();
  }
}

class MemoryInfo {
  static double getCurrentUsage() {
    // This is a placeholder implementation
    // In a real app, you would use platform-specific methods to get memory usage
    return 0.0;
  }
}

class PerformanceAnalytics extends ConsumerWidget {
  final List<Map<String, dynamic>> performanceData;

  const PerformanceAnalytics({
    super.key,
    required this.performanceData,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (performanceData.isEmpty) {
      return const Center(child: Text('No performance data available'));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Performance Analytics',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: performanceData.length,
                itemBuilder: (context, index) {
                  final data = performanceData[index];
                  return ListTile(
                    leading: Icon(_getIconForMetric(data['metric'])),
                    title: Text(data['metric']),
                    subtitle: Text('Value: ${data['value']}'),
                    trailing: Text(
                      data['timestamp'] ?? '',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getIconForMetric(String metric) {
    switch (metric.toLowerCase()) {
      case 'fps':
        return Icons.speed;
      case 'memory':
        return Icons.memory;
      case 'cpu':
        return Icons.computer;
      case 'network':
        return Icons.network_check;
      default:
        return Icons.analytics;
    }
  }
}