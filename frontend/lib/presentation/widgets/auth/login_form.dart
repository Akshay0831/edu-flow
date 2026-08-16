import 'package:flutter/material.dart';

class LoginForm extends StatefulWidget {
  final VoidCallback? onRegisterTap;
  final VoidCallback? onForgotPasswordTap;
  final Function(String email, String password, {bool rememberMe})? onLogin;
  final bool showSocialLogin;

  const LoginForm({
    super.key,
    this.onRegisterTap,
    this.onForgotPasswordTap,
    this.onLogin,
    this.showSocialLogin = false,
  });

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _rememberMe = false;
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      if (widget.onLogin != null) {
        widget.onLogin!(
          _emailController.text.trim(),
          _passwordController.text,
          rememberMe: _rememberMe,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Login',
            style: Theme.of(context).textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(
              labelText: 'Email',
              hintText: 'Enter your email',
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Email is required';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'Password',
              hintText: 'Enter your password',
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Password is required';
              }
              return null;
            },
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Checkbox(
                    value: _rememberMe,
                    onChanged: (val) => setState(() => _rememberMe = val ?? false),
                  ),
                  const Text('Remember me'),
                ],
              ),
              if (widget.onForgotPasswordTap != null)
                TextButton(
                  onPressed: widget.onForgotPasswordTap,
                  child: const Text('Forgot Password?'),
                ),
            ],
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _isLoading ? null : _submit,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Sign In'),
          ),
          if (widget.showSocialLogin) ...[
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () {},
              child: const Text('Sign In with Google'),
            ),
          ],
          if (widget.onRegisterTap != null) ...[
            const SizedBox(height: 16),
            TextButton(
              onPressed: widget.onRegisterTap,
              child: const Text("Don't have an account? Register"),
            ),
          ],
        ],
      ),
    );
  }
}
