from django.db import models
from targets.models import Target


class Subdomain(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="subdomains")
    host = models.CharField(max_length=255, db_index=True)
    source = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("target", "host")
        ordering = ["host"]

    def __str__(self):
        return self.host


class DNSRecord(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="dns_records")
    record_type = models.CharField(max_length=10)
    value = models.TextField()
    ttl = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["target", "record_type"])]
        ordering = ["record_type", "value"]

    def __str__(self):
        return f"{self.record_type} {self.value[:60]}"


class SSLCertificate(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="ssl_certs")
    port = models.IntegerField()
    subject_cn = models.CharField(max_length=255, blank=True, default="")
    issuer_cn = models.CharField(max_length=255, blank=True, default="")
    org = models.CharField(max_length=255, blank=True, default="")
    san = models.TextField(blank=True, default="")
    not_before = models.CharField(max_length=100, blank=True, default="")
    not_after = models.CharField(max_length=100, blank=True, default="")
    expires = models.CharField(max_length=100, blank=True, default="")
    remaining_days = models.IntegerField(null=True, blank=True)
    serial = models.CharField(max_length=100, blank=True, default="")
    signature_algorithm = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("target", "port")
        ordering = ["port"]

    def __str__(self):
        return f"SSL on {self.target.domain}:{self.port}"


class EmailResult(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField(max_length=254)
    source = models.CharField(max_length=100, blank=True, default="harvester")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("target", "email")
        ordering = ["email"]

    def __str__(self):
        return self.email
