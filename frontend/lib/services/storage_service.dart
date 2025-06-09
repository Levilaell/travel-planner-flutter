import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const _storage = FlutterSecureStorage();
  
  static Future<void> write({required String key, required String value}) async {
    if (kIsWeb) {
      // Para web, usar SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
    } else {
      // Para mobile, usar secure storage
      await _storage.write(key: key, value: value);
    }
  }
  
  static Future<String?> read({required String key}) async {
    if (kIsWeb) {
      // Para web, ler do SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(key);
    } else {
      // Para mobile, usar secure storage
      return await _storage.read(key: key);
    }
  }
  
  static Future<void> delete({required String key}) async {
    if (kIsWeb) {
      // Para web, remover do SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(key);
    } else {
      // Para mobile, usar secure storage
      await _storage.delete(key: key);
    }
  }
  
  static Future<void> deleteAll() async {
    if (kIsWeb) {
      // Para web, limpar SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
    } else {
      // Para mobile, usar secure storage
      await _storage.deleteAll();
    }
  }
}