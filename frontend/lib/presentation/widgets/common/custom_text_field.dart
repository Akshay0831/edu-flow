import 'package:flutter/material.dart';

class CustomTextField extends StatefulWidget {
  final String? labelText;
  final String? label;
  final String? hintText;
  final String? hint;
  final dynamic prefixIcon;
  final dynamic suffixIcon;
  final TextEditingController? controller;
  final bool obscureText;
  final bool? isPassword;
  final bool enabled;
  final bool? isEnabled;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final Function(String)? onChanged;
  final Function(String)? onSubmitted;
  final String? Function(String?)? validator;
  final int? maxLines;
  final int? minLines;
  final double? borderRadius;
  final Color? fillColor;
  final EdgeInsetsGeometry? contentPadding;
  final bool? showCursor;
  final bool autofocus;
  final VoidCallback? onTap;
  final double? width;
  final double? height;
  final String? helperText;
  final String? errorText;

  const CustomTextField({
    super.key,
    this.labelText,
    this.label,
    this.hintText,
    this.hint,
    this.controller,
    this.obscureText = false,
    this.isPassword,
    this.enabled = true,
    this.isEnabled,
    this.keyboardType,
    this.textInputAction,
    this.onChanged,
    this.onSubmitted,
    this.validator,
    this.maxLines = 1,
    this.minLines,
    this.borderRadius = 8.0,
    this.fillColor,
    this.contentPadding,
    this.showCursor,
    this.autofocus = false,
    this.prefixIcon,
    this.suffixIcon,
    this.onTap,
    this.width,
    this.height,
    this.helperText,
    this.errorText,
  })  : assert(labelText != null || label != null, 'label cannot be null or empty'),
        assert(controller != null, 'controller cannot be null');

  @override
  State<CustomTextField> createState() => _CustomTextFieldState();
}

class _CustomTextFieldState extends State<CustomTextField> {
  late bool _obscureText;
  bool _hasFocus = false;

  bool get _isPassword => widget.isPassword ?? widget.obscureText;
  bool get _effectiveEnabled => widget.isEnabled ?? widget.enabled;
  String get _effectiveLabel => widget.label ?? widget.labelText ?? '';
  String get _effectiveHint => widget.hint ?? widget.hintText ?? '';

  @override
  void initState() {
    super.initState();
    _obscureText = _isPassword;
  }

  @override
  Widget build(BuildContext context) {
    final fillColor = widget.fillColor ?? Colors.grey[50];
    final borderRadius = BorderRadius.circular(widget.borderRadius ?? 8.0);
    final contentPadding = widget.contentPadding ??
        const EdgeInsets.symmetric(horizontal: 16, vertical: 12);

    Widget widgetContent = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Label
        if (_effectiveLabel.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8.0, left: 4.0),
            child: Text(
              _effectiveLabel,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: _effectiveEnabled
                    ? Theme.of(context).colorScheme.onSurface
                    : Colors.grey[600],
              ),
            ),
          ),

        // Text field
        Focus(
          onFocusChange: (hasFocus) {
            setState(() => _hasFocus = hasFocus);
          },
          child: TextFormField(
            controller: widget.controller,
            obscureText: _isPassword ? _obscureText : false,
            enabled: _effectiveEnabled,
            onTap: widget.onTap,
            keyboardType: widget.keyboardType,
            textInputAction: widget.textInputAction,
            onChanged: widget.onChanged,
            onFieldSubmitted: widget.onSubmitted,
            validator: widget.validator,
            maxLines: _isPassword ? 1 : widget.maxLines,
            minLines: widget.minLines,
            showCursor: widget.showCursor,
            autofocus: widget.autofocus,
            style: TextStyle(
              fontSize: 16,
              color: _effectiveEnabled
                  ? Theme.of(context).colorScheme.onSurface
                  : Colors.grey[600],
            ),
            decoration: InputDecoration(
              hintText: _effectiveHint.isNotEmpty ? _effectiveHint : null,
              helperText: widget.helperText,
              errorText: widget.errorText,
              hintStyle: TextStyle(
                fontSize: 16,
                color: Colors.grey[400],
              ),
              filled: true,
              fillColor: fillColor,
              border: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: BorderSide(
                  color: _hasFocus
                      ? Theme.of(context).colorScheme.primary
                      : Colors.grey[300]!,
                  width: 1,
                ),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: BorderSide(
                  color: _effectiveEnabled ? Colors.grey[300]! : Colors.grey[200]!,
                  width: 1,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: BorderSide(
                  color: Theme.of(context).colorScheme.primary,
                  width: 2,
                ),
              ),
              disabledBorder: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: BorderSide(
                  color: Colors.grey[200]!,
                  width: 1,
                ),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: const BorderSide(
                  color: Colors.red,
                  width: 1,
                ),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: borderRadius,
                borderSide: const BorderSide(
                  color: Colors.red,
                  width: 2,
                ),
              ),
              contentPadding: contentPadding,
              prefixIcon: widget.prefixIcon != null
                  ? (widget.prefixIcon is Widget
                      ? widget.prefixIcon as Widget
                      : Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12.0),
                          child: Icon(
                            _getIconData(widget.prefixIcon),
                            color: _effectiveEnabled ? Colors.grey[600] : Colors.grey[400],
                            size: 20,
                          ),
                        ))
                  : null,
              suffixIcon: _isPassword
                  ? IconButton(
                      icon: Icon(
                        _obscureText
                            ? Icons.visibility_off
                            : Icons.visibility,
                        color: _effectiveEnabled ? Colors.grey[600] : Colors.grey[400],
                        size: 20,
                      ),
                      onPressed: _effectiveEnabled
                          ? () => setState(() => _obscureText = !_obscureText)
                          : null,
                    )
                  : widget.suffixIcon != null
                      ? (widget.suffixIcon is Widget
                          ? widget.suffixIcon as Widget
                          : Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 12.0),
                              child: Icon(
                                _getIconData(widget.suffixIcon),
                                color: _effectiveEnabled ? Colors.grey[600] : Colors.grey[400],
                                size: 20,
                              ),
                            ))
                      : null,
            ),
          ),
        ),
      ],
    );

    if (widget.width != null || widget.height != null) {
      widgetContent = SizedBox(
        width: widget.width,
        height: widget.height,
        child: widgetContent,
      );
    }

    return widgetContent;
  }

  IconData _getIconData(dynamic icon) {
    if (icon is IconData) return icon;
    if (icon is String) {
      switch (icon.toLowerCase()) {
        case 'email':
        case 'mail':
          return Icons.email_outlined;
        case 'password':
          return Icons.lock_outlined;
        case 'visibility':
          return Icons.visibility;
        case 'visibility_off':
          return Icons.visibility_off;
        case 'person':
          return Icons.person_outlined;
        case 'phone':
          return Icons.phone_outlined;
        case 'calendar':
          return Icons.calendar_today_outlined;
        case 'search':
          return Icons.search_outlined;
        case 'user':
          return Icons.person_outline;
        case 'lock':
          return Icons.lock_outline;
        case 'eye':
          return Icons.visibility;
        case 'eye_off':
          return Icons.visibility_off;
        case 'school':
          return Icons.school_outlined;
        case 'book':
          return Icons.book_outlined;
        case 'home':
          return Icons.home_outlined;
        case 'settings':
          return Icons.settings_outlined;
        case 'help':
          return Icons.help_outline;
        case 'info':
          return Icons.info_outline;
        case 'warning':
          return Icons.warning_outlined;
        case 'success':
          return Icons.check_circle_outline;
        case 'error':
          return Icons.error_outline;
        default:
          return Icons.text_fields;
      }
    }
    return Icons.text_fields;
  }
}