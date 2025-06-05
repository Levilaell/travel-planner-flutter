import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  static const _storage      = FlutterSecureStorage();
  static const _loginUrl     = 'http://192.168.21.28:8000/profile/api/login/';
  static const _registerUrl  = 'http://192.168.21.28:8000/profile/api/register/';

  /// Faz login e armazena access token
  static Future<bool> login(String username, String password) async {
    final resp = await http.post(
      Uri.parse(_loginUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      // Corrija para 'token', que é o que seu backend retorna:
      await _storage.write(key: 'access', value: data['token']);
      return true;
    }
    return false;
  }

  /// Registra novo usuário
  static Future<bool> register(
    String username,
    String email,
    String password,
    String password2,
  ) async {
    final resp = await http.post(
      Uri.parse(_registerUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username':  username,
        'email':     email,
        'password':  password,   // CORRETO!
        'password2': password2,  // CORRETO!
      }),
    );
    // 201 é Created, mas pode ser 200 conforme backend
    return resp.statusCode == 201 || resp.statusCode == 200;
  }

  static Future<String?> getAccessToken() async =>
      await _storage.read(key: 'access');

  static Future<void> logout() async => await _storage.deleteAll();
}
