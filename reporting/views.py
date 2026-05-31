import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from targets.models import Target
from recon.models import Subdomain, DNSRecord
from dorking.models import DorkQuery
from reporting.models import Report
from reporting.pdf_export import build_pdf


@login_required
def report_list(request):
    reports = Report.objects.filter(user=request.user).order_by("-created_at")[:100]
    return render(request, "reporting/list.html", {"reports": reports})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    return render(request, "reporting/detail.html", {"report": report})


@login_required
def report_generate(request):
    if request.method == "POST":
        target_id = request.POST.get("target_id")
        report_type = request.POST.get("report_type", "full")
        title = request.POST.get("title", "").strip()
        target = None
        if target_id:
            target = get_object_or_404(Target, pk=target_id, user=request.user)

        data = {}
        stats = {}

        if target:
            if report_type in ("full", "subdomains"):
                subs = Subdomain.objects.filter(target=target).values_list("host", flat=True)
                data["subdomains"] = list(subs)
                stats["subdomains"] = len(subs)

            if report_type in ("full", "dns"):
                dns_recs = DNSRecord.objects.filter(target=target).values("record_type", "value")
                data["dns"] = list(dns_recs)
                stats["dns_records"] = len(dns_recs)

        if report_type in ("full", "dorks"):
            dorks = DorkQuery.objects.filter(user=request.user).values("query", "category", "source")
            data["dorks"] = list(dorks)
            stats["saved_dorks"] = len(dorks)

        if target:
            stats["scans"] = target.scan_count

        data["stats"] = stats
        data["target_domain"] = target.domain if target else "N/A"

        report = Report.objects.create(
            user=request.user,
            target=target,
            title=title or f"Report: {target.domain if target else 'General'} - {report_type}",
            report_type=report_type,
        )
        report.set_data(data)
        report.save(update_fields=["data_snapshot"])

        messages.success(request, "Report generated successfully!")
        return redirect("reporting:detail", pk=report.pk)

    targets = Target.objects.filter(user=request.user)
    return render(request, "reporting/generate.html", {"targets": targets})


@login_required
def report_export_html(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    html = render_to_string("reporting/export_html.html", {"report": report})
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@login_required
def report_export_json(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    data = report.get_data()
    data["_meta"] = {
        "title": report.title,
        "type": report.report_type,
        "created": report.created_at.isoformat(),
        "author": "SahminINT - Ruushy (https://ruushy.github.io/protfolio/)",
    }
    return JsonResponse(data, json_dumps_params={"indent": 2})


@login_required
def report_export_pdf(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    buf = build_pdf(report)
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report.title[:50].replace(" ", "_")}.pdf"'
    return response


@login_required
def report_delete(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    if request.method == "POST":
        report.delete()
        messages.success(request, "Report deleted.")
    return redirect("reporting:list")
