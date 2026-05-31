import json
from django.db import models
from django.conf import settings
from targets.models import Target


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ("full", "Full Report"),
        ("subdomains", "Subdomains"),
        ("dns", "DNS Records"),
        ("dorks", "Saved Dorks"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.ForeignKey(Target, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default="full")
    data_snapshot = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_data(self):
        try:
            return json.loads(self.data_snapshot) if self.data_snapshot else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_data(self, data):
        self.data_snapshot = json.dumps(data, default=str)
