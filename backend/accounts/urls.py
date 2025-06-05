from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path

from . import views
from .api_views import CustomAuthToken, LogoutView, RegisterAPIView, ProfileView  # importe aqui

# --- ROTAS WEB (templates) ---
def direct_logout_view(request):
    logout(request)
    return redirect('login')

urlpatterns = [
    # registro e login via html
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout_direct/', direct_logout_view, name='logout'),
]

# --- ROTAS API (JSON para Flutter / Postman) ---
urlpatterns += [
    # endpoint de registro JSON
    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    # endpoint de obtenção de token
    path('api/login/',    CustomAuthToken.as_view(), name='api_login'),
    # endpoint de logout (invalidate token etc)
    path('api/logout/',   LogoutView.as_view(),    name='api_logout'),
    # endpoint de perfil do usuário
    path('api/profile/',  ProfileView.as_view(),    name='api_profile'),
]
