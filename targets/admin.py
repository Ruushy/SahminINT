from django.contrib import admin
from targets.models import Tag, Target, TargetNote, SearchHistory

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color")
    list_filter = ("user",)

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("domain", "user", "is_favorite", "scan_count", "created_at")
    list_filter = ("is_favorite", "user")
    search_fields = ("domain", "notes")

@admin.register(TargetNote)
class TargetNoteAdmin(admin.ModelAdmin):
    list_display = ("target", "created_at")

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "source", "created_at")
