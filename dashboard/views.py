from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from targets.models import Target
from recon.models import Subdomain, DNSRecord
from dorking.models import DorkQuery
from reporting.models import Report
from core.models import ActivityLog


PASSIVE_MODULE_COUNT = 10


@login_required
def home(request):
    user = request.user
    targets_qs = Target.objects.filter(user=user)
    recon_scans_qs = targets_qs.aggregate(s=Count("scan_count"))["s"] or 0
    subdomain_count = Subdomain.objects.filter(target__user=user).count()
    dns_count = DNSRecord.objects.filter(target__user=user).count()
    dork_count = DorkQuery.objects.filter(user=user).count()
    report_count = Report.objects.filter(user=user).count()
    target_count = targets_qs.count()

    # Recent targets
    recent_targets = targets_qs.order_by("-created_at")[:6]

    # Recent activity
    recent_activity = ActivityLog.objects.filter(user=user)[:10]

    # Quick stats for cards
    stats = {
        "targets": target_count,
        "recon_scans": recon_scans_qs,
        "subdomains": subdomain_count,
        "dns": dns_count,
        "dorks": dork_count,
        "reports": report_count,
        "modules": PASSIVE_MODULE_COUNT,
    }

    return render(request, "dashboard/home.html", {
        "stats": stats,
        "recent_targets": recent_targets,
        "recent_activity": recent_activity,
    })


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()
    results = {"targets": [], "subdomains": [], "dorks": [], "reports": []}
    if query:
        results["targets"] = Target.objects.filter(
            user=request.user, domain__icontains=query
        )[:10]
        results["subdomains"] = Subdomain.objects.filter(
            target__user=request.user, host__icontains=query
        )[:10]
        results["dorks"] = DorkQuery.objects.filter(
            user=request.user, query__icontains=query
        )[:10]
        results["reports"] = Report.objects.filter(
            user=request.user, title__icontains=query
        )[:10]
    return render(request, "dashboard/search.html", {"query": query, "results": results})


@login_required
def activity_feed(request):
    activities = ActivityLog.objects.filter(user=request.user)[:100]
    return render(request, "dashboard/activity.html", {"activities": activities})
