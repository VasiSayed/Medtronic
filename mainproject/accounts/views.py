# accounts/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .forms import LoginForm

def login_view(request):
    """Render and process the custom login form."""
    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(reverse_lazy("home")) 
    return render(request, "accounts/login.html", {"form": form})




from django.contrib import messages

@login_required
def register_view(request):
    if not request.user.role == 'admin':
        messages.error(request, "You are not authorized to access the registration page.")
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('home')  
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


