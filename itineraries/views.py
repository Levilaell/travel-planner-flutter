import base64
import json
import logging
import os
import time
from datetime import timedelta
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
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            # 1) Criar itinerário
            itinerary = form.save(commit=False)
            itinerary.user = request.user
            selected_interests = request.POST.getlist('interests_list')
            itinerary.interests = ', '.join(selected_interests)
            itinerary.save()
            logger.info(f"[dashboard_view] Novo itinerário criado ID={itinerary.id}, destino={itinerary.destination}")

            # 2) Coordenadas do destino principal
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng
            logger.info(f"[dashboard_view] Geocoding => lat={lat}, lng={lng}")

            # 3) Texto IA (overview)
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()
            logger.info(f"[dashboard_view] Overview gerado p/ itinerário {itinerary.id}")

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
                logger.info(f"[dashboard_view] Criando Day={day.id} => data={current_date}")

                day_text, final_places = plan_one_day_itinerary(itinerary, day, visited_places_list)
                day.generated_text = day_text
                day.save()

                visited_places_list.extend(final_places)
                current_date += timedelta(days=1)
                day_number += 1

            return redirect(f"{reverse('dashboard')}?new_itinerary_id={itinerary.id}")
        else:
            # Form inválido => exibir erros
            logger.warning("[dashboard_view] Form inválido ao criar itinerário.")
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
        logger.debug(f"[dashboard_view] Render GET. Tem new_itinerary_id? {new_itinerary_id}")
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
