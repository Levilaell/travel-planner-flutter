# urls.py

from django.urls import path

from . import chatbot_views, views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chat/', chatbot_views.chatbot_view, name='chatbot_view'),

    # Rota p/ troca de lugar
    path('replace-place/', views.replace_place_view, name='replace_place'),



    # NOVAS ROTAS:
    path('delete-itinerary/<int:pk>/', views.delete_itinerary_view, name='delete_itinerary'),
    path('export-pdf/<int:pk>/', views.export_itinerary_pdf_view, name='export_itinerary_pdf'),
]
