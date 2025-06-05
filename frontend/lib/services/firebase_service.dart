import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import '../models/itinerary.dart';
import '../models/user.dart' as app_user;

class FirebaseService {
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  static final FirebaseAuth _auth = FirebaseAuth.instance;
  
  // Initialize Firebase
  static Future<void> initialize() async {
    await Firebase.initializeApp();
  }
  
  // User Authentication
  static Future<User?> getCurrentUser() async {
    return _auth.currentUser;
  }
  
  static Future<UserCredential?> signInWithEmailAndPassword(
      String email, String password) async {
    try {
      return await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
    } catch (e) {
      print('Error signing in: $e');
      return null;
    }
  }
  
  static Future<UserCredential?> createUserWithEmailAndPassword(
      String email, String password) async {
    try {
      return await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
    } catch (e) {
      print('Error creating user: $e');
      return null;
    }
  }
  
  static Future<void> signOut() async {
    await _auth.signOut();
  }
  
  // User Profile Management
  static Future<void> saveUserProfile(app_user.User userProfile) async {
    try {
      await _firestore
          .collection('users')
          .doc(userProfile.id.toString())
          .set(userProfile.toJson());
    } catch (e) {
      print('Error saving user profile: $e');
      throw Exception('Failed to save user profile');
    }
  }
  
  static Future<app_user.User?> getUserProfile(int userId) async {
    try {
      DocumentSnapshot doc = await _firestore
          .collection('users')
          .doc(userId.toString())
          .get();
      
      if (doc.exists) {
        return app_user.User.fromJson(doc.data() as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      print('Error getting user profile: $e');
      return null;
    }
  }
  
  // Itinerary Management
  static Future<void> saveItinerary(Itinerary itinerary) async {
    try {
      await _firestore
          .collection('itineraries')
          .doc(itinerary.id.toString())
          .set(itinerary.toJson());
    } catch (e) {
      print('Error saving itinerary: $e');
      throw Exception('Failed to save itinerary');
    }
  }
  
  static Future<Itinerary?> getItinerary(int itineraryId) async {
    try {
      DocumentSnapshot doc = await _firestore
          .collection('itineraries')
          .doc(itineraryId.toString())
          .get();
      
      if (doc.exists) {
        return Itinerary.fromJson(doc.data() as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      print('Error getting itinerary: $e');
      return null;
    }
  }
  
  static Future<List<Itinerary>> getUserItineraries(int userId) async {
    try {
      QuerySnapshot querySnapshot = await _firestore
          .collection('itineraries')
          .where('user', isEqualTo: userId)
          .orderBy('created_at', descending: true)
          .get();
      
      return querySnapshot.docs
          .map((doc) => Itinerary.fromJson(doc.data() as Map<String, dynamic>))
          .toList();
    } catch (e) {
      print('Error getting user itineraries: $e');
      return [];
    }
  }
  
  static Future<void> deleteItinerary(int itineraryId) async {
    try {
      // Delete the itinerary document
      await _firestore
          .collection('itineraries')
          .doc(itineraryId.toString())
          .delete();
      
      // Delete associated days
      QuerySnapshot daysSnapshot = await _firestore
          .collection('days')
          .where('itinerary', isEqualTo: itineraryId)
          .get();
      
      WriteBatch batch = _firestore.batch();
      for (QueryDocumentSnapshot doc in daysSnapshot.docs) {
        batch.delete(doc.reference);
      }
      await batch.commit();
      
    } catch (e) {
      print('Error deleting itinerary: $e');
      throw Exception('Failed to delete itinerary');
    }
  }
  
  // Real-time listeners
  static Stream<List<Itinerary>> getUserItinerariesStream(int userId) {
    return _firestore
        .collection('itineraries')
        .where('user', isEqualTo: userId)
        .orderBy('created_at', descending: true)
        .snapshots()
        .map((snapshot) => snapshot.docs
            .map((doc) => Itinerary.fromJson(doc.data()))
            .toList());
  }
  
  static Stream<Itinerary?> getItineraryStream(int itineraryId) {
    return _firestore
        .collection('itineraries')
        .doc(itineraryId.toString())
        .snapshots()
        .map((doc) => doc.exists
            ? Itinerary.fromJson(doc.data()!)
            : null);
  }
  
  // Sync with backend (for hybrid approach)
  static Future<void> syncWithBackend() async {
    // This method can be used to sync Firebase data with Django backend
    // if you want to maintain both systems temporarily
    try {
      // Implement sync logic here if needed
      print('Syncing with backend...');
    } catch (e) {
      print('Error syncing with backend: $e');
    }
  }
  
  // Batch operations for better performance
  static Future<void> batchUpdateItineraries(List<Itinerary> itineraries) async {
    WriteBatch batch = _firestore.batch();
    
    for (Itinerary itinerary in itineraries) {
      DocumentReference docRef = _firestore
          .collection('itineraries')
          .doc(itinerary.id.toString());
      batch.set(docRef, itinerary.toJson());
    }
    
    await batch.commit();
  }
}