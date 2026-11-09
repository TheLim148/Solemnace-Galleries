from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import GalleryForm
from ..models import Category, Exhibit, Gallery, Media
from ..permissions import can_manage_gallery


def gallery_list(request):
    galleries = (
        Gallery.objects
        .select_related("location", "owner")
        .annotate(
            published_count=Count(
                "exhibits",
                filter=Q(exhibits__status=Exhibit.Status.PUBLISHED),
                distinct=True,
            )
        )
        .order_by("name")
    )

    return render(
        request,
        "archive/gallery_list.html",
        {"galleries": galleries},
    )


def gallery_detail(request, pk):
    media_prefetch = Prefetch(
        "media",
        queryset=Media.objects.order_by("position", "pk"),
        to_attr="ordered_media",
    )

    gallery = get_object_or_404(
        Gallery.objects.select_related("location", "owner"),
        pk=pk,
    )

    exhibits = (
        gallery.exhibits
        .filter(status=Exhibit.Status.PUBLISHED)
        .select_related("category", "owner")
        .prefetch_related("tags", media_prefetch)
        .order_by("title")
    )

    published_total = exhibits.count()

    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")

    if query:
        exhibits = exhibits.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()

    if category_id:
        exhibits = exhibits.filter(category_id=category_id)

    categories = (
        Category.objects
        .filter(
            exhibits__galleries=gallery,
            exhibits__status=Exhibit.Status.PUBLISHED,
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request,
        "archive/gallery_detail.html",
        {
            "gallery": gallery,
            "exhibits": exhibits,
            "categories": categories,
            "query": query,
            "selected_category": category_id,
            "published_total": published_total,
            "can_manage": can_manage_gallery(request.user, gallery),
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
