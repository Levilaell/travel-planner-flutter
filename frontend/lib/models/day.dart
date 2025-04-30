class Day {
  final int dayNumber;
  final String date;
  final String generatedText;

  Day({
    required this.dayNumber,
    required this.date,
    required this.generatedText,
  });

  factory Day.fromJson(Map<String, dynamic> json) {
    return Day(
      dayNumber: json['day_number'],
      date: json['date'],
      generatedText: json['generated_text'] ?? '',
    );
  }
}
