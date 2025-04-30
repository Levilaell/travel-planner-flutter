import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/itinerary.dart';
import '../models/itinerary_detail.dart';

class ItineraryService {
  final String baseUrl = 'http://127.0.0.1:8000/itinerary/api';

  Future<List<Itinerary>> fetchItineraries(String token) async {
    final url = Uri.parse('$baseUrl/itineraries/');
    final res = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    if (res.statusCode == 200) {
      final data = json.decode(res.body) as List<dynamic>;
      return data.map((j) => Itinerary.fromJson(j)).toList();
    } else {
      throw Exception('Não foi possível carregar itinerários');
    }
  }

  Future<ItineraryDetail> fetchItineraryDetail(int id, String token) async {
    final url = Uri.parse('$baseUrl/itineraries/$id/');
    final res = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    if (res.statusCode == 200) {
      return ItineraryDetail.fromJson(json.decode(res.body));
    } else {
      throw Exception('Não foi possível carregar detalhes');
    }
  }
}
