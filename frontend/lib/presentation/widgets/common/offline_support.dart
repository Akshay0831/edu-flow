import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

class OfflineSupportManager extends StateNotifier<OfflineSupportState> {
  OfflineSupportManager() : super(const OfflineSupportState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    await _checkConnectivity();
    await _loadOfflineData();
    _startConnectivityMonitoring();
  }

  Future<void> _checkConnectivity() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    final isConnected = connectivityResult != ConnectivityResult.none;
    
    state = state.copyWith(isConnected: isConnected);
    
    if (!isConnected) {
      await _saveOfflineData();
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
    state = state.copyWith(hasOfflineData: false);
  }

  void _startConnectivityMonitoring() {
    Connectivity().onConnectivityChanged.listen((result) {
      final isConnected = result != ConnectivityResult.none;
      state = state.copyWith(isConnected: isConnected);
    });
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
            color: Colors.orange.withOpacity(0.1),
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
      onPressed: () async {
        try {
          if (onSync != null) {
            await onSync!();
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

extension on OfflineSupportManager {
  Future<void> addPendingOperation() async {
    state = state.copyWith(
      pendingOperations: (state.pendingOperations ?? 0) + 1,
    );
  }

  Future<void> removePendingOperation() async {
    final newPending = (state.pendingOperations ?? 0) - 1;
    state = state.copyWith(
      pendingOperations: newPending > 0 ? newPending : null,
    );
  }

  Future<void> updateLastSyncTime() async {
    state = state.copyWith(lastSyncTime: DateTime.now());
  }
}