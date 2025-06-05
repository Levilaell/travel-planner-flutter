import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({Key? key}) : super(key: key);
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _userCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _pass2Ctrl = TextEditingController();
  bool _loading = false;
  String? _error;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });

    final ok = await AuthService.register(
      _userCtrl.text.trim(),
      _emailCtrl.text.trim(),
      _passCtrl.text,
      _pass2Ctrl.text,
    );

    setState(() {
      _loading = false;
    });

    if (ok) {
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Registrado com sucesso! Faça login.'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    } else {
      setState(() {
        _error = 'Falha no registro. Verifique seus dados.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              children: [
                SizedBox(height: size.height * 0.05),
                
                // Header
                Row(
                  children: [
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.arrow_back_ios),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white,
                        side: const BorderSide(color: Color(0xFFE2E8F0)),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Text(
                      'Criar Nova Conta',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF1E293B),
                      ),
                    ),
                  ],
                ),
                
                SizedBox(height: size.height * 0.08),
                
                // Register Form
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                  ),
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Informações da Conta',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF1E293B),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Preencha os dados abaixo para criar sua conta',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFF64748B),
                          ),
                        ),
                        const SizedBox(height: 24),
                        
                        // Username Field
                        TextFormField(
                          controller: _userCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Nome de usuário',
                            prefixIcon: Icon(Icons.person_outline),
                            hintText: 'Digite seu nome de usuário',
                          ),
                          validator: (v) => v == null || v.isEmpty ? 'Informe o usuário' : null,
                        ),
                        const SizedBox(height: 20),
                        
                        // Email Field
                        TextFormField(
                          controller: _emailCtrl,
                          keyboardType: TextInputType.emailAddress,
                          decoration: const InputDecoration(
                            labelText: 'E-mail',
                            prefixIcon: Icon(Icons.email_outlined),
                            hintText: 'seu@email.com',
                          ),
                          validator: (v) => v == null || !v.contains('@') ? 'Informe um e-mail válido' : null,
                        ),
                        const SizedBox(height: 20),
                        
                        // Password Field
                        TextFormField(
                          controller: _passCtrl,
                          obscureText: _obscurePassword,
                          decoration: InputDecoration(
                            labelText: 'Senha',
                            prefixIcon: const Icon(Icons.lock_outline),
                            hintText: 'Mínimo 6 caracteres',
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword ? Icons.visibility : Icons.visibility_off,
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscurePassword = !_obscurePassword;
                                });
                              },
                            ),
                          ),
                          validator: (v) => v == null || v.length < 6 ? 'Mínimo 6 caracteres' : null,
                        ),
                        const SizedBox(height: 20),
                        
                        // Confirm Password Field
                        TextFormField(
                          controller: _pass2Ctrl,
                          obscureText: _obscureConfirmPassword,
                          decoration: InputDecoration(
                            labelText: 'Confirmar Senha',
                            prefixIcon: const Icon(Icons.lock_outline),
                            hintText: 'Digite a senha novamente',
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureConfirmPassword ? Icons.visibility : Icons.visibility_off,
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscureConfirmPassword = !_obscureConfirmPassword;
                                });
                              },
                            ),
                          ),
                          validator: (v) => v != _passCtrl.text ? 'As senhas não conferem' : null,
                        ),
                        const SizedBox(height: 24),
                        
                        // Error Message
                        if (_error != null)
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFEE2E2),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: const Color(0xFFFECACA)),
                            ),
                            child: Row(
                              children: [
                                const Icon(
                                  Icons.error_outline,
                                  color: Color(0xFFDC2626),
                                  size: 16,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    _error!,
                                    style: const TextStyle(
                                      color: Color(0xFFDC2626),
                                      fontSize: 14,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        if (_error != null) const SizedBox(height: 16),
                        
                        // Register Button
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: ElevatedButton(
                            onPressed: _loading ? null : _register,
                            child: _loading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Text('Criar Conta'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // Login Link
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Já tem uma conta?',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: const Color(0xFF64748B),
                      ),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Fazer login'),
                    ),
                  ],
                ),
                
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _userCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _pass2Ctrl.dispose();
    super.dispose();
  }
}
