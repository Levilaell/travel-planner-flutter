import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/itinerary.dart';
import '../models/itinerary_detail.dart';

class ItineraryService {
  final String baseUrl = 'http://192.168.15.6:8000/itinerary/api';

  Future<List<Itinerary>> fetchItineraries(String token) async {
    try {
      print('🔄 Carregando itinerários...');
      print('🌐 URL: $baseUrl/itineraries/');
      print('🔑 Token: ${token.substring(0, 10)}...');
      
      final url = Uri.parse('$baseUrl/itineraries/');
      final res = await http.get(
        url,
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 15));
      
      print('📡 Status code: ${res.statusCode}');
      print('📝 Response body: ${res.body}');
      
      if (res.statusCode == 200) {
        final data = json.decode(res.body) as List<dynamic>;
        print('✅ ${data.length} itinerários carregados');
        return data.map((j) => Itinerary.fromJson(j)).toList();
      } else {
        print('❌ Erro HTTP: ${res.statusCode}');
        throw Exception('Erro HTTP ${res.statusCode}: ${res.body}');
      }
    } catch (e) {
      print('❌ Erro ao carregar itinerários: $e');
      throw Exception('Erro ao carregar itinerários: $e');
    }
  }

  Future<ItineraryDetail> fetchItineraryDetail(int id, String token) async {
    try {
      print('🔄 Carregando detalhes do itinerário $id...');
      
      final url = Uri.parse('$baseUrl/itineraries/$id/');
      final res = await http.get(
        url,
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 15));
      
      print('📡 Status code: ${res.statusCode}');
      print('📝 Response body: ${res.body.substring(0, 200)}...');
      
      if (res.statusCode == 200) {
        return ItineraryDetail.fromJson(json.decode(res.body));
      } else {
        print('❌ Erro HTTP: ${res.statusCode}');
        throw Exception('Erro HTTP ${res.statusCode}: ${res.body}');
      }
    } catch (e) {
      print('❌ Erro ao carregar detalhes: $e');
      throw Exception('Erro ao carregar detalhes: $e');
    }
  }
}
