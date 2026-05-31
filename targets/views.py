import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from core.utils import sanitize_domain
from targets.models import Target, Tag, TargetNote, SearchHistory


@login_required
def target_list(request):
    query = request.GET.get("q", "").strip()
    favorites_only = request.GET.get("favorites", "") == "1"
    targets = Target.objects.filter(user=request.user)
    if query:
        targets = targets.filter(
            Q(domain__icontains=query) | Q(notes__icontains=query)
        )
    if favorites_only:
        targets = targets.filter(is_favorite=True)
    targets = targets.order_by("-created_at")
    return render(request, "targets/list.html", {"targets": targets, "query": query, "favorites_only": favorites_only})


@login_required
def target_create(request):
    if request.method == "POST":
        domain_raw = request.POST.get("domain", "")
        domain = sanitize_domain(domain_raw)
        if not domain:
            messages.error(request, "Invalid domain format.")
            return render(request, "targets/form.html", {"target": None})
        notes = request.POST.get("notes", "")
        tags_csv = request.POST.get("tags", "").strip()
        target, created = Target.objects.get_or_create(
            user=request.user,
            domain=domain,
            defaults={"notes": notes},
        )
        if not created:
            messages.warning(request, f"Target '{domain}' already exists.")
            return redirect("targets:detail", pk=target.pk)
        if tags_csv:
            for tname in [t.strip() for t in tags_csv.split(",") if t.strip()]:
                tag, _ = Tag.objects.get_or_create(user=request.user, name=tname)
                target.tags.add(tag)
        messages.success(request, f"Target '{domain}' added.")
        return redirect("targets:detail", pk=target.pk)
    return render(request, "targets/form.html", {"target": None})


@login_required
def target_detail(request, pk):
    target = get_object_or_404(Target, pk=pk, user=request.user)
    return render(request, "targets/detail.html", {"target": target})


@login_required
def target_update(request, pk):
    target = get_object_or_404(Target, pk=pk, user=request.user)
    if request.method == "POST":
        domain_raw = request.POST.get("domain", target.domain)
        domain = sanitize_domain(domain_raw) or target.domain
        target.domain = domain
        target.notes = request.POST.get("notes", target.notes)
        tags_csv = request.POST.get("tags", "").strip()
        target.tags.clear()
        if tags_csv:
            for tname in [t.strip() for t in tags_csv.split(",") if t.strip()]:
                tag, _ = Tag.objects.get_or_create(user=request.user, name=tname)
                target.tags.add(tag)
        target.save()
        messages.success(request, "Target updated.")
        return redirect("targets:detail", pk=target.pk)
    return render(request, "targets/form.html", {"target": target})


@login_required
def target_delete(request, pk):
    target = get_object_or_404(Target, pk=pk, user=request.user)
    if request.method == "POST":
        domain = target.domain
        target.delete()
        messages.success(request, f"Target '{domain}' deleted.")
    return redirect("targets:list")


@login_required
def target_favorite(request, pk):
    target = get_object_or_404(Target, pk=pk, user=request.user)
    if request.method == "POST":
        target.is_favorite = not target.is_favorite
        target.save(update_fields=["is_favorite"])
        return JsonResponse({"favorite": target.is_favorite})
    return JsonResponse({"error": "POST required"}, status=405)


@login_required
def target_add_note(request, pk):
    target = get_object_or_404(Target, pk=pk, user=request.user)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            TargetNote.objects.create(target=target, content=content)
            messages.success(request, "Note added.")
    return redirect("targets:detail", pk=pk)


@login_required
def search_history(request):
    history = SearchHistory.objects.filter(user=request.user)[:50]
    return render(request, "targets/search_history.html", {"history": history})
