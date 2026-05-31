from django.contrib import admin
from recon.models import Subdomain, DNSRecord

@admin.register(Subdomain)
class SubdomainAdmin(admin.ModelAdmin):
    list_display = ("host", "target", "source", "created_at")
    search_fields = ("host",)
    list_filter = ("source",)

@admin.register(DNSRecord)
class DNSRecordAdmin(admin.ModelAdmin):
    list_display = ("target", "record_type", "value_short", "created_at")
    list_filter = ("record_type",)

    def value_short(self, obj):
        return obj.value[:60] if obj.value else ""

