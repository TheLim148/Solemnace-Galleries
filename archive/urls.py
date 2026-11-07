from django.urls import path

from . import views


app_name = "archive"

urlpatterns = [
    path("", views.home, name="home"),

    path("locations/", views.location_list, name="location_list"),
    path(
        "locations/<int:pk>/",
        views.location_detail,
        name="location_detail",
    ),

    path("galleries/", views.gallery_list, name="gallery_list"),
    path(
        "galleries/<int:pk>/",
        views.gallery_detail,
        name="gallery_detail",
    ),

    path("exhibits/", views.exhibit_list, name="exhibit_list"),
    path(
      "exhibits/create/",
        views.exhibit_create,
        name="exhibit_create",
    ),
    path(
        "exhibits/<int:pk>/edit/",
        views.exhibit_edit,
        name="exhibit_edit",
    ),
    path(
        "exhibits/<int:pk>/delete/",
        views.exhibit_delete,
        name="exhibit_delete",
    ),
    path(
        "exhibits/<int:pk>/",
        views.exhibit_detail,
        name="exhibit_detail",
    ),
]
