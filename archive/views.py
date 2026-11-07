from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Exhibit, ExhibitRelation


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
