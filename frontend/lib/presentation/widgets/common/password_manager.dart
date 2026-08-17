import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'custom_app_bar.dart';
import 'custom_snackbar.dart';
import 'custom_text_field.dart';

class PasswordStrengthIndicator extends StatefulWidget {
  final String password;
  final String? label;
  final double? width;
  final bool showDetailedScore;

  const PasswordStrengthIndicator({
    super.key,
    required this.password,
    this.label,
    this.width,
    this.showDetailedScore = true,
  });

  @override
  State<PasswordStrengthIndicator> createState() => _PasswordStrengthIndicatorState();
}

class _PasswordStrengthIndicatorState extends State<PasswordStrengthIndicator> {
  late double _strength;
  late Color _strengthColor;
  late String _strengthText;

  @override
  void initState() {
    super.initState();
    _updateStrength();
  }

  @override
  void didUpdateWidget(PasswordStrengthIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.password != widget.password) {
      _updateStrength();
    }
  }

  void _updateStrength() {
    setState(() {
      _strength = _calculatePasswordStrength(widget.password);
      _strengthColor = _getStrengthColor(_strength);
      _strengthText = _getStrengthText(_strength);
    });
  }

  double _calculatePasswordStrength(String password) {
    if (password.isEmpty) return 0.0;
    
    double strength = 0.0;
    
    // Length check (0-25 points)
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 25;
    
    // Character variety (0-50 points)
    if (password.contains(RegExp(r'[a-z]'))) strength += 10;
    if (password.contains(RegExp(r'[A-Z]'))) strength += 10;
    if (password.contains(RegExp(r'[0-9]'))) strength += 10;
    if (password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) strength += 10;
    if (password.contains(RegExp(r'[^\w\s]'))) strength += 10;
    
    // Common patterns (0 points penalty)
    if (password.length < 8) strength -= 10;
    if (password.toLowerCase() == 'password') strength = 0;
    if (password.toLowerCase() == widget.password.toLowerCase()) strength = 0;
    
    return strength.clamp(0.0, 100.0);
  }

  Color _getStrengthColor(double strength) {
    if (strength < 30) return Colors.red;
    if (strength < 70) return Colors.orange;
    if (strength < 90) return Colors.yellow;
    return Colors.green;
  }

  String _getStrengthText(double strength) {
    if (strength < 30) return 'Weak';
    if (strength < 70) return 'Fair';
    if (strength < 90) return 'Good';
    return 'Strong';
  }

  @override
  Widget build(BuildContext context) {
    final effectiveWidth = widget.width ?? double.infinity;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              widget.label!,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        Container(
          width: effectiveWidth,
          height: 8,
          decoration: BoxDecoration(
            color: Colors.grey[200],
            borderRadius: BorderRadius.circular(4),
          ),
          child: FractionallySizedBox(
            alignment: Alignment.centerLeft,
            widthFactor: _strength / 100,
            child: Container(
              decoration: BoxDecoration(
                color: _strengthColor,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          ),
        ),
        if (widget.showDetailedScore) ...[
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _strengthText,
                style: TextStyle(
                  color: _strengthColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                '${_strength.toInt()}%',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          if (widget.password.isNotEmpty)
            _buildPasswordRequirements(),
        ],
      ],
    );
  }

  Widget _buildPasswordRequirements() {
    final List<Widget> requirements = [];
    
    void addRequirement({
      required bool isMet,
      required String text,
      required IconData icon,
    }) {
      requirements.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            children: [
              Icon(
                icon,
                color: isMet ? Colors.green : Colors.grey,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                text,
                style: TextStyle(
                  color: isMet ? Colors.green : Colors.grey,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      );
    }

    addRequirement(
      isMet: widget.password.length >= 8,
      text: 'At least 8 characters',
      icon: Icons.check_circle,
    );
    addRequirement(
      isMet: widget.password.contains(RegExp(r'[A-Z]')),
      text: 'Contains uppercase letter',
      icon: Icons.check_circle,
    );
    addRequirement(
      isMet: widget.password.contains(RegExp(r'[a-z]')),
      text: 'Contains lowercase letter',
      icon: Icons.check_circle,
    );
    addRequirement(
      isMet: widget.password.contains(RegExp(r'[0-9]')),
      text: 'Contains number',
      icon: Icons.check_circle,
    );
    addRequirement(
      isMet: widget.password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]')),
      text: 'Contains special character',
      icon: Icons.check_circle,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: requirements,
    );
  }
}

class PasswordGenerator extends StatefulWidget {
  final String? initialPassword;
  final Function(String)? onPasswordGenerated;
  final bool includeUppercase;
  final bool includeLowercase;
  final bool includeNumbers;
  final bool includeSymbols;
  final int length;

  const PasswordGenerator({
    super.key,
    this.initialPassword,
    this.onPasswordGenerated,
    this.includeUppercase = true,
    this.includeLowercase = true,
    this.includeNumbers = true,
    this.includeSymbols = true,
    this.length = 12,
  });

  @override
  State<PasswordGenerator> createState() => _PasswordGeneratorState();
}

class _PasswordGeneratorState extends State<PasswordGenerator> {
  late TextEditingController _passwordController;
  bool _isCopied = false;

  @override
  void initState() {
    super.initState();
    _passwordController = TextEditingController(text: widget.initialPassword ?? _generatePassword());
  }

  String _generatePassword() {
    final uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    final lowercase = 'abcdefghijklmnopqrstuvwxyz';
    final numbers = '0123456789';
    final symbols = '!@#\$%^&*()_+-=[]{}|;:,.<>?';

    String allowedChars = '';
    if (widget.includeUppercase) allowedChars += uppercase;
    if (widget.includeLowercase) allowedChars += lowercase;
    if (widget.includeNumbers) allowedChars += numbers;
    if (widget.includeSymbols) allowedChars += symbols;

    if (allowedChars.isEmpty) {
      return '';
    }

    String password = '';
    for (int i = 0; i < widget.length; i++) {
      password += allowedChars[
          (DateTime.now().millisecondsSinceEpoch + i) % allowedChars.length];
    }

    return password;
  }

  void _copyToClipboard() async {
    await Clipboard.setData(ClipboardData(text: _passwordController.text));
    setState(() {
      _isCopied = true;
    });
    
    CustomSnackBar.showSuccess(
      context: context,
      message: 'Password copied to clipboard',
    );

    if (widget.onPasswordGenerated != null) {
      widget.onPasswordGenerated!(_passwordController.text);
    }

    Future.delayed(const Duration(seconds: 2), () {
      setState(() {
        _isCopied = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: CustomTextField(
                labelText: 'Generated Password',
                hintText: 'Click generate to create password',
                controller: _passwordController,
                obscureText: true,
                enabled: false,
                suffixIcon: IconButton(
                  icon: Icon(_isCopied ? Icons.check : Icons.copy),
                  onPressed: _copyToClipboard,
                  tooltip: 'Copy password',
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () {
                final newPassword = _generatePassword();
                _passwordController.text = newPassword;
                setState(() {
                  _isCopied = false;
                });
                
                if (widget.onPasswordGenerated != null) {
                  widget.onPasswordGenerated!(newPassword);
                }
              },
              tooltip: 'Generate new password',
            ),
          ],
        ),
        const SizedBox(height: 16),
        PasswordStrengthIndicator(
          password: _passwordController.text,
          label: 'Password Strength',
        ),
      ],
    );
  }
}

class PasswordPolicyScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? policy;

  const PasswordPolicyScreen({
    super.key,
    this.policy,
  });

  @override
  ConsumerState<PasswordPolicyScreen> createState() => _PasswordPolicyScreenState();
}

class _PasswordPolicyScreenState extends ConsumerState<PasswordPolicyScreen> {

  @override
  Widget build(BuildContext context) {
    final defaultPolicy = {
      'minLength': 8,
      'maxLength': 128,
      'requireUppercase': true,
      'requireLowercase': true,
      'requireNumbers': true,
      'requireSymbols': true,
      'preventReusedPasswords': true,
      'preventCommonPasswords': true,
      'changeFrequency': 90, // days
    };

    final policy = widget.policy ?? defaultPolicy;

    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Password Policy',
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.security, color: Colors.blue),
                      const SizedBox(width: 8),
                      Text(
                        'Password Requirements',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  ExpansionTile(
                    title: const Text('View Detailed Requirements'),
                    children: [
                      _buildPolicyDetails(policy),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.history, color: Colors.orange),
                      const SizedBox(width: 8),
                      Text(
                        'Password History',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Your last password was changed 45 days ago.',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PasswordChangeScreen(),
                      ),
                    ),
                    child: const Text('Change Password Now'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPolicyDetails(Map<String, dynamic> policy) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildPolicyItem(
            'Minimum Length',
            '${policy['minLength']} characters',
            policy['minLength'] != null,
          ),
          _buildPolicyItem(
            'Maximum Length',
            '${policy['maxLength']} characters',
            policy['maxLength'] != null,
          ),
          _buildPolicyItem(
            'Require Uppercase',
            policy['requireUppercase'] ? 'Required' : 'Not Required',
            policy['requireUppercase'] != null,
          ),
          _buildPolicyItem(
            'Require Lowercase',
            policy['requireLowercase'] ? 'Required' : 'Not Required',
            policy['requireLowercase'] != null,
          ),
          _buildPolicyItem(
            'Require Numbers',
            policy['requireNumbers'] ? 'Required' : 'Not Required',
            policy['requireNumbers'] != null,
          ),
          _buildPolicyItem(
            'Require Symbols',
            policy['requireSymbols'] ? 'Required' : 'Not Required',
            policy['requireSymbols'] != null,
          ),
          _buildPolicyItem(
            'Prevent Reused Passwords',
            policy['preventReusedPasswords'] ? 'Enabled' : 'Disabled',
            policy['preventReusedPasswords'] != null,
          ),
          _buildPolicyItem(
            'Password Change Frequency',
            '${policy['changeFrequency']} days',
            policy['changeFrequency'] != null,
          ),
        ],
      ),
    );
  }

  Widget _buildPolicyItem(String label, String value, bool isRequired) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label: ',
            style: const TextStyle(
              fontWeight: FontWeight.w500,
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: isRequired ? Colors.black : Colors.grey,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class PasswordChangeScreen extends ConsumerStatefulWidget {
  const PasswordChangeScreen({super.key});

  @override
  ConsumerState<PasswordChangeScreen> createState() => _PasswordChangeScreenState();
}

class _PasswordChangeScreenState extends ConsumerState<PasswordChangeScreen> {
  final TextEditingController _currentPasswordController = TextEditingController();
  final TextEditingController _newPasswordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  bool _showCurrentPassword = false;
  bool _showNewPassword = false;
  bool _showConfirmPassword = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Change Password',
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CustomTextField(
              labelText: 'Current Password',
              hintText: 'Enter your current password',
              controller: _currentPasswordController,
              obscureText: !_showCurrentPassword,
              suffixIcon: IconButton(
                icon: Icon(_showCurrentPassword ? Icons.visibility : Icons.visibility_off),
                onPressed: () {
                  setState(() {
                    _showCurrentPassword = !_showCurrentPassword;
                  });
                },
              ),
            ),
            const SizedBox(height: 16),
            CustomTextField(
              labelText: 'New Password',
              hintText: 'Enter your new password',
              controller: _newPasswordController,
              obscureText: !_showNewPassword,
              suffixIcon: IconButton(
                icon: Icon(_showNewPassword ? Icons.visibility : Icons.visibility_off),
                onPressed: () {
                  setState(() {
                    _showNewPassword = !_showNewPassword;
                  });
                },
              ),
            ),
            const SizedBox(height: 8),
            PasswordStrengthIndicator(
              password: _newPasswordController.text,
              label: 'New Password Strength',
            ),
            const SizedBox(height: 16),
            CustomTextField(
              labelText: 'Confirm New Password',
              hintText: 'Confirm your new password',
              controller: _confirmPasswordController,
              obscureText: !_showConfirmPassword,
              suffixIcon: IconButton(
                icon: Icon(_showConfirmPassword ? Icons.visibility : Icons.visibility_off),
                onPressed: () {
                  setState(() {
                    _showConfirmPassword = !_showConfirmPassword;
                  });
                },
              ),
              validator: (value) {
                if (value != _newPasswordController.text) {
                  return 'Passwords do not match';
                }
                return null;
              },
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _changePassword,
              child: const Text('Change Password'),
            ),
          ],
        ),
      ),
    );
  }

  void _changePassword() async {
    if (_newPasswordController.text != _confirmPasswordController.text) {
      CustomSnackBar.showError(
        context: context,
        message: 'Passwords do not match',
      );
      return;
    }

    // Simulate password change
    await Future.delayed(const Duration(seconds: 2));
    
    CustomSnackBar.showSuccess(
      context: context,
      message: 'Password changed successfully',
    );
    
    Navigator.pop(context);
  }
}