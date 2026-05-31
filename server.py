import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reconhub.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@sahminint.local", "Recon@2026")

from reconhub.asgi import application as app
