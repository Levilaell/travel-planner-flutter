class Itinerary {
  final int id;
  final String destination;
  final String startDate;
  final String endDate;
  final String generatedText;

  Itinerary({
    required this.id,
    required this.destination,
    required this.startDate,
    required this.endDate,
    required this.generatedText,
  });

  factory Itinerary.fromJson(Map<String, dynamic> json) {
    return Itinerary(
      id: json['id'],
      destination: json['destination'],
      startDate: json['start_date'],
      endDate: json['end_date'],
      generatedText: json['generated_text'] ?? '',
    );
  }
}
