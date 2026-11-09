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
    path(
        "my/locations/",
        views.my_locations,
        name="my_locations",
    ),
    path(
        "locations/create/",
        views.location_create,
        name="location_create",
    ),
    path(
        "locations/<int:pk>/edit/",
        views.location_edit,
        name="location_edit",
    ),
    path(
        "locations/<int:pk>/delete/",
        views.location_delete,
        name="location_delete",
    ),

    path("galleries/", views.gallery_list, name="gallery_list"),
    path(
        "galleries/<int:pk>/",
        views.gallery_detail,
        name="gallery_detail",
    ),
    path(
        "my/galleries/",
        views.my_galleries,
        name="my_galleries",
    ),
    path(
        "galleries/create/",
        views.gallery_create,
        name="gallery_create",
    ),
    path(
        "galleries/<int:pk>/edit/",
        views.gallery_edit,
        name="gallery_edit",
    ),
    path(
        "galleries/<int:pk>/delete/",
        views.gallery_delete,
        name="gallery_delete",
    ),

    path("exhibits/", views.exhibit_list, name="exhibit_list"),
    path(
      "exhibits/create/",
        views.exhibit_create,
        name="exhibit_create",
    ),
    path(
        "exhibits/<int:exhibit_pk>/media/create/",
        views.media_create,
        name="media_create",
    ),
    path(
        "media/<int:pk>/delete/",
        views.media_delete,
        name="media_delete",
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
        "my/exhibits/",
        views.my_exhibits,
        name="my_exhibits",
    ),
    path(
        "exhibits/<int:pk>/submit/",
        views.exhibit_submit_for_review,
        name="exhibit_submit_for_review",
    ),
    path(
        "exhibits/<int:pk>/",
        views.exhibit_detail,
        name="exhibit_detail",
    ),
    path(
        "exhibits/<int:pk>/favorite/",
        views.favorite_toggle,
        name="favorite_toggle",
    ),
    path(
        "favorites/",
        views.my_favorites,
        name="my_favorites",
    ),
]
