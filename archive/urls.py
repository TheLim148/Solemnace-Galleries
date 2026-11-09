from django.urls import path

from .views import exhibits, favorites, galleries, locations, pages


app_name = "archive"

urlpatterns = [
    # Main page
    path("", pages.home, name="home"),

    # Exhibits
    path("exhibits/", exhibits.exhibit_list, name="exhibit_list"),
    path("exhibits/create/", exhibits.exhibit_create, name="exhibit_create"),
    path("my/exhibits/", exhibits.my_exhibits, name="my_exhibits"),
    path(
        "exhibits/<int:pk>/",
        exhibits.exhibit_detail,
        name="exhibit_detail",
    ),
    path(
        "exhibits/<int:pk>/edit/",
        exhibits.exhibit_edit,
        name="exhibit_edit",
    ),
    path(
        "exhibits/<int:pk>/delete/",
        exhibits.exhibit_delete,
        name="exhibit_delete",
    ),
    path(
        "exhibits/<int:pk>/submit/",
        exhibits.exhibit_submit_for_review,
        name="exhibit_submit_for_review",
    ),

    # Exhibit media
    path(
        "exhibits/<int:exhibit_pk>/media/create/",
        exhibits.media_create,
        name="media_create",
    ),
    path(
        "media/<int:pk>/delete/",
        exhibits.media_delete,
        name="media_delete",
    ),

    # Galleries
    path("galleries/", galleries.gallery_list, name="gallery_list"),
    path("galleries/create/", galleries.gallery_create, name="gallery_create"),
    path("my/galleries/", galleries.my_galleries, name="my_galleries"),
    path(
        "galleries/<int:pk>/",
        galleries.gallery_detail,
        name="gallery_detail",
    ),
    path(
        "galleries/<int:pk>/edit/",
        galleries.gallery_edit,
        name="gallery_edit",
    ),
    path(
        "galleries/<int:pk>/delete/",
        galleries.gallery_delete,
        name="gallery_delete",
    ),

    # Locations
    path("locations/", locations.location_list, name="location_list"),
    path("locations/create/", locations.location_create, name="location_create"),
    path("my/locations/", locations.my_locations, name="my_locations"),
    path(
        "locations/<int:pk>/",
        locations.location_detail,
        name="location_detail",
    ),
    path(
        "locations/<int:pk>/edit/",
        locations.location_edit,
        name="location_edit",
    ),
    path(
        "locations/<int:pk>/delete/",
        locations.location_delete,
        name="location_delete",
    ),

    # Favorites
    path("favorites/", favorites.my_favorites, name="my_favorites"),
    path(
        "exhibits/<int:pk>/favorite/",
        favorites.favorite_toggle,
        name="favorite_toggle",
    ),
]
