from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Exhibit, Favorite
from ..permissions import can_view_exhibit, is_archive_admin


@login_required
def favorite_toggle(request, pk):
    if request.method != "POST":
        raise PermissionDenied

    exhibit = get_object_or_404(Exhibit, pk=pk)

    if not can_view_exhibit(request.user, exhibit):
        raise Http404

    favorite = Favorite.objects.filter(
        user=request.user,
        exhibit=exhibit,
    ).first()

    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(
            user=request.user,
            exhibit=exhibit,
        )

    return redirect("archive:exhibit_detail", pk=exhibit.pk)


@login_required
def my_favorites(request):
    favorites = (
        Favorite.objects
        .filter(user=request.user)
        .select_related(
            "exhibit",
            "exhibit__category",
            "exhibit__owner",
        )
        .order_by("-created_at")
    )

    if not is_archive_admin(request.user):
        favorites = favorites.filter(
            Q(exhibit__status=Exhibit.Status.PUBLISHED)
            | Q(exhibit__owner=request.user)
        )

    return render(
        request,
        "archive/my_favorites.html",
        {"favorites": favorites},
    )
