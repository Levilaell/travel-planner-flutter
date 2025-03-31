# views.py

import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required # type: ignore
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItineraryForm, ReviewForm
from .models import Day, Itinerary
from .services import (generate_itinerary_overview,
                       get_cordinates_google_geocoding, plan_one_day_itinerary)


@login_required
def dashboard_view(request):
    """
    Página principal:
    - Painel esquerdo: form de criação (POST -> PRG)
    - Painel direito: lista de itinerários em cards (GET)
    - Cada itinerário tem markers_json c/ destino + places_visited (para exibir no mapa do modal)
    """
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            # 1) Criar itinerário

            itinerary = form.save(commit=False)
            itinerary.user = request.user

            # Interesses (checkboxes) => string
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
                day_text, final_places = plan_one_day_itinerary(
                    itinerary=itinerary,
                    day=day,
                    already_visited=visited_places_list
                )
                day.generated_text = day_text
                day.save()

                visited_places_list.extend(final_places)
                current_date += timedelta(days=1)
                day_number += 1

            # Evitar reenvio do form ao dar F5
            return redirect('dashboard')
        else:
            # Form inválido => exibir erros
            itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')

            # Montar markers_json para cada itinerary
            for it in itineraries:
                it.markers_json = build_markers_json(it)

            return render(request, 'itineraries/dashboard.html', {
                'form': form,
                'itineraries': itineraries,
                'googlemaps_key': settings.GOOGLEMAPS_KEY,
            })
    else:
        # GET normal: form vazio + lista itinerários
        form = ItineraryForm()
        itineraries = Itinerary.objects.filter(user=request.user).order_by('-created_at')

        # Preencher markers_json em cada itinerary
        for it in itineraries:
            it.markers_json = build_markers_json(it)

        return render(request, 'itineraries/dashboard.html', {
            'form': form,
            'itineraries': itineraries,
            'googlemaps_key': settings.GOOGLEMAPS_KEY,
        })


def build_markers_json(itinerary):
    """
    Retorna uma string JSON contendo [ {name, lat, lng}, ... ]
    com o destino principal e os lugares dos Days (places_visited).
    """
    all_markers = []
    # Destino principal
    if itinerary.lat is not None and itinerary.lng is not None:
        all_markers.append({
            "name": itinerary.destination,
            "lat": float(itinerary.lat),
            "lng": float(itinerary.lng),
        })

    # Percorrer Days -> places_visited
    days = itinerary.days.all()
    for d in days:
        if d.places_visited:
            try:
                day_places = json.loads(d.places_visited)  # ex: [ {name,lat,lng}, ...]
                all_markers.extend(day_places)
            except json.JSONDecodeError:
                pass

    return json.dumps(all_markers, ensure_ascii=False)


@login_required
def add_review_view(request, pk):
    """
    Exemplo se quiser adicionar reviews
    """
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