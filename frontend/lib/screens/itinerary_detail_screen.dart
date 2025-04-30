import 'package:flutter/material.dart';
import '../models/itinerary_detail.dart';
import '../services/itinerary_service.dart';

class ItineraryDetailScreen extends StatefulWidget {
  final int itineraryId;
  final String token;
  const ItineraryDetailScreen({
    super.key,
    required this.itineraryId,
    required this.token,
  });

  @override
  State<ItineraryDetailScreen> createState() => _ItineraryDetailScreenState();
}

class _ItineraryDetailScreenState extends State<ItineraryDetailScreen> {
  late Future<ItineraryDetail> _detailFuture;

  @override
  void initState() {
    super.initState();
    _detailFuture = ItineraryService().fetchItineraryDetail(
      widget.itineraryId,
      widget.token,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalhes do Itinerário')),
      body: FutureBuilder<ItineraryDetail>(
        future: _detailFuture,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Erro: ${snap.error}'));
          }
          final detail = snap.data!;
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  detail.destination,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text('${detail.startDate} → ${detail.endDate}'),
                const SizedBox(height: 16),
                const Text(
                  'Overview',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
                Text(detail.overview),
                const SizedBox(height: 16),
                const Text(
                  'Dias',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.builder(
                    itemCount: detail.days.length,
                    itemBuilder: (ctx, i) {
                      final day = detail.days[i];
                      return ExpansionTile(
                        title: Text('Dia ${day.dayNumber} — ${day.date}'),
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(8),
                            child: Text(day.generatedText),
                          ),
                        ],
                      );
                    },
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
