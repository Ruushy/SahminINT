from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/api/dashboard/", permanent=False)),
    path("api/auth/", include("users.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/targets/", include("targets.urls")),
    path("api/dorking/", include("dorking.urls")),
    path("api/recon/", include("recon.urls")),
    path("api/reporting/", include("reporting.urls")),
]
