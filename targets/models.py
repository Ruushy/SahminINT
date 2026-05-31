from django.db import models
from django.conf import settings


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    color = models.CharField(max_length=40, default="#22d3ee")

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


class Target(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255, db_index=True)
    notes = models.TextField(blank=True, default="")
    tags = models.ManyToManyField(Tag, blank=True)
    is_favorite = models.BooleanField(default=False, db_index=True)
    scan_count = models.PositiveIntegerField(default=0)
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "domain")

    def __str__(self):
        return self.domain

    def mark_scanned(self):
        from django.utils import timezone
        self.scan_count += 1
        self.last_scanned_at = timezone.now()
        self.save(update_fields=["scan_count", "last_scanned_at"])


class TargetNote(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="target_notes")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.target.domain}"


class SearchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    query = models.CharField(max_length=400)
    source = models.CharField(max_length=40, default="dork")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Search histories"

    def __str__(self):
        return f"{self.user}: {self.query[:50]}"
