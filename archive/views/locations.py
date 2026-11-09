from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import LocationForm
from ..models import Location
from ..permissions import can_manage_location


def _get_location_ancestors(location):
    """Return the parent chain from the root to the direct parent."""
    ancestors = []
    current = location.parent
    seen = set()

    while current is not None and current.pk not in seen:
        seen.add(current.pk)
        ancestors.append(current)
        current = current.parent

    ancestors.reverse()
    return ancestors


def location_list(request):
    locations = (
        Location.objects
        .select_related("parent", "owner")
        .prefetch_related("children", "galleries")
        .order_by("-is_system", "name")
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
        .prefetch_related(
            "children",
            "children__children",
            "children__galleries",
            "galleries",
        ),
        pk=pk,
    )

    return render(
        request,
        "archive/location_detail.html",
        {
            "location": location,
            "ancestors": _get_location_ancestors(location),
        },
    )


@login_required
def my_locations(request):
    locations = (
        Location.objects
        .filter(owner=request.user)
        .select_related("parent")
        .order_by("name")
    )

    return render(
        request,
        "archive/my_locations.html",
        {"locations": locations},
    )


@login_required
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST, user=request.user)

        if form.is_valid():
            location = form.save(commit=False)
            location.owner = request.user
            location.is_system = False
            location.save()
            return redirect("archive:location_detail", pk=location.pk)
    else:
        form = LocationForm(user=request.user)

    return render(
        request,
        "archive/location_form.html",
        {
            "form": form,
            "editing": False,
        },
    )


@login_required
def location_edit(request, pk):
    location = get_object_or_404(
        Location.objects.select_related("owner", "parent"),
        pk=pk,
    )

    if not can_manage_location(request.user, location):
        raise PermissionDenied

    if request.method == "POST":
        form = LocationForm(
            request.POST,
            instance=location,
            user=request.user,
        )

        if form.is_valid():
            location = form.save()
            return redirect("archive:location_detail", pk=location.pk)
    else:
        form = LocationForm(
            instance=location,
            user=request.user,
        )

    return render(
        request,
        "archive/location_form.html",
        {
            "form": form,
            "location": location,
            "editing": True,
        },
    )


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if not can_manage_location(request.user, location):
        raise PermissionDenied

    error = None

    if request.method == "POST":
        if location.children.exists():
            error = (
                "Нельзя удалить локацию, пока она содержит "
                "дочерние локации."
            )
        elif location.galleries.exists():
            error = (
                "Нельзя удалить локацию, пока она содержит галереи."
            )
        else:
            location.delete()
            return redirect("archive:my_locations")

    return render(
        request,
        "archive/location_confirm_delete.html",
        {
            "location": location,
            "error": error,
        },
    )
