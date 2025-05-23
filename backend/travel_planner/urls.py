from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('allauth.urls')), 
    path('profile/', include('accounts.urls')),
    path('itinerary/', include('itineraries.urls'))
]
