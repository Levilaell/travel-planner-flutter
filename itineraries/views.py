# views.py

import json
import os
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ItineraryForm, ReviewForm
from .models import Day, Itinerary
from .services import (build_markers_json_for_day_replacement,
                       generate_itinerary_overview,
                       get_cordinates_google_geocoding, plan_one_day_itinerary,
                       replace_single_place_in_day)


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


def build_markers_json(itinerary):
    all_markers = []
    if itinerary.lat is not None and itinerary.lng is not None:
        all_markers.append({
            "name": itinerary.destination,
            "lat": float(itinerary.lat),
            "lng": float(itinerary.lng),
        })
    days = itinerary.days.all()
    for d in days:
        if d.places_visited:
            try:
                day_places = json.loads(d.places_visited)
                all_markers.extend(day_places)
            except json.JSONDecodeError:
                pass
    return json.dumps(all_markers, ensure_ascii=False)


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


###################################
# NOVAS FUNÇÕES DE EXCLUSÃO E PDF #
###################################

import tempfile

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


@login_required
def delete_itinerary_view(request, pk):
    """
    Exclui um itinerário do usuário logado.
    """
    if request.method == 'POST':
        itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
        itinerary.delete()
    return redirect('dashboard')


@login_required
def export_itinerary_pdf_view(request, pk):
    """
    Gera um PDF do itinerário, incluindo imagem de mapa salva localmente.
    """
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    map_img_path = None
    temp_file_path = None

    if itinerary.lat and itinerary.lng:
        map_url = (
            f"https://maps.googleapis.com/maps/api/staticmap"
            f"?center={itinerary.lat},{itinerary.lng}"
            f"&zoom=10&size=600x300"
            f"&markers=color:red%7Clabel:D%7C{itinerary.lat},{itinerary.lng}"
            f"&key={settings.GOOGLEMAPS_KEY}"
        )

        try:
            response = requests.get(map_url)
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()

                # Importante: usar "file://" + caminho
                map_img_path = f"file://{temp_file.name}"
                temp_file_path = temp_file.name
        except Exception as e:
            print("Erro ao baixar imagem do mapa:", e)

    # Renderiza HTML com caminho local da imagem
    html_string = render_to_string('itineraries/pdf_template.html', {
        'itinerary': itinerary,
        'map_img_path': map_img_path,
    })

    # Gera o PDF usando o caminho base do sistema de arquivos
    pdf_file = HTML(string=html_string, base_url=os.getcwd()).write_pdf()

    # Remove imagem temporária após gerar PDF
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Itinerario_{itinerary.destination}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response