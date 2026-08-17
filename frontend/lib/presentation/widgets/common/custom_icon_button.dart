import 'package:flutter/material.dart';

class CustomIconButton extends StatelessWidget {
  final IconData? icon;
  final VoidCallback? onPressed;
  final String? tooltip;
  final double? size;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final bool isDisabled;
  final int? badgeCount;
  final String? badgeText;
  final bool isLoading;
  final String? label;
  final BoxShape shape;
  final Color? borderColor;
  final double borderWidth;

  const CustomIconButton({
    super.key,
    this.icon,
    this.onPressed,
    this.tooltip,
    this.size,
    this.backgroundColor,
    this.foregroundColor,
    this.isDisabled = false,
    this.badgeCount,
    this.badgeText,
    this.isLoading = false,
    this.label,
    this.shape = BoxShape.rectangle,
    this.borderColor,
    this.borderWidth = 1.0,
  })  : assert(icon != null, 'icon cannot be null'),
        assert(onPressed != null, 'onPressed cannot be null');

  @override
  Widget build(BuildContext context) {
    final effectiveFgColor =
        foregroundColor ?? Theme.of(context).colorScheme.primary;

    Widget content = isLoading
        ? SizedBox(
            width: (size ?? 24.0) * 0.8,
            height: (size ?? 24.0) * 0.8,
            child: const CircularProgressIndicator(strokeWidth: 2),
          )
        : Icon(
            icon,
            size: size ?? 24.0,
            color: isDisabled ? Colors.grey : effectiveFgColor,
          );

    if (label != null) {
      content = Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          content,
          const SizedBox(width: 4),
          Text(label!),
        ],
      );
    }

    final hasBadge =
        (badgeCount != null && badgeCount! > 0) || (badgeText != null && badgeText!.isNotEmpty);

    if (hasBadge) {
      content = Stack(
        clipBehavior: Clip.none,
        children: [
          content,
          Positioned(
            right: -6,
            top: -6,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(10),
              ),
              constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
              child: Text(
                badgeText ?? '$badgeCount',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      );
    }

    Widget button = InkWell(
      onTap: isDisabled ? null : onPressed,
      borderRadius: BorderRadius.circular(shape == BoxShape.circle ? 50 : 8),
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          shape: shape,
          color: backgroundColor,
          borderRadius: shape == BoxShape.circle ? null : BorderRadius.circular(8),
          border: borderColor != null
              ? Border.all(color: borderColor!, width: borderWidth)
              : null,
        ),
        child: content,
      ),
    );

    if (tooltip != null) {
      button = Tooltip(
        message: tooltip!,
        child: button,
      );
    }

    return button;
  }
}
