import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'auth_wrapper.dart';
import 'custom_snackbar.dart';
import 'custom_alert_dialog.dart';

class MultiFactorAuthScreen extends ConsumerStatefulWidget {
  final String email;
  final String password;
  final String? role;

  const MultiFactorAuthScreen({
    super.key,
    required this.email,
    required this.password,
    this.role,
  });

  @override
  ConsumerState<MultiFactorAuthScreen> createState() => _MultiFactorAuthScreenState();
}

class _MultiFactorAuthScreenState extends ConsumerState<MultiFactorAuthScreen> {
  int _selectedMethod = 0;
  String _verificationCode = '';
  final TextEditingController _codeController = TextEditingController();
  bool _isLoading = false;
  bool _isCodeSent = false;

  final List<Map<String, dynamic>> _authMethods = [
    {
      'id': 1,
      'title': 'SMS Verification',
      'subtitle': 'Receive verification code via SMS',
      'icon': Icons.sms,
      'color': Colors.blue,
    },
    {
      'id': 2,
      'title': 'Email Verification',
      'subtitle': 'Receive verification code via email',
      'icon': Icons.email,
      'color': Colors.green,
    },
    {
      'id': 3,
      'title': 'Google Authenticator',
      'subtitle': 'Use Google Authenticator app',
      'icon': Icons.phone_android,
      'color': Colors.red,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Two-Factor Authentication',
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Choose verification method',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'We\'ll send a verification code to secure your account',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 32),
            if (!_isCodeSent) ...[
              Expanded(
                child: ListView.builder(
                  itemCount: _authMethods.length,
                  itemBuilder: (context, index) {
                    final method = _authMethods[index];
                    return Card(
                      elevation: 2,
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: method['color'].withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Icon(
                            method['icon'],
                            color: method['color'],
                          ),
                        ),
                        title: Text(method['title']),
                        subtitle: Text(method['subtitle']),
                        trailing: _selectedMethod == method['id']
                            ? const Icon(Icons.check_circle, color: Colors.green)
                            : null,
                        onTap: () {
                          setState(() {
                            _selectedMethod = method['id'];
                          });
                        },
                      ),
                    );
                  },
                ),
              ),
              ElevatedButton(
                onPressed: _sendVerificationCode,
                child: const Text('Send Verification Code'),
              ),
            ] else ...[
              Text(
                'Enter verification code',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 16),
              CustomTextField(
                labelText: 'Verification Code',
                hintText: 'Enter 6-digit code',
                controller: _codeController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                onChanged: (value) {
                  _verificationCode = value;
                },
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _verifyCode,
                      child: _isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                              ),
                            )
                          : const Text('Verify & Continue'),
                    ),
                  ),
                  const SizedBox(width: 16),
                  TextButton(
                    onPressed: _resendCode,
                    child: const Text('Resend Code'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _sendVerificationCode() async {
    setState(() {
      _isLoading = true;
      _isCodeSent = true;
    });

    try {
      // Simulate sending verification code
      await Future.delayed(const Duration(seconds: 2));
      
      CustomSnackBar.showSuccess(
        context: context,
        message: 'Verification code sent successfully',
      );
    } catch (e) {
      setState(() {
        _isCodeSent = false;
      });
      CustomSnackBar.showError(
        context: context,
        message: 'Failed to send verification code: ${e.toString()}',
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _verifyCode() async {
    if (_verificationCode.length != 6) {
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
      // Simulate code verification
      await Future.delayed(const Duration(seconds: 2));
      
      if (_verificationCode == '123456') {
        // Code is valid, continue with registration/login
        CustomSnackBar.showSuccess(
          context: context,
          message: 'Verification successful',
        );
        
        // Navigate to main app
        context.go('/dashboard');
      } else {
        throw Exception('Invalid verification code');
      }
    } catch (e) {
      CustomSnackBar.showError(
        context: context,
        message: 'Verification failed: ${e.toString()}',
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _resendCode() async {
    setState(() {
      _isLoading = true;
      _codeController.clear();
      _verificationCode = '';
    });

    try {
      await Future.delayed(const Duration(seconds: 1));
      CustomSnackBar.showSuccess(
        context: context,
        message: 'Verification code resent',
      );
    } catch (e) {
      CustomSnackBar.showError(
        context: context,
        message: 'Failed to resend code: ${e.toString()}',
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
}

class SocialAuthButtons extends ConsumerWidget {
  final VoidCallback? onGoogleSignIn;
  final VoidCallback? onAppleSignIn;
  final VoidCallback? onMicrosoftSignIn;

  const SocialAuthButtons({
    super.key,
    this.onGoogleSignIn,
    this.onAppleSignIn,
    this.onMicrosoftSignIn,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        const SizedBox(height: 24),
        const Text(
          'Or continue with',
          style: TextStyle(
            color: Colors.grey,
            fontSize: 16,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildSocialButton(
                icon: Icons.g_translate,
                label: 'Google',
                color: Colors.red,
                onTap: onGoogleSignIn,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSocialButton(
                icon: Icons.apple,
                label: 'Apple',
                color: Colors.black,
                onTap: onAppleSignIn,
              ),
            ),
          ],
        ),
        if (onMicrosoftSignIn != null) ...[
          const SizedBox(height: 12),
          Expanded(
            child: _buildSocialButton(
              icon: Icons.microsoft,
              label: 'Microsoft',
              color: Colors.blue,
              onTap: onMicrosoftSignIn,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildSocialButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback? onTap,
  }) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        side: BorderSide(color: color),
        foregroundColor: color,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 8),
          Text(label),
        ],
      ),
    );
  }
}

class BiometricAuthButton extends ConsumerWidget {
  final VoidCallback? onAuthenticate;
  final String? errorMessage;

  const BiometricAuthButton({
    super.key,
    this.onAuthenticate,
    this.errorMessage,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Consumer(
      builder: (context, ref, child) {
        final canUseBiometrics = _canUseBiometrics();
        
        if (!canUseBiometrics) {
          return const SizedBox.shrink();
        }

        return Card(
          child: ListTile(
            leading: const Icon(
              Icons.fingerprint,
              color: Colors.blue,
            ),
            title: const Text('Use Biometric Authentication'),
            subtitle: const Text('Quick access with fingerprint or face'),
            trailing: const Icon(Icons.arrow_forward_ios),
            onTap: onAuthenticate,
          ),
        );
      },
    );
  }

  bool _canUseBiometrics() {
    // This is a placeholder implementation
    // In a real app, you would check if biometrics are available and enabled
    return true;
  }
}