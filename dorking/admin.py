from django.contrib import admin
from dorking.models import DorkQuery

@admin.register(DorkQuery)
class DorkQueryAdmin(admin.ModelAdmin):
    list_display = ("query", "user", "category", "source", "created_at")
    list_filter = ("category", "source")
    search_fields = ("query",)
