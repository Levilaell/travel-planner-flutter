# itineraries/urls.py

from django.urls import path
from . import views, api_views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('replace-place/', views.replace_place_view, name='replace_place'),
    path("proxy_google_places/", views.proxy_google_places, name="proxy_google_places"),
    path("proxy_google_photo/", views.google_photo_proxy, name="proxy_google_photo"),
    path('delete-itinerary/<int:pk>/', views.delete_itinerary_view, name='delete_itinerary'),
    path('export-pdf/<int:pk>/', views.export_itinerary_pdf_view, name='export_itinerary_pdf'),

    # API REST endpoints
    path("api/itineraries/", api_views.ItineraryListCreateView.as_view(), name="api_itineraries"),
    path("api/itineraries/<int:pk>/", api_views.ItineraryDetailView.as_view(), name="api_itinerary_detail"),
    path("api/replace_place/", api_views.ReplacePlaceAPIView.as_view(), name="api_replace_place"),
    path("api/test/", api_views.TestAPIView.as_view(), name="api_test"),
]
