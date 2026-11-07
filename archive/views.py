from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Exhibit, ExhibitRelation, Gallery, Location


def home(request):
    return render(request, "archive/home.html")


def exhibit_list(request):
    exhibits = (
        Exhibit.objects
        .filter(status=Exhibit.Status.PUBLISHED)
        .select_related("category", "owner")
        .order_by("-created_at")
    )

    return render(
        request,
        "archive/exhibit_list.html",
        {"exhibits": exhibits},
    )


def exhibit_detail(request, pk):
    exhibit = get_object_or_404(
        Exhibit.objects
        .select_related("category", "owner")
        .prefetch_related(
            "tags",
            "sources",
            "media",
            "galleries",
        ),
        pk=pk,
        status=Exhibit.Status.PUBLISHED,
    )

    relations = (
        ExhibitRelation.objects
        .filter(
            Q(exhibit_a=exhibit)
            | Q(exhibit_b=exhibit)
        )
        .select_related("exhibit_a", "exhibit_b")
    )

    related_exhibits = []

    for relation in relations:
        if relation.exhibit_a_id == exhibit.id:
            related_exhibits.append(relation.exhibit_b)
        else:
            related_exhibits.append(relation.exhibit_a)

    return render(
        request,
        "archive/exhibit_detail.html",
        {
            "exhibit": exhibit,
            "related_exhibits": related_exhibits,
        },
    )

def location_list(request):
    locations = (
        Location.objects
        .select_related("parent", "owner")
        .order_by("name")
    )

    return render(
        request,
        "archive/location_list.html",
        {"locations": locations},
    )


def location_detail(request, pk):
    location = get_object_or_404(
        Location.objects
        .select_related("parent", "owner")
        .prefetch_related("children", "galleries"),
        pk=pk,
    )

    return render(
        request,
        "archive/location_detail.html",
        {"location": location},
    )


def gallery_list(request):
    galleries = (
        Gallery.objects
        .select_related("location", "owner")
        .order_by("name")
    )

    return render(
        request,
        "archive/gallery_list.html",
        {"galleries": galleries},
    )


def gallery_detail(request, pk):
    gallery = get_object_or_404(
        Gallery.objects
        .select_related("location", "owner")
        .prefetch_related(
            "exhibits__category",
            "exhibits__owner",
        ),
        pk=pk,
    )

    published_exhibits = gallery.exhibits.filter(
        status=Exhibit.Status.PUBLISHED
    )

    return render(
        request,
        "archive/gallery_detail.html",
        {
            "gallery": gallery,
            "exhibits": published_exhibits,
        },
    )
