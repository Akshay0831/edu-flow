import 'package:flutter/material.dart';

class CustomListTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;
  final bool isSelected;
  final bool isThreeLine;
  final EdgeInsetsGeometry? contentPadding;
  final Color? selectedColor;
  final Color? textColor;
  final double? horizontalPadding;
  final double? verticalPadding;

  const CustomListTile({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
    this.isSelected = false,
    this.isThreeLine = false,
    this.contentPadding,
    this.selectedColor,
    this.textColor,
    this.horizontalPadding,
    this.verticalPadding,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveSelectedColor = selectedColor ?? Theme.of(context).colorScheme.primary.withValues(alpha: 0.1);
    final effectiveTextColor = textColor ?? Theme.of(context).colorScheme.onSurface;
    final effectiveHorizontalPadding = horizontalPadding ?? 16.0;
    final effectiveVerticalPadding = verticalPadding ?? 8.0;

    return Container(
      decoration: BoxDecoration(
        color: isSelected ? effectiveSelectedColor : Colors.transparent,
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: ListTile(
        title: Text(
          title,
          style: TextStyle(
            color: effectiveTextColor,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
        subtitle: subtitle != null
            ? Text(
                subtitle!,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            : null,
        leading: leading,
        trailing: trailing,
        onTap: onTap,
        isThreeLine: isThreeLine,
        contentPadding: contentPadding ?? EdgeInsets.symmetric(
          horizontal: effectiveHorizontalPadding,
          vertical: effectiveVerticalPadding,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8.0),
        ),
        selected: isSelected,
        selectedTileColor: effectiveSelectedColor,
      ),
    );
  }
}