from django.contrib import admin
from reporting.models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "target", "report_type", "created_at")
    list_filter = ("report_type", "created_at")
    search_fields = ("title",)
