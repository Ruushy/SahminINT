from django.urls import path
from reporting import views

app_name = "reporting"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("generate/", views.report_generate, name="generate"),
    path("<int:pk>/", views.report_detail, name="detail"),
    path("<int:pk>/html/", views.report_export_html, name="export_html"),
    path("<int:pk>/json/", views.report_export_json, name="export_json"),
    path("<int:pk>/pdf/", views.report_export_pdf, name="export_pdf"),
    path("<int:pk>/delete/", views.report_delete, name="delete"),
]
