# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a full-stack travel planning application with AI-powered itinerary generation:

- **Backend**: Django 5.1.6 + Django REST Framework with Firebase Firestore database
- **Frontend**: Flutter mobile app with Firebase SDK integration
- **Database**: Firebase Firestore for real-time data synchronization
- **AI Integration**: OpenAI API for generating personalized travel itineraries
- **Maps Integration**: Google Maps, Places, and Geocoding APIs

## Development Commands

### Backend Setup
```bash
cd backend/
python manage.py migrate
python manage.py runserver  # Runs on default Django port
```

### Frontend Setup  
```bash
cd frontend/
flutter pub get
flutter run
```

### Environment Configuration
- Copy `backend/.env.example` to `backend/.env` and fill in required values
- Place Google service account credentials at `backend/config/credentials.json`
- Follow `FIREBASE_SETUP.md` for detailed Firebase configuration
- Required environment variables:
  - `DJANGO_SECRET_KEY`: Django secret key
  - `DEBUG`: True/False for development/production
  - `OPENAI_KEY`: OpenAI API key for itinerary generation
  - `GOOGLEMAPS_KEY`: Google Maps API key
  - `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`: For OAuth authentication
  - `FIREBASE_*`: Firebase configuration keys (see .env.example)
  - `USE_FIREBASE`: Set to True to enable Firebase integration

## Key Architecture Patterns

### Authentication Flow
- **Primary**: Firebase Authentication for user management
- **Secondary**: Django token auth for API compatibility
- Flutter app uses Firebase Auth with `firebase_auth` package
- Real-time sync between Firebase Auth and Django User model
- Secure storage using `flutter_secure_storage`

### Data Flow
- **Real-time**: Firebase Firestore for live data synchronization
- **API Backup**: Django REST endpoints for complex operations
- Automatic sync between Django models and Firestore collections
- Firebase rules enforce user data isolation

### API Communication (Hybrid)
- Base URL: `http://192.168.21.28:8000` (development)
- Firebase: Real-time data operations
- Django API: AI generation and complex business logic
- Main endpoints:
  - Authentication: Firebase Auth + `/profile/api/login/`
  - Itineraries: Firestore + `/itinerary/api/itineraries/`
  - Place replacement: `/itinerary/api/replace_place/`

### AI Integration
- `backend/itineraries/services.py` contains core AI logic
- Uses OpenAI API to generate trip overviews and daily plans
- Google APIs for geocoding and place suggestions
- Place replacement functionality for customizing generated itineraries

### Data Models
- **Itinerary**: Main travel plan with destination, dates, budget, generated content
- **Day**: Individual day plans with AI-generated activities and places
- **TravelerProfile**: Extended user profile with travel preferences
- **Review**: User reviews for itineraries

## File Organization

### Backend Structure
- `travel_planner/`: Main Django project configuration
- `accounts/`: User authentication and profiles
- `itineraries/`: Core business logic for trip planning
- `core/`: Landing pages and general views
- `templates/`: HTML templates for web interface
- `static/`: CSS and images

### Frontend Structure
- `lib/main.dart`: App entry point
- `lib/models/`: Data models (Itinerary, Day, User)  
- `lib/screens/`: UI screens for different app sections
- `lib/services/`: API communication services

## Important Configuration

### Network Setup
- Backend runs on local network IP `192.168.21.28:8000`
- CORS enabled for all origins in development (`ALLOWED_HOSTS = ['*']`)
- Request timeout set to 15 seconds for external API calls
- Maximum itinerary length: 7 days

### Google APIs Setup
- Service account credentials required at `backend/config/credentials.json`
- Uses Geocoding API for location coordinates
- Uses Places API for venue suggestions
- Uses Maps API for location services

### Dependencies
- Backend: See `requirements.txt` for Python packages
- Frontend: See `frontend/pubspec.yaml` for Flutter dependencies
- Key packages: 
  - Backend: firebase-admin (6.6.0), OpenAI (0.28.0), WeasyPrint
  - Frontend: firebase_core, cloud_firestore, firebase_auth

## Development Notes

- **Database**: Hybrid approach with Firestore primary + Django migrations for compatibility
- **State Management**: Flutter Provider pattern + Firebase streams
- **Real-time Updates**: Firestore listeners for live data synchronization
- **API Responses**: Detailed error handling with Firebase error codes
- **PDF Generation**: WeasyPrint for itinerary exports
- **Authentication**: Firebase Auth with Django User model sync
- **Data Migration**: Use `firebase_adapter.py` utilities for sync operations