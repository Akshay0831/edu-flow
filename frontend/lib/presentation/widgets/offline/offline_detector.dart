import 'package:flutter/material.dart';

class OfflineDetector extends StatefulWidget {
  final Widget child;
  final bool isOnline;
  final ValueChanged<bool>? onStatusChanged;
  final String? offlineMessage;
  final String? onlineMessage;
  final Widget? offlineWidget;
  final Widget? onlineWidget;
  final bool showRetryButton;
  final VoidCallback? onRetry;
  final bool isLoading;
  final bool showLoading;
  final Duration? autoRefreshInterval;
  final Color? offlineColor;
  final Color? onlineColor;
  final Color? offlineTextColor;
  final Color? onlineTextColor;
  final double? borderRadius;
  final EdgeInsetsGeometry? padding;
  final bool manualRefreshEnabled;
  final bool enableLogging;
  final Duration? timeout;
  final Widget? errorWidget;

  OfflineDetector({
    Key? key,
    Widget? child,
    this.isOnline = true,
    this.onStatusChanged,
    this.offlineMessage,
    this.onlineMessage,
    this.offlineWidget,
    this.onlineWidget,
    this.showRetryButton = false,
    this.onRetry,
    this.isLoading = false,
    this.showLoading = false,
    this.autoRefreshInterval,
    this.offlineColor,
    this.onlineColor,
    this.offlineTextColor,
    this.onlineTextColor,
    this.borderRadius,
    this.padding,
    this.manualRefreshEnabled = true,
    this.enableLogging = false,
    this.timeout,
    this.errorWidget,
  })  : assert(child != null, 'child parameter cannot be null'),
        child = child!,
        super(key: key);

  @override
  State<OfflineDetector> createState() => _OfflineDetectorState();
}

class _OfflineDetectorState extends State<OfflineDetector> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.onStatusChanged?.call(widget.isOnline);
    });
  }

  @override
  void didUpdateWidget(covariant OfflineDetector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.isOnline != widget.isOnline) {
      widget.onStatusChanged?.call(widget.isOnline);
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget banner;

    if (widget.showLoading && widget.isLoading) {
      banner = const CircularProgressIndicator();
    } else if (!widget.isOnline) {
      if (widget.errorWidget != null) {
        banner = widget.errorWidget!;
      } else if (widget.offlineWidget != null) {
        banner = widget.offlineWidget!;
      } else {
        banner = Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              widget.offlineMessage ?? 'Offline',
              style: TextStyle(color: widget.offlineTextColor),
            ),
            if (widget.showRetryButton)
              ElevatedButton(
                onPressed: widget.onRetry,
                child: const Text('Retry'),
              ),
          ],
        );
      }
    } else {
      if (widget.onlineWidget != null) {
        banner = widget.onlineWidget!;
      } else if (widget.onlineMessage != null) {
        banner = Text(
          widget.onlineMessage!,
          style: TextStyle(color: widget.onlineTextColor),
        );
      } else {
        banner = const SizedBox.shrink();
      }
    }

    return Column(
      children: [
        banner,
        Expanded(child: widget.child),
      ],
    );
  }
}
