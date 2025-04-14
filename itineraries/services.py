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

# Configurando logs
logger = logging.getLogger(__name__)

# ========================================================
#                  Funções de utilidade
# ========================================================

def request_with_retry(url, params=None, max_attempts=3, timeout=60):
    """
    Função genérica para realizar requisições HTTP GET com até max_attempts tentativas.
    Em caso de falha, faz log de erro. Se não tiver sucesso, relança a exceção ao final.
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
                f"[request_with_retry] Tentativa {attempt+1}/{max_attempts} falhou: {e}. "
                f"URL: {url}, Params: {params}"
            )
            if attempt == max_attempts - 1:
                logger.error(f"[request_with_retry] Erro definitivo: {e}")
                raise
            # Opcional: adicionar um pequeno delay entre as tentativas
            time.sleep(2**attempt)


def openai_chatcompletion_with_retry(messages, model="gpt-4o-mini", temperature=0.8, max_attempts=3, max_tokens=6000):
    """
    Função genérica para chamadas ao OpenAI com até max_attempts tentativas.
    Registra logs de erro e relança a exceção se falhar todas as vezes.
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
                f"[openai_chatcompletion_with_retry] Tentativa {attempt+1}/{max_attempts} falhou: {e}"
            )
            if attempt == max_attempts - 1:
                logger.error(f"[openai_chatcompletion_with_retry] Erro definitivo: {e}")
                raise
            time.sleep(2**attempt)


def build_markers_json(itinerary):
    all_markers = []
    # Marcador principal: destino
    if itinerary.lat is not None and itinerary.lng is not None:
        all_markers.append({
            "name": itinerary.destination,
            "lat": float(itinerary.lat),
            "lng": float(itinerary.lng),
        })
    # Acrescenta marcadores dos locais visitados em cada dia
    for day in itinerary.days.all():
        if day.places_visited:
            try:
                places = json.loads(day.places_visited)
                if isinstance(places, list):
                    all_markers.extend(places)
            except Exception as e:
                logger.warning(f"[build_markers_json] Falha ao processar places_visited do dia {day.id}: {e}")
                continue
    return json.dumps(all_markers, ensure_ascii=False)

# ========================================================
#                  Views Principais
# ========================================================

@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            # 1) Criar itinerário
            itinerary = form.save(commit=False)
            itinerary.user = request.user
            selected_interests = request.POST.getlist('interests_list')
            itinerary.interests = ', '.join(selected_interests)
            itinerary.save()

            # 2) Coordenadas do destino principal
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            # 3) Texto IA (overview)
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

            # 4) Criar Days (um por data)
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
            # Form inválido => exibir erros
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

    # Usando nossa função de request com retry
    try:
        response = request_with_retry(map_url, params=None, max_attempts=3)
        if response and response.status_code == 200 and response.content:
            raw_image = base64.b64encode(response.content).decode('utf-8')
            map_img_b64 = f"data:image/png;base64,{raw_image}"
        else:
            logger.warning(f"[export_itinerary_pdf_view] Erro ou conteúdo vazio na imagem do mapa. status={response.status_code if response else 'N/A'}")
    except Exception as e:
        logger.error(f"[export_itinerary_pdf_view] Falha ao baixar a imagem do mapa: {e}")

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
#           Funções Principais de Planejamento
# ========================================================

def generate_itinerary_overview(itinerary):
    """
    Gera um overview usando GPT, com retries e logs em caso de erro.
    """
    prompt = f"""
Você é um planejador de viagens inteligente. Gere um **overview** geral sobre a viagem:

Destino: {itinerary.destination}
Data: {itinerary.start_date} a {itinerary.end_date}
Orçamento: {itinerary.budget}
Viajantes: {itinerary.travelers}
Interesses: {itinerary.interests}
Extras: {itinerary.extras}

A resposta deve ser no seguinte padrão (mantendo um tom amigável e coeso):

Viagem a Paris - Visão Geral

Prepare-se para uma experiência inesquecível na encantadora cidade de Paris, França, no dia 15 de abril de 2025! Com um orçamento de 2000 reais, você terá a oportunidade de explorar a rica cultura, a deliciosa gastronomia e os icônicos pontos turísticos que a capital francesa tem a oferecer. 

Sua jornada começará com a visita à famosa Torre Eiffel, onde poderá admirar a vista deslumbrante da cidade. Em seguida, não perca a chance de passear pelo charmoso bairro de Montmartre, conhecido por sua atmosfera artística e pelas lindas ruas de paralelepípedos. A Basílica de Sacré-Cœur, que se ergue majestosa no topo da colina, é uma parada obrigatória.

Para os amantes da arte, o Museu do Louvre é um verdadeiro paraíso, abrigando obras-primas como a Monalisa e a Vênus de Milo. Reserve um tempo para se perder nas suas galerias e desfrutar da impressionante arquitetura do edifício.

A gastronomia parisiense também merece destaque! Explore os bistrôs locais e experimente pratos tradicionais como croissants, quiches e, claro, macarons. Uma refeição em um café à beira do Sena pode ser uma forma perfeita de relaxar e absorver a atmosfera vibrante da cidade.

Além disso, considere um passeio de barco pelo rio Sena, proporcionando uma perspectiva única dos monumentos e pontes de Paris. À noite, o espetáculo da cidade iluminada é simplesmente mágico e cria memórias que durarão para sempre.

Com um itinerário bem planejado e um olhar atento para os detalhes, sua viagem a Paris será uma combinação perfeita de exploração, cultura e sabor. Prepare-se para descobrir os encantos da Cidade Luz!
"""

    # Chamada OpenAI com retry
    response = openai_chatcompletion_with_retry(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=6000,
        max_attempts=3
    )
    return response.choices[0].message["content"]


def suggest_places_gpt(itinerary, day_number, already_visited):
    visited_str = ", ".join(already_visited) if already_visited else "Nenhum"

    prompt = f"""
Você é um planejador de viagens especializado no destino {itinerary.destination}.
Para o dia {day_number} da viagem, considerando:
- Interesses: {itinerary.interests}
- Orçamento: {itinerary.budget}
- Viajantes: {itinerary.travelers}
- Locais já visitados em dias anteriores: {visited_str}

Gere uma lista de 6 locais interessantes e REAIS para visitar neste dia (desde a manhã até a noite, considerando lugar para almoçar em horário de almoço, pontos turísticos de tarde, etc), SEM repetir lugares já visitados.
Certifique-se de que os locais sugeridos existam de fato, que sejam facilmente verificados no Google Maps e que tenham uma logística coesa para o turista.

Responda em formato JSON, assim:

[
  "Local 1",
  "Local 2",
  "Local 3",
  "Local 4",
  "Local 5",
  "Local 6"
]

Apenas retorne a lista, sem texto adicional.

Obs: Cuidado para não indicar lugares perigosos, como favelas, etc.
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
        logger.error(f"[suggest_places_gpt] Erro ao fazer parse do JSON retornado pelo GPT: {e}")
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
                f"[get_place_coordinates] Nenhum resultado para '{query}'. Status={data.get('status')}"
            )
            return None, None
    except Exception as e:
        logger.error(f"[get_place_coordinates] Erro ao obter coordenadas: {e}")
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
        logger.error(f"[build_distance_matrix] Erro ao construir distance matrix: {e}")
        return None


def find_optimal_route(locations, distance_matrix):
    """
    Heurística simples: inicia no primeiro local e segue sempre para o mais próximo.
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


def generate_day_text_gpt(itinerary, day, ordered_places, weather_info=None):
    date_formatted = day.date.strftime("%d de %B de %Y")
    day_title = f"Dia {day.day_number} - {date_formatted}"
    destination = itinerary.destination

    if weather_info.get("error"):
        weather_str = "Erro ao obter clima"
    elif weather_info.get("warning"):
        weather_str = weather_info["warning"]
    else:
        temp_min_raw = weather_info.get("temp_min")
        temp_max_raw = weather_info.get("temp_max")
        temp_min = round(temp_min_raw) if isinstance(temp_min_raw, (int, float)) else "N/A"
        temp_max = round(temp_max_raw) if isinstance(temp_max_raw, (int, float)) else "N/A"
        condition = weather_info.get("conditions", "Desconhecido")
        desc = weather_info.get("description", "")
        weather_str = f"{condition} ({desc}), entre {temp_min}°C e {temp_max}°C"


    visited_names = [loc['name'] for loc in ordered_places]
    visited_str = ", ".join(visited_names) if visited_names else "Nenhum"

    prompt = f"""
Você é um planejador de viagens inteligente e criativo.
Gere um roteiro detalhado para o dia, no seguinte formato:

{day_title}
📍 Roteiro Detalhado para um Dia em {destination}
📅 Data: {date_formatted}
🌤️ Previsão do Tempo: {weather_str}
🍽️ Destaques Gastronômicos: (exemplos de comida típica)
📸 Locais Visitados: {visited_str}

Agora, para cada local abaixo (mantendo a ordem exata listada), crie um bloco com:
- Horário (ex: 7h30 – Café da Manhã ...)
- Marcador "📍" seguido do nome e endereço verificado
- Texto explicativo completo sobre o local, destacando o que fazer, pontos de interesse e informações relevantes.
NÃO altere ou confunda os nomes dos locais listados.

Ordem de Locais a Visitar:
"""
    for i, name in enumerate(visited_names, start=1):
        prompt += f"{i}. {name}\n"

    prompt += """
No final, inclua uma 'DICA FINAL' sobre o destino.
Responda em português mantendo um tom amigável.
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
                not_found_msg = f"{line}\n⚠️ [AVISO] Não encontramos '{place_candidate}' no Google Places."
                new_lines.append(not_found_msg)
            else:
                address = place_data.get("formatted_address", "Endereço não encontrado")
                encoded_addr = quote(address)
                new_line = (
                    f"{line}\n"
                    f"(endereço verificado: {address})\n"
                    f"[Ver no Google Maps](https://www.google.com/maps/search/?api=1&query={encoded_addr})"
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
                f"[search_place_in_google_maps] Nenhum resultado para '{query}'. Status={data.get('status')}"
            )
            return None
    except Exception as e:
        logger.error(f"[search_place_in_google_maps] Erro ao pesquisar lugar: {e}")
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
        logger.warning("[plan_one_day_itinerary] Não foi possível encontrar locais após 5 tentativas.")
        return ("Não foi possível encontrar locais para este dia após 5 tentativas.", [])

    lower_visited = [p.lower() for p in already_visited]
    filtered_places = []
    for p in raw_places:
        if p.lower() not in lower_visited and p not in filtered_places:
            filtered_places.append(p)

    if not filtered_places:
        logger.warning("[plan_one_day_itinerary] Todos os lugares sugeridos eram repetidos.")
        return ("Todos os lugares sugeridos já foram visitados ou são duplicados.", [])

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
        logger.warning("[plan_one_day_itinerary] Nenhuma coordenada foi obtida para os locais sugeridos.")
        return ("Não foi possível obter coordenadas para os locais sugeridos.", [])

    distance_matrix = build_distance_matrix(locations)
    if not distance_matrix:
        logger.warning("[plan_one_day_itinerary] Falha ao calcular matriz de distâncias.")
        return ("Não foi possível calcular distâncias entre os locais.", [])

    route_indices = find_optimal_route(locations, distance_matrix)
    route_ordered = [locations[i] for i in route_indices]

    # ✅ Substituição aqui: previsão do tempo do Google baseada na data e localização
    weather_data = get_google_weather_forecast(day.date, itinerary.lat, itinerary.lng)

    raw_day_text = generate_day_text_gpt(itinerary, day, route_ordered, weather_info=weather_data)
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng, itinerary.destination)

    final_place_names = [loc["name"] for loc in route_ordered]

    day.places_visited = json.dumps(route_ordered, ensure_ascii=False)
    day.generated_text = verified_text
    day.save(update_fields=["places_visited", "generated_text"])

    return (verified_text, final_place_names)



def get_google_weather_forecast(target_date, lat, lng):
    """
    Consulta a Google Weather API v1 (forecast.days:lookup) e retorna a previsão para a data exata, se disponível.
    """
    try:
        url = "https://weather.googleapis.com/v1/forecast/days:lookup"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "days": 10,  # busca até 10 dias à frente
            "languageCode": "pt-BR",
            "unitsSystem": "METRIC",
            "key": settings.GOOGLEMAPS_KEY,
        }

        response = request_with_retry(url, params=params, max_attempts=3)
        data = response.json()
        logger.debug(f"[get_google_weather_forecast] Dados retornados: {data}")

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
                # Use a descrição presente dentro de "description" para a condição
                condition = weather_condition.get("description", {}).get("text", "Desconhecido")
                # Para as temperaturas, use a chave "degrees"
                temp_max = day.get("maxTemperature", {}).get("degrees")
                temp_min = day.get("minTemperature", {}).get("degrees")

                return {
                    "date": forecast_date.isoformat(),
                    "conditions": condition,
                    "description": "",  # campo não utilizado separadamente
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                }

        return {"warning": "Previsão não disponível para esta data (fora dos próximos 10 dias)."}
    except Exception as e:
        logger.error(f"[get_google_weather_forecast] Erro ao buscar previsão: {e}")
        return {"error": "Erro ao buscar previsão do tempo"}


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
        logger.error(f"[get_cordinates_google_geocoding] Erro ao obter coordenadas por geocoding: {e}")
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
                # Ignora o local exato que estamos substituindo
                if d.id == day.id and i == int(place_index):
                    continue
                visited_set.add(pl["name"].lower())
        except Exception as e:
            logger.warning(f"[replace_single_place_in_day] Erro ao processar places_visited do dia {d.id}: {e}")

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
    visited_str = ", ".join(list(visited_set)) if visited_set else "Nenhum"
    day_number = day.day_number

    prompt = f"""
Você é um planejador de viagens especializado em {itinerary.destination}.
Preciso substituir um local que não agradou.
Detalhes:
- Dia da viagem: {day_number}
- Interesses: {itinerary.interests}
- Orçamento: {itinerary.budget}
- Viajantes: {itinerary.travelers}
- Locais já visitados (não repetir): {visited_str}
- Observação do usuário sobre o novo local: {user_observation}

Sugira APENAS UM lugar (apenas o nome, sem explicação) que seja real, existente e coerente com o contexto acima.
Responda apenas com o nome do lugar, sem texto adicional.
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
        logger.error(f"[suggest_one_new_place_gpt] Falha ao sugerir um lugar: {e}")
        return ""

