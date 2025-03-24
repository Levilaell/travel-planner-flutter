from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path

from . import views


def direct_logout_view(request):
    logout(request)
    return redirect('login')  # ou redirecione pra onde quiser

urlpatterns = [
    path('register/', views.register_view, name='register'), 
    path('login/', views.login_view, name='login'),
    path('logout_direct/', direct_logout_view, name='logout'),  # <- sem conflito
]
