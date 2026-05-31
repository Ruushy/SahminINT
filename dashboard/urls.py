from django.urls import path
from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.global_search, name="search"),
    path("activity/", views.activity_feed, name="activity"),
]
