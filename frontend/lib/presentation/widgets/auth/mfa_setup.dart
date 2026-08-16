import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:edu_flow/presentation/widgets/common/custom_snackbar.dart';
import 'package:edu_flow/presentation/widgets/common/custom_button.dart';
import 'package:edu_flow/presentation/widgets/common/custom_text_field.dart';
import 'package:edu_flow/presentation/widgets/common/custom_app_bar.dart';

class MfaSetup extends ConsumerStatefulWidget {
  final bool showBackupCodes;
  final bool showRecoveryOptions;

  const MfaSetup({
    super.key,
    this.showBackupCodes = false,
    this.showRecoveryOptions = false,
  });

  @override
  ConsumerState<MfaSetup> createState() => _MfaSetupState();
}

class _MfaSetupState extends ConsumerState<MfaSetup> {
  bool _isMfaEnabled = false;
  bool _isLoading = false;
  bool _showQrSetup = false;
  bool _showCodeSetup = false;
  bool _showBackupCodesScreen = false;
  bool _showRecoveryScreen = false;
  
  final TextEditingController _mfaCodeController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _recoveryCodeController = TextEditingController();
  
  // Mock data - in real app, this would come from backend
  List<String> _backupCodes = [
    'ABC123DEF456',
    'GHI789JKL012',
    'MNO345PQR678',
    'STU901VWX234',
    'YZA567BCD890'
  ];

  @override
  void initState() {
    super.initState();
    _checkMfaStatus();
  }

  Future<void> _checkMfaStatus() async {
    // Simulate checking MFA status from backend
    await Future.delayed(const Duration(milliseconds: 500));
    setState(() {
      _isMfaEnabled = false; // Default to disabled
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Two-Factor Authentication',
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: _buildMainContent(),
      ),
    );
  }

  Widget _buildMainContent() {
    if (_showBackupCodesScreen) {
      return _buildBackupCodesScreen();
    }
    
    if (_showRecoveryScreen) {
      return _buildRecoveryScreen();
    }
    
    if (_isMfaEnabled) {
      return _buildDisableMfaScreen();
    } else {
      return _buildEnableMfaScreen();
    }
  }

  Widget _buildEnableMfaScreen() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Enable Two-Factor Authentication',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Add an extra layer of security to your account',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        
        // Setup method selection
        if (!_showQrSetup && !_showCodeSetup) ...[
          _buildSetupMethodSelector(),
        ],
        
        // QR Code Setup
        if (_showQrSetup) ...[
          _buildQrCodeSetup(),
        ],
        
        // Code Setup
        if (_showCodeSetup) ...[
          _buildCodeSetup(),
        ],
        
        // Help section
        if (!_showQrSetup && !_showCodeSetup) ...[
          const SizedBox(height: 32),
          _buildHelpSection(),
        ],
        
        // Backup codes option
        if (widget.showBackupCodes && _isMfaEnabled) ...[
          const SizedBox(height: 24),
          _buildBackupCodesOption(),
        ],
        
        // Recovery options
        if (widget.showRecoveryOptions) ...[
          const SizedBox(height: 24),
          _buildRecoveryOptions(),
        ],
      ],
    );
  }

  Widget _buildSetupMethodSelector() {
    return Column(
      children: [
        Card(
          child: ListTile(
            leading: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.qr_code_scanner,
                color: Colors.blue,
                size: 24,
              ),
            ),
            title: const Text('Scan QR Code'),
            subtitle: const Text('Use authenticator app to scan QR code'),
            onTap: () {
              setState(() {
                _showQrSetup = true;
                _showCodeSetup = false;
              });
            },
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.code,
                color: Colors.green,
                size: 24,
              ),
            ),
            title: const Text('Setup with Code'),
            subtitle: const Text('Enter setup manually using secret key'),
            onTap: () {
              setState(() {
                _showQrSetup = false;
                _showCodeSetup = true;
              });
            },
          ),
        ),
      ],
    );
  }

  Widget _buildQrCodeSetup() {
    return Column(
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Icon(
                  Icons.qr_code_2,
                  size: 120,
                  color: Colors.blue,
                ),
                const SizedBox(height: 16),
                const Text(
                  'Scan this QR Code',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Use your authenticator app (Google Authenticator, Authy, etc.) to scan this QR code',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                CustomButton(
                  text: 'I\'ve Scanned the Code',
                  onPressed: _enableMfa,
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    setState(() {
                      _showQrSetup = false;
                    });
                  },
                  child: const Text('Back to Methods'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCodeSetup() {
    return Column(
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Icon(
                  Icons.key,
                  size: 60,
                  color: Colors.green,
                ),
                const SizedBox(height: 16),
                const Text(
                  'Manual Setup',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Enter this secret key in your authenticator app:',
                  style: TextStyle(
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 16),
                SelectableText(
                  'JBSWY3DPEHPK3PXP',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 24),
                CustomTextField(
                  labelText: 'Enter 6-digit Code',
                  hintText: 'Enter code from authenticator app',
                  controller: _mfaCodeController,
                  keyboardType: TextInputType.number,
                  onChanged: (value) {
                    // Remove non-numeric characters
                    final numericValue = value.replaceAll(RegExp(r'[^0-9]'), '');
                    if (numericValue != value) {
                      _mfaCodeController.text = numericValue;
                    }
                  },
                  validator: (value) {
                    if (value == null || value.length != 6) {
                      return 'Please enter a valid 6-digit code';
                    }
                    if (!RegExp(r'^\d{6}$').hasMatch(value)) {
                      return 'Please enter only numbers';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                CustomButton(
                  text: 'Enable MFA',
                  onPressed: _enableMfa,
                  isLoading: _isLoading,
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    setState(() {
                      _showCodeSetup = false;
                      _mfaCodeController.clear();
                    });
                  },
                  child: const Text('Back to Methods'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDisableMfaScreen() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Disable Two-Factor Authentication',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Remove two-factor authentication from your account',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Icon(
                  Icons.warning_amber,
                  size: 60,
                  color: Colors.orange,
                ),
                const SizedBox(height: 16),
                const Text(
                  'Security Warning',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: Colors.orange,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Disabling two-factor authentication reduces your account security.',
                  style: TextStyle(
                    fontSize: 14,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                CustomTextField(
                  labelText: 'Enter Your Password',
                  hintText: 'Confirm your identity',
                  controller: _passwordController,
                  obscureText: true,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your password';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                CustomButton(
                  text: 'Disable MFA',
                  onPressed: _disableMfa,
                  isLoading: _isLoading,
                  backgroundColor: Colors.red,
                  textColor: Colors.white,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBackupCodesScreen() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Backup Codes',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Save these codes securely. You can use them to access your account if you lose your authenticator device.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Text(
                  'Your Backup Codes',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Store these codes in a safe place. Each code can only be used once.',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 24),
                ..._backupCodes.map((code) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    children: [
                      const Icon(Icons.key, size: 16, color: Colors.grey),
                      const SizedBox(width: 8),
                      Expanded(
                        child: SelectableText(
                          code,
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 16,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy),
                        onPressed: () => _copyToClipboard(code),
                        tooltip: 'Copy code',
                      ),
                    ],
                  ),
                )),
                const SizedBox(height: 24),
                CustomButton(
                  text: 'I\'ve Saved the Codes',
                  onPressed: () {
                    setState(() {
                      _showBackupCodesScreen = false;
                    });
                    CustomSnackBar.showSuccess(
                      context: context,
                      message: 'Backup codes saved successfully',
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRecoveryScreen() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Use Backup Code',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Enter one of your backup codes to regain access to your account.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 32),
        
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                CustomTextField(
                  labelText: 'Backup Code',
                  hintText: 'Enter your backup code',
                  controller: _recoveryCodeController,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter a backup code';
                    }
                    if (!_backupCodes.contains(value)) {
                      return 'Invalid backup code';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),
                CustomButton(
                  text: 'Verify',
                onPressed: _verifyRecoveryCode,
                isLoading: _isLoading,
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: () {
                  setState(() {
                    _showRecoveryScreen = false;
                  });
                },
                child: const Text('Cancel'),
              ),
            ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHelpSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'What is 2FA?',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Two-factor authentication adds an extra layer of security to your account by requiring two different methods of verification.',
            ),
            const SizedBox(height: 16),
            GestureDetector(
              onTap: () {
                // Show help dialog
                _showHelpDialog();
              },
              child: const Text(
                'How to set up',
                style: TextStyle(
                  color: Colors.blue,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBackupCodesOption() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.backup, color: Colors.blue),
        title: const Text('Backup Codes'),
        subtitle: const Text('View and copy your backup codes'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          setState(() {
            _showBackupCodesScreen = true;
          });
        },
      ),
    );
  }

  Widget _buildRecoveryOptions() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.help_outline, color: Colors.orange),
        title: const Text('Lost Authenticator?'),
        subtitle: const Text('Use backup codes to regain access'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          setState(() {
            _showRecoveryScreen = true;
          });
        },
      ),
    );
  }

  Future<void> _enableMfa() async {
    if (_showCodeSetup && _mfaCodeController.text.length != 6) {
      CustomSnackBar.showError(
        context: context,
        message: 'Please enter a valid 6-digit code',
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Simulate API call to enable MFA
      await Future.delayed(const Duration(seconds: 2));
      
      // In real app, this would call the backend API
      // await ref.read(authServiceProvider).enableMfa(_mfaCodeController.text);
      
      setState(() {
        _isMfaEnabled = true;
        _isLoading = false;
        _showQrSetup = false;
        _showCodeSetup = false;
        _mfaCodeController.clear();
      });

      CustomSnackBar.showSuccess(
        context: context,
        message: 'MFA enabled successfully',
      );

      // Navigate to backup codes screen if enabled
      if (widget.showBackupCodes) {
        setState(() {
          _showBackupCodesScreen = true;
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      CustomSnackBar.showError(
        context: context,
        message: 'Failed to enable MFA: ${e.toString()}',
      );
    }
  }

  Future<void> _disableMfa() async {
    if (_passwordController.text.isEmpty) {
      CustomSnackBar.showError(
        context: context,
        message: 'Please enter your password to confirm',
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Simulate API call to disable MFA
      await Future.delayed(const Duration(seconds: 2));
      
      // In real app, this would call the backend API
      // await ref.read(authServiceProvider).disableMfa(_passwordController.text);
      
      setState(() {
        _isMfaEnabled = false;
        _isLoading = false;
        _passwordController.clear();
      });

      CustomSnackBar.showSuccess(
        context: context,
        message: 'MFA disabled successfully',
      );
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      CustomSnackBar.showError(
        context: context,
        message: 'Failed to disable MFA: ${e.toString()}',
      );
    }
  }

  Future<void> _verifyRecoveryCode() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Simulate API call to verify recovery code
      await Future.delayed(const Duration(seconds: 1));
      
      // Remove used backup code
      _backupCodes.remove(_recoveryCodeController.text);
      
      setState(() {
        _isLoading = false;
        _showRecoveryScreen = false;
        _recoveryCodeController.clear();
      });

      CustomSnackBar.showSuccess(
        context: context,
        message: 'Recovery code verified successfully',
      );
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      CustomSnackBar.showError(
        context: context,
        message: 'Invalid recovery code',
      );
    }
  }

  void _copyToClipboard(String text) {
    // In real app, use clipboard package
    CustomSnackBar.showSuccess(
      context: context,
      message: 'Code copied to clipboard',
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('How to Set Up Two-Factor Authentication'),
        content: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('1. Choose your preferred method (QR Code or Manual Setup)'),
            SizedBox(height: 8),
            Text('2. For QR Code: Use an authenticator app to scan the QR code'),
            SizedBox(height: 8),
            Text('3. For Manual Setup: Enter the secret key in your authenticator app'),
            SizedBox(height: 8),
            Text('4. Enter the 6-digit code shown in the app'),
            SizedBox(height: 8),
            Text('5. Complete the setup and save your backup codes'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _mfaCodeController.dispose();
    _passwordController.dispose();
    _recoveryCodeController.dispose();
    super.dispose();
  }
}