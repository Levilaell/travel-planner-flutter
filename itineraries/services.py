# services.py

import json
import os
from datetime import datetime

import openai
import requests
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

A resposta deve ser no seguinte padrão:

Viagem a Paris - Visão Geral

Bonjour! Prepare-se para uma viagem encantadora à Cidade Luz, Paris, em 25 de março de 2025. Esta cidade, conhecida por sua rica história, arquitetura deslumbrante e cultura vibrante, certamente proporcionará uma experiência inesquecível.

Características Gerais do Destino:
Paris é famosa por seus icônicos pontos turísticos, como a Torre Eiffel, o Museu do Louvre e a Catedral de Notre-Dame. A cidade oferece uma mistura de arte, moda e gastronomia, com charmosos cafés e boulangeries a cada esquina. Na primavera, Paris floresce com uma beleza especial, tornando seus parques e jardins ainda mais encantadores para passeios relaxantes.

Com apenas um dia, faça uma lista dos locais principais que deseja visitar e organize seu tempo para aproveitar ao máximo. Considere começar cedo para evitar multidões.

Embora Paris seja uma cidade caminhável, usar transporte público ou dirigir pode ser útil para cobrir mais locais em menos tempo. Lembre-se de planejar rotas de estacionamento, pois a cidade pode ser desafiadora para motoristas.

Com um orçamento de 2000, você terá flexibilidade para desfrutar de algumas das melhores experiências gastronômicas e culturais que Paris oferece. Considere reservar ingressos para atrações com antecedência para economizar tempo e dinheiro.

Esperamos que você tenha uma viagem maravilhosa, cheia de descobertas e momentos inesquecíveis. Aproveite cada instante e absorva toda a beleza e charme que Paris tem a oferecer. Bon voyage!
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000,
        temperature=0.8
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
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000,
        temperature=0.8
    )

    content = response.choices[0].message["content"]
    try:
        # Aqui, como está no Python, precisamos interpretar a resposta
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
# 6) Texto final do dia (GPT)
#############################

def generate_day_text_gpt(itinerary, day, ordered_places, weather_info=None):
    date_formatted = day.date.strftime("%d de %B de %Y")
    day_title = f"Dia {day.day_number} - {date_formatted}"
    destination = itinerary.destination

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
- Texto completo explicativo, falando sobre o lugar, o que fazer e tudo mais.

Padrão de resposta:

7h30 – Café da Manhã

📍 Boulangerie Poilâne, 8 Rue du Cherche-Midi
(endereço verificado: 8 Rue du Cherche-Midi, 75006 Paris, France)
Comece o seu dia em Paris com um delicioso café da manhã na famosa Boulangerie Poilâne. Experimente um croissant fresco ou uma fatia de pão de centeio, acompanhado por um café expresso. Este local é conhecido por suas receitas tradicionais e ingredientes de alta qualidade, tornando-se uma excelente escolha para se energizar antes de um dia cheio de turismo.


Ordem de Locais a Visitar (não alterar!):
"""

    for i, name in enumerate(visited_names, start=1):
        prompt += f"{i}. {name}\n"

    prompt += """
No final, inclua uma 'DICA FINAL' ou 'OBSERVAÇÃO' sobre o destino.
Responda em português e mantenha um tom amigável.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000,
        temperature=0.8
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
    if already_visited is None:
        already_visited = []

    # -------------------------------------------
    # 1) Tentar Sugerir lugares (GPT) até 5 vezes
    # -------------------------------------------
    max_attempts = 5
    raw_places = []
    for attempt in range(1, max_attempts + 1):
        raw_places = suggest_places_gpt(itinerary, day.day_number, already_visited)
        if raw_places:  # Se não for vazio, ok
            break

    if not raw_places:
        return ("Não foi possível encontrar locais para este dia após 5 tentativas.", [])

    # 2) Filtro manual p/ remover duplicados e places já visitados
    lower_visited = [p.lower() for p in already_visited]
    filtered_places = []
    for p in raw_places:
        if p.lower() not in lower_visited and p not in filtered_places:
            filtered_places.append(p)

    if not filtered_places:
        return ("Todos os lugares sugeridos já foram visitados ou são duplicados.", [])

    # 3) Obter lat/lng
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

    # 4) Distâncias
    distance_matrix = build_distance_matrix(locations)
    if not distance_matrix:
        return ("Não foi possível calcular distâncias entre os locais.", [])

    # 5) Rota
    route_indices = find_optimal_route(locations, distance_matrix)
    route_ordered = [locations[i] for i in route_indices]

    # 6) Gera texto final
    weather_data = get_weather_info(itinerary.destination)
    raw_day_text = generate_day_text_gpt(itinerary, day, route_ordered, weather_info=weather_data)

    # 7) Verificar endereços
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng)

    # Monta lista final de nomes confirmados
    final_place_names = [loc["name"] for loc in route_ordered]

    # SALVA a lista de lugares (com lat/lng) no campo places_visited do Day (JSON serializado)
    day.places_visited = json.dumps(route_ordered, ensure_ascii=False)
    day.generated_text = verified_text
    day.save(update_fields=["places_visited", "generated_text"])

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


################################################
# 10) Trocar um lugar específico
################################################

def build_markers_json_for_day_replacement(day):
    """
    Recria markers com base nos lugares do day.
    """
    all_markers = []
    try:
        if day.places_visited:
            places = json.loads(day.places_visited)
            all_markers.extend(places)
    except:
        pass
    return json.dumps(all_markers, ensure_ascii=False)


def replace_single_place_in_day(day, place_index, user_observation):
    """
    Tenta substituir somente UM local do day por outro,
    mantendo todo o resto.
    - Evita duplicar ou repetir lugares (considerando days anteriores e o dia atual).
    - Faz nova chamada GPT p/ 1 sugestão, considerando a observation do usuário.
    - Atualiza places_visited e re-regenera day.generated_text no final.
    """
    itinerary = day.itinerary
    # 1) Já visitados: todos os dias anteriores + todos do dia atual (exceto o place a remover)
    all_days = itinerary.days.all().order_by('day_number')
    visited_set = set()

    for d in all_days:
        if not d.places_visited:
            continue
        try:
            arr = json.loads(d.places_visited)
            for i, pl in enumerate(arr):
                # Se for o dia e o index que vamos remover, não conta como visited
                if d.id == day.id and i == int(place_index):
                    continue
                visited_set.add(pl["name"].lower())
        except:
            pass

    # remove do day
    current_places = []
    try:
        current_places = json.loads(day.places_visited)
    except:
        current_places = []
    if int(place_index) < len(current_places):
        current_places.pop(int(place_index))

    # 2) Chamar GPT para sugerir UM único lugar substituto
    new_place_name = suggest_one_new_place_gpt(itinerary, day, visited_set, user_observation)
    if not new_place_name:
        # Caso não consiga, nada é alterado
        # (poderíamos inserir "Local indisponível" mas deixamos vazio)
        pass
    else:
        # Obter lat/lng
        reference_location = f"{itinerary.lat},{itinerary.lng}" if itinerary.lat and itinerary.lng else "48.8566,2.3522"
        latlng = get_place_coordinates(new_place_name, reference_location=reference_location)
        if latlng[0] is not None:
            current_places.insert(int(place_index), {
                "name": new_place_name,
                "lat": latlng[0],
                "lng": latlng[1]
            })
        else:
            # Não conseguiu achar lat/lng: reinserir mesmo assim, mas sem coords
            current_places.insert(int(place_index), {
                "name": new_place_name,
                "lat": None,
                "lng": None
            })

    # 3) Re-gerar o texto do dia
    # Montar route_ordered com base na ordem atual (não mexemos nas posições)
    route_ordered = current_places

    weather_data = get_weather_info(itinerary.destination)
    raw_day_text = generate_day_text_gpt(itinerary, day, route_ordered, weather_info=weather_data)
    verified_text = verify_and_update_places(raw_day_text, itinerary.lat, itinerary.lng)

    # 4) Persistir
    day.places_visited = json.dumps(route_ordered, ensure_ascii=False)
    day.generated_text = verified_text
    day.save(update_fields=["places_visited", "generated_text"])


def suggest_one_new_place_gpt(itinerary, day, visited_set, user_observation):
    """
    Chama GPT para sugerir apenas 1 local substituto,
    evitando repetição de 'visited_set'.
    """
    visited_str = ", ".join(list(visited_set)) if visited_set else "Nenhum"
    day_number = day.day_number

    # Prompt adicional. Não estamos alterando os prompts anteriores;
    # apenas adicionamos este para a troca de lugar.
    prompt = f"""
Você é um planejador de viagens especializado em {itinerary.destination}.
Preciso substituir um único local que não agradou.
Aqui estão detalhes:

Dia da viagem: {day_number}
Interesses: {itinerary.interests}
Preferências Alimentares: {itinerary.food_preferences}
Orçamento: {itinerary.budget}
Viajantes: {itinerary.travelers}
Locais já visitados (não repetir): {visited_str}

Observação do usuário sobre o novo local: {user_observation}

Sugira APENAS UM lugar (apenas o nome, sem explicação), que seja coerente com esse contexto.
Responda apenas com o nome do lugar, sem texto adicional.

Padrão de resposta para cada lugar:

7h30 – Café da Manhã

📍 Boulangerie Poilâne, 8 Rue du Cherche-Midi
(endereço verificado: 8 Rue du Cherche-Midi, 75006 Paris, France)
Comece o seu dia em Paris com um delicioso café da manhã na famosa Boulangerie Poilâne. Experimente um croissant fresco ou uma fatia de pão de centeio, acompanhado por um café expresso. Este local é conhecido por suas receitas tradicionais e ingredientes de alta qualidade, tornando-se uma excelente escolha para se energizar antes de um dia cheio de turismo.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=6000,
            temperature=0.8
        )
        content = response.choices[0].message["content"].strip()
        # Retorna só a string
        return content
    except:
        return ""
