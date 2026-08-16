import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String? title;
  final Widget? titleWidget;
  final List<dynamic>? actions;
  final dynamic leading;
  final bool automaticallyImplyLeading;
  final VoidCallback? onLeadingPressed;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double? elevation;
  final bool centerTitle;
  final PreferredSizeWidget? bottom;
  final bool hasBackButton;
  final String? backTooltip;
  final bool? showShadow;
  final String? semanticLabel;
  final double? fontSize;
  final FontWeight? fontWeight;
  final Color? titleColor;
  final Color? iconColor;

  const CustomAppBar({
    super.key,
    this.title,
    this.titleWidget,
    this.actions,
    this.leading,
    this.automaticallyImplyLeading = true,
    this.onLeadingPressed,
    this.backgroundColor,
    this.foregroundColor,
    this.elevation,
    this.centerTitle = true,
    this.bottom,
    this.hasBackButton = true,
    this.backTooltip,
    this.showShadow = false,
    this.semanticLabel,
    this.fontSize,
    this.fontWeight,
    this.titleColor,
    this.iconColor,
  }) : assert(titleWidget != null || (title != null && title.length > 0),
          'Either non-empty title or titleWidget must be provided');

  @override
  Widget build(BuildContext context) {
    final effectiveBackgroundColor = backgroundColor ?? Theme.of(context).primaryColor;
    final effectiveForegroundColor = foregroundColor ?? Theme.of(context).primaryColorLight;
    final effectiveTitleColor = titleColor ?? effectiveForegroundColor;
    final effectiveElevation = elevation ?? (showShadow! ? 4.0 : 0.0);

    Widget? effectiveLeading;
    if (leading != null) {
      if (leading is Widget) {
        effectiveLeading = leading as Widget;
      } else if (leading is IconData) {
        effectiveLeading = IconButton(
          icon: Icon(leading as IconData, color: iconColor ?? effectiveForegroundColor),
          onPressed: onLeadingPressed,
        );
      }
    } else if (hasBackButton) {
      effectiveLeading = IconButton(
        icon: Icon(Icons.arrow_back, color: iconColor ?? effectiveForegroundColor),
        onPressed: onLeadingPressed ?? () => Navigator.of(context).pop(),
        tooltip: backTooltip ?? 'Back',
      );
    }

    List<Widget>? effectiveActions;
    if (actions != null) {
      effectiveActions = actions!.map<Widget>((action) {
        if (action is Widget) return action;
        if (action is IconData) {
          return IconButton(
            icon: Icon(action, color: iconColor ?? effectiveForegroundColor),
            onPressed: () {},
          );
        }
        return const SizedBox.shrink();
      }).toList();
    }

    Widget appBarWidget = AppBar(
      title: titleWidget ??
          Text(
            title ?? '',
            style: TextStyle(
              fontSize: fontSize ?? 20,
              fontWeight: fontWeight ?? FontWeight.w600,
              color: effectiveTitleColor,
            ),
          ),
      backgroundColor: effectiveBackgroundColor,
      foregroundColor: effectiveForegroundColor,
      elevation: effectiveElevation,
      centerTitle: centerTitle,
      automaticallyImplyLeading: automaticallyImplyLeading,
      leading: effectiveLeading,
      actions: effectiveActions,
      bottom: bottom,
    );

    if (semanticLabel != null) {
      return Semantics(
        label: semanticLabel,
        child: appBarWidget,
      );
    }

    return appBarWidget;
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

class CustomSliverAppBar extends StatelessWidget {
  final String? title;
  final Widget? titleWidget;
  final Widget? leading;
  final List<Widget>? actions;
  final bool automaticallyImplyLeading;
  final VoidCallback? onLeadingPressed;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double? expandedHeight;
  final double? collapsedHeight;
  final bool pinned;
  final bool floating;
  final bool snap;
  final bool stretch;
  final Widget? flexibleSpace;
  final Widget? background;
  final double? titleSpacing;
  final bool centerTitle;
  final bool? forceElevated;
  final double? collapsedElevation;

  const CustomSliverAppBar({
    super.key,
    this.title,
    this.titleWidget,
    this.leading,
    this.actions,
    this.automaticallyImplyLeading = true,
    this.onLeadingPressed,
    this.backgroundColor,
    this.foregroundColor,
    this.expandedHeight,
    this.collapsedHeight,
    this.pinned = false,
    this.floating = false,
    this.snap = false,
    this.stretch = false,
    this.flexibleSpace,
    this.background,
    this.titleSpacing,
    this.centerTitle = true,
    this.forceElevated,
    this.collapsedElevation,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveBackgroundColor = backgroundColor ?? Theme.of(context).primaryColor;
    final effectiveForegroundColor = foregroundColor ?? Theme.of(context).primaryColorLight;

    return SliverAppBar(
      title: titleWidget ??
          (title != null
              ? Text(
                  title!,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: effectiveForegroundColor,
                  ),
                )
              : null),
      backgroundColor: effectiveBackgroundColor,
      foregroundColor: effectiveForegroundColor,
      expandedHeight: expandedHeight,
      collapsedHeight: collapsedHeight,
      pinned: pinned,
      floating: floating,
      snap: snap,
      stretch: stretch,
      flexibleSpace: flexibleSpace,
      automaticallyImplyLeading: automaticallyImplyLeading,
      leading: leading ??
          IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: onLeadingPressed ?? () => Navigator.of(context).pop(),
          ),
      actions: actions,
      centerTitle: centerTitle,
      titleSpacing: titleSpacing,
      forceElevated: forceElevated ?? false,
      elevation: collapsedElevation,
    );
  }
}