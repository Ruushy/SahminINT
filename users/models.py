from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    THEME_CHOICES = [
        ("dark", "Dark"),
        ("light", "Light"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True, default="")
    timezone = models.CharField(max_length=60, default="UTC")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="dark")

    def __str__(self):
        return f"Profile: {self.user.username}"


class UserSettings(models.Model):
    PAGE_SIZE_CHOICES = [
        (10, "10"),
        (25, "25"),
        (50, "50"),
        (100, "100"),
    ]
    DEFAULT_DORK_ENGINE_CHOICES = [
        ("google", "Google"),
        ("bing", "Bing"),
        ("duckduckgo", "DuckDuckGo"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    page_size = models.PositiveIntegerField(choices=PAGE_SIZE_CHOICES, default=25)
    default_dork_engine = models.CharField(
        max_length=20, choices=DEFAULT_DORK_ENGINE_CHOICES, default="google"
    )
    auto_open_results = models.BooleanField(default=False)

    shodan_api_key = models.CharField(max_length=200, blank=True, default="")
    censys_api_id = models.CharField(max_length=200, blank=True, default="")
    censys_api_secret = models.CharField(max_length=200, blank=True, default="")
    virustotal_api_key = models.CharField(max_length=200, blank=True, default="")
    github_api_key = models.CharField(max_length=200, blank=True, default="")
    securitytrails_api_key = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"Settings: {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile_settings(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserSettings.objects.create(user=instance)
