from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import GalleryForm
from ..models import Exhibit, Gallery
from ..permissions import can_manage_gallery


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
        .prefetch_related("exhibits__category", "exhibits__owner"),
        pk=pk,
    )

    exhibits = gallery.exhibits.filter(status=Exhibit.Status.PUBLISHED)

    return render(
        request,
        "archive/gallery_detail.html",
        {
            "gallery": gallery,
            "exhibits": exhibits,
        },
    )


@login_required
def my_galleries(request):
    galleries = (
        Gallery.objects
        .filter(owner=request.user)
        .select_related("location")
        .order_by("-updated_at")
    )

    return render(
        request,
        "archive/my_galleries.html",
        {"galleries": galleries},
    )


@login_required
def gallery_create(request):
    if request.method == "POST":
        form = GalleryForm(request.POST, user=request.user)

        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.owner = request.user
            gallery.save()
            return redirect("archive:gallery_detail", pk=gallery.pk)
    else:
        form = GalleryForm(user=request.user)

    return render(
        request,
        "archive/gallery_form.html",
        {
            "form": form,
            "editing": False,
        },
    )


@login_required
def gallery_edit(request, pk):
    gallery = get_object_or_404(
        Gallery.objects.select_related("location", "owner"),
        pk=pk,
    )

    if not can_manage_gallery(request.user, gallery):
        raise PermissionDenied

    if request.method == "POST":
        form = GalleryForm(
            request.POST,
            instance=gallery,
            user=request.user,
        )

        if form.is_valid():
            gallery = form.save()
            return redirect("archive:gallery_detail", pk=gallery.pk)
    else:
        form = GalleryForm(
            instance=gallery,
            user=request.user,
        )

    return render(
        request,
        "archive/gallery_form.html",
        {
            "form": form,
            "gallery": gallery,
            "editing": True,
        },
    )


@login_required
def gallery_delete(request, pk):
    gallery = get_object_or_404(Gallery, pk=pk)

    if not can_manage_gallery(request.user, gallery):
        raise PermissionDenied

    if request.method == "POST":
        gallery.delete()
        return redirect("archive:my_galleries")

    return render(
        request,
        "archive/gallery_confirm_delete.html",
        {"gallery": gallery},
    )
