import json
import logging
from urllib.parse import urlparse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from core.utils import sanitize_domain, safe_truncate
from targets.models import Target
from recon.models import (
    Subdomain, DNSRecord, SSLCertificate, EmailResult,
)
from recon import services as recon_svc

logger = logging.getLogger(__name__)


@login_required
def recon_home(request):
    return render(request, "recon/home.html")


# ── Subdomains ─────────────────────────────────────────────────────

@login_required
def subdomain_list(request):
    target_id = request.GET.get("target_id")
    subs = Subdomain.objects.filter(target__user=request.user)
    if target_id:
        subs = subs.filter(target_id=target_id)
    subs = subs.select_related("target").order_by("host")[:500]
    targets = Target.objects.filter(user=request.user)
    return render(request, "recon/subdomains.html", {"subdomains": subs, "targets": targets})


@login_required
def subdomain_run(request):
    if request.method == "POST":
        target_id = request.POST.get("target_id")
        target = get_object_or_404(Target, pk=target_id, user=request.user)
        results = recon_svc.enumerate_subdomains(target.domain)
        count = 0
        for host, sources in results.items():
            _, created = Subdomain.objects.get_or_create(
                target=target, host=host, defaults={"source": sources[0]}
            )
            if created:
                count += 1
        target.mark_scanned()
        messages.success(request, f"Enumerated {count} subdomains for {target.domain}")
        return redirect("recon:subdomain_list")
    return redirect("recon:recon_home")


@login_required
def subdomain_export(request):
    target_id = request.GET.get("target_id")
    subs = Subdomain.objects.filter(target__user=request.user)
    if target_id:
        subs = subs.filter(target_id=target_id)
    hosts = [s.host for s in subs.order_by("host")]
    return HttpResponse("\n".join(hosts), content_type="text/plain; charset=utf-8")


# ── DNS ────────────────────────────────────────────────────────────

@login_required
def dns_list(request):
    target_id = request.GET.get("target_id")
    records = DNSRecord.objects.filter(target__user=request.user)
    if target_id:
        records = records.filter(target_id=target_id)
    records = records.select_related("target").order_by("record_type", "value")[:500]
    targets = Target.objects.filter(user=request.user)
    return render(request, "recon/dns.html", {"records": records, "targets": targets})


@login_required
def dns_run(request):
    if request.method == "POST":
        target_id = request.POST.get("target_id")
        target = get_object_or_404(Target, pk=target_id, user=request.user)
        DNSRecord.objects.filter(target=target).delete()
        results = recon_svc.query_dns(target.domain)
        for r in results:
            DNSRecord.objects.create(
                target=target,
                record_type=r["record_type"],
                value=r["value"],
                ttl=r.get("ttl"),
            )
        target.mark_scanned()
        messages.success(request, f"DNS lookup complete for {target.domain} ({len(results)} records)")
        return redirect("recon:dns_list")
    return redirect("recon:recon_home")


# ── SSL / TLS ──────────────────────────────────────────────────────

@login_required
def ssl_list(request):
    target_id = request.GET.get("target_id")
    certs = SSLCertificate.objects.filter(target__user=request.user)
    if target_id:
        certs = certs.filter(target_id=target_id)
    certs = certs.select_related("target").order_by("target__domain", "port")
    targets = Target.objects.filter(user=request.user)
    return render(request, "recon/ssl.html", {"certs": certs, "targets": targets})


@login_required
def ssl_run(request):
    if request.method == "POST":
        target_id = request.POST.get("target_id")
        target = get_object_or_404(Target, pk=target_id, user=request.user)
        results = recon_svc.check_ssl(target.domain)
        count = 0
        for r in results:
            _, created = SSLCertificate.objects.update_or_create(
                target=target,
                port=r["port"],
                defaults={
                    "subject_cn": r.get("subject_cn", "")[:255],
                    "issuer_cn": r.get("issuer_cn", "")[:255],
                    "org": r.get("org", "")[:255],
                    "san": r.get("san", "")[:1000],
                    "not_before": r.get("not_before", "")[:100],
                    "not_after": r.get("not_after", "")[:100],
                    "expires": r.get("expires", "")[:100],
                    "remaining_days": r.get("remaining_days"),
                    "serial": r.get("serial", "")[:100],
                    "signature_algorithm": r.get("signature_algorithm", "")[:100],
                },
            )
            if created:
                count += 1
        target.mark_scanned()
        messages.success(request, f"SSL check complete for {target.domain} ({len(results)} certs)")
        return redirect("recon:ssl_list")
    return redirect("recon:recon_home")


# ── Email Harvester ────────────────────────────────────────────────

@login_required
def email_list(request):
    target_id = request.GET.get("target_id")
    emails = EmailResult.objects.filter(target__user=request.user)
    if target_id:
        emails = emails.filter(target_id=target_id)
    emails = emails.select_related("target").order_by("email")
    targets = Target.objects.filter(user=request.user)
    return render(request, "recon/emails.html", {"emails": emails, "targets": targets})


@login_required
def email_run(request):
    if request.method == "POST":
        target_id = request.POST.get("target_id")
        target = get_object_or_404(Target, pk=target_id, user=request.user)
        results = recon_svc.harvest_emails(target.domain)
        count = 0
        for e in results:
            _, created = EmailResult.objects.get_or_create(
                target=target,
                email=e,
                defaults={"source": "harvester"},
            )
            if created:
                count += 1
        target.mark_scanned()
        messages.success(request, f"Harvested {count} emails for {target.domain}")
        return redirect("recon:email_list")
    return redirect("recon:recon_home")


# ── Export helpers ─────────────────────────────────────────────────

@login_required
def dns_export(request):
    target_id = request.GET.get("target_id")
    records = DNSRecord.objects.filter(target__user=request.user)
    if target_id:
        records = records.filter(target_id=target_id)
    lines = [f"{r.record_type}\t{r.value}\t{r.ttl or ''}" for r in records.order_by("record_type")]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@login_required
def email_export(request):
    target_id = request.GET.get("target_id")
    emails = EmailResult.objects.filter(target__user=request.user)
    if target_id:
        emails = emails.filter(target_id=target_id)
    return HttpResponse("\n".join(e.email for e in emails), content_type="text/plain; charset=utf-8")
