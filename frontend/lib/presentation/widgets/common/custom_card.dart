import 'package:flutter/material.dart';

class CustomCard extends StatelessWidget {
  final Widget? child;
  final String? title;
  final String? subtitle;
  final Widget? action;
  final double? width;
  final double? height;
  final bool isLoading;
  final bool isDisabled;
  final Color? backgroundColor;
  final double? elevation;
  final EdgeInsetsGeometry? margin;
  final EdgeInsetsGeometry? padding;
  final BorderRadius? borderRadius;
  final VoidCallback? onTap;
  final bool hasBorder;
  final Color? borderColor;
  final double? borderWidth;

  const CustomCard({
    super.key,
    this.child,
    this.title,
    this.subtitle,
    this.action,
    this.width,
    this.height,
    this.isLoading = false,
    this.isDisabled = false,
    this.backgroundColor,
    this.elevation,
    this.margin,
    this.padding,
    this.borderRadius,
    this.onTap,
    this.hasBorder = false,
    this.borderColor,
    this.borderWidth,
  }) : assert(child != null, 'child cannot be null');

  @override
  Widget build(BuildContext context) {
    final effectiveElevation = elevation ?? (onTap != null ? 2.0 : 0.0);
    final effectiveBackgroundColor = backgroundColor ?? Theme.of(context).cardColor;
    final effectiveBorderRadius = borderRadius ?? BorderRadius.circular(12.0);
    final effectiveBorderColor = borderColor ?? (hasBorder ? Theme.of(context).colorScheme.outline.withOpacity(0.2) : Colors.transparent);
    final effectiveBorderWidth = borderWidth ?? 1.0;

    Widget cardContent;

    if (isLoading) {
      cardContent = const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: CircularProgressIndicator(),
        ),
      );
    } else {
      final List<Widget> columnChildren = [];

      if (title != null || subtitle != null || action != null) {
        columnChildren.add(
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (title != null)
                      Text(
                        title!,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        subtitle!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey[600],
                            ),
                      ),
                    ],
                  ],
                ),
              ),
              if (action != null) action!,
            ],
          ),
        );
        columnChildren.add(const SizedBox(height: 8));
      }

      if (child != null) {
        columnChildren.add(child!);
      }

      cardContent = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: columnChildren,
      );
    }

    Widget card = Card(
      elevation: effectiveElevation,
      color: effectiveBackgroundColor,
      margin: margin ?? const EdgeInsets.all(8.0),
      shape: RoundedRectangleBorder(
        borderRadius: effectiveBorderRadius,
        side: (hasBorder || borderColor != null)
            ? BorderSide(color: effectiveBorderColor, width: effectiveBorderWidth)
            : BorderSide.none,
      ),
      child: padding != null 
          ? Padding(padding: padding!, child: cardContent)
          : Padding(padding: const EdgeInsets.all(16.0), child: cardContent),
    );

    if (onTap != null && !isDisabled) {
      card = InkWell(
        onTap: onTap,
        borderRadius: effectiveBorderRadius,
        child: card,
      );
    }

    if (width != null || height != null) {
      card = SizedBox(
        width: width,
        height: height,
        child: card,
      );
    }

    return card;
  }
}