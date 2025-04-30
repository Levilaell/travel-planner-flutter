# itineraries/api_views.py

from rest_framework import generics, permissions, status 
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from .models import Itinerary, Day
from .serializers import ItinerarySerializer
from .services import (
    get_cordinates_google_geocoding, generate_itinerary_overview,
    plan_one_day_itinerary, replace_single_place_in_day
)
from datetime import timedelta


class ItineraryListCreateView(generics.ListCreateAPIView):
    serializer_class = ItinerarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Itinerary.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        itinerary = serializer.save(user=self.request.user)
        itinerary.interests = self.request.data.get('interests', '')
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


class ItineraryDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ItinerarySerializer

    def get_queryset(self):
        # prefetch_related carrega os days numa única query
        return Itinerary.objects.filter(user=self.request.user).prefetch_related('days')


class ReplacePlaceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        day_id = request.data.get('day_id')
        place_index = request.data.get('place_index')
        observation = request.data.get('observation', '')

        try:
            day = Day.objects.get(id=day_id, itinerary__user=request.user)
        except Day.DoesNotExist:
            return Response({'error': 'Invalid day ID'}, status=404)

        replace_single_place_in_day(day, place_index, observation)
        return Response({'success': True})
