# urls.py

from django.urls import path

from . import chatbot_views, views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Rota p/ troca de lugar
    path('replace-place/', views.replace_place_view, name='replace_place'),

    path("proxy_google_places/", views.proxy_google_places, name="proxy_google_places"),
    path("proxy_google_photo/", views.google_photo_proxy, name="proxy_google_photo"),


    # NOVAS ROTAS:
    path('delete-itinerary/<int:pk>/', views.delete_itinerary_view, name='delete_itinerary'),
    path('export-pdf/<int:pk>/', views.export_itinerary_pdf_view, name='export_itinerary_pdf'),
]
