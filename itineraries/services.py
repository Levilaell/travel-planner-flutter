# services.py

import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import openai
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2 import service_account
from weasyprint import HTML

from .forms import ItineraryForm, ReviewForm
from .models import Day, Itinerary

load_dotenv()
openai.api_key = os.getenv('OPENAI_KEY')

# Configure logging
logger = logging.getLogger(__name__)

# ========================================================
#                  Utility Functions
# ========================================================

def request_with_retry(url, params=None, max_attempts=3, timeout=60):
    """
    Generic function to perform HTTP GET requests with up to max_attempts retries.
    Logs warnings on failures; re-raises exception if all attempts fail.
    """
    if params is None:
        params = {}

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(
                f"[request_with_retry] Attempt {attempt+1}/{max_attempts} failed: {e}. "
                f"URL: {url}, Params: {params}"
            )
            if attempt == max_attempts - 1:
                logger.error(f"[request_with_retry] Final failure: {e}")
                raise
            time.sleep(2**attempt)


def openai_chatcompletion_with_retry(messages, model="gpt-4o-mini", temperature=0.8, max_attempts=3, max_tokens=6000):
    """
    Generic function for OpenAI ChatCompletion calls with up to max_attempts retries.
    Logs warnings on failures; re-raises exception if all attempts fail.
    """
    for attempt in range(max_attempts):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response
        except openai.error.OpenAIError as e:
            logger.warning(
                f"[openai_chatcompletion_with_retry] Attempt {attempt+1}/{max_attempts} failed: {e}"
            )
            if attempt == max_attempts - 1:
                logger.error(f"[openai_chatcompletion_with_retry] Final failure: {e}")
                raise
            time.sleep(2**attempt)


def build_markers_json(itinerary):
    """
    Build a JSON array of all map markers: the main destination plus each day's visited places.
    """
    all_markers = []
    # Main destination marker
    if itinerary.lat is not None and itinerary.lng is not None:
        all_markers.append({
            "name": itinerary.destination,
            "lat": float(itinerary.lat),
            "lng": float(itinerary.lng),
        })
    # Add markers for places visited each day
    for day in itinerary.days.all():
        if day.places_visited:
            try:
                places = json.loads(day.places_visited)
                if isinstance(places, list):
                    all_markers.extend(places)
            except Exception as e:
                logger.warning(f"[build_markers_json] Failed to parse places_visited for day {day.id}: {e}")
                continue
    return json.dumps(all_markers, ensure_ascii=False)

# ========================================================
#                  Main Views
# ========================================================

@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            # 1) Create itinerary
            itinerary = form.save(commit=False)
            itinerary.user = request.user
            selected_interests = request.POST.getlist('interests_list')
            itinerary.interests = ', '.join(selected_interests)
            itinerary.save()

            # 2) Get main destination coordinates
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            # 3) Generate AI overview text
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

            # 4) Create Day entries (one per date)
            current_date = itinerary.start_date
            day_number = 1
            visited_places_list = []
            while current_date <= itinerary.end_date:
                day = Day.objects.create(
                    itinerary=itinerary,
                    day_number=day_number,
                    date=current_date
                )
                day_text, final_places = plan_one_day_itinerary(itinerary, day, visited_places_list)
                day.generated_text = day_text
                day.save()

                visited_places_list.extend(final_places)
                current_date += timedelta(days=1)
                day_number += 1

            return redirect(f"{reverse('dashboard')}?new_itinerary_id={itinerary.id}")
        else:
            # Invalid form: re-render with errors
            itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')
            for it in itineraries:
                it.markers_json = build_markers_json(it)
            return render(request, 'itineraries/dashboard.html', {
                'form': form,
                'itineraries': itineraries,
                'googlemaps_key': settings.GOOGLEMAPS_KEY,
            })
    else:
        form = ItineraryForm()
        itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')
        for it in itineraries:
            it.markers_json = build_markers_json(it)
        new_itinerary_id = request.GET.get('new_itinerary_id', '')
        return render(request, 'itineraries/dashboard.html', {
            'form': form,
            'itineraries': itineraries,
            'googlemaps_key': settings.GOOGLEMAPS_KEY,
            'new_itinerary_id': new_itinerary_id,
        })


@login_required
def delete_itinerary_view(request, pk):
    if request.method == 'POST':
        itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
        itinerary.delete()
        return redirect('dashboard')


@login_required
def export_itinerary_pdf_view(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    map_img_b64 = None
    markers_list = []
    if itinerary.lat and itinerary.lng:
        try:
            markers_list.append({
                "name": itinerary.destination,
                "lat": float(itinerary.lat),
                "lng": float(itinerary.lng),
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"[export_itinerary_pdf_view] Failed to convert lat/lng: {e}")

    for day in itinerary.days.all():
        if day.places_visited:
            try:
                day_places = json.loads(day.places_visited)
                if isinstance(day_places, list):
                    for place in day_places:
                        try:
                            markers_list.append({
                                "name": place.get("name", ""),
                                "lat": float(place["lat"]),
                                "lng": float(place["lng"]),
                            })
                        except (KeyError, ValueError, TypeError) as e:
                            logger.warning(f"[export_itinerary_pdf_view] Error extracting lat/lng: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"[export_itinerary_pdf_view] JSON decode error: {e}")

    # Build static map URL parameters
    markers_params = []
    for i, marker in enumerate(markers_list):
        if i == 0:
            label = "D"
            color = "red"
        else:
            label = str(i)
            color = "blue"
        markers_params.append(
            f"markers=color:{color}%7Clabel:{label}%7C{marker['lat']},{marker['lng']}"
        )
    markers_str = "&".join(markers_params)
    map_url = (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?size=600x300&scale=2"
        f"&{markers_str}"
        f"&key={settings.GOOGLEMAPS_KEY}"
    )

    # Fetch map image with retry
    try:
        response = request_with_retry(map_url, max_attempts=3)
        if response and response.status_code == 200 and response.content:
            raw_image = base64.b64encode(response.content).decode('utf-8')
            map_img_b64 = f"data:image/png;base64,{raw_image}"
        else:
            logger.warning(f"[export_itinerary_pdf_view] Map image fetch failed. Status={response.status_code if response else 'N/A'}")
    except Exception as e:
        logger.error(f"[export_itinerary_pdf_view] Failed to download map image: {e}")

    html_string = render_to_string('itineraries/pdf_template.html', {
        'itinerary': itinerary,
        'map_img_b64': map_img_b64,
    })

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Itinerary_{itinerary.destination}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def add_review_view(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.itinerary = itinerary
            review.user = request.user
            review.save()
            return redirect('dashboard')
    else:
        form = ReviewForm()
    return render(request, 'itineraries/add_review.html', {'form': form, 'itinerary': itinerary})


@login_required
def replace_place_view(request):
    if request.method == 'POST':
        day_id = request.POST.get('day_id')
        place_index = request.POST.get('place_index')
        observation = request.POST.get('observation', '')

        day = get_object_or_404(Day, pk=day_id, itinerary__user=request.user)
        itinerary = day.itinerary
        replace_single_place_in_day(day, place_index, observation)
        return redirect(f"{reverse('dashboard')}?new_itinerary_id={itinerary.id}")

    return redirect('dashboard')


# ========================================================
#           Core Planning Functions
# ========================================================

def generate_itinerary_overview(itinerary):
    """
    Generate a trip overview using GPT, with retries and logging on error.
    """
    prompt = f"""
You are an intelligent travel planner. Generate a **general overview** for the trip:

Destination: {itinerary.destination}
Dates: {itinerary.start_date} to {itinerary.end_date}
Budget: {itinerary.budget}
Travelers: {itinerary.travelers}
Interests: {itinerary.interests}
Extras: {itinerary.extras}

Use a friendly, cohesive tone, following this pattern:

Trip to Paris - Overview

Get ready for an unforgettable experience in the charming city of Paris, France, from April 15, 2025 to April 20, 2025! With a budget of 2000 BRL, explore rich culture, delicious cuisine, and iconic landmarks.

Start with a visit to the Eiffel Tower for breathtaking views. Then wander through the artistic Montmartre neighborhood and admire the Sacré-Cœur Basilica. Art lovers should spend time at the Louvre Museum, home to masterpieces like the Mona Lisa.

Don’t miss Parisian gastronomy: try croissants, quiches, and macarons at local bistros. A café by the Seine offers the perfect relaxation spot. Consider a boat tour on the Seine for unique views of monuments and bridges.

At night, Paris lights up in a magical display that creates lasting memories. With a well-planned itinerary, your trip to the City of Light will be a perfect blend of exploration, culture, and flavor. Get ready to discover Paris’s charms!
"""

    response = openai_chatcompletion_with_retry(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=6000,
        max_attempts=3
    )
    return response.choices[0].message["content"]


def suggest_places_gpt(itinerary, day_number, already_visited):
    visited_str = ", ".join(already_visited) if already_visited else "None"

    prompt = f"""
You are a travel planner specialized in {itinerary.destination}.
For day {day_number}, considering:
- Interests: {itinerary.interests}
- Budget: {itinerary.budget}
- Travelers: {itinerary.travelers}
- Already visited places: {visited_str}

Generate a list of REAL, existing places to visit throughout the day (morning to evening), including a lunch spot. Do NOT repeat visited places. Ensure all suggestions can be found on Google Maps and make logistical sense.

Respond in JSON format only, like:

[
  "Place 1",
  "Place 2",
  ...
]

Do not include any extra text.
"""
    response = openai_chatcompletion_with_retry(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=6000,
        max_attempts=3
    )
    content = response.choices[0].message["content"]
    try:
        places_list = json.loads(content)
        return [p.strip() for p in places_list if isinstance(p, str)]
    except Exception as e:
        logger.error(f"[suggest_places_gpt] JSON parse error: {e}")
        return []


def get_place_coordinates(place_name, reference_location="48.8566,2.3522", destination=None, radius=5000):
    """
    Use Google Places Text Search to get coordinates for a place name.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{place_name}, {destination}" if destination else place_name
    params = {
        "query": query,
        "location": reference_location,
        "radius": radius,
        "key": settings.GOOGLEMAPS_KEY,
    }

    try:
        response = request_with_retry(base_url, params=params, max_attempts=3)
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            logger.warning(f"[get_place_coordinates] No results for '{query}'. Status={data.get('status')}")
            return None, None
    except Exception as e:
        logger.error(f"[get_place_coordinates] Error fetching coordinates: {e}")
        return None, None


def build_distance_matrix(locations):
    """
    Build a distance matrix (in meters) using Google Distance Matrix API.
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    coords = [f"{loc['lat']},{loc['lng']}" for loc in locations]
    params = {
        "origins": "|".join(coords),
        "destinations": "|".join(coords),
        "key": settings.GOOGLEMAPS_KEY,
        "units": "metric"
    }
    try:
        response = request_with_retry(base_url, params=params, max_attempts=3)
        data = response.json()
        if data.get('status') != 'OK':
            logger.warning(f"[build_distance_matrix] Status not OK: {data}")
            return None

        matrix = []
        for row in data['rows']:
            distances_row = []
            for element in row['elements']:
                distances_row.append(
                    element['distance']['value'] if element['status'] == 'OK' else float('inf')
                )
            matrix.append(distances_row)
        return matrix
    except Exception as e:
        logger.error(f"[build_distance_matrix] Error building matrix: {e}")
        return None


def find_optimal_route(locations, distance_matrix):
    """
    Simple nearest-neighbor heuristic: start at index 0, then always go to the closest unvisited location.
    """
    if not locations or not distance_matrix:
        return []

    n = len(locations)
    unvisited = set(range(n))
    route = [0]
    current = 0
    unvisited.remove(0)

    while unvisited:
        nearest = min(unvisited, key=lambda i: distance_matrix[current][i])
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return route


def generate_day_text_gpt(itinerary, day, ordered_places, budget, travelers, interests, extras, weather_info=None):
    """
    Generate a detailed day itinerary narrative using GPT.
    """
    date_formatted = day.date.strftime("%d %B %Y")
    day_title = f"Day {day.day_number} - {date_formatted}"
    destination = itinerary.destination

    # Format weather string
    if weather_info.get("error"):
        weather_str = "Error fetching weather"
    elif weather_info.get("warning"):
        weather_str = weather_info["warning"]
    else:
        min_tmp = round(weather_info.get("temp_min", 0))
        max_tmp = round(weather_info.get("temp_max", 0))
        condition = weather_info.get("conditions", "Unknown")
        weather_str = f"{condition}, between {min_tmp}°C and {max_tmp}°C"

    visited_names = [loc['name'] for loc in ordered_places]
    visited_str = ", ".join(visited_names) if visited_names else "None"

    prompt = f"""
{day_title}
📍 Detailed itinerary for a day in {destination}
📅 Date: {date_formatted}
🌤️ Weather: {weather_str}
🍽️ Food Highlights: (typical dishes)
📸 Places Visited: {visited_str}

For each place below (in the exact order listed), create a block including:
- Time (e.g., 07:30 - Eiffel Tower ...)
- "📍" followed by the place name and verified address
- A complete explanatory paragraph highlighting what to do and points of interest.

Do NOT change or confuse the place names.

Trip details:
Budget: {budget}
Travelers: {travelers}
Interests: {interests}
Extras: {extras}

Order of places:
"""
    for i, name in enumerate(visited_names, start=1):
        prompt += f"{i}. {name}\n"

    prompt += """
At the end, include a 'FINAL TIP' about the destination.

Respond in English with a friendly tone.
"""

    response = openai_chatcompletion_with_retry(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=6000,
        max_attempts=3
    )

    return response.choices[0].message["content"]


def verify_and_update_places(day_text, lat, lng, destination):
    """
    Find each "📍" line in the day_text, verify address via Google Places,
    and append the verified address and a Maps link.
    """
    location_str = f"{lat},{lng}" if lat and lng else "48.8566,2.3522"
    lines = day_text.splitlines()
    new_lines = []

    for line in lines:
        if "📍" in line:
            place_candidate = line.split("📍", 1)[-1].strip()
            if not place_candidate:
                new_lines.append(line)
                continue

            place_data = search_place_in_google_maps(place_candidate, location=location_str, destination=destination)
            if place_data is None:
                new_lines.append(f"{line}\n⚠️ [WARNING] Could not find '{place_candidate}' on Google Places.")
            else:
                address = place_data.get("formatted_address", "Address not found")
                encoded = quote(address)
                new_lines.append(
                    f"{line}\n"
                    f"(verified address: {address})\n"
                    f"[View on Google Maps](https://www.google.com/maps/search/?api=1&query={encoded})"
                )
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def search_place_in_google_maps(place_name, location="48.8566,2.3522", destination=None, radius=5000):
    """
    Search for a place using Google Places Text Search API.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{place_name}, {destination}" if destination else place_name
    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "key": settings.GOOGLEMAPS_KEY,
    }
    try:
        response = request_with_retry(base_url, params=params, max_attempts=3)
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            return data["results"][0]
        else:
            logger.warning(f"[search_place_in_google_maps] No results for '{query}'. Status={data.get('status')}")
            return None
    except Exception as e:
        logger.error(f"[search_place_in_google_maps] Error searching place: {e}")
        return None


def plan_one_day_itinerary(itinerary, day, already_visited=None):
    """
    Plan one day's itinerary: suggest places, get coords, optimize route, fetch weather,
    generate narrative, verify addresses, and save Day model fields.
    Returns (generated_text, list_of_place_names).
    """
    if already_visited is None:
        already_visited = []

    # Suggest places with retries
    raw_places = []
    for attempt in range(5):
        raw_places = suggest_places_gpt(itinerary, day.day_number, already_visited)
        if raw_places:
            break
    if not raw_places:
        logger.warning("[plan_one_day_itinerary] No places found after 5 attempts.")
        return ("Could not find places for this day.", [])

    # Filter out duplicates and already visited
    lower_visited = {p.lower() for p in already_visited}
    filtered = [p for p in raw_places if p.lower() not in lower_visited]
    if not filtered:
        logger.warning("[plan_one_day_itinerary] All suggested places were duplicates.")
        return ("All suggested places have already been visited or are duplicates.", [])

    # Get coordinates for each place
    reference = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
    locations = []
    for place in filtered:
        latlng = get_place_coordinates(place, reference_location=reference, destination=itinerary.destination)
        if latlng[0] is not None:
            locations.append({"name": place, "lat": latlng[0], "lng": latlng[1]})

    if not locations:
        logger.warning("[plan_one_day_itinerary] No coordinates obtained for suggested places.")
        return ("Could not obtain coordinates for suggested places.", [])

    # Optimize visit order
    matrix = build_distance_matrix(locations)
    if not matrix:
        logger.warning("[plan_one_day_itinerary] Failed to build distance matrix.")
        return ("Could not calculate distances between places.", [])

    order = find_optimal_route(locations, matrix)
    ordered_places = [locations[i] for i in order]

    # Fetch weather forecast
    weather = get_google_weather_forecast(day.date, itinerary.lat, itinerary.lng)

    # Generate narrative
    raw_text = generate_day_text_gpt(
        itinerary,
        day,
        ordered_places,
        budget=str(itinerary.budget),
        travelers=itinerary.travelers,
        interests=itinerary.interests,
        extras=itinerary.extras,
        weather_info=weather,
    )
    verified = verify_and_update_places(raw_text, itinerary.lat, itinerary.lng, itinerary.destination)

    # Save to Day model
    day.places_visited = json.dumps(ordered_places, ensure_ascii=False)
    day.generated_text = verified
    day.save(update_fields=["places_visited", "generated_text"])

    final_names = [loc["name"] for loc in ordered_places]
    return (verified, final_names)


def get_google_weather_forecast(target_date, lat, lng):
    """
    Call Google Weather API v1 forecast/days:lookup and return forecast for the target date.
    """
    try:
        url = "https://weather.googleapis.com/v1/forecast/days:lookup"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "days": 10,
            "languageCode": "pt-BR",
            "unitsSystem": "METRIC",
            "key": settings.GOOGLEMAPS_KEY,
        }

        response = request_with_retry(url, params=params, max_attempts=3)
        data = response.json()
        logger.debug(f"[get_google_weather_forecast] Response data: {data}")

        for day in data.get("forecastDays", []):
            info = day.get("displayDate", {})
            d = datetime(year=int(info.get("year",0)), month=int(info.get("month",0)), day=int(info.get("day",0))).date()
            if d == target_date:
                cond = day.get("daytimeForecast", {}).get("weatherCondition", {}).get("description", {}).get("text", "Unknown")
                temp_max = day.get("maxTemperature", {}).get("degrees")
                temp_min = day.get("minTemperature", {}).get("degrees")
                return {
                    "date": d.isoformat(),
                    "conditions": cond,
                    "description": "",
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                }
        return {"warning": "Forecast not available for this date (beyond 10-day range)."}
    except Exception as e:
        logger.error(f"[get_google_weather_forecast] Error fetching forecast: {e}")
        return {"error": "Error fetching weather forecast"}


def get_cordinates_google_geocoding(address):
    """
    Use Google Geocoding API to get lat/lng for an address.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': address, 'key': settings.GOOGLEMAPS_KEY}
    try:
        response = request_with_retry(base_url, params=params, max_attempts=3)
        data = response.json()
        if data['status'] == 'OK':
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception as e:
        logger.error(f"[get_cordinates_google_geocoding] Error geocoding address: {e}")
    return None, None


def replace_single_place_in_day(day, place_index, user_observation):
    """
    Replace one place in a day's itinerary based on user feedback.
    """
    itinerary = day.itinerary
    all_days = itinerary.days.all().order_by('day_number')
    visited = set()

    # Gather all other visited places
    for d in all_days:
        if d.places_visited:
            try:
                arr = json.loads(d.places_visited)
                for i, pl in enumerate(arr):
                    if d.id == day.id and i == int(place_index):
                        continue
                    visited.add(pl["name"].lower())
            except Exception as e:
                logger.warning(f"[replace_single_place_in_day] Error parsing places_visited for day {d.id}: {e}")

    try:
        current = json.loads(day.places_visited)
    except:
        current = []
    if int(place_index) < len(current):
        current.pop(int(place_index))

    new_place = suggest_one_new_place_gpt(itinerary, day, visited, user_observation)
    if new_place:
        reference = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
        latlng = get_place_coordinates(new_place, reference_location=reference, destination=itinerary.destination)
        current.insert(int(place_index), {"name": new_place, "lat": latlng[0], "lng": latlng[1] if latlng else None})

    weather = get_google_weather_forecast(day.date, itinerary.lat, itinerary.lng)
    raw_text = generate_day_text_gpt(itinerary, day, current, budget=str(itinerary.budget),
                                     travelers=itinerary.travelers, interests=itinerary.interests,
                                     extras=itinerary.extras, weather_info=weather)
    verified = verify_and_update_places(raw_text, itinerary.lat, itinerary.lng, itinerary.destination)

    day.places_visited = json.dumps(current, ensure_ascii=False)
    day.generated_text = verified
    day.save(update_fields=["places_visited", "generated_text"])


def suggest_one_new_place_gpt(itinerary, day, visited_set, user_observation):
    """
    Ask GPT for a single new place suggestion, given visited_set and user observation.
    """
    visited_str = ", ".join(visited_set) if visited_set else "None"
    prompt = f"""
You are a travel planner specialized in {itinerary.destination}.
I need to replace a place that didn't fit my preferences.
Details:
- Trip day: {day.day_number}
- Interests: {itinerary.interests}
- Budget: {itinerary.budget}
- Travelers: {itinerary.travelers}
- Already visited (do not repeat): {visited_str}
- User note for new place: {user_observation}

Suggest ONLY ONE place name (no explanation), real and coherent with the context.
Respond with the place name only.
"""
    try:
        response = openai_chatcompletion_with_retry(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=6000,
            max_attempts=3
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logger.error(f"[suggest_one_new_place_gpt] Failed to suggest place: {e}")
        return ""
