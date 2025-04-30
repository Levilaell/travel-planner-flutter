from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path

from . import views
from .api_views import CustomAuthToken, LogoutView

# Web logout (redireciona)
def direct_logout_view(request):
    logout(request)
    return redirect('login')

urlpatterns = [
    # ROTAS WEB
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout_direct/', direct_logout_view, name='logout'),

    # ROTAS API (Flutter / Postman)
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
]
