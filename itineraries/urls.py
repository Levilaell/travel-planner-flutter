# urls.py

from django.urls import path  # type: ignore

from . import chatbot_views, views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chat/', chatbot_views.chatbot_view, name='chatbot_view'),

    # Rota p/ troca de lugar
    path('replace-place/', views.replace_place_view, name='replace_place'),

    # Exemplo de review
    path('add-review/<int:pk>/', views.add_review_view, name='add_review'),
]
