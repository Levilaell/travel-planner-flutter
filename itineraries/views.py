from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from datetime import timedelta

from .forms import ItineraryForm, ReviewForm
from .models import Itinerary, Day
from .services import (
    generate_itinerary_overview,
    plan_one_day_itinerary,
    get_weather_info,
    get_cordinates_google_geocoding
)

@login_required
def create_itinerary_view(request):
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            # 1. Cria o objeto Itinerary (sem salvar completamente)
            itinerary = form.save(commit=False)
            itinerary.user = request.user

            # 2. Captura lista de interesses e converte em string
            selected_interests = request.POST.getlist('interests_list')
            interests_str = ', '.join(selected_interests)
            itinerary.interests = interests_str

            # 3. Salva o Itinerary (sem overview ainda)
            itinerary.save()

            # 4. Obtém coordenadas do destino
            lat, lng = get_cordinates_google_geocoding(itinerary.destination)
            itinerary.lat = lat
            itinerary.lng = lng

            # 5. Gera overview do itinerário
            overview = generate_itinerary_overview(itinerary)
            itinerary.generated_text = overview
            itinerary.save()

            # 6. Gera dias
            current_date = itinerary.start_date
            day_number = 1
            visited_places_list = []  # Acumula lugares já visitados

            while current_date <= itinerary.end_date:
                # Cria o Day
                day = Day.objects.create(
                    itinerary=itinerary,
                    day_number=day_number,
                    date=current_date
                )

                # 7. Gera texto do dia usando plan_one_day_itinerary
                #    que já evita lugares repetidos (usando visited_places_list)
                day_text, final_places = plan_one_day_itinerary(
                    itinerary=itinerary,
                    day=day,
                    already_visited=visited_places_list
                )
                day.generated_text = day_text
                day.save()

                # 8. Atualiza visited_places_list com os lugares confirmados
                visited_places_list.extend(final_places)

                current_date += timedelta(days=1)
                day_number += 1

            return redirect('itinerary_detail', pk=itinerary.pk)
        else:
            return render(request, 'itineraries/create_itinerary.html', {'form': form})
    else:
        form = ItineraryForm()
        return render(request, 'itineraries/create_itinerary.html', {'form': form})


@login_required
def list_itineraries_view(request):
    itineraries = Itinerary.objects.filter(user=request.user)
    return render(request, 'itineraries/list_itineraries.html', {'itineraries': itineraries})


@login_required
def itinerary_detail_view(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    days = itinerary.days.all().order_by('day_number')

    # Exemplo de uso para dados de clima (opcional)
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
    itinerary = get_object_or_404(Itinerary, pk=itinerary_id, user=request.user)
    day = get_object_or_404(Day, pk=day_id, itinerary=itinerary)
    return render(request, 'itineraries/day_detail.html', {
        'itinerary': itinerary,
        'day': day,
    })


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
            return redirect('itinerary_detail', pk=itinerary.pk)
    else:
        form = ReviewForm()
    return render(request, 'itineraries/add_review.html', {'form': form, 'itinerary': itinerary})
