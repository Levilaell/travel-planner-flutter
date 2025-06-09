import 'dart:convert';
import 'package:http/http.dart' as http;
import 'storage_service.dart';

class AuthService {
  static const _baseUrl      = 'http://192.168.21.250:8000';
  static const _loginUrl     = '$_baseUrl/profile/api/login/';
  static const _registerUrl  = '$_baseUrl/profile/api/register/';
  static const _profileUrl   = '$_baseUrl/profile/api/profile/';

  /// Faz login e armazena access token
  static Future<bool> login(String username, String password) async {
    try {
      print('🔄 Tentando fazer login: $username');
      print('🌐 URL: $_loginUrl');
      
      final resp = await http.post(
        Uri.parse(_loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}),
      ).timeout(const Duration(seconds: 15));

      print('📡 Status code: ${resp.statusCode}');
      print('📝 Response body: ${resp.body}');

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        print('✅ Login successful, token received: ${data['token']?.substring(0, 10)}...');
        await StorageService.write(key: 'access', value: data['token']);
        print('✅ Token stored in secure storage');
        return true;
      }
      print('❌ Login failed with status: ${resp.statusCode}');
      return false;
    } catch (e) {
      print('❌ Erro no login: $e');
      return false;
    }
  }

  /// Registra novo usuário
  static Future<bool> register(
    String username,
    String email,
    String password,
    String password2,
  ) async {
    try {
      print('🔄 Tentando registrar usuário: $username');
      print('🌐 URL: $_registerUrl');
      
      final resp = await http.post(
        Uri.parse(_registerUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username':  username,
          'email':     email,
          'password':  password,
          'password2': password2,
        }),
      ).timeout(const Duration(seconds: 15));
      
      print('📡 Status code: ${resp.statusCode}');
      print('📝 Response body: ${resp.body}');
      
      return resp.statusCode == 201 || resp.statusCode == 200;
    } catch (e) {
      print('❌ Erro no registro: $e');
      return false;
    }
  }

  static Future<String?> getAccessToken() async =>
      await StorageService.read(key: 'access');

  static Future<void> logout() async => await StorageService.deleteAll();

  /// Busca dados do perfil do usuário
  static Future<Map<String, dynamic>?> getUserProfile() async {
    final token = await getAccessToken();
    if (token == null) return null;

    try {
      final resp = await http.get(
        Uri.parse(_profileUrl),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
      );

      if (resp.statusCode == 200) {
        return jsonDecode(resp.body);
      }
    } catch (e) {
      print('Erro ao carregar perfil: $e');
    }
    return null;
  }

  /// Atualiza dados do perfil do usuário
  static Future<bool> updateUserProfile(Map<String, dynamic> profileData) async {
    final token = await getAccessToken();
    if (token == null) return false;

    try {
      final resp = await http.put(
        Uri.parse(_profileUrl),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $token',
        },
        body: jsonEncode(profileData),
      );

      return resp.statusCode == 200;
    } catch (e) {
      print('Erro ao atualizar perfil: $e');
      return false;
    }
  }
}
