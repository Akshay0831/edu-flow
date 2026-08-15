import 'package:flutter/material.dart';

class CustomSnackBar {
  static void show({
    required BuildContext context,
    required String message,
    String? actionLabel,
    VoidCallback? onAction,
    bool isError = false,
    bool isLong = false,
    Duration? duration,
  }) {
    final effectiveDuration = duration ?? 
        (isLong ? const Duration(seconds: 5) : const Duration(seconds: 3));
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            if (isError)
              const Icon(Icons.error_outline, color: Colors.white, size: 20)
            else
              const Icon(Icons.check_circle_outline, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                ),
              ),
            ),
          ],
        ),
        backgroundColor: isError 
            ? Colors.red 
            : Theme.of(context).colorScheme.primary,
        duration: effectiveDuration,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8.0),
        ),
        action: actionLabel != null && onAction != null
            ? SnackBarAction(
                label: actionLabel,
                textColor: Colors.white,
                onPressed: onAction,
              )
            : null,
      ),
    );
  }

  static void showSuccess({
    required BuildContext context,
    required String message,
    String? actionLabel,
    VoidCallback? onAction,
    bool isLong = false,
    Duration? duration,
  }) {
    show(
      context: context,
      message: message,
      actionLabel: actionLabel,
      onAction: onAction,
      isError: false,
      isLong: isLong,
      duration: duration,
    );
  }

  static void showError({
    required BuildContext context,
    required String message,
    String? actionLabel,
    VoidCallback? onAction,
    bool isLong = false,
    Duration? duration,
  }) {
    show(
      context: context,
      message: message,
      actionLabel: actionLabel,
      onAction: onAction,
      isError: true,
      isLong: isLong,
      duration: duration,
    );
  }

  static void showInfo({
    required BuildContext context,
    required String message,
    String? actionLabel,
    VoidCallback? onAction,
    bool isLong = false,
    Duration? duration,
  }) {
    show(
      context: context,
      message: message,
      actionLabel: actionLabel,
      onAction: onAction,
      isError: false,
      isLong: isLong,
      duration: duration,
    );
  }
}