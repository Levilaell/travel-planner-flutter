import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CreateItineraryScreen extends StatefulWidget {
  final String token;
  const CreateItineraryScreen({Key? key, required this.token})
    : super(key: key);

  @override
  State<CreateItineraryScreen> createState() => _CreateItineraryScreenState();
}

class _CreateItineraryScreenState extends State<CreateItineraryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _destinationController = TextEditingController();
  final _budgetController = TextEditingController();
  final _travelersController = TextEditingController(text: '1');
  final _extrasController = TextEditingController();

  DateTime? _startDate;
  DateTime? _endDate;
  List<String> _selectedInterests = [];
  final _interestsOptions = [
    'Culture',
    'Gastronomy',
    'Adventure',
    'Nature',
    'Shopping',
    'History',
    'Romance',
  ];

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;
    if (_startDate == null || _endDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select start and end dates.')),
      );
      return;
    }

    final url = Uri.parse('http://127.0.0.1:8000/itinerary/api/itineraries/');
    final body = {
      'destination': _destinationController.text,
      'start_date': _startDate!.toIso8601String().split('T').first,
      'end_date': _endDate!.toIso8601String().split('T').first,
      'budget': _budgetController.text,
      'travelers': _travelersController.text,
      'extras': _extrasController.text,
      'interests': _selectedInterests.join(', '),
    };

    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
        body: json.encode(body),
      );

      if (response.statusCode == 201) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) Navigator.of(context).pop(true);
        });
      } else {
        final msg = response.body;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Erro ao criar roteiro: ${response.statusCode}\n$msg',
            ),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Erro ao criar roteiro: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Itinerary')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              TextFormField(
                controller: _destinationController,
                decoration: const InputDecoration(labelText: 'Destination'),
                validator: (v) => v == null || v.isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextButton(
                      onPressed: () async {
                        final date = await showDatePicker(
                          context: context,
                          initialDate: DateTime.now(),
                          firstDate: DateTime(2020),
                          lastDate: DateTime(2100),
                        );
                        if (date != null) setState(() => _startDate = date);
                      },
                      child: Text(
                        _startDate == null
                            ? 'Start Date'
                            : 'Start: ${_startDate!.toLocal().toString().split(' ')[0]}',
                      ),
                    ),
                  ),
                  Expanded(
                    child: TextButton(
                      onPressed: () async {
                        final date = await showDatePicker(
                          context: context,
                          initialDate: _startDate ?? DateTime.now(),
                          firstDate: DateTime(2020),
                          lastDate: DateTime(2100),
                        );
                        if (date != null) setState(() => _endDate = date);
                      },
                      child: Text(
                        _endDate == null
                            ? 'End Date'
                            : 'End: ${_endDate!.toLocal().toString().split(' ')[0]}',
                      ),
                    ),
                  ),
                ],
              ),
              TextFormField(
                controller: _budgetController,
                decoration: const InputDecoration(labelText: 'Budget'),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _travelersController,
                decoration: const InputDecoration(labelText: 'Travelers'),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 20),
              const Text('Interests'),
              Wrap(
                spacing: 8,
                children:
                    _interestsOptions.map((interest) {
                      final selected = _selectedInterests.contains(interest);
                      return FilterChip(
                        label: Text(interest),
                        selected: selected,
                        onSelected: (v) {
                          setState(() {
                            if (v) {
                              _selectedInterests.add(interest);
                            } else {
                              _selectedInterests.remove(interest);
                            }
                          });
                        },
                      );
                    }).toList(),
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: _extrasController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Extras / Observations',
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _submitForm,
                child: const Text('Generate Itinerary'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
