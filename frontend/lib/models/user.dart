class User {
  final int id;
  final String username;
  final String email;
  final String? firstName;
  final String? lastName;
  final DateTime dateJoined;
  final double? budget;
  final String? interests;
  final bool? accessibilityNeeds;
  final List<String>? favoriteDestinations;
  final String? phoneNumber;
  final String? preferredLanguage;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.firstName,
    this.lastName,
    required this.dateJoined,
    this.budget,
    this.interests,
    this.accessibilityNeeds,
    this.favoriteDestinations,
    this.phoneNumber,
    this.preferredLanguage,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      dateJoined: DateTime.parse(json['date_joined']),
      budget: json['budget']?.toDouble(),
      interests: json['interests'],
      accessibilityNeeds: json['acessibility_needs'] ?? false,
      favoriteDestinations: json['favorite_destinations'] != null
          ? List<String>.from(json['favorite_destinations'])
          : null,
      phoneNumber: json['phone_number'],
      preferredLanguage: json['preferred_language'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'date_joined': dateJoined.toIso8601String(),
      'budget': budget,
      'interests': interests,
      'acessibility_needs': accessibilityNeeds,
      'favorite_destinations': favoriteDestinations,
      'phone_number': phoneNumber,
      'preferred_language': preferredLanguage,
    };
  }
}

class TravelerProfile {
  final User user;
  final double? budget;
  final String? interests;
  final bool accessibilityNeeds;
  final List<String>? favoriteDestinations;
  final String? phoneNumber;
  final String? preferredLanguage;

  TravelerProfile({
    required this.user,
    this.budget,
    this.interests,
    this.accessibilityNeeds = false,
    this.favoriteDestinations,
    this.phoneNumber,
    this.preferredLanguage,
  });

  factory TravelerProfile.fromJson(Map<String, dynamic> json) {
    return TravelerProfile(
      user: User.fromJson(json['user']),
      budget: json['budget']?.toDouble(),
      interests: json['interests'],
      accessibilityNeeds: json['acessibility_needs'] ?? false,
      favoriteDestinations: json['favorite_destinations'] != null
          ? List<String>.from(json['favorite_destinations'])
          : null,
      phoneNumber: json['phone_number'],
      preferredLanguage: json['preferred_language'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'budget': budget,
      'interests': interests,
      'acessibility_needs': accessibilityNeeds,
      'favorite_destinations': favoriteDestinations,
      'phone_number': phoneNumber,
      'preferred_language': preferredLanguage,
    };
  }
}