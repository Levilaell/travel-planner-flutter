from django.urls import path

from . import views

urlpatterns = [
    path('create/', views.dashboard_view, name='dashboard'),
    #path('list/', views.list_itineraries_view, name='list_itineraries'),
    
    # Detalhes do itinerário
    #path('<int:pk>/', views.itinerary_detail_view, name='itinerary_detail'),
    
    
    # Detalhes de um dia específico (Day) dentro do itinerário
    #path('<int:itinerary_id>/day/<int:day_id>/', views.day_detail_view, name='day_detail'),
]
