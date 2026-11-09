from django.db.models import Prefetch
from django.shortcuts import render

from archive.models import Exhibit, Gallery, Location, Media


def home(request):
    published_exhibits = Exhibit.objects.filter(
        status=Exhibit.Status.PUBLISHED,
    )

    featured_exhibits = (
        published_exhibits
        .select_related("category", "owner")
        .prefetch_related(
            Prefetch(
                "media",
                queryset=Media.objects.order_by("position", "id"),
            ),
        )
        .order_by("-updated_at")[:3]
    )

    root_location = (
        Location.objects
        .filter(is_system=True, parent__isnull=True)
        .order_by("id")
        .first()
    )

    context = {
        "featured_exhibits": featured_exhibits,
        "root_location": root_location,
        "published_exhibit_count": published_exhibits.count(),
        "gallery_count": Gallery.objects.count(),
        "location_count": Location.objects.count(),
    }

    return render(request, "archive/home.html", context)
