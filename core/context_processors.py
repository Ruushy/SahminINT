from core.models import ActivityLog
from targets.models import Target


def sidebar_data(request):
    ctx = {}
    if request.user.is_authenticated:
        ctx["recent_activity"] = ActivityLog.objects.filter(
            user=request.user
        )[:5]
        ctx["target_count"] = Target.objects.filter(user=request.user).count()
    else:
        ctx["recent_activity"] = []
        ctx["target_count"] = 0
    return ctx
