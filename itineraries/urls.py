# urls.py

from django.urls import path # type: ignore

from . import chatbot_views, views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chat/', chatbot_views.chatbot_view, name='chatbot_view'),
]
