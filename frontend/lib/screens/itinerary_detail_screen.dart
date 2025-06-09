// lib/screens/itinerary_detail_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
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

  Future<void> _launchUrl(String url) async {
    final Uri uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      throw Exception('Could not launch $url');
    }
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
            appBar: AppBar(title: const Text('Details')),
            body: Center(child: Text('Error: ${snap.error}')),
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
                    Tab(text: 'Day ${d.dayNumber}'),
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
                      MarkdownBody(
                        data: detail.overview,
                        styleSheet: MarkdownStyleSheet(
                          p: const TextStyle(fontSize: 16),
                          h1: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                          h2: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                          h3: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        onTapLink: (text, href, title) {
                          if (href != null) {
                            _launchUrl(href);
                          }
                        },
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
                              'Day ${day.dayNumber} — ${day.date}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Divider(height: 24),
                            MarkdownBody(
                              data: day.generatedText,
                              styleSheet: MarkdownStyleSheet(
                                p: const TextStyle(fontSize: 16),
                                h1: const TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                ),
                                h2: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                                h3: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                                blockquote: const TextStyle(
                                  fontSize: 14,
                                  fontStyle: FontStyle.italic,
                                  color: Colors.grey,
                                ),
                              ),
                              onTapLink: (text, href, title) {
                                if (href != null) {
                                  _launchUrl(href);
                                }
                              },
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
