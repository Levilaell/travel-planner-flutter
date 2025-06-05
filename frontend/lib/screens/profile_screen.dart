import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class ProfileScreen extends StatefulWidget {
  final String token;
  const ProfileScreen({Key? key, required this.token}) : super(key: key);

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String? _username;
  String? _email;
  Map<String, dynamic>? _profileData;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
  }

  Future<void> _loadUserInfo() async {
    setState(() => _isLoading = true);
    
    try {
      final profileData = await AuthService.getUserProfile();
      
      setState(() {
        if (profileData != null) {
          _profileData = profileData;
          _username = profileData['user']?['username'] ?? 'Usuario';
          _email = profileData['user']?['email'] ?? '';
        } else {
          _username = 'Usuario';
          _email = '';
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _username = 'Usuario';
        _email = '';
        _isLoading = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Erro ao carregar dados do perfil'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _logout() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: const Text('Confirmar Logout'),
        content: const Text('Tem certeza que deseja sair?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await AuthService.logout();
              if (mounted) {
                Navigator.pushReplacementNamed(context, '/');
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
            ),
            child: const Text('Sair'),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileOption({
    required IconData icon,
    required String title,
    required String subtitle,
    VoidCallback? onTap,
    Color? iconColor,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: (iconColor ?? const Color(0xFF6366F1)).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    icon,
                    color: iconColor ?? const Color(0xFF6366F1),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFF1E293B),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: const Color(0xFF64748B),
                        ),
                      ),
                    ],
                  ),
                ),
                if (onTap != null)
                  const Icon(
                    Icons.arrow_forward_ios,
                    size: 16,
                    color: Color(0xFF94A3B8),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Text(
                  'Perfil',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF1E293B),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Gerencie sua conta e preferências',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: const Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 32),

                // Profile Card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: _isLoading
                      ? const Center(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 2,
                            ),
                          ),
                        )
                      : Column(
                          children: [
                            Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(40),
                              ),
                              child: const Icon(
                                Icons.person,
                                color: Colors.white,
                                size: 40,
                              ),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              _username ?? 'Carregando...',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 8),
                            if (_email?.isNotEmpty == true)
                              Text(
                                _email!,
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: Colors.white.withValues(alpha: 0.9),
                                ),
                              ),
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                'Membro Premium',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                ),

                const SizedBox(height: 32),

                // Account Options
                Text(
                  'Conta',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: const Color(0xFF1E293B),
                  ),
                ),
                const SizedBox(height: 16),

                _buildProfileOption(
                  icon: Icons.person_outline,
                  title: 'Informações Pessoais',
                  subtitle: 'Edite seus dados pessoais',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Funcionalidade em desenvolvimento'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),

                _buildProfileOption(
                  icon: Icons.security,
                  title: 'Segurança',
                  subtitle: 'Altere sua senha',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Funcionalidade em desenvolvimento'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),

                _buildProfileOption(
                  icon: Icons.notifications_none,
                  title: 'Notificações',
                  subtitle: 'Configure suas preferências',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Funcionalidade em desenvolvimento'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),

                const SizedBox(height: 24),

                // App Options
                Text(
                  'App',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: const Color(0xFF1E293B),
                  ),
                ),
                const SizedBox(height: 16),

                _buildProfileOption(
                  icon: Icons.help_outline,
                  title: 'Ajuda & Suporte',
                  subtitle: 'FAQ e contato',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Funcionalidade em desenvolvimento'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),

                _buildProfileOption(
                  icon: Icons.star_outline,
                  title: 'Avalie o App',
                  subtitle: 'Sua opinião é importante',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Obrigado! Redirecionando para a loja...'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),

                _buildProfileOption(
                  icon: Icons.info_outline,
                  title: 'Sobre',
                  subtitle: 'Versão 1.0.0',
                  onTap: () {
                    showAboutDialog(
                      context: context,
                      applicationName: 'TripPlanner AI',
                      applicationVersion: '1.0.0',
                      applicationIcon: Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: const Icon(
                          Icons.flight_takeoff,
                          color: Colors.white,
                          size: 32,
                        ),
                      ),
                      children: [
                        const Text(
                          'Planeje viagens incríveis com o poder da inteligência artificial.',
                        ),
                      ],
                    );
                  },
                ),

                const SizedBox(height: 24),

                // Logout Button
                Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEE2E2),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(16),
                      onTap: _logout,
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Row(
                          children: [
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                color: const Color(0xFFEF4444).withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Icon(
                                Icons.logout,
                                color: Color(0xFFEF4444),
                                size: 24,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Sair da Conta',
                                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.w600,
                                      color: const Color(0xFFEF4444),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Desconectar da sua conta',
                                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      color: const Color(0xFFEF4444),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Icon(
                              Icons.arrow_forward_ios,
                              size: 16,
                              color: Color(0xFFEF4444),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}