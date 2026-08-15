import 'package:flutter/material.dart';

class CustomAlertDialog extends StatelessWidget {
  final String title;
  final String? content;
  final String? confirmText;
  final String? cancelText;
  final VoidCallback? onConfirm;
  final VoidCallback? onCancel;
  final bool isDestructiveAction;
  final Widget? icon;
  final EdgeInsetsGeometry? titlePadding;
  final EdgeInsetsGeometry? contentPadding;
  final double? borderRadius;
  final Color? backgroundColor;

  const CustomAlertDialog({
    super.key,
    required this.title,
    this.content,
    this.confirmText,
    this.cancelText,
    this.onConfirm,
    this.onCancel,
    this.isDestructiveAction = false,
    this.icon,
    this.titlePadding,
    this.contentPadding,
    this.borderRadius,
    this.backgroundColor,
  });

  static Future<bool?> show({
    required BuildContext context,
    required String title,
    String? content,
    String? confirmText,
    String? cancelText,
    VoidCallback? onConfirm,
    VoidCallback? onCancel,
    bool isDestructiveAction = false,
    Widget? icon,
    EdgeInsetsGeometry? titlePadding,
    EdgeInsetsGeometry? contentPadding,
    double? borderRadius,
    Color? backgroundColor,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (context) => CustomAlertDialog(
        title: title,
        content: content,
        confirmText: confirmText,
        cancelText: cancelText,
        onConfirm: onConfirm,
        onCancel: onCancel,
        isDestructiveAction: isDestructiveAction,
        icon: icon,
        titlePadding: titlePadding,
        contentPadding: contentPadding,
        borderRadius: borderRadius,
        backgroundColor: backgroundColor,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final effectiveConfirmText = confirmText ?? 'Confirm';
    final effectiveCancelText = cancelText ?? 'Cancel';
    final effectiveBorderRadius = borderRadius ?? 16.0;

    return AlertDialog(
      backgroundColor: backgroundColor ?? Theme.of(context).dialogBackgroundColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(effectiveBorderRadius),
      ),
      titlePadding: titlePadding ?? const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
      contentPadding: contentPadding ?? const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
      title: Row(
        children: [
          if (icon != null) ...[
            icon!,
            const SizedBox(width: 16),
          ],
          Expanded(
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      content: content != null
          ? Text(
              content,
              style: Theme.of(context).textTheme.bodyMedium,
            )
          : null,
      actions: [
        if (onCancel != null)
          TextButton(
            onPressed: () {
              onCancel!();
              Navigator.of(context).pop(false);
            },
            child: Text(effectiveCancelText),
          ),
        TextButton(
          onPressed: () {
            if (onConfirm != null) onConfirm!();
            Navigator.of(context).pop(isDestructiveAction ? true : false);
          },
          style: isDestructiveAction
              ? TextButton.styleFrom(
                  foregroundColor: Theme.of(context).colorScheme.error,
                )
              : null,
          child: Text(effectiveConfirmText),
        ),
      ],
    );
  }
}