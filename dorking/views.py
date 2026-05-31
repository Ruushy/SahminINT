import json
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from dorking.models import DorkQuery
from dorking.dork_catalogs import GOOGLE_DORKS, GITHUB_DORKS
from dorking.services import build_search_urls, build_github_url
from targets.models import Target, SearchHistory


SEARCH_ENGINES = [
    {"name": "Google", "url": "https://www.google.com/search?q={query}"},
    {"name": "Bing", "url": "https://www.bing.com/search?q={query}"},
    {"name": "DuckDuckGo", "url": "https://duckduckgo.com/?q={query}"},
    {"name": "GitHub", "url": "https://github.com/search?q={query}&type=code"},
    {"name": "GitLab", "url": "https://gitlab.com/search?search={query}"},
    {"name": "Reddit", "url": "https://www.reddit.com/search/?q={query}"},
    {"name": "Stack Overflow", "url": "https://stackoverflow.com/search?q={query}"},
    {"name": "Shodan", "url": "https://www.shodan.io/search?query={query}"},
    {"name": "Censys", "url": "https://search.censys.io/search?resource=hosts&q={query}"},
    {"name": "crt.sh", "url": "https://crt.sh/?q={query}"},
    {"name": "VirusTotal", "url": "https://www.virustotal.com/ui/search?query={query}"},
    {"name": "Wayback Machine", "url": "https://web.archive.org/web/*/{query}"},
]


def _log_search(user, query, source="dork"):
    try:
        SearchHistory.objects.create(user=user, query=query[:400], source=source)
    except Exception:
        pass


@login_required
def dorking_home(request):
    return render(request, "dorking/home.html", {
        "google_categories": GOOGLE_DORKS,
        "github_categories": GITHUB_DORKS,
    })


@login_required
def google_dorks(request):
    domain = request.GET.get("domain", "").strip()
    results = []
    for category, queries in GOOGLE_DORKS.items():
        for q in queries:
            urls = build_search_urls(q, domain or "{domain}")
            results.append({
                "category": category,
                "query": urls["query"],
                "google": urls["google"],
                "bing": urls["bing"],
                "duckduckgo": urls["duckduckgo"],
            })
    return render(request, "dorking/google.html", {
        "results": results, "domain": domain, "categories": list(GOOGLE_DORKS.keys()),
    })


@login_required
def github_dorks(request):
    domain = request.GET.get("domain", "").strip()
    results = []
    for category, queries in GITHUB_DORKS.items():
        for q in queries:
            urls = build_github_url(q, domain or "{domain}")
            results.append({
                "category": category,
                "query": urls["query"],
                "github": urls["github"],
            })
    return render(request, "dorking/github.html", {
        "results": results, "domain": domain, "categories": list(GITHUB_DORKS.keys()),
    })


@login_required
def browser_search(request):
    query = request.GET.get("q", "").strip()
    domain = request.GET.get("domain", "").strip()
    engines = []
    for eng in SEARCH_ENGINES:
        url = eng["url"]
        if domain:
            url = url.replace("{query}", urllib.parse.quote(domain))
        else:
            url = url.replace("{query}", urllib.parse.quote(query or ""))
        engines.append({"name": eng["name"], "url": url})
    return render(request, "dorking/browser_search.html", {
        "engines": engines, "query": query, "domain": domain,
    })


@login_required
def save_dork(request):
    if request.method == "POST":
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        category = data.get("category", "").strip()
        source = data.get("source", "google")
        target_id = data.get("target_id")
        target = None
        if target_id:
            target = get_object_or_404(Target, pk=target_id, user=request.user)
        if query:
            dq = DorkQuery.objects.create(
                user=request.user,
                target=target,
                query=query[:500],
                category=category[:60],
                source=source,
            )
            _log_search(request.user, query, source)
            return JsonResponse({"saved": True, "id": dq.pk})
        return JsonResponse({"saved": False, "error": "Empty query"}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)


@login_required
def list_saved_dorks(request):
    dorks = DorkQuery.objects.filter(user=request.user).order_by("-created_at")[:100]
    return render(request, "dorking/saved.html", {"dorks": dorks})
