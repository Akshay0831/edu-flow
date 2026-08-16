import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'custom_snackbar.dart';

class OfflineSupportManager extends StateNotifier<OfflineSupportState> {
  OfflineSupportManager() : super(const OfflineSupportState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    await _loadOfflineData();
  }

  void setConnected(bool isConnected) {
    state = state.copyWith(isConnected: isConnected);
    if (!isConnected) {
      _saveOfflineData();
    }
  }

  Future<void> _loadOfflineData() async {
    final prefs = await SharedPreferences.getInstance();
    final hasOfflineData = prefs.getBool('hasOfflineData') ?? false;
    state = state.copyWith(hasOfflineData: hasOfflineData);
  }

  Future<void> _saveOfflineData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('hasOfflineData', true);
    state = state.copyWith(hasOfflineData: true);
  }

  Future<void> clearOfflineData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('hasOfflineData');
    state = state.copyWith(hasOfflineData: false, pendingOperations: 0);
  }

  void addPendingOperation() {
    state = state.copyWith(
      pendingOperations: (state.pendingOperations ?? 0) + 1,
      hasOfflineData: true,
    );
    _saveOfflineData();
  }
}

class OfflineSupportState {
  final bool isConnected;
  final bool hasOfflineData;
  final DateTime? lastSyncTime;
  final int? pendingOperations;

  const OfflineSupportState({
    this.isConnected = true,
    this.hasOfflineData = false,
    this.lastSyncTime,
    this.pendingOperations,
  });

  OfflineSupportState copyWith({
    bool? isConnected,
    bool? hasOfflineData,
    DateTime? lastSyncTime,
    int? pendingOperations,
  }) {
    return OfflineSupportState(
      isConnected: isConnected ?? this.isConnected,
      hasOfflineData: hasOfflineData ?? this.hasOfflineData,
      lastSyncTime: lastSyncTime ?? this.lastSyncTime,
      pendingOperations: pendingOperations ?? this.pendingOperations,
    );
  }
}

class OfflineSupportIndicator extends ConsumerWidget {
  final String message;
  final Widget? child;

  const OfflineSupportIndicator({
    super.key,
    this.message = 'You are offline. Changes will be synced when online.',
    this.child,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offlineState = ref.watch(offlineSupportProvider);

    return Column(
      children: [
        if (!offlineState.isConnected)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            color: Colors.orange.withValues(alpha: 0.1),
            child: Row(
              children: [
                const Icon(Icons.wifi_off, color: Colors.orange),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    message,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.orange[800],
                    ),
                  ),
                ),
              ],
            ),
          ),
        if (child != null) child!,
      ],
    );
  }
}

class SyncButton extends ConsumerWidget {
  final VoidCallback? onSync;
  final String? successMessage;
  final String? errorMessage;

  const SyncButton({
    super.key,
    this.onSync,
    this.successMessage,
    this.errorMessage,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offlineState = ref.watch(offlineSupportProvider);

    return ElevatedButton.icon(
      onPressed: () {
        try {
          if (onSync != null) {
            onSync!();
          }
          CustomSnackBar.showSuccess(
            context: context,
            message: successMessage ?? 'Sync completed successfully',
          );
          ref.read(offlineSupportProvider.notifier).clearOfflineData();
        } catch (e) {
          CustomSnackBar.showError(
            context: context,
            message: errorMessage ?? 'Sync failed: ${e.toString()}',
          );
        }
      },
      icon: const Icon(Icons.sync),
      label: Text(
        offlineState.hasOfflineData
            ? 'Sync (${offlineState.pendingOperations ?? 0} pending)'
            : 'Sync Now',
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: offlineState.hasOfflineData
            ? Colors.orange
            : Theme.of(context).primaryColor,
      ),
    );
  }
}

final offlineSupportProvider = StateNotifierProvider<OfflineSupportManager, OfflineSupportState>(
  (ref) => OfflineSupportManager(),
);