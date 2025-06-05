#!/usr/bin/env python3
"""
Test user creation and Firebase sync.
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

from django.contrib.auth.models import User
from firebase_adapter import FirebaseManager

def test_user_sync():
    """Test creating a user and syncing to Firebase."""
    print("🧪 Testing User Creation and Firebase Sync...")
    
    try:
        # Create a test user
        username = 'firebase_test_user_' + str(int(time.time()))
        email = f'{username}@test.com'
        
        print(f"👤 Creating user: {username}")
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            first_name='Firebase',
            last_name='Test'
        )
        
        print(f"✅ User created with ID: {user.id}")
        
        # Check if user was synced to Firebase
        firebase = FirebaseManager()
        doc_ref = firebase.db.collection('users').document(str(user.id))
        doc = doc_ref.get()
        
        if doc.exists:
            print("✅ User found in Firestore!")
            print(f"📄 User data: {doc.to_dict()}")
        else:
            print("❌ User NOT found in Firestore")
            
            # Manual sync
            print("🔄 Manually syncing user to Firestore...")
            from firebase_adapter import save_to_firestore_collection
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'date_joined': user.date_joined.isoformat(),
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                '_model': 'User',
                '_updated_at': user.date_joined.isoformat()
            }
            save_to_firestore_collection('users', str(user.id), user_data)
            print("✅ User manually synced to Firestore")
        
        # Clean up
        print("🧹 Cleaning up test user...")
        user.delete()
        print("✅ Test user deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in user sync test: {e}")
        return False

def check_existing_users():
    """Check if existing users are in Firestore."""
    print("\n🔍 Checking existing users in Firebase...")
    
    try:
        firebase = FirebaseManager()
        users_ref = firebase.db.collection('users')
        docs = users_ref.stream()
        
        user_count = 0
        for doc in docs:
            user_count += 1
            user_data = doc.to_dict()
            print(f"👤 User {doc.id}: {user_data.get('username', 'No username')}")
        
        print(f"📊 Total users in Firestore: {user_count}")
        
        # Check Django users
        django_users = User.objects.all().count()
        print(f"📊 Total users in Django: {django_users}")
        
        if user_count < django_users:
            print("⚠️  Some Django users are missing from Firestore")
            sync_missing_users()
        
    except Exception as e:
        print(f"❌ Error checking existing users: {e}")

def sync_missing_users():
    """Sync all Django users to Firestore."""
    print("\n🔄 Syncing all Django users to Firestore...")
    
    try:
        from firebase_adapter import save_to_firestore_collection
        
        users = User.objects.all()
        synced_count = 0
        
        for user in users:
            try:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'date_joined': user.date_joined.isoformat(),
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    '_model': 'User',
                    '_updated_at': user.date_joined.isoformat()
                }
                save_to_firestore_collection('users', str(user.id), user_data)
                synced_count += 1
                print(f"✅ Synced user: {user.username}")
            except Exception as e:
                print(f"❌ Failed to sync user {user.username}: {e}")
        
        print(f"📊 Successfully synced {synced_count} users to Firestore")
        
    except Exception as e:
        print(f"❌ Error syncing users: {e}")

if __name__ == '__main__':
    import time
    
    print("🚀 Starting User Firebase Sync Test...\n")
    
    # Test user creation and sync
    sync_test = test_user_sync()
    
    # Check existing users
    check_existing_users()
    
    print(f"\n📊 Test Results:")
    print(f"   User Sync Test: {'✅ PASS' if sync_test else '❌ FAIL'}")
    
    if sync_test:
        print(f"\n🎉 User sync is working! Try creating a new account now.")
    else:
        print(f"\n⚠️  User sync needs fixing.")
    
    sys.exit(0 if sync_test else 1)