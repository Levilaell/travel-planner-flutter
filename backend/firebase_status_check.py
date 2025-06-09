#!/usr/bin/env python3
"""
Comprehensive Firebase status check for the travel planner application.
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

from django.conf import settings
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_adapter import FirebaseManager

def check_environment():
    """Check environment configuration."""
    print("🔧 Checking Environment Configuration...")
    
    required_vars = [
        'DJANGO_SECRET_KEY',
        'FIREBASE_PROJECT_ID',
        'USE_FIREBASE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(settings, var, None) or os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            if var == 'DJANGO_SECRET_KEY':
                print(f"✅ {var}: {'*' * 10}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    return True

def check_firebase_credentials():
    """Check Firebase credentials file."""
    print("\n🔑 Checking Firebase Credentials...")
    
    cred_path = os.path.join(settings.BASE_DIR, 'config/credentials.json')
    
    if not os.path.exists(cred_path):
        print(f"❌ Credentials file not found at: {cred_path}")
        return False
    
    try:
        with open(cred_path, 'r') as f:
            import json
            cred_data = json.load(f)
            
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in cred_data:
                print(f"❌ Missing field in credentials: {field}")
                return False
        
        print(f"✅ Credentials file valid")
        print(f"✅ Project ID: {cred_data['project_id']}")
        print(f"✅ Service account: {cred_data['client_email']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def check_firebase_connection():
    """Check Firebase connection."""
    print("\n🔥 Checking Firebase Connection...")
    
    try:
        firebase_manager = FirebaseManager()
        db = firebase_manager.db
        
        # Test basic operations
        test_doc = {'test': True, 'timestamp': firestore.SERVER_TIMESTAMP}
        doc_ref = db.collection('status_check').add(test_doc)
        
        # Read back
        doc = doc_ref[1].get()
        if not doc.exists:
            print("❌ Failed to read test document")
            return False
        
        # Delete test document
        doc_ref[1].delete()
        
        print("✅ Firebase connection successful")
        print(f"✅ Connected to project: {firebase_admin.get_app().project_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

def check_django_models():
    """Check Django models Firebase integration."""
    print("\n🗄️  Checking Django Models Integration...")
    
    try:
        from django.contrib.auth.models import User
        from itineraries.models import Itinerary
        from accounts.models import TravelerProfile
        
        # Check if models have Firebase methods
        models_to_check = [Itinerary, TravelerProfile]
        
        for model in models_to_check:
            if not hasattr(model, 'save_to_firestore'):
                print(f"❌ {model.__name__} missing Firebase integration")
                return False
            else:
                print(f"✅ {model.__name__} has Firebase integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Model integration check failed: {e}")
        return False

def check_flutter_config():
    """Check Flutter Firebase configuration."""
    print("\n📱 Checking Flutter Configuration...")
    
    frontend_path = Path(settings.BASE_DIR).parent / 'frontend'
    
    # Check pubspec.yaml
    pubspec_path = frontend_path / 'pubspec.yaml'
    if not pubspec_path.exists():
        print(f"❌ Flutter pubspec.yaml not found")
        return False
    
    with open(pubspec_path, 'r') as f:
        pubspec_content = f.read()
    
    firebase_deps = ['firebase_core', 'cloud_firestore', 'firebase_auth']
    missing_deps = []
    
    for dep in firebase_deps:
        if dep not in pubspec_content:
            missing_deps.append(dep)
        else:
            print(f"✅ {dep} dependency found")
    
    if missing_deps:
        print(f"❌ Missing Flutter dependencies: {missing_deps}")
        return False
    
    # Check firebase_options.dart
    firebase_options_path = frontend_path / 'lib' / 'firebase_options.dart'
    if not firebase_options_path.exists():
        print(f"❌ firebase_options.dart not found")
        return False
    
    print(f"✅ firebase_options.dart exists")
    
    # Check google-services.json
    google_services_path = frontend_path / 'android' / 'app' / 'google-services.json'
    if not google_services_path.exists():
        print(f"❌ google-services.json not found")
        return False
    
    print(f"✅ google-services.json exists")
    
    return True

def main():
    """Main status check function."""
    print("🚀 Firebase Integration Status Check")
    print("=" * 50)
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Firebase Credentials", check_firebase_credentials),
        ("Firebase Connection", check_firebase_connection),
        ("Django Models Integration", check_django_models),
        ("Flutter Configuration", check_flutter_config),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
            results[check_name] = False
    
    print("\n" + "=" * 50)
    print("📊 FINAL STATUS REPORT")
    print("=" * 50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("Firebase integration is fully functional!")
        print("\nNext steps:")
        print("- Start Django server: python manage.py runserver")
        print("- Start Flutter app: flutter run")
        print("- Use Firebase services in your app")
    else:
        print("⚠️  SOME CHECKS FAILED!")
        print("Please fix the issues above before using Firebase.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)