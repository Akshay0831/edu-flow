import 'package:flutter/material.dart';

class CustomCard extends StatelessWidget {
  final Widget child;
  final Color? backgroundColor;
  final double? elevation;
  final EdgeInsetsGeometry? margin;
  final EdgeInsetsGeometry? padding;
  final BorderRadiusGeometry? borderRadius;
  final VoidCallback? onTap;
  final bool hasBorder;
  final Color? borderColor;
  final double? borderWidth;

  const CustomCard({
    super.key,
    required this.child,
    this.backgroundColor,
    this.elevation,
    this.margin,
    this.padding,
    this.borderRadius,
    this.onTap,
    this.hasBorder = false,
    this.borderColor,
    this.borderWidth,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveElevation = elevation ?? (onTap != null ? 2.0 : 0.0);
    final effectiveBackgroundColor = backgroundColor ?? Theme.of(context).cardColor;
    final effectiveBorderRadius = borderRadius ?? BorderRadius.circular(12.0);
    final effectiveBorderColor = borderColor ?? Theme.of(context).colorScheme.outline.withOpacity(0.2);
    final effectiveBorderWidth = borderWidth ?? 1.0;

    Widget card = Card(
      elevation: effectiveElevation,
      color: effectiveBackgroundColor,
      margin: margin ?? const EdgeInsets.all(8.0),
      shape: RoundedRectangleBorder(
        borderRadius: effectiveBorderRadius,
        side: hasBorder 
            ? BorderSide(color: effectiveBorderColor, width: effectiveBorderWidth)
            : BorderSide.none,
      ),
      child: padding != null 
          ? Padding(padding: padding!, child: child)
          : child,
    );

    if (onTap != null) {
      card = InkWell(
        onTap: onTap,
        borderRadius: effectiveBorderRadius,
        child: card,
      );
    }

    return card;
  }
}