#!/usr/bin/env python3
"""
Test script to verify Firebase connection and setup.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_planner.settings')
django.setup()

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_adapter import FirebaseManager

def test_firebase_connection():
    """Test Firebase connection and basic operations."""
    print("🔥 Testing Firebase connection...")
    
    try:
        # Initialize Firebase Manager
        firebase_manager = FirebaseManager()
        db = firebase_manager.db
        
        print("✅ Firebase initialized successfully!")
        print(f"📊 Connected to project: {firebase_admin.get_app().project_id}")
        
        # Test writing a document
        test_collection = 'test_collection'
        test_doc = {
            'message': 'Hello from Django!',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'test': True
        }
        
        print(f"📝 Writing test document to '{test_collection}'...")
        doc_ref = db.collection(test_collection).add(test_doc)
        print(f"✅ Document written with ID: {doc_ref[1].id}")
        
        # Test reading the document
        print(f"📖 Reading test document...")
        doc = doc_ref[1].get()
        if doc.exists:
            print(f"✅ Document data: {doc.to_dict()}")
        else:
            print("❌ Document not found")
        
        # Test deleting the document
        print(f"🗑️  Deleting test document...")
        doc_ref[1].delete()
        print("✅ Test document deleted")
        
        # Test listing collections
        print(f"📋 Listing collections...")
        collections = db.collections()
        collection_names = [col.id for col in collections]
        print(f"✅ Found collections: {collection_names}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection error: {str(e)}")
        return False

def test_model_integration():
    """Test Django model integration with Firebase."""
    print("\n🔗 Testing Django model integration...")
    
    try:
        from django.contrib.auth.models import User
        from itineraries.models import Itinerary
        from datetime import date
        
        # Check if we can create models (they should sync to Firebase)
        print("👤 Testing User model...")
        
        # Create a test user
        test_user, created = User.objects.get_or_create(
            username='firebase_test_user',
            defaults={
                'email': 'test@firebase.com',
                'first_name': 'Firebase',
                'last_name': 'Test'
            }
        )
        
        if created:
            print("✅ Test user created")
        else:
            print("✅ Test user already exists")
        
        # Create a test itinerary
        print("🗺️  Testing Itinerary model...")
        test_itinerary, created = Itinerary.objects.get_or_create(
            user=test_user,
            destination='Firebase Test City',
            defaults={
                'start_date': date.today(),
                'end_date': date.today(),
                'budget': 1000.00,
                'travelers': 2,
                'interests': 'Testing Firebase integration'
            }
        )
        
        if created:
            print("✅ Test itinerary created")
            # Test Firebase sync
            if hasattr(test_itinerary, 'save_to_firestore'):
                test_itinerary.save_to_firestore()
                print("✅ Itinerary synced to Firestore")
        else:
            print("✅ Test itinerary already exists")
        
        # Clean up
        print("🧹 Cleaning up test data...")
        test_itinerary.delete()
        test_user.delete()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Model integration error: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Firebase integration tests...\n")
    
    # Test basic Firebase connection
    firebase_ok = test_firebase_connection()
    
    # Test Django model integration
    model_ok = test_model_integration()
    
    print(f"\n📊 Test Results:")
    print(f"   Firebase Connection: {'✅ PASS' if firebase_ok else '❌ FAIL'}")
    print(f"   Model Integration:   {'✅ PASS' if model_ok else '❌ FAIL'}")
    
    if firebase_ok and model_ok:
        print(f"\n🎉 All tests passed! Firebase is ready to use.")
        return True
    else:
        print(f"\n⚠️  Some tests failed. Check the configuration.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)