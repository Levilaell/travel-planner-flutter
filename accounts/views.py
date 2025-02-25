from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()  # Agora o password já é salvo corretamente
            login(request, user)  # Loga automaticamente
            return redirect('home')

    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    error_message = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Credenciais inválidas.'

    return render(request, 'accounts/login.html', {'error': error_message})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
