from django.contrib import admin
from users.models import Profile, UserSettings

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "timezone", "theme")

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "page_size", "default_dork_engine")
