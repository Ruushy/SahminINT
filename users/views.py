from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from users.models import Profile, UserSettings


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("dashboard:home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard:home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("users:login")


@login_required
def profile_view(request):
    return render(request, "users/profile.html")


@login_required
def settings_view(request):
    profile = request.user.profile
    settings = request.user.settings
    if request.method == "POST":
        profile.bio = request.POST.get("bio", profile.bio)
        profile.timezone = request.POST.get("timezone", profile.timezone)
        profile.theme = request.POST.get("theme", profile.theme)
        profile.save()
        settings.page_size = int(request.POST.get("page_size", settings.page_size))
        settings.default_dork_engine = request.POST.get(
            "default_dork_engine", settings.default_dork_engine
        )
        settings.auto_open_results = request.POST.get("auto_open_results") == "on"
        settings.shodan_api_key = request.POST.get("shodan_api_key", "")
        settings.censys_api_id = request.POST.get("censys_api_id", "")
        settings.censys_api_secret = request.POST.get("censys_api_secret", "")
        settings.virustotal_api_key = request.POST.get("virustotal_api_key", "")
        settings.github_api_key = request.POST.get("github_api_key", "")
        settings.securitytrails_api_key = request.POST.get("securitytrails_api_key", "")
        settings.save()
        messages.success(request, "Settings saved successfully!")
        return redirect("users:settings")
    from users.models import UserSettings as US
    return render(request, "users/settings.html", {
        "profile": profile,
        "settings": settings,
        "PAGE_SIZE_CHOICES": US.PAGE_SIZE_CHOICES,
        "DEFAULT_DORK_ENGINE_CHOICES": US.DEFAULT_DORK_ENGINE_CHOICES,
    })


class CustomPasswordResetView(PasswordResetView):
    template_name = "auth/password_reset.html"


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "auth/password_reset_complete.html"
