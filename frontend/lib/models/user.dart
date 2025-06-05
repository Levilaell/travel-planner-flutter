class User {
  final int id;
  final String username;
  final String email;
  final String? firstName;
  final String? lastName;
  final DateTime dateJoined;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.firstName,
    this.lastName,
    required this.dateJoined,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      dateJoined: DateTime.parse(json['date_joined']),
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
    };
  }
}

class TravelerProfile {
  final User user;
  final double? budget;
  final String? interests;
  final bool accessibilityNeeds;

  TravelerProfile({
    required this.user,
    this.budget,
    this.interests,
    this.accessibilityNeeds = false,
  });

  factory TravelerProfile.fromJson(Map<String, dynamic> json) {
    return TravelerProfile(
      user: User.fromJson(json['user']),
      budget: json['budget']?.toDouble(),
      interests: json['interests'],
      accessibilityNeeds: json['acessibility_needs'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'budget': budget,
      'interests': interests,
      'acessibility_needs': accessibilityNeeds,
    };
  }
}