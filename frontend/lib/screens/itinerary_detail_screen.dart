// lib/screens/itinerary_detail_screen.dart

import 'package:flutter/material.dart';
import '../models/itinerary_detail.dart';
import '../services/itinerary_service.dart';

class ItineraryDetailScreen extends StatefulWidget {
  final int itineraryId;
  final String token;
  const ItineraryDetailScreen({
    Key? key,
    required this.itineraryId,
    required this.token,
  }) : super(key: key);

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
    return FutureBuilder<ItineraryDetail>(
      future: _detailFuture,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (snap.hasError) {
          return Scaffold(
            appBar: AppBar(title: const Text('Detalhes')),
            body: Center(child: Text('Erro: ${snap.error}')),
          );
        }
        final detail = snap.data!;
        // número total de abas = 1 (overview) + dias.length
        final tabCount = 1 + detail.days.length;

        return DefaultTabController(
          length: tabCount,
          child: Scaffold(
            appBar: AppBar(
              title: Text(detail.destination),
              bottom: TabBar(
                isScrollable: true,
                indicatorColor: Colors.white,
                tabs: [
                  const Tab(text: 'Overview'),
                  for (final d in detail.days)
                    Tab(text: 'Dia ${d.dayNumber}'),
                ],
              ),
            ),
            body: TabBarView(
              children: [
                // Aba Overview
                SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${detail.startDate} → ${detail.endDate}',
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.black54,
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Overview',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        detail.overview,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                ),

                // Abas de cada dia
                for (final day in detail.days)
                  SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Card(
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8)),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Dia ${day.dayNumber} — ${day.date}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Divider(height: 24),
                            Text(
                              day.generatedText,
                              style: const TextStyle(fontSize: 16),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
