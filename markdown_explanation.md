Below are the complete codes with all originally Portuguese text translated into English. The structure, variable names, URLs, and logic remain the same. Only user-facing text, comments, and explanatory strings have been translated.

--------------------------------------------------------------------------------
File: templates/itineraries/dashboard.html
--------------------------------------------------------------------------------
{% extends "base.html" %}
{% load static %}
{% load markdownify %}

{% block content %}
<div class="container-fluid" style="background-color:#2C2C2E">
  <div class="row full-height-row">

    {# =====================  LEFT PANEL – FORM  ===================== #}
    <div class="col-md-4 left-panel d-flex align-items-start flex-column p-4">
      <h3 class="text-white">Create New Itinerary</h3>

      {% if form.errors %}
      <div class="alert alert-danger w-100">
        <ul class="mb-0">
          {% for field, errors in form.errors.items %}
            {% for error in errors %}
              <li><strong>{{ field }}:</strong> {{ error }}</li>
            {% endfor %}
          {% endfor %}
        </ul>
      </div>
      {% endif %}

      <form method="POST" action="{% url 'dashboard' %}" class="w-100 needs-validation" novalidate id="itineraryForm">
        {% csrf_token %}
      
        <!-- Destination -->
        <div class="mb-3">
          <label for="destination" class="form-label">Destination *</label>
          <input type="text" class="form-control" id="destination" name="destination"
                 placeholder="E.g: Natal, Brazil" required>
          <div class="form-text">Provide a city, country, or region you wish to visit.</div>
        </div>
      
        <!-- Dates -->
        <div class="row g-2 mb-3">
          <div class="col">
            <label for="startDate" class="form-label">Start Date *</label>
            <input type="date" class="form-control" id="startDate" name="start_date" required>
          </div>
          <div class="col">
            <label for="endDate" class="form-label">End Date *</label>
            <input type="date" class="form-control" id="endDate" name="end_date" required>
          </div>
        </div>
      
        <!-- Total Budget -->
        <div class="mb-3">
          <label for="budget" class="form-label">Total Budget (R$)</label>
          <input type="number" class="form-control" id="budget" name="budget" step="0.01"
                 placeholder="E.g: 2000">
          <div class="form-text">How much do you plan to spend in total on this trip?</div>
        </div>
      
        <!-- Number of travelers -->
        <div class="mb-3">
          <label for="travelers" class="form-label">Number of Travelers</label>
          <input type="number" class="form-control" id="travelers" name="travelers" min="1" value="1">
        </div>
      
        <!-- Interests -->
        <div class="mb-3">
          <label class="form-label d-block">Travel Interests</label>
          <div class="row">
            {% for interest in interests %}
            <div class="col-md-6">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="interest{{ interest }}"
                       name="interests_list" value="{{ interest }}">
                <label class="form-check-label" for="interest{{ interest }}">{{ interest }}</label>
              </div>
            </div>
            {% endfor %}
          </div>
          <div class="form-text">You can select multiple themes you wish to focus on during the trip.</div>
        </div>
    
        <!-- Additional considerations -->
        <div class="mb-3">
          <label for="extras" class="form-label">Anything else we should consider?</label>
          <textarea class="form-control" id="extras" name="extras" rows="3"
                    placeholder="E.g: Accessibility, avoid beaches, 4-star hotels, etc."
                    style="::placeholder { color: white; }"></textarea>
        </div>
      
        <div class="text-center">
          <button type="submit" class="btn btn-primary w-100 btn-lg shadow-sm">Generate Itinerary</button>
        </div>
      </form>
      
    </div>

    {# =====================  RIGHT PANEL – ITINERARIES  ===================== #}
    <div class="col-md-8 px-3 right-panel">
      <h3 class="mb-4 pt-3 text-white">My Itineraries</h3>

      {% if itineraries %}
      <div class="row p-3">
        {% for it in itineraries %}
        <div class="col-md-6 mb-4">
          <div class="card h-100 p-3" style="background-color:#2c2c2e;color:#fff;">
            <div class="card-body">
              <h3 class="card-title">{{ it.destination }}</h3>
              <p class="card-text">{{ it.start_date }} → {{ it.end_date }}</p>

              <div class="my-2">
                <form method="POST" action="{% url 'delete_itinerary' it.id %}" style="display:inline;">
                  {% csrf_token %}
                  <button class="btn btn-sm btn-outline-light" type="button"
                          data-bs-toggle="modal" data-bs-target="#modalIt{{ it.id }}">
                    View Details
                  </button>
                  <a href="{% url 'export_itinerary_pdf' it.id %}"
                     class="btn btn-sm btn-outline-light">Download PDF</a>
                  <button type="submit" class="btn btn-sm btn-outline-danger"
                          onclick="return confirm('Are you sure you want to delete this itinerary?')">
                    Delete
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>

        {# ----------  DETAILS MODAL  ---------- #}
        <div class="modal fade" id="modalIt{{ it.id }}" tabindex="-1"
             aria-labelledby="modalItLabel{{ it.id }}" aria-hidden="true">
          <div class="modal-dialog modal-xl modal-dialog-centered">
            <div class="modal-content" style="background-color:#202023;color:#fff;">
              <div class="modal-header">
                <h5 class="modal-title" id="modalItLabel{{ it.id }}">
                  {{ it.destination }} - {{ it.start_date }} → {{ it.end_date }}
                </h5>
                <button type="button" class="btn-close btn-close-white"
                        data-bs-dismiss="modal" aria-label="Close"></button>
              </div>

              <div class="modal-body">
                <h5>Overview</h5>
                <div class="ai-text mb-3">{{ it.generated_text|markdownify }}</div>

                <h5>Days</h5>
                <ul class="nav nav-tabs mt-3" id="daysTab{{ it.id }}" role="tablist">
                  {% for d in it.days.all|dictsort:"day_number" %}
                  <li class="nav-item" role="presentation">
                    <button class="nav-link {% if forloop.first %}active{% endif %}"
                            id="day{{ it.id }}-{{ d.id }}-tab"
                            data-bs-toggle="tab" data-bs-target="#day{{ it.id }}-{{ d.id }}"
                            type="button" role="tab">
                      Day {{ d.day_number }}
                    </button>
                  </li>
                  {% endfor %}
                </ul>

                <div class="tab-content mt-3" id="daysTabContent{{ it.id }}">
                  {% for d in it.days.all|dictsort:"day_number" %}
                  <div class="tab-pane fade {% if forloop.first %}show active{% endif %}"
                       id="day{{ it.id }}-{{ d.id }}" role="tabpanel">
                    <div class="result-card mb-3">
                      <div class="ai-text" data-dayid="{{ d.id }}">{{ d.generated_text|markdownify|safe }}
                      <div class="places-photo-gallery row mt-3" id="photos-for-day-{{ d.id }}"></div>
                      </div>

                      {% if d.places_visited %}
                      <div class="mt-3">
                        <strong>Places (Edit individually):</strong>
                        <div id="day-places-{{ d.id }}"
                        data-places='{{ d.places_visited|safe }}'></div>

                        <script>
                          (function(){
                            const container = document.getElementById("day-places-{{ d.id }}");
                            const rawData = `{{ d.places_visited|safe }}`;
                            try {
                              const arr = JSON.parse(rawData);
                              if (Array.isArray(arr)) {
                                let html = "";
                                arr.forEach((p, idx) => {
                                  const name = p.name || "Unknown place";
                                  html += `
                                    <div class="mt-2">
                                      ${idx+1}. ${name}
                                      <button class="btn btn-sm btn-link text-warning replace-place-btn"
                                              data-dayid="{{ d.id }}" data-index="${idx}"
                                              data-bs-toggle="modal" data-bs-target="#replaceModal">
                                        🔄
                                      </button>
                                    </div>`;
                                });
                                container.innerHTML = html;
                              }
                            } catch(e){}
                          })();
                        </script>
                      </div>
                      {% endif %}
                    </div>
                  </div>
                  {% endfor %}
                </div>

                <h5>Map</h5>
                <div id="map{{ it.id }}"
                     data-lat="{{ it.lat|floatformat:'6' }}"
                     data-lng="{{ it.lng|floatformat:'6' }}"
                     data-markers='{{ it.markers_json|escape }}'
                     style="height:400px; border:1px solid #3a3a3c; border-radius:6px;"></div>
              </div>

              <div class="modal-footer">
                <button type="button" class="btn btn-outline-light"
                        data-bs-dismiss="modal">Close</button>
              </div>
            </div>
          </div>
        </div>
        {# ----------  /DETAILS MODAL  ---------- #}
        {% endfor %}
      </div>
      {% else %}
        <p class="text-white">No itineraries created yet...</p>
      {% endif %}
    </div>
  </div>
</div>

{# ===================  REPLACE PLACE MODAL  =================== #}
<div class="modal fade" id="replaceModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered" style="color:#fff;">
    <div class="modal-content" style="background-color:#202023;">
      <div class="modal-header">
        <h5 class="modal-title">Replace Place</h5>
        <button type="button" class="btn-close btn-close-white"
                data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <form method="POST" action="{% url 'replace_place' %}">
        {% csrf_token %}
        <div class="modal-body">
          <input type="hidden" id="replaceDayId" name="day_id">
          <input type="hidden" id="replaceIndex" name="place_index">
          <div class="mb-3">
            <label for="replaceObservation" class="form-label">
              Observation / Preference for the New Place
            </label>
            <textarea class="form-control" id="replaceObservation" name="observation"
                      rows="3" placeholder="E.g: I want somewhere more central, no repeated places, or typical food"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-light"
                  data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Confirm Replacement</button>
        </div>
      </form>
    </div>
  </div>
</div>

{# ===================  LOADING OVERLAY  =================== #}
<div id="loadingOverlay" style="display:none;">
  <div class="loading-backdrop"></div>
  <div class="loading-box text-center">
    <div class="spinner-border text-light" role="status" style="width:4rem; height:4rem;"></div>
    <div class="progress mt-4" style="height:10px;">
      <div id="loadingBar" class="progress-bar bg-primary" role="progressbar" style="width:0%;"></div>
    </div>
    <p id="loadingText" class="mt-3 fs-5 text-white">Preparing itinerary...</p>
  </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
/* ---------- UTILITY ---------- */
function normalizeText(str) {
  return (str||"")
    .normalize("NFD")            // separates accents
    .replace(/[̀-ͯ]/g, "")       // removes accents
    .replace(/[^\w\s]/g, " ")    // removes punctuation
    .toLowerCase()
    .trim();
}

/* ---------- PHOTO ---------- */
const photoCache = new Map();  // key = query, value = url

function textMatchesPlace(elText, placeName) {
  const a = normalizeText(elText);
  const b = normalizeText(placeName);
  return a.includes(b);
}

/* ---------- PHOTO ---------- */
function insertPhotoInGallery(dayId, placeName, photoUrl) {
  // 1) look for the div with that day's entire description
  const aiContainer = document.querySelector(`.ai-text[data-dayid="${dayId}"]`);
  if (!aiContainer) return;

  /* 2) go through all text elements in the description
        until we find the first whose text includes the place name. */
  const walker = document.createTreeWalker(aiContainer, NodeFilter.SHOW_ELEMENT, null);
  let targetEl = null;
  while (walker.nextNode()) {
    const el = walker.currentNode;
    if (textMatchesPlace(el.textContent, placeName)) {
      targetEl = el;  // found the paragraph/heading
      break;
    }
  }

  // 3) if not found, put the photo in the fallback gallery at the end
  if (!targetEl) {
    const fallback = document.getElementById(`photos-for-day-${dayId}`);
    if (fallback) {
      fallback.insertAdjacentHTML(
        "beforeend",
        `<div class="col-12 mb-3">
           <img src="${photoUrl}" class="img-fluid rounded" alt="Photo of ${placeName}">
         </div>`
      );
    }
    return;
  }

  // 4) insert the image right AFTER the found text element
  targetEl.insertAdjacentHTML(
    "afterend",
    `<div class="my-3">
       <img src="${photoUrl}" class="img-fluid rounded w-100" alt="Photo of ${placeName}">
     </div>`
  );
}

/* The rest is the same – just removed references to day-places‑… */
function fetchPhotosForPlaces(dayId, placesJson, destination) {
  let places;
  try { places = JSON.parse(placesJson); } catch { return; }

  places.forEach(place => {
    const query = `${place.name}, ${destination}`;
    const cacheKey = query.toLowerCase();

    if (photoCache.has(cacheKey)) {
      insertPhotoInGallery(dayId, place.name, photoCache.get(cacheKey));
      return;
    }

    const googleUrl =
      `https://maps.googleapis.com/maps/api/place/findplacefromtext/json` +
      `?input=${encodeURIComponent(query)}` +
      `&inputtype=textquery&fields=photos&key={{ googlemaps_key }}`;

    fetch("{% url 'proxy_google_places' %}?url=" + encodeURIComponent(googleUrl))
      .then(r => r.json())
      .then(data => {
        let photoUrl;
        const ref = data.candidates?.[0]?.photos?.[0]?.photo_reference;

        photoUrl = ref
          ? "{% url 'proxy_google_photo' %}?photo_ref=" + ref
          : `https://source.unsplash.com/600x400/?${encodeURIComponent(place.name + ' ' + destination)}`;

        photoCache.set(cacheKey, photoUrl);
        insertPhotoInGallery(dayId, place.name, photoUrl);
      })
      .catch(err => console.error("Photo error:", err));
  });
}
</script>

<script id="places-{{ d.id }}" type="application/json">
  {{ d.places_visited|safe }}
</script>

<script>
/* ---------- LOADER / FORM ---------- */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("itineraryForm");
  const overlay = document.getElementById("loadingOverlay");
  const bar = document.getElementById("loadingBar");
  const text = document.getElementById("loadingText");

  const msgs = [
    "Analyzing destination...",
    "Selecting the best places...",
    "Optimizing routes...",
    "Planning unique experiences...",
    "Generating the perfect itinerary..."
  ];
  let p = 0, idx = 0, iv;

  function startLoader() {
    overlay.style.display = "flex";
    p = 0; idx = 0;
    bar.style.width = "0%";
    text.textContent = msgs[0];

    iv = setInterval(() => {
      p += Math.random() * 5;
      bar.style.width = `${Math.min(p, 100)}%`;
      if (p >= 20 && idx < 1) text.textContent = msgs[(idx = 1)];
      if (p >= 40 && idx < 2) text.textContent = msgs[(idx = 2)];
      if (p >= 60 && idx < 3) text.textContent = msgs[(idx = 3)];
      if (p >= 80 && idx < 4) text.textContent = msgs[(idx = 4)];
    }, 400);
  }

  form?.addEventListener("submit", startLoader);
});
</script>

<script>
/* ---------- GOOGLE MAPS / MODAL ---------- */
function initAutocomplete() {
  const destInput = document.getElementById("destination");
  if (destInput) {
    new google.maps.places.Autocomplete(destInput, { types: ["(cities)"] });
  }

  /* photos + map when the user opens a modal */
  document.querySelectorAll(".modal.fade").forEach(modal => {
    modal.addEventListener("shown.bs.modal", () => {
      const id = modal.getAttribute("id");
      if (!id?.startsWith("modalIt")) return;

      const itinId = id.replace("modalIt", "");
      initMultipleMarkers(itinId);

      /* Photos */
      modal.querySelectorAll('[id^="day-places-"]').forEach(div => {
        const dayId      = div.id.replace("day-places-", "");
        const placesJson = div.dataset.places;
        if (placesJson) {
            const destination =
                modal.querySelector(".modal-title")
                     ?.textContent.split(" - ")[0].trim() || "";
            fetchPhotosForPlaces(dayId, placesJson, destination);
        }
      });
    });
  });
}

function initMultipleMarkers(itineraryId) {
  const mapDiv = document.getElementById("map" + itineraryId);
  if (!mapDiv) return;

  let markers = [];
  try { markers = JSON.parse(mapDiv.dataset.markers || "[]"); } catch {}

  let lat = parseFloat(mapDiv.dataset.lat);
  let lng = parseFloat(mapDiv.dataset.lng);
  if (isNaN(lat) || isNaN(lng)) { lat = markers[0]?.lat; lng = markers[0]?.lng; }

  const map = new google.maps.Map(mapDiv, { zoom: 12, center: { lat, lng } });
  const bounds = new google.maps.LatLngBounds();

  markers.forEach(m => {
    if (m.lat && m.lng) {
      const pos = { lat: m.lat, lng: m.lng };
      new google.maps.Marker({ position: pos, map, title: m.name });
      bounds.extend(pos);
    }
  });
  if (markers.length > 1) map.fitBounds(bounds);
}

/* auto‑open newly created modal */
document.addEventListener("DOMContentLoaded", () => {
  const autoId = "{{ new_itinerary_id|default:'' }}";
  if (autoId) new bootstrap.Modal(document.getElementById("modalIt" + autoId)).show();

  /* fill in hidden fields for place replacement */
  document.body.addEventListener("click", e => {
    if (e.target?.classList.contains("replace-place-btn")) {
      document.getElementById("replaceDayId").value = e.target.dataset.dayid;
      document.getElementById("replaceIndex").value = e.target.dataset.index;
      document.getElementById("replaceObservation").value = "";
    }
  });
});
</script>

<script src="https://maps.googleapis.com/maps/api/js?key={{ googlemaps_key }}&libraries=places&callback=initAutocomplete" async defer></script>
{% endblock %}

--------------------------------------------------------------------------------
File: services.py
--------------------------------------------------------------------------------
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

# Configuring logs
logger = logging.getLogger(__name__)

# ========================================================
#               Utility Functions
# ========================================================

def request_with_retry(url, params=None, max_attempts=3, timeout=60):
    """
    Generic function to perform HTTP GET requests with up to max_attempts tries.
    Logs an error on failure. If unsuccessful, re-raises the exception in the end.
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
                logger.error(f"[request_with_retry] Definitive error: {e}")
                raise
            # Optional: add a small delay between tries
            time.sleep(2**attempt)


def openai_chatcompletion_with_retry(messages, model="gpt-4o-mini", temperature=0.8, max_attempts=3, max_tokens=6000):
    """
    Generic function for OpenAI calls with up to max_attempts tries.
    Logs errors and re-raises the exception if it fails every time.
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
                logger.error(f"[openai_chatcompletion_with_retry] Definitive error: {e}")
                raise
            time.sleep(2**attempt)


def build_markers_json(itinerary):
    all_markers = []
    # Main marker: destination
    if itinerary.lat is not None and itinerary.lng is not None:
        all_markers.append({
            "name": itinerary.destination,
            "lat": float(itinerary.lat),
            "lng": float(itinerary.lng),
        })
    # Add markers for visited places each day
    for day in itinerary.days.all():
        if day.places_visited:
            try:
                places = json.loads(day.places_visited)
                if isinstance(places, list):
                    all_markers.extend(places)
            except Exception as e:
                logger.warning(f"[build_markers_json] Failed to process places_visited for day {day.id}: {e}")
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

            # 2) Main destination coordinates
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            # 3) IA text (overview)
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

            # 4) Create Days (one per date)
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
            # Invalid form => show errors
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
                            logger.warning(f"[export_itinerary_pdf_view] Error extracting lat/lng from place: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"[export_itinerary_pdf_view] JSONDecodeError while processing places_visited: {e}")

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

    # Using our retry function
    try:
        response = request_with_retry(map_url, params=None, max_attempts=3)
        if response and response.status_code == 200 and response.content:
            raw_image = base64.b64encode(response.content).decode('utf-8')
            map_img_b64 = f"data:image/png;base64,{raw_image}"
        else:
            logger.warning(f"[export_itinerary_pdf_view] Error or empty content in map image. status={response.status_code if response else 'N/A'}")
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
    from .models import Itinerary
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
#             Main Planning Functions
# ========================================================

def generate_itinerary_overview(itinerary):
    """
    Generates a general overview using GPT, with retries and logs upon error.
    """
    prompt = f"""
You are an intelligent travel planner. Generate an overall **overview** about the trip:

Destination: {itinerary.destination}
Date: {itinerary.start_date} to {itinerary.end_date}
Budget: {itinerary.budget}
Travelers: {itinerary.travelers}
Interests: {itinerary.interests}
Extras: {itinerary.extras}

Answer in the following format (keeping a friendly and cohesive tone):

Trip to Paris - Overview

Get ready for an unforgettable experience in the charming city of Paris, France, on April 15, 2025! With a budget of 2000 reais, you will have the opportunity to explore the rich culture, delicious cuisine, and iconic tourist spots that the French capital has to offer.

Your journey will begin with a visit to the famous Eiffel Tower, where you can admire the breathtaking view of the city. Then, be sure not to miss strolling through the charming Montmartre district, known for its artistic atmosphere and beautiful cobblestone streets. The Sacré-Cœur Basilica, majestically perched on top of the hill, is a must-see.

For art lovers, the Louvre Museum is a true paradise, housing masterpieces such as the Mona Lisa and the Venus de Milo. Take time to wander through its galleries and enjoy the building's impressive architecture.

Parisian cuisine also deserves special mention! Explore local bistros and try traditional dishes like croissants, quiches, and of course, macarons. A meal at a café by the Seine can be a perfect way to relax and soak in the vibrant city atmosphere.

Additionally, consider a boat ride on the Seine River, providing a unique perspective of Paris's monuments and bridges. At night, the spectacle of the City of Light is simply magical and creates memories that will last a lifetime.

With carefully planned scheduling and an attention to detail, your trip to Paris will be the perfect combination of exploration, culture, and flavor. Prepare to discover the charms of the City of Light!
"""

    # OpenAI call with retry
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
You are a travel planner specialized in the destination {itinerary.destination}.
For day {day_number} of the trip, considering:
- Interests: {itinerary.interests}
- Budget: {itinerary.budget}
- Travelers: {itinerary.travelers}
- Places already visited on previous days: {visited_str}

Generate a list of interesting and REAL places to visit throughout the entire day (from morning to night, considering somewhere for lunch around lunchtime, tourist spots in the afternoon, etc.), WITHOUT repeating places already visited.
Ensure the suggested places actually exist, can be easily verified on Google Maps, and are logistically coherent for the tourist.

Respond in JSON format, like this:

[
  "Place 1",
  "Place 2",
  "Place 3",
  "Place 4",
  "Place 5",
  "Place 6"
]

Return only the list, without additional text.

Note: Be careful not to suggest dangerous locations.
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
        places_list = [p.strip() for p in places_list if isinstance(p, str)]
        return places_list
    except Exception as e:
        logger.error(f"[suggest_places_gpt] Error parsing JSON returned by GPT: {e}")
        return []


def get_place_coordinates(place_name, reference_location="48.8566,2.3522", destination=None, radius=5000):
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
            logger.warning(
                f"[get_place_coordinates] No results for '{query}'. Status={data.get('status')}"
            )
            return None, None
    except Exception as e:
        logger.error(f"[get_place_coordinates] Error fetching coordinates: {e}")
        return None, None


def build_distance_matrix(locations):
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
            logger.warning(f"[build_distance_matrix] status != OK. data={data}")
            return None

        distance_matrix = []
        for row in data['rows']:
            distances_row = []
            for element in row['elements']:
                if element['status'] == 'OK':
                    distances_row.append(element['distance']['value'])
                else:
                    distances_row.append(float('inf'))
            distance_matrix.append(distances_row)
        return distance_matrix
    except Exception as e:
        logger.error(f"[build_distance_matrix] Error building distance matrix: {e}")
        return None


def find_optimal_route(locations, distance_matrix):
    """
    Simple heuristic: start at the first location and always go to the nearest next.
    """
    if not locations or not distance_matrix:
        return []

    n = len(locations)
    unvisited = set(range(n))
    route = []
    current = 0
    route.append(current)
    unvisited.remove(current)

    while unvisited:
        nearest = None
        min_dist = float('inf')
        for candidate in unvisited:
            dist = distance_matrix[current][candidate]
            if dist < min_dist:
                min_dist = dist
                nearest = candidate
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return route


def generate_day_text_gpt(itinerary, day, ordered_places, budget, travelers, interests, extras, weather_info=None):
    date_formatted = day.date.strftime("%d %B %Y")
    day_title = f"Day {day.day_number} - {date_formatted}"
    destination = itinerary.destination

    if weather_info.get("error"):
        weather_str = "Error fetching weather"
    elif weather_info.get("warning"):
        weather_str = weather_info["warning"]
    else:
        temp_min_raw = weather_info.get("temp_min")
        temp_max_raw = weather_info.get("temp_max")
        temp_min = round(temp_min_raw) if isinstance(temp_min_raw, (int, float)) else "N/A"
        temp_max = round(temp_max_raw) if isinstance(temp_max_raw, (int, float)) else "N/A"
        condition = weather_info.get("conditions", "Unknown")
        desc = weather_info.get("description", "")
        weather_str = f"{condition} ({desc}), between {temp_min}°C and {temp_max}°C"

    visited_names = [loc['name'] for loc in ordered_places]
    visited_str = ", ".join(visited_names) if visited_names else "None"

    prompt = f"""
You are an intelligent and creative travel planner.
Generate a detailed itinerary for the day, in the following format:

{day_title}
📍 Detailed Day Itinerary in {destination}
📅 Date: {date_formatted}
🌤️ Weather Forecast: {weather_str}
🍽️ Gastronomic Highlights: (e.g. typical food)
📸 Places Visited: {visited_str}

For each place below (keeping the exact listed order), create a block with:
- Time (e.g. 7:30 AM - Eiffel Tower ...)
- Marker "📍" followed by the name and verified address
- A complete explanatory text about the place, highlighting what to do, points of interest, and relevant information.
DO NOT deviate from the pattern and DO NOT change or confuse the listed place names.

Follow carefully the user's provided info:
Budget: {budget}
Travelers: {travelers}
Interests: {interests}
Extras: {extras}

Order of Places to Visit:
"""
    for i, name in enumerate(visited_names, start=1):
        prompt += f"{i}. {name}\n"

    prompt += """
Finally, include a 'FINAL TIP' about the destination.

Reply in Portuguese (originally was in Portuguese, but here we keep the same style—only the code comment is in English). 
Keep a friendly tone.
Note: The schedule should be spread out during the day to last the entire day.
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
                not_found_msg = f"{line}\n⚠️ [NOTICE] We could not find '{place_candidate}' in Google Places."
                new_lines.append(not_found_msg)
            else:
                address = place_data.get("formatted_address", "Address not found")
                encoded_addr = quote(address)
                new_line = (
                    f"{line}\n"
                    f"(verified address: {address})\n"
                    f"[View on Google Maps](https://www.google.com/maps/search/?api=1&query={encoded_addr})"
                )
                new_lines.append(new_line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def search_place_in_google_maps(place_name, location="48.8566,2.3522", destination=None, radius=5000):
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
            logger.warning(
                f"[search_place_in_google_maps] No result for '{query}'. Status={data.get('status')}"
            )
            return None
    except Exception as e:
        logger.error(f"[search_place_in_google_maps] Error searching place: {e}")
        return None


def plan_one_day_itinerary(itinerary, day, already_visited=None):
    if already_visited is None:
        already_visited = []

    max_attempts = 5
    raw_places = []
    for attempt in range(1, max_attempts + 1):
        raw_places = suggest_places_gpt(itinerary, day.day_number, already_visited)
        if raw_places:
            break

    if not raw_places:
        logger.warning("[plan_one_day_itinerary] Could not find places after 5 attempts.")
        return ("It was not possible to find places for this day after 5 attempts.", [])

    lower_visited = [p.lower() for p in already_visited]
    filtered_places = []
    for p in raw_places:
        if p.lower() not in lower_visited and p not in filtered_places:
            filtered_places.append(p)

    if not filtered_places:
        logger.warning("[plan_one_day_itinerary] All suggested places were repeats.")
        return ("All suggested places were already visited or are duplicates.", [])

    reference_location = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
    locations = []
    for place in filtered_places:
        latlng = get_place_coordinates(place, reference_location=reference_location, destination=itinerary.destination)
        if latlng[0] is not None:
            locations.append({
                "name": place,
                "lat": latlng[0],
                "lng": latlng[1]
            })

    if not locations:
        logger.warning("[plan_one_day_itinerary] No coordinates obtained for the suggested places.")
        return ("Could not get coordinates for the suggested places.", [])

    distance_matrix = build_distance_matrix(locations)
    if not distance_matrix:
        logger.warning("[plan_one_day_itinerary] Failed to calculate distance matrix.")
        return ("Could not calculate distances between places.", [])

    route_indices = find_optimal_route(locations, distance_matrix)
    route_ordered = [locations[i] for i in route_indices]

    # ✅ Replacement here: Google-based weather info for date and location
    weather_data = get_google_weather_forecast(day.date, itinerary.lat, itinerary.lng)

    raw_day_text = generate_day_text_gpt(
        itinerary,
        day,
        route_ordered,
        budget=str(itinerary.budget),  # Decimal → string to avoid formatting issues
        travelers=itinerary.travelers,
        interests=itinerary.interests,
        extras=itinerary.extras,
        weather_info=weather_data,
    )
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng, itinerary.destination)

    final_place_names = [loc["name"] for loc in route_ordered]

    day.places_visited = json.dumps(route_ordered, ensure_ascii=False)
    day.generated_text = verified_text
    day.save(update_fields=["places_visited", "generated_text"])

    return (verified_text, final_place_names)


def get_google_weather_forecast(target_date, lat, lng):
    """
    Consults the Google Weather API v1 (forecast.days:lookup) and returns the forecast for the exact date, if available.
    """
    try:
        url = "https://weather.googleapis.com/v1/forecast/days:lookup"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "days": 10,  # fetch up to 10 days ahead
            "languageCode": "pt-BR",  # This is the language code for Portuguese results
            "unitsSystem": "METRIC",
            "key": settings.GOOGLEMAPS_KEY,
        }

        response = request_with_retry(url, params=params, max_attempts=3)
        data = response.json()
        logger.debug(f"[get_google_weather_forecast] Returned data: {data}")

        forecast_days = data.get("forecastDays", [])
        for day in forecast_days:
            date_info = day.get("displayDate", {})
            forecast_date = datetime(
                year=int(date_info.get("year", 0)),
                month=int(date_info.get("month", 0)),
                day=int(date_info.get("day", 0))
            ).date()

            if forecast_date == target_date:
                day_part = day.get("daytimeForecast", {})
                weather_condition = day_part.get("weatherCondition", {})
                condition = weather_condition.get("description", {}).get("text", "Unknown")
                temp_max = day.get("maxTemperature", {}).get("degrees")
                temp_min = day.get("minTemperature", {}).get("degrees")

                return {
                    "date": forecast_date.isoformat(),
                    "conditions": condition,
                    "description": "",  # not used separately
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                }

        return {"warning": "Forecast not available for this date (beyond the next 10 days)."}
    except Exception as e:
        logger.error(f"[get_google_weather_forecast] Error fetching forecast: {e}")
        return {"error": "Error fetching weather forecast"}


def get_cordinates_google_geocoding(address):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': settings.GOOGLEMAPS_KEY
    }
    try:
        response = request_with_retry(base_url, params=params, max_attempts=3)
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    except Exception as e:
        logger.error(f"[get_cordinates_google_geocoding] Error getting coordinates by geocoding: {e}")
    return None, None


def replace_single_place_in_day(day, place_index, user_observation):
    itinerary = day.itinerary
    all_days = itinerary.days.all().order_by('day_number')
    visited_set = set()

    for d in all_days:
        if not d.places_visited:
            continue
        try:
            arr = json.loads(d.places_visited)
            for i, pl in enumerate(arr):
                # Ignore the exact location we're replacing
                if d.id == day.id and i == int(place_index):
                    continue
                visited_set.add(pl["name"].lower())
        except Exception as e:
            logger.warning(f"[replace_single_place_in_day] Error processing places_visited for day {d.id}: {e}")

    current_places = []
    try:
        current_places = json.loads(day.places_visited)
    except:
        current_places = []
    if int(place_index) < len(current_places):
        current_places.pop(int(place_index))

    new_place_name = suggest_one_new_place_gpt(itinerary, day, visited_set, user_observation)
    if new_place_name:
        reference_location = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
        latlng = get_place_coordinates(new_place_name, reference_location=reference_location, destination=itinerary.destination)
        if latlng[0] is not None:
            current_places.insert(int(place_index), {
                "name": new_place_name,
                "lat": latlng[0],
                "lng": latlng[1]
            })
        else:
            current_places.insert(int(place_index), {
                "name": new_place_name,
                "lat": None,
                "lng": None
            })

    weather_data = get_google_weather_forecast(day.date, itinerary.lat, itinerary.lng)

    raw_day_text = generate_day_text_gpt(itinerary, day, current_places, weather_info=weather_data)
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng, itinerary.destination)

    day.places_visited = json.dumps(current_places, ensure_ascii=False)
    day.generated_text = verified_text
    day.save(update_fields=["places_visited", "generated_text"])


def suggest_one_new_place_gpt(itinerary, day, visited_set, user_observation):
    visited_str = ", ".join(list(visited_set)) if visited_set else "None"
    day_number = day.day_number

    prompt = f"""
You are a travel planner specialized in {itinerary.destination}.
I need to replace a place that wasn't appealing.
Details:
- Trip day: {day_number}
- Interests: {itinerary.interests}
- Budget: {itinerary.budget}
- Travelers: {itinerary.travelers}
- Already visited places (don't repeat): {visited_str}
- User observation about the new place: {user_observation}

Suggest ONLY ONE place (just the name, no explanation) that is real, existing, and consistent with the above context.
Answer only with the place name, no additional text.
"""
    try:
        response = openai_chatcompletion_with_retry(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=6000,
            max_attempts=3
        )
        content = response.choices[0].message["content"].strip()
        return content
    except Exception as e:
        logger.error(f"[suggest_one_new_place_gpt] Failed to suggest a place: {e}")
        return ""


--------------------------------------------------------------------------------
File: templates/itineraries/pdf_template.html
--------------------------------------------------------------------------------
{% load static %}
{% load filters %}
{% load markdownify %}

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PDF - {{ itinerary.destination }}</title>
  <style>
    body {
      font-family: "Arial", sans-serif;
      color: #333;
      margin: 20px;
    }
    h1, h2, h3 {
      margin-bottom: 0.2em;
      color: #444;
    }
    .itinerary-info {
      margin-bottom: 20px;
      border-bottom: 1px solid #ccc;
      padding-bottom: 15px;
    }
    .day-section {
      margin-bottom: 30px;
      padding: 10px;
      border: 1px solid #ccc;
    }
    .day-section h2 {
      margin-top: 0;
      color: #555;
    }
    pre {
      white-space: pre-wrap;
      font-family: "Arial", sans-serif;
      font-size: 14px;
    }
    .map-img {
      margin-top: 10px;
      display: block;
      max-width: 100%;
      height: auto;
    }
    .text-block {
      white-space: pre-line;
      font-size: 15px;
      line-height: 1.6;
      margin-top: 1em;
    }
    a {
      color: #1a0dab;
      text-decoration: none;
      word-break: break-all; /* avoids line overflow */
    }
  </style>
</head>
<body>

  <h1>Itinerary: {{ itinerary.destination }}</h1>
  <div class="itinerary-info">
    <p><strong>Date:</strong> {{ itinerary.start_date }} → {{ itinerary.end_date }}</p>
    <p><strong>Budget:</strong> R$ {{ itinerary.budget }}</p>
    <p><strong>Travelers:</strong> {{ itinerary.travelers }}</p>
    <p><strong>Interests:</strong> {{ itinerary.interests }}</p>
    <p><strong>Food Preferences:</strong> {{ itinerary.food_preferences }}</p>
    <p><strong>Transport:</strong> {{ itinerary.transport_mode }}</p>
    <p><strong>Extras:</strong> {{ itinerary.extras }}</p>

    <h3>General Summary</h3>
    <div class="text-block">{{ itinerary.generated_text|markdownify }}</div>
  </div>

  {% for d in itinerary.days.all|dictsort:"day_number" %}
    <div class="day-section">
      <h2>Day {{ d.day_number }} - {{ d.date }}</h2>
      <div class="text-block">{{ d.generated_text|markdownify }}</div>
    </div>
  {% endfor %}

  {% if map_img_b64 %}
    <h3>🗺️ General Map</h3>
    <img class="map-img" src="{{ map_img_b64 }}" alt="Static Map">
  {% endif %}

</body>
</html>

--------------------------------------------------------------------------------

That’s all! All strings, labels, hints, and comments previously in Portuguese are now in English, while the code logic and structure remain unchanged.