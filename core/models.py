from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    action = models.CharField(max_length=80)
    target_domain = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Activity logs"

    def __str__(self):
        return f"[{self.created_at}] {self.user or 'anon'} – {self.action}"
