import json  # para manipular o JSON de places_visited
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItineraryForm, ReviewForm
from .models import Day, Itinerary
from .services import (generate_itinerary_overview,
                       get_cordinates_google_geocoding, get_weather_info,
                       plan_one_day_itinerary)


@login_required
def create_itinerary_view(request):
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            itinerary = form.save(commit=False)
            itinerary.user = request.user

            # Interesses (checkbox)
            selected_interests = request.POST.getlist('interests_list')
            interests_str = ', '.join(selected_interests)
            itinerary.interests = interests_str
            itinerary.save()

            # Coordenadas do destino principal
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            # Texto geral/overview da IA
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

            # Gerar Days (um para cada data do intervalo)
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

                # Acumula lugares já visitados para não repetir
                visited_places_list.extend(final_places)
                current_date += timedelta(days=1)
                day_number += 1

            # Agora, vamos buscar todos os Days do itinerário
            days = itinerary.days.all().order_by('day_number')

            # =====================================================
            # 1) Juntar todos os lugares de todos os days numa lista
            # =====================================================
            all_markers = []
            for d in days:
                if d.places_visited:
                    try:
                        # Convertendo a string JSON em uma lista de dicionários
                        day_places = json.loads(d.places_visited)
                        for place_dict in day_places:
                            # place_dict = {"name": "...", "lat": 0.0, "lng": 0.0}
                            all_markers.append(place_dict)
                    except json.JSONDecodeError:
                        pass  # Se der erro de parse, ignore

            # Se quiser também marcar o destino principal:
            # (opcional)
            # all_markers.append({
            #    "name": itinerary.destination,
            #    "lat": float(itinerary.lat) if itinerary.lat else 0.0,
            #    "lng": float(itinerary.lng) if itinerary.lng else 0.0
            # })

            # =====================================================
            # 2) Transformar em JSON para enviar ao template
            # =====================================================
            markers_json = json.dumps(all_markers, ensure_ascii=False)

            # Renderiza a mesma página com o resultado (painel direito)
            return render(request, 'itineraries/create_itinerary.html', {
                'form': form,
                'itinerary': itinerary,
                'days': days,
                'lat': itinerary.lat,
                'lng': itinerary.lng,
                'markers_json': markers_json,  # AQUI -> Template usará
                'googlemaps_key': settings.GOOGLEMAPS_KEY,
            })
        else:
            # Form inválido
            return render(request, 'itineraries/create_itinerary.html', {'form': form})

    else:
        # GET: Exibe form vazio
        form = ItineraryForm()
        return render(request, 'itineraries/create_itinerary.html', {'form': form})


@login_required
def list_itineraries_view(request):
    """Lista todos os itinerários do usuário logado."""
    itineraries = Itinerary.objects.filter(user=request.user)
    return render(request, 'itineraries/list_itineraries.html', {'itineraries': itineraries})


@login_required
def itinerary_detail_view(request, pk):
    """
    Mostra detalhes de um itinerário específico (incluindo Days).
    """
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    days = itinerary.days.all().order_by('day_number')
    weather_data = get_weather_info(itinerary.destination)

    context = {
        'itinerary': itinerary,
        'days': days,
        'weather_data': weather_data,
        'lat': itinerary.lat,
        'lng': itinerary.lng,
        'googlemaps_key': settings.GOOGLEMAPS_KEY,
    }
    return render(request, 'itineraries/itinerary_detail.html', context)


@login_required
def day_detail_view(request, itinerary_id, day_id):
    """Exemplo de detalhe de um único dia do itinerário."""
    itinerary = get_object_or_404(Itinerary, pk=itinerary_id, user=request.user)
    day = get_object_or_404(Day, pk=day_id, itinerary=itinerary)
    return render(request, 'itineraries/day_detail.html', {
        'itinerary': itinerary,
        'day': day,
    })


@login_required
def add_review_view(request, pk):
    """Exemplo de view para adicionar uma review ao Itinerary."""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.itinerary = itinerary
            review.user = request.user
            review.save()
            return redirect('itinerary_detail', pk=itinerary.pk)
    else:
        form = ReviewForm()
    return render(request, 'itineraries/add_review.html', {'form': form, 'itinerary': itinerary})
