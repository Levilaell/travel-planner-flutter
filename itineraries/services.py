import os
import json
import openai
import requests
from datetime import datetime
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_KEY')

#############################
# 1) Overview do itinerário
#############################

def generate_itinerary_overview(itinerary):
    prompt = f"""
Você é um planejador de viagens inteligente. Gere um **overview** geral sobre a viagem:

Destino: {itinerary.destination}
Data: {itinerary.start_date} a {itinerary.end_date}
Orçamento: {itinerary.budget}
Viajantes: {itinerary.travelers}
Interesses: {itinerary.interests}
Preferências Alimentares: {itinerary.food_preferences}
Extras: {itinerary.extras}
Modo de Transporte: {itinerary.transport_mode}
Locais de Interesse: {itinerary.interest_places}

A resposta deve ser um texto breve em português, destacando:
- Características gerais do destino
- Dicas iniciais
- Tom amigável
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.7
    )
    return response.choices[0].message["content"]


#############################
# 2) Sugerir lugares (GPT)
#############################

def suggest_places_gpt(itinerary, day_number, already_visited):
    visited_str = ", ".join(already_visited) if already_visited else "Nenhum"

    prompt = f"""
Você é um planejador de viagens especializado no destino {itinerary.destination}.
Para o dia {day_number} da viagem, considerando:
- Interesses: {itinerary.interests}
- Preferências Alimentares: {itinerary.food_preferences}
- Orçamento: {itinerary.budget}
- Viajantes: {itinerary.travelers}
- Locais já visitados em dias anteriores: {visited_str}

Gere uma lista (de 3 a 6) locais interessantes para visitar neste dia, incluindo pontos turísticos,
restaurantes, atrações culturais, etc. Sem repetir lugares já visitados.
Responda em formato JSON, assim:

[
  "Lugar 1",
  "Lugar 2",
  "Lugar 3"
]

Apenas retorne a lista, sem texto adicional.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.7
    )

    content = response.choices[0].message["content"]
    try:
        places_list = json.loads(content)
        places_list = [p.strip() for p in places_list if isinstance(p, str)]
        return places_list
    except:
        return []


#############################
# 3) Google Places: coordenadas
#############################

def get_place_coordinates(place_name, reference_location="48.8566,2.3522", radius=5000):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": place_name,
        "location": reference_location,
        "radius": radius,
        "key": settings.GOOGLEMAPS_KEY,
    }
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            return None, None
    except requests.RequestException:
        return None, None


#############################
# 4) Distance Matrix
#############################

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
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'OK':
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
    except:
        return None


#############################
# 5) Rota "ótima" (heurística)
#############################

def find_optimal_route(locations, distance_matrix):
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


#############################
# 6) Texto final do dia
#############################

def generate_day_text_gpt(itinerary, day, ordered_places, weather_info=None):
    date_formatted = day.date.strftime("%d de %B de %Y")
    day_title = f"Dia {day.day_number} - {date_formatted}"
    destination = itinerary.destination

    # Previsão de tempo simples (opcional)
    if weather_info and weather_info.get("main"):
        temp_min = round(weather_info["main"].get("temp_min", 0))
        temp_max = round(weather_info["main"].get("temp_max", 0))
        descriptions = [w["description"] for w in weather_info.get("weather", [])]
        conditions = " / ".join(descriptions)
        weather_str = f"{conditions}, entre {temp_min}°C e {temp_max}°C"
    else:
        weather_str = "Sem dados de clima"

    visited_names = [loc['name'] for loc in ordered_places]
    visited_str = ", ".join(visited_names) if visited_names else "Nenhum"

    # Prompt personalizado
    prompt = f"""
Você é um planejador de viagens inteligente e criativo.
Gere um roteiro detalhado para o dia, no formato abaixo:

{day_title}
📍 Roteiro Detalhado para um Dia em {destination}
📅 Data: {date_formatted}
🌤️ Previsão do Tempo: {weather_str}
🚗 Transporte Principal: {itinerary.transport_mode}
🍽️ Destaques Gastronômicos: (exemplos de comida típica)
📸 Locais Visitados: {visited_str}

Agora, para cada local abaixo (nesta ordem!), crie um bloco com:
- Horário (ex: 7h30 – Café da Manhã ...)
- Marcador '📍' + endereço (ex: '📍 Boulangerie X, 8 Rue ...')
- Pequeno texto explicativo.

Ordem de Locais a Visitar (não alterar!):
"""

    for i, name in enumerate(visited_names, start=1):
        prompt += f"{i}. {name}\n"

    prompt += """
No final, inclua uma 'DICA FINAL' ou 'OBSERVAÇÃO' sobre o destino.
Responda em português e mantenha um tom amigável.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.7
    )

    return response.choices[0].message["content"]


#############################
# 7) Verificar e inserir endereços
#############################

def verify_and_update_places(day_text, lat, lng):
    location_str = f"{lat},{lng}" if lat and lng else "48.8566,2.3522"
    lines = day_text.splitlines()
    new_lines = []

    for line in lines:
        if "📍" in line:
            place_candidate = line.split("📍", 1)[-1].strip()
            if not place_candidate:
                new_lines.append(line)
                continue

            place_data = search_place_in_google_maps(place_candidate, location=location_str)
            if place_data is None:
                not_found_msg = f"{line}\n⚠️ [AVISO] Não encontramos '{place_candidate}' no Google Places."
                new_lines.append(not_found_msg)
            else:
                address = place_data.get("formatted_address", "Endereço não encontrado")
                new_line = f"{line}\n(endereço verificado: {address})"
                new_lines.append(new_line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def search_place_in_google_maps(place_name, location="48.8566,2.3522", radius=5000):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": place_name,
        "location": location,
        "radius": radius,
        "key": settings.GOOGLEMAPS_KEY,
    }
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            return data["results"][0]
        else:
            return None
    except:
        return None


#############################
# 8) Fluxo principal de 1 dia
#############################

def plan_one_day_itinerary(itinerary, day, already_visited=None):
    """
    Retorna: (day_text, final_places_list)
      - day_text: string final gerada
      - final_places_list: lista com os lugares efetivamente usados (p/ evitar repetição)
    """
    if already_visited is None:
        already_visited = []

    # Passo 1: Sugerir lugares
    raw_places = suggest_places_gpt(itinerary, day.day_number, already_visited)
    if not raw_places:
        return ("Não foi possível encontrar locais para este dia.", [])

    # Filtro manual p/ remover duplicados e places já visitados
    lower_visited = [p.lower() for p in already_visited]
    filtered_places = []
    for p in raw_places:
        if p.lower() not in lower_visited and p not in filtered_places:
            filtered_places.append(p)

    if not filtered_places:
        return ("Todos os lugares sugeridos já foram visitados ou são duplicados.", [])

    # Passo 2: Obter lat/lng
    reference_location = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
    locations = []
    for place in filtered_places:
        latlng = get_place_coordinates(place, reference_location=reference_location)
        if latlng[0] is not None:
            locations.append({
                "name": place,
                "lat": latlng[0],
                "lng": latlng[1]
            })

    if not locations:
        return ("Não foi possível obter coordenadas para os locais sugeridos.", [])

    # Passo 3: Distâncias
    distance_matrix = build_distance_matrix(locations)
    if not distance_matrix:
        return ("Não foi possível calcular distâncias entre os locais.", [])

    # Passo 4: Rota
    route_indices = find_optimal_route(locations, distance_matrix)
    route_ordered = [locations[i] for i in route_indices]

    # Passo 5: Gera texto final
    weather_data = get_weather_info(itinerary.destination)
    raw_day_text = generate_day_text_gpt(itinerary, day, route_ordered, weather_info=weather_data)

    # Passo 6: Verificar endereços
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng)

    # Monta lista final de lugares confirmados
    final_place_names = [loc["name"] for loc in route_ordered]

    return (verified_text, final_place_names)


#############################
# 9) Outras utilidades
#############################

def get_weather_info(city_name):
    api_key = os.getenv('OPENWEATHERMAP_KEY')
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric',
        'lang': 'pt',
    }
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_cordinates_google_geocoding(address):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': settings.GOOGLEMAPS_KEY
    }
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    except (requests.RequestException, IndexError, KeyError):
        pass
    return None, None
