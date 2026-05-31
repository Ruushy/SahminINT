from django.urls import path
from targets import views

app_name = "targets"

urlpatterns = [
    path("", views.target_list, name="list"),
    path("create/", views.target_create, name="create"),
    path("<int:pk>/", views.target_detail, name="detail"),
    path("<int:pk>/update/", views.target_update, name="update"),
    path("<int:pk>/delete/", views.target_delete, name="delete"),
    path("<int:pk>/favorite/", views.target_favorite, name="favorite"),
    path("<int:pk>/add-note/", views.target_add_note, name="add_note"),
    path("search-history/", views.search_history, name="search_history"),
]
