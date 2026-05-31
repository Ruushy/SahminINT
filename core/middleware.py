import re
from django.utils.deprecation import MiddlewareMixin
from core.models import ActivityLog


class ActivityLogMiddleware(MiddlewareMixin):
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in self.SAFE_METHODS:
            return None
        if request.user.is_authenticated:
            path = request.path
            if any(p in path for p in ("/api/auth/", "/admin/")):
                return None
            domain = view_kwargs.get("pk") or view_kwargs.get("target_id") or ""
            action = path.strip("/").replace("/", ":").replace("api:", "")[:60]
            desc = f"{request.method} {path}"
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    action=action[:80],
                    target_domain=str(domain)[:255] if domain else None,
                    description=desc[:500],
                )
            except Exception:
                pass
        return None
