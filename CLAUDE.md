# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a full-stack travel planning application with AI-powered itinerary generation:

- **Backend**: Django 5.1.6 + Django REST Framework with SQLite database
- **Frontend**: Flutter mobile app communicating via REST APIs
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
- Required environment variables:
  - `DJANGO_SECRET_KEY`: Django secret key
  - `DEBUG`: True/False for development/production
  - `OPENAI_KEY`: OpenAI API key for itinerary generation
  - `GOOGLEMAPS_KEY`: Google Maps API key
  - `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`: For OAuth authentication

## Key Architecture Patterns

### Authentication Flow
- Flutter app sends credentials to Django `/profile/api/login/`
- Django returns authentication token
- Token stored securely using `flutter_secure_storage`
- Subsequent API calls include `Authorization: Token {token}` header

### API Communication
- Base URL hardcoded in Flutter: `http://192.168.21.28:8000` (development)
- Main endpoints:
  - Authentication: `/profile/api/login/`, `/profile/api/register/`
  - Itineraries: `/itinerary/api/itineraries/`, `/itinerary/api/itineraries/{id}/`
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
- Key packages: OpenAI (0.28.0), WeasyPrint (PDF generation), django-allauth (OAuth)

## Development Notes

- Database migrations handled via standard Django `manage.py migrate`
- Flutter state management using Provider pattern
- API responses include detailed error handling
- PDF generation available for itineraries using WeasyPrint
- Token-based authentication with automatic logout on token expiry