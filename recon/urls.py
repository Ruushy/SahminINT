from django.urls import path
from recon import views

app_name = "recon"

urlpatterns = [
    path("", views.recon_home, name="recon_home"),

    # Subdomains
    path("subdomains/", views.subdomain_list, name="subdomain_list"),
    path("subdomains/run/", views.subdomain_run, name="subdomain_run"),
    path("subdomains/export/", views.subdomain_export, name="subdomain_export"),

    # DNS
    path("dns/", views.dns_list, name="dns_list"),
    path("dns/run/", views.dns_run, name="dns_run"),
    path("dns/export/", views.dns_export, name="dns_export"),

    # SSL / TLS
    path("ssl/", views.ssl_list, name="ssl_list"),
    path("ssl/run/", views.ssl_run, name="ssl_run"),

    # Email Harvester
    path("emails/", views.email_list, name="email_list"),
    path("emails/run/", views.email_run, name="email_run"),
    path("emails/export/", views.email_export, name="email_export"),
]
