import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:edu_flow/core/theme/app_theme.dart';
import 'package:edu_flow/presentation/widgets/common/loading_indicator.dart';
import 'package:edu_flow/presentation/widgets/common/custom_button.dart';
import 'package:edu_flow/presentation/widgets/common/custom_text_field.dart';
import 'package:edu_flow/data/services/auth_service.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _authService = AuthService();
  
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final result = await _authService.login(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Login successful'),
            backgroundColor: AppTheme.successColor,
          ),
        );
        
        // Navigate to dashboard
        Navigator.of(context).pushReplacementNamed('/dashboard');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Login failed: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 60),
                  
                  // Logo
                  Container(
                    alignment: Alignment.center,
                    child: Column(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(
                            Icons.school,
                            size: 40,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'EduFlow',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        Text(
                          'Education Management System',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 48),
                  
                  // Welcome text
                  Text(
                    'Welcome Back!',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  
                  const SizedBox(height: 8),
                  
                  Text(
                    'Sign in to continue to your account',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Email field
                  CustomTextField(
                    controller: _emailController,
                    labelText: 'Email',
                    hintText: 'Enter your email address',
                    prefixIcon: 'email',
                    keyboardType: TextInputType.emailAddress,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter your email';
                      }
                      if (!value.contains('@')) {
                        return 'Please enter a valid email';
                      }
                      return null;
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Password field
                  CustomTextField(
                    controller: _passwordController,
                    labelText: 'Password',
                    hintText: 'Enter your password',
                    prefixIcon: 'lock',
                    obscureText: !_obscurePassword,
                    suffixIcon: 'visibility',
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter your password';
                      }
                      if (value.length < 8) {
                        return 'Password must be at least 8 characters';
                      }
                      return null;
                    },
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Login button
                  _isLoading
                      ? const LoadingIndicator()
                      : CustomButton(
                          text: 'Sign In',
                          onPressed: _handleLogin,
                          icon: 'login',
                        ),
                  
                  const SizedBox(height: 16),
                  
                  // Forgot password
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).pushNamed('/forgot-password');
                    },
                    child: Text(
                      'Forgot Password?',
                      style: TextStyle(
                        color: AppTheme.primaryColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Divider
                  Row(
                    children: [
                      Expanded(child: Divider(color: AppTheme.borderColor)),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Text(
                          'OR',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      Expanded(child: Divider(color: AppTheme.borderColor)),
                    ],
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Register link
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        "Don't have an account? ",
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      TextButton(
                        onPressed: () {
                          Navigator.of(context).pushNamed('/register');
                        },
                        child: Text(
                          'Sign Up',
                          style: TextStyle(
                            color: AppTheme.primaryColor,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}