import 'day.dart';

class ItineraryDetail {
  final int id;
  final String destination;
  final String startDate;
  final String endDate;
  final String overview;
  final List<Day> days;

  ItineraryDetail({
    required this.id,
    required this.destination,
    required this.startDate,
    required this.endDate,
    required this.overview,
    required this.days,
  });

  factory ItineraryDetail.fromJson(Map<String, dynamic> json) {
    // Se json['days'] for nulo, usamos lista vazia
    final daysJson = (json['days'] as List<dynamic>?) ?? <dynamic>[];
    final daysList =
        daysJson.map((d) => Day.fromJson(d as Map<String, dynamic>)).toList();

    return ItineraryDetail(
      id: json['id'] as int,
      destination: json['destination'] as String,
      startDate: json['start_date'] as String,
      endDate: json['end_date'] as String,
      overview: json['generated_text'] as String? ?? '',
      days: daysList,
    );
  }
}
