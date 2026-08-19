import 'package:flutter/material.dart';

enum CustomNavBarType {
  fixed,
  shifting,
}

class CustomBottomNavBarItem {
  final IconData icon;
  final String label;
  final bool showIndicator;

  const CustomBottomNavBarItem({
    required this.icon,
    required this.label,
    this.showIndicator = false,
  });
}

class CustomNavigationBar extends StatelessWidget {
  final List<CustomBottomNavBarItem> items;
  final int currentIndex;
  final ValueChanged<int> onTap;
  final Color? backgroundColor;
  final Color? activeColor;
  final Color? inactiveColor;
  final double? height;
  final CustomNavBarType type;
  final EdgeInsetsGeometry? labelPadding;

  CustomNavigationBar({
    super.key,
    required this.items,
    required this.currentIndex,
    required this.onTap,
    this.backgroundColor,
    this.activeColor,
    this.inactiveColor,
    this.height,
    this.type = CustomNavBarType.fixed,
    this.labelPadding,
  })  : assert(items.isNotEmpty, 'items cannot be empty'),
        assert(currentIndex >= 0 && currentIndex < items.length,
            'currentIndex out of bounds');

  @override
  Widget build(BuildContext context) {
    final effectiveBgColor =
        backgroundColor ?? Theme.of(context).bottomAppBarTheme.color ?? Colors.white;
    final effectiveActiveColor =
        activeColor ?? Theme.of(context).colorScheme.primary;
    final effectiveInactiveColor =
        inactiveColor ?? Colors.grey;

    return Container(
      height: height ?? 60.0,
      color: effectiveBgColor,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: items.asMap().entries.map((entry) {
          final index = entry.key;
          final item = entry.value;
          final isSelected = index == currentIndex;

          return Expanded(
            child: InkWell(
              onTap: () => onTap(index),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    item.icon,
                    color: isSelected ? effectiveActiveColor : effectiveInactiveColor,
                  ),
                  Padding(
                    padding: labelPadding ?? const EdgeInsets.only(top: 4.0),
                    child: Text(
                      item.label,
                      style: TextStyle(
                        color:
                            isSelected ? effectiveActiveColor : effectiveInactiveColor,
                        fontSize: 12,
                        fontWeight:
                            isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
