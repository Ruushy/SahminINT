from django.urls import path
from dorking import views

app_name = "dorking"

urlpatterns = [
    path("", views.dorking_home, name="home"),
    path("google/", views.google_dorks, name="google"),
    path("github/", views.github_dorks, name="github"),
    path("browser/", views.browser_search, name="browser_search"),
    path("save/", views.save_dork, name="save_dork"),
    path("saved/", views.list_saved_dorks, name="saved"),
]
