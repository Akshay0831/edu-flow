import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final dynamic icon;
  final Color? backgroundColor;
  final Color? textColor;
  final double? width;
  final double? height;
  final bool isLoading;
  final bool isOutlined;
  final bool isDisabled;
  final double? borderRadius;
  final FontWeight? fontWeight;

  const CustomButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.icon,
    this.backgroundColor,
    this.textColor,
    this.width,
    this.height,
    this.isLoading = false,
    this.isOutlined = false,
    this.isDisabled = false,
    this.borderRadius,
    this.fontWeight,
  }) : assert(text.length > 0, 'text cannot be empty');

  @override
  Widget build(BuildContext context) {
    final effectiveBackgroundColor = isOutlined 
        ? Colors.transparent 
        : (backgroundColor ?? Theme.of(context).colorScheme.primary);
    
    final effectiveTextColor = textColor ?? (isOutlined 
        ? Theme.of(context).colorScheme.primary 
        : Colors.white);
    
    final effectiveBorderRadius = borderRadius ?? 8.0;
    
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(effectiveBorderRadius),
        border: isOutlined ? Border.all(
          color: Theme.of(context).colorScheme.primary,
          width: 1.5,
        ) : null,
      ),
      child: Material(
        color: isDisabled ? Colors.grey[300] : effectiveBackgroundColor,
        borderRadius: BorderRadius.circular(effectiveBorderRadius),
        child: InkWell(
          borderRadius: BorderRadius.circular(effectiveBorderRadius),
          onTap: isDisabled || isLoading ? null : onPressed,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
            child: isLoading
                ? const Center(
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                  )
                : Row(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (icon != null)
                        Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: _buildIcon(icon, effectiveTextColor),
                        ),
                      Text(
                        text,
                        style: TextStyle(
                          color: isDisabled ? Colors.grey[600] : effectiveTextColor,
                          fontSize: 16,
                          fontWeight: fontWeight ?? FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildIcon(dynamic icon, Color effectiveColor) {
    if (icon is Widget) return icon;
    if (icon is IconData) {
      return Icon(icon, color: effectiveColor, size: 20);
    }
    if (icon is String) {
      return Icon(_getIconData(icon), color: effectiveColor, size: 20);
    }
    return const SizedBox.shrink();
  }

  IconData _getIconData(String icon) {
    switch (icon) {
      case 'email':
        return Icons.email;
      case 'password':
        return Icons.lock;
      case 'login':
        return Icons.login;
      case 'register':
        return Icons.app_registration;
      case 'save':
        return Icons.save;
      case 'cancel':
        return Icons.cancel;
      case 'delete':
        return Icons.delete;
      case 'edit':
        return Icons.edit;
      case 'add':
        return Icons.add;
      case 'remove':
        return Icons.remove;
      case 'search':
        return Icons.search;
      case 'filter':
        return Icons.filter_list;
      case 'close':
        return Icons.close;
      case 'check':
        return Icons.check;
      case 'arrow_back':
        return Icons.arrow_back;
      case 'arrow_forward':
        return Icons.arrow_forward;
      case 'home':
        return Icons.home;
      case 'dashboard':
        return Icons.dashboard;
      case 'user':
        return Icons.person;
      case 'settings':
        return Icons.settings;
      case 'help':
        return Icons.help;
      case 'info':
        return Icons.info;
      case 'warning':
        return Icons.warning;
      case 'success':
        return Icons.check_circle;
      case 'error':
        return Icons.error;
      case 'loading':
        return Icons.refresh;
      default:
        return Icons.add;
    }
  }
}