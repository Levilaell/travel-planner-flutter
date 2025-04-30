import 'package:flutter/material.dart';
import '../models/itinerary.dart';
import '../services/itinerary_service.dart';
import 'create_itinerary_screen.dart';
import 'itinerary_detail_screen.dart';

class DashboardScreen extends StatefulWidget {
  final String token;
  const DashboardScreen({Key? key, required this.token}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<List<Itinerary>> _itineraries;

  @override
  void initState() {
    super.initState();
    _loadItineraries();
  }

  void _loadItineraries() {
    _itineraries = ItineraryService().fetchItineraries(widget.token);
  }

  Future<void> _goToCreateScreen() async {
    final result = await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CreateItineraryScreen(token: widget.token),
      ),
    );

    if (result == true) {
      setState(() => _loadItineraries());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Meus Roteiros')),
      body: FutureBuilder<List<Itinerary>>(
        future: _itineraries,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Erro: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('Nenhum itinerário encontrado.'));
          }

          final itineraries = snapshot.data!;
          return ListView.builder(
            itemCount: itineraries.length,
            itemBuilder: (context, index) {
              final it = itineraries[index];
              return Card(
                margin: const EdgeInsets.all(8),
                child: ListTile(
                  title: Text(it.destination),
                  subtitle: Text('${it.startDate} → ${it.endDate}'),
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder:
                            (_) => ItineraryDetailScreen(
                              itineraryId: it.id,
                              token: widget.token,
                            ),
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _goToCreateScreen,
        icon: const Icon(Icons.add),
        label: const Text('Novo Roteiro'),
      ),
    );
  }
}
