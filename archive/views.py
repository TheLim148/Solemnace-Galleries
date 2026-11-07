
from django.shortcuts import get_object_or_404, render

from .models import Exhibit


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
        Exhibit.objects.select_related("category", "owner"),
        pk=pk,
        status=Exhibit.Status.PUBLISHED,
    )

    return render(
        request,
        "archive/exhibit_detail.html",
        {"exhibit": exhibit},
    )
