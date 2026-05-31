from django.db import models
from django.conf import settings
from targets.models import Target


class DorkQuery(models.Model):
    CATEGORY_CHOICES = [
        ("google", "Google Dork"),
        ("github", "GitHub Dork"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    target = models.ForeignKey(
        Target, on_delete=models.SET_NULL, null=True, blank=True
    )
    query = models.CharField(max_length=500)
    category = models.CharField(max_length=60, db_index=True)
    source = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="google")
    description = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.query[:80]
