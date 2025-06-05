import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../models/user.dart';

class ProfileEditScreen extends StatefulWidget {
  final User user;

  const ProfileEditScreen({Key? key, required this.user}) : super(key: key);

  @override
  _ProfileEditScreenState createState() => _ProfileEditScreenState();
}

class _ProfileEditScreenState extends State<ProfileEditScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;

  late TextEditingController _firstNameController;
  late TextEditingController _lastNameController;
  late TextEditingController _emailController;
  late TextEditingController _phoneController;
  late TextEditingController _budgetController;
  late TextEditingController _interestsController;
  
  List<String> _favoriteDestinations = [];
  final TextEditingController _destinationController = TextEditingController();
  String _preferredLanguage = 'en';
  bool _accessibilityNeeds = false;

  @override
  void initState() {
    super.initState();
    _firstNameController = TextEditingController(text: widget.user.firstName);
    _lastNameController = TextEditingController(text: widget.user.lastName);
    _emailController = TextEditingController(text: widget.user.email);
    _phoneController = TextEditingController(text: widget.user.phoneNumber ?? '');
    _budgetController = TextEditingController(text: widget.user.budget?.toString() ?? '');
    _interestsController = TextEditingController(text: widget.user.interests ?? '');
    _favoriteDestinations = List<String>.from(widget.user.favoriteDestinations ?? []);
    _preferredLanguage = widget.user.preferredLanguage ?? 'en';
    _accessibilityNeeds = widget.user.accessibilityNeeds ?? false;
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _budgetController.dispose();
    _interestsController.dispose();
    _destinationController.dispose();
    super.dispose();
  }

  void _addDestination(String destination) {
    if (destination.isNotEmpty && !_favoriteDestinations.contains(destination)) {
      setState(() {
        _favoriteDestinations.add(destination);
        _destinationController.clear();
      });
    }
  }

  void _removeDestination(String destination) {
    setState(() {
      _favoriteDestinations.remove(destination);
    });
  }

  Future<void> _saveProfile() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);

      try {
        final profileData = {
          'first_name': _firstNameController.text,
          'last_name': _lastNameController.text,
          'email': _emailController.text,
          'phone_number': _phoneController.text,
          'budget': _budgetController.text.isNotEmpty ? double.parse(_budgetController.text) : null,
          'interests': _interestsController.text,
          'favorite_destinations': _favoriteDestinations,
          'preferred_language': _preferredLanguage,
          'acessibility_needs': _accessibilityNeeds,
        };

        await AuthService.updateUserProfile(profileData);
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Profile updated successfully!')),
          );
          Navigator.pop(context, true);
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error updating profile: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('Edit Profile'),
        backgroundColor: Theme.of(context).primaryColor,
        foregroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Personal Information Section
                    Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Personal Information',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 16),
                            Row(
                              children: [
                                Expanded(
                                  child: TextFormField(
                                    controller: _firstNameController,
                                    decoration: const InputDecoration(
                                      labelText: 'First Name',
                                      border: OutlineInputBorder(),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: TextFormField(
                                    controller: _lastNameController,
                                    decoration: const InputDecoration(
                                      labelText: 'Last Name',
                                      border: OutlineInputBorder(),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _emailController,
                              decoration: const InputDecoration(
                                labelText: 'Email',
                                border: OutlineInputBorder(),
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) {
                                  return 'Please enter an email';
                                }
                                if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
                                  return 'Please enter a valid email';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _phoneController,
                              decoration: const InputDecoration(
                                labelText: 'Phone Number',
                                border: OutlineInputBorder(),
                              ),
                              keyboardType: TextInputType.phone,
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Travel Preferences Section
                    Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Travel Preferences',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _budgetController,
                              decoration: const InputDecoration(
                                labelText: 'Average Travel Budget',
                                border: OutlineInputBorder(),
                                prefixText: '\$ ',
                              ),
                              keyboardType: TextInputType.number,
                              validator: (value) {
                                if (value != null && value.isNotEmpty) {
                                  if (double.tryParse(value) == null) {
                                    return 'Please enter a valid number';
                                  }
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            TextFormField(
                              controller: _interestsController,
                              decoration: const InputDecoration(
                                labelText: 'Interests',
                                border: OutlineInputBorder(),
                                hintText: 'e.g., History, Food, Adventure, Culture',
                              ),
                              maxLines: 2,
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Favorite Destinations',
                              style: TextStyle(fontWeight: FontWeight.w500),
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Expanded(
                                  child: TextFormField(
                                    controller: _destinationController,
                                    decoration: const InputDecoration(
                                      hintText: "Add destination",
                                      border: OutlineInputBorder(),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                ElevatedButton(
                                  onPressed: () {
                                    if (_destinationController.text.isNotEmpty) {
                                      _addDestination(_destinationController.text);
                                    }
                                  },
                                  child: const Text('Add'),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              children: _favoriteDestinations.map((destination) {
                                return Chip(
                                  label: Text(destination),
                                  deleteIcon: const Icon(Icons.close, size: 18),
                                  onDeleted: () => _removeDestination(destination),
                                );
                              }).toList(),
                            ),
                            const SizedBox(height: 16),
                            DropdownButtonFormField<String>(
                              value: _preferredLanguage,
                              decoration: const InputDecoration(
                                labelText: 'Preferred Language',
                                border: OutlineInputBorder(),
                              ),
                              items: const [
                                DropdownMenuItem(value: 'en', child: Text('English')),
                                DropdownMenuItem(value: 'pt', child: Text('Portuguese')),
                              ],
                              onChanged: (value) {
                                setState(() {
                                  _preferredLanguage = value!;
                                });
                              },
                            ),
                            const SizedBox(height: 16),
                            SwitchListTile(
                              title: const Text('Accessibility Needs'),
                              subtitle: const Text('I require accessibility accommodations'),
                              value: _accessibilityNeeds,
                              onChanged: (value) {
                                setState(() {
                                  _accessibilityNeeds = value;
                                });
                              },
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Save Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _saveProfile,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Theme.of(context).primaryColor,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: const Text(
                          'Save Changes',
                          style: TextStyle(fontSize: 16),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}