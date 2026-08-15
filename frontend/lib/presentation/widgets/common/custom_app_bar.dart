import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String? title;
  final Widget? titleWidget;
  final List<Widget>? actions;
  final Widget? leading;
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
  }) : assert(title != null || titleWidget != null,
          'Either title or titleWidget must be provided');

  @override
  Widget build(BuildContext context) {
    final effectiveBackgroundColor = backgroundColor ?? Theme.of(context).primaryColor;
    final effectiveForegroundColor = foregroundColor ?? Theme.of(context).primaryColorLight;
    final effectiveElevation = elevation ?? (showShadow! ? 4.0 : 0.0);

    return AppBar(
      title: titleWidget ?? Text(
        title!,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          color: effectiveForegroundColor,
        ),
      ),
      backgroundColor: effectiveBackgroundColor,
      foregroundColor: effectiveForegroundColor,
      elevation: effectiveElevation,
      centerTitle: centerTitle,
      automaticallyImplyLeading: automaticallyImplyLeading,
      leading: leading ?? (hasBackButton
          ? IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: onLeadingPressed ?? () => Navigator.of(context).pop(),
              tooltip: backTooltip ?? 'Back',
            )
          : null),
      actions: actions,
      bottom: bottom,
    );
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
      title: titleWidget ?? Text(
        title!,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          color: effectiveForegroundColor,
        ),
      ),
      backgroundColor: effectiveBackgroundColor,
      foregroundColor: effectiveForegroundColor,
      expandedHeight: expandedHeight,
      collapsedHeight: collapsedHeight,
      pinned: pinned,
      floating: floating,
      snap: snap,
      stretch: stretch,
      flexibleSpace: flexibleSpace,
      background: background,
      titleSpacing: titleSpacing,
      centerTitle: centerTitle,
      forceElevated: forceElevated,
      collapsedElevation: collapsedElevation,
      leading: leading ?? (automaticallyImplyLeading
          ? IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: onLeadingPressed ?? () => Navigator.of(context).pop(),
              tooltip: 'Back',
            )
          : null),
      actions: actions,
    );
  }
}