import openai
import os
from dotenv import load_dotenv

load_dotenv()

def gpt_to_markdown(prompt, filename="output.md", api_key=os.getenv('OPENAI_KEY')):

    openai.api_key = api_key
    
    try:
        # Fazer a requisição para a API do GPT
        response = openai.ChatCompletion.create(
            model="o3",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=9000,
        )
        
        # Extrair o texto da resposta
        gpt_response = response['choices'][0]['message']['content']
        
        # Salvar no arquivo Markdown
        with open(filename, "w", encoding="utf-8") as file:
            file.write(gpt_response)
        
        print(f"Resposta salva com sucesso em {filename}!")
    
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}")

prompt = '''

{# templates/itineraries/dashboard.html #}
{% extends "base.html" %}
{% load static %}
{% load markdownify %}

{% block content %}
<div class="container-fluid" style="background-color:#2C2C2E">
  <div class="row full-height-row">

    {# =====================  PAINEL ESQUERDO – Formulário  ===================== #}
    <div class="col-md-4 left-panel d-flex align-items-start flex-column p-4">
      <h3 class="text-white">Criar Novo Itinerário</h3>

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
      
        <!-- Destino -->
        <div class="mb-3">
          <label for="destination" class="form-label">Destino *</label>
          <input type="text" class="form-control" id="destination" name="destination"
                 placeholder="Ex: Natal, Brasil" required>
          <div class="form-text">Informe uma cidade, país ou região que deseja visitar.</div>
        </div>
      
        <!-- Datas -->
        <div class="row g-2 mb-3">
          <div class="col">
            <label for="startDate" class="form-label">Data de Início *</label>
            <input type="date" class="form-control" id="startDate" name="start_date" required>
          </div>
          <div class="col">
            <label for="endDate" class="form-label">Data de Término *</label>
            <input type="date" class="form-control" id="endDate" name="end_date" required>
          </div>
        </div>
      
        <!-- Orçamento -->
        <div class="mb-3">
          <label for="budget" class="form-label">Orçamento Total (R$)</label>
          <input type="number" class="form-control" id="budget" name="budget" step="0.01"
                 placeholder="Ex: 2000">
          <div class="form-text">Quanto pretende gastar no total da viagem?</div>
        </div>
      
        <!-- Nº de viajantes -->
        <div class="mb-3">
          <label for="travelers" class="form-label">Número de Viajantes</label>
          <input type="number" class="form-control" id="travelers" name="travelers" min="1" value="1">
        </div>
      
        <!-- Interesses -->
        <div class="mb-3">
          <label class="form-label d-block">Interesses na Viagem</label>
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
          <div class="form-text">Você pode escolher vários temas que deseja focar durante a viagem.</div>
        </div>
    
      
        
      
        <!-- Campo extra opcional -->
        <div class="mb-3">
          <label for="extras" class="form-label">Algo que devemos considerar?</label>
          <textarea class="form-control" id="extras" name="extras" rows="3"
                    placeholder="Ex: Acessibilidade, evitar praias, hotéis 4 estrelas, etc."
                    style="::placeholder { color: white; }"></textarea>
        </div>
      
        <div class="text-center">
          <button type="submit" class="btn btn-primary w-100 btn-lg shadow-sm">Gerar Roteiro</button>
        </div>
      </form>
      
    </div>

    {# =====================  PAINEL DIREITO – Itinerários  ===================== #}
    <div class="col-md-8 px-3 right-panel">
      <h3 class="mb-4 pt-3 text-white">Meus Itinerários</h3>

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
                    Ver Detalhes
                  </button>
                  <a href="{% url 'export_itinerary_pdf' it.id %}"
                     class="btn btn-sm btn-outline-light">Baixar PDF</a>
                  <button type="submit" class="btn btn-sm btn-outline-danger"
                          onclick="return confirm('Tem certeza que deseja excluir este itinerário?')">
                    Excluir
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>

        {# ----------  MODAL DE DETALHES  ---------- #}
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
                      Dia {{ d.day_number }}
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
                      {# opcional: fallback, pode deixar ou remover #}
                      <div class="places-photo-gallery" id="photos-for-day-{{ d.id }}"></div>


                      {% if d.places_visited %}
                      <div class="mt-3">
                        <strong>Lugares (Editar individualmente):</strong>
                        <div id="day-places-{{ d.id }}" data-places='{{ d.places_visited|safe }}'></div>

                        <script>
                          (function(){
                            const container = document.getElementById("day-places-{{ d.id }}");
                            const rawData = `{{ d.places_visited|safe }}`;
                            try {
                              const arr = JSON.parse(rawData);
                              if (Array.isArray(arr)) {
                                let html = "";
                                arr.forEach((p, idx) => {
                                  const name = p.name || "Local desconhecido";
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
                        data-bs-dismiss="modal">Fechar</button>
              </div>
            </div>
          </div>
        </div>
        {# ----------  /MODAL DE DETALHES  ---------- #}
        {% endfor %}
      </div>
      {% else %}
        <p class="text-white">Nenhum itinerário criado ainda...</p>
      {% endif %}
    </div>
  </div>
</div>

{# ===================  MODAL TROCA DE LUGAR  =================== #}
<div class="modal fade" id="replaceModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered" style="color:#fff;">
    <div class="modal-content" style="background-color:#202023;">
      <div class="modal-header">
        <h5 class="modal-title">Trocar Lugar</h5>
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
              Observação / Preferência para o novo local
            </label>
            <textarea class="form-control" id="replaceObservation" name="observation"
                      rows="3" placeholder="Ex: Quero algo mais central, sem repetir lugares ou com comida típica"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-light"
                  data-bs-dismiss="modal">Cancelar</button>
          <button type="submit" class="btn btn-primary">Confirmar Troca</button>
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
    <p id="loadingText" class="mt-3 fs-5 text-white">Preparando roteiro...</p>
  </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
/* ---------- UTIL ---------- */
function normalizeText(str) {
  return (str||"")
    .normalize("NFD")            // separa acentos
    .replace(/[\u0300-\u036f]/g, "")  // remove acentos
    .replace(/[^\w\s]/g, " ")    // remove pontuação
    .toLowerCase()
    .trim();
}

/* ---------- FOTO ---------- */
const photoCache = new Map();            // chave = query, valor = url

function textMatchesPlace(elText, placeName) {
  const a = normalizeText(elText);
  const b = normalizeText(placeName);
  return a.includes(b);
}

function insertPhotoInGallery(dayId, placeName, photoUrl) {
  const listContainer = document.getElementById(`day-places-${dayId}`);
  if (!listContainer) return;
  // cada filho <div> é um lugar (você montou assim lá no template)
  const items = Array.from(listContainer.children);
  for (let item of items) {
    if (normalizeText(item.textContent).includes(normalizeText(placeName))) {
      item.insertAdjacentHTML(
        "beforeend",
        `<img src="${photoUrl}" class="place-photo img-fluid rounded mt-2" 
              alt="Foto de ${placeName}" />`
      );
      return;
    }
  }
}

function fetchPhotosForPlaces(dayId, placesJson, destination) {
  let places;
  try { places = JSON.parse(placesJson); } catch { return; }

  places.forEach(place => {
    const query = `${place.name}, ${destination}`;
    const cacheKey = query.toLowerCase();

    if (photoCache.has(cacheKey)) {
      return insertPhotoInGallery(dayId, place.name, photoCache.get(cacheKey));

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

        if (ref) {
          photoUrl = "{% url 'proxy_google_photo' %}?photo_ref=" + ref;
        } else {
          photoUrl =
            `https://source.unsplash.com/600x400/?${encodeURIComponent(place.name + ' ' + destination)}`;
        }

        photoCache.set(cacheKey, photoUrl);
        insertPhotoInGallery(dayId, place.name, photoUrl);
      })
      .catch(err => console.error("Foto:", err));
  });
}
</script>




<script>
/* ---------- LOADER / FORM ---------- */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("itineraryForm");
  const overlay = document.getElementById("loadingOverlay");
  const bar = document.getElementById("loadingBar");
  const text = document.getElementById("loadingText");

  const msgs = [
    "Analisando destino...",
    "Selecionando melhores locais...",
    "Otimizando rotas...",
    "Planejando experiências únicas...",
    "Gerando roteiro perfeito..."
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

  /* fotos + mapa quando o usuário abrir um modal */
  document.querySelectorAll(".modal.fade").forEach(modal => {
    modal.addEventListener("shown.bs.modal", () => {
      const id = modal.getAttribute("id");
      if (!id?.startsWith("modalIt")) return;

      const itinId = id.replace("modalIt", "");
      initMultipleMarkers(itinId);

      /* Fotos */
      modal.querySelectorAll('[id^="day-places-"]').forEach(div => {
        const dayId = div.id.replace("day-places-", "");
        const raw = div.dataset.places;
        if (raw) {
          const destination =
            modal.querySelector(".modal-title")?.textContent.split(" - ")[0] || "";
            setTimeout(() => {
              requestAnimationFrame(() => {
                fetchPhotosForPlaces(dayId, raw, destination);
              });
            }, 0);
            
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

/* auto‑abrir modal recém‑criado (mantido) */
document.addEventListener("DOMContentLoaded", () => {
  const autoId = "{{ new_itinerary_id|default:'' }}";
  if (autoId) new bootstrap.Modal(document.getElementById("modalIt" + autoId)).show();

  /* preencher campos ocultos p/ troca de lugar */
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


# views.py

import base64
import json
import logging
import os
import time
import urllib.parse
from datetime import timedelta
from urllib.parse import quote

import openai
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from dotenv import load_dotenv
from weasyprint import HTML

from .forms import ItineraryForm, ReviewForm
from .models import Day, Itinerary
from .services import (generate_itinerary_overview,
                       get_cordinates_google_geocoding, plan_one_day_itinerary,
                       replace_single_place_in_day)

load_dotenv()
openai.api_key = os.getenv('OPENAI_KEY')

logger = logging.getLogger(__name__)


def build_markers_json(itinerary):
    """
    Gera um JSON com todos os marcadores (destino principal + locais visitados).
    Se estiver vazio, o JS do front-end vai avisar "Nenhum marcador".
    """
    all_markers = []

    # Marcador principal: destino
    if itinerary.lat is not None and itinerary.lng is not None:
        try:
            all_markers.append({
                "name": itinerary.destination,
                "lat": float(itinerary.lat),
                "lng": float(itinerary.lng),
            })
        except (TypeError, ValueError) as e:
            logger.warning(
                f"[build_markers_json] Falha ao converter lat/lng do itinerário {itinerary.id}: {e}"
            )

    # Acrescenta marcadores dos locais visitados em cada dia
    for day in itinerary.days.all():
        if day.places_visited:
            try:
                places = json.loads(day.places_visited)
                if isinstance(places, list):
                    for p in places:
                        # Verifica se p tem lat/lng
                        if "lat" in p and "lng" in p:
                            all_markers.append(p)
                        else:
                            logger.info(f"[build_markers_json] Local sem coordenadas, day={day.id}, place={p}")
                else:
                    logger.info(f"[build_markers_json] places_visited não é lista, day={day.id}")
            except Exception as ex:
                logger.warning(
                    f"[build_markers_json] Erro ao processar JSON places_visited do dia {day.id}: {ex}"
                )

    logger.debug(f"[build_markers_json] Itinerário={itinerary.id}, total de marcadores={len(all_markers)}")
    return json.dumps(all_markers, ensure_ascii=False)


@login_required
def dashboard_view(request):
    interests = ["Cultura", "Gastronomia", "Aventura", "Natureza", "Compras", "História", "Romance"]

    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            itinerary = form.save(commit=False)
            itinerary.user = request.user
            selected_interests = request.POST.getlist('interests_list')
            itinerary.interests = ', '.join(selected_interests)
            itinerary.save()

            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

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
            itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')
            for it in itineraries:
                it.markers_json = build_markers_json(it)
            return render(request, 'itineraries/dashboard.html', {
                'form': form,
                'itineraries': itineraries,
                'googlemaps_key': settings.GOOGLEMAPS_KEY,
                'interests': interests,
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
            'interests': interests,
        })


@login_required
def delete_itinerary_view(request, pk):
    if request.method == 'POST':
        itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
        logger.info(f"[delete_itinerary_view] Excluindo itinerário ID={pk}")
        itinerary.delete()
        return redirect('dashboard')


@login_required
def export_itinerary_pdf_view(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    logger.info(f"[export_itinerary_pdf_view] Exportando PDF para itinerário ID={pk}")

    map_img_b64 = None
    markers_list = []

    # Monta lista de marcadores
    if itinerary.lat and itinerary.lng:
        try:
            markers_list.append({
                "name": itinerary.destination,
                "lat": float(itinerary.lat),
                "lng": float(itinerary.lng),
            })
        except (ValueError, TypeError) as e:
            logger.warning(f"[export_itinerary_pdf_view] Falha ao converter lat/lng: {e}")

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
                            logger.warning(f"[export_itinerary_pdf_view] Erro ao extrair lat/lng de place: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"[export_itinerary_pdf_view] JSONDecodeError ao processar places_visited: {e}")

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

    # Download do mapa para incluir no PDF
    try:
        response = requests.get(map_url, timeout=10)
        if response.status_code == 200 and response.content:
            raw_image = base64.b64encode(response.content).decode('utf-8')
            map_img_b64 = f"data:image/png;base64,{raw_image}"
        else:
            logger.warning(f"[export_itinerary_pdf_view] Erro ao baixar mapa. code={response.status_code}")
    except Exception as e:
        logger.error(f"[export_itinerary_pdf_view] Exceção ao baixar mapa: {e}")

    # Renderiza template PDF
    html_string = render_to_string('itineraries/pdf_template.html', {
        'itinerary': itinerary,
        'map_img_b64': map_img_b64,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Itinerario_{itinerary.destination}.pdf"
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
            logger.info(f"[add_review_view] Nova review para itinerário {pk}")
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
        logger.info(f"[replace_place_view] Substituindo lugar do dia {day_id}, place_index={place_index}")
        replace_single_place_in_day(day, place_index, observation)
        return redirect(f"{reverse('dashboard')}?new_itinerary_id={itinerary.id}")

    return redirect('dashboard')



def proxy_google_places(request):
    encoded_url = request.GET.get("url")
    if not encoded_url or "maps.googleapis.com/maps/api/place" not in encoded_url:
        return JsonResponse({"error": "URL inválida ou ausente"}, status=400)

    # Decodifica a URL para remover a duplo codificação
    url = urllib.parse.unquote(encoded_url)
    try:
        response = requests.get(url, timeout=10)
        return JsonResponse(response.json(), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def google_photo_proxy(request):
    photo_ref = request.GET.get("photo_ref")
    if not photo_ref:
        return HttpResponse("Parâmetro ausente", status=400)

    url = f"https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "photoreference": photo_ref,
        "maxwidth": 600,
        "key": settings.GOOGLEMAPS_KEY,
    }

    try:
        response = requests.get(url, params=params, stream=True)
        if response.status_code == 200:
            return HttpResponse(response.content, content_type=response.headers.get("Content-Type"))
        return HttpResponse("Erro ao buscar imagem", status=500)
    except Exception as e:
        return HttpResponse(f"Erro interno: {e}", status=500)

Gpt, as imagens estão sendo inseridas após seu nome na parte que dá opção de mudar os lugares, mas preciso que elas sejam inseridas após a descrição do lugar. Exemplo:

9h00 – Praia de Ponta Negra

📍 Praia de Ponta Negra - Ponta Negra, Natal - RN
(endereço verificado: Ponta Negra, Natal - State of Rio Grande do Norte, Brazil)
Ver no Google Maps
Após o café, dirija-se à famosa Praia de Ponta Negra. Este cartão-postal de Natal é conhecido por suas águas quentes e calmas, além da vibrante faixa de areia. Você pode relaxar sob um guarda-sol, nadar no mar ou até mesmo aproveitar para fazer uma caminhada pela orla. Não se esqueça de tirar fotos do icônico Morro do Careca ao fundo!

[Foto da praia da ponta negra]

11h00 – Morro do Careca

📍 Morro do Careca - Praia de Ponta Negra, Natal - RN
(endereço verificado: Praia de Ponta Negra s/n - Ponta Negra, RN, 59090-210, Brazil)
Ver no Google Maps
Caminhe ao longo da praia até chegar ao Morro do Careca, uma das mais famosas dunas do Brasil. É um local emblemático e um excelente ponto para fotos. Embora não seja permitido subir a duna, você pode apreciar a beleza natural ao redor e aprender mais sobre a importância ambiental do lugar. Aproveite a brisa do mar e a vista deslumbrante!

[Foto do morro do careca]

O que mudar e onde fazer as mudanças?














'''


gpt_to_markdown(prompt, filename="markdown_explanation.md", api_key=os.getenv('OPENAI_KEY'))