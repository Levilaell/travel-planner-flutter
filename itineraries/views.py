# views.py

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

            selected_interests = request.POST.getlist('interests_list')
            interests_str = ', '.join(selected_interests)
            itinerary.interests = interests_str

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
