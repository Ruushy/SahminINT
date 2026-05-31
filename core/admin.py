from django.contrib import admin
from core.models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "target_domain", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "target_domain", "description")
