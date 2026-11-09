from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth.decorators import login_required
from django.db import transaction

from django.core.exceptions import PermissionDenied

from django.http import Http404


from .forms import (
    ExhibitForm,
    GalleryForm,
    LocationForm,
    MediaForm,
)

from .models import (
    Category,
    Exhibit,
    ExhibitRelation,
    ExhibitSource,
    ExhibitTag,
    Favorite,
    Gallery,
    GalleryExhibit,
    Location,
    Media,
    Tag,
)

def home(request):
    return render(request, "archive/home.html")


def exhibit_list(request):
    exhibits = (
        Exhibit.objects
        .filter(status=Exhibit.Status.PUBLISHED)
        .select_related("category", "owner")
        .prefetch_related("tags")
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    tag_id = request.GET.get("tag", "")

    if query:
        exhibits = exhibits.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(sources__title__icontains=query)
        ).distinct()

    if category_id:
        exhibits = exhibits.filter(
            category_id=category_id,
        )

    if tag_id:
        exhibits = exhibits.filter(
            tags__id=tag_id,
        ).distinct()

    categories = Category.objects.order_by("name")
    tags = Tag.objects.order_by("name")

    return render(
        request,
        "archive/exhibit_list.html",
        {
            "exhibits": exhibits,
            "categories": categories,
            "tags": tags,
            "query": query,
            "selected_category": category_id,
            "selected_tag": tag_id,
        },
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
    )

    is_admin = (
        request.user.is_authenticated
        and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == "ADMIN"
        )
    )

    is_owner = (
        request.user.is_authenticated
        and exhibit.owner_id == request.user.id
    )

    if (
        exhibit.status != Exhibit.Status.PUBLISHED
        and not is_owner
        and not is_admin
    ):
        raise Http404

    relations = (
        ExhibitRelation.objects
        .filter(
            Q(exhibit_a=exhibit)
            | Q(exhibit_b=exhibit)
        )
        .select_related("exhibit_a", "exhibit_b")
    )

    related_ids = []

    for relation in relations:
        if relation.exhibit_a_id == exhibit.id:
            related_ids.append(relation.exhibit_b_id)
        else:
            related_ids.append(relation.exhibit_a_id)

    related_exhibits = Exhibit.objects.filter(
        pk__in=related_ids
    )

    if not is_admin:
        if request.user.is_authenticated:
            related_exhibits = related_exhibits.filter(
                Q(status=Exhibit.Status.PUBLISHED)
                | Q(owner=request.user)
            )
        else:
            related_exhibits = related_exhibits.filter(
                status=Exhibit.Status.PUBLISHED,
            )

    is_favorite = False

    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user,
            exhibit=exhibit,
        ).exists()

    return render(
        request,
        "archive/exhibit_detail.html",
        {
            "exhibit": exhibit,
            "related_exhibits": related_exhibits,
            "is_favorite": is_favorite,
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

@login_required
def exhibit_create(request):
    if request.method == "POST":
        form = ExhibitForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                exhibit = form.save(commit=False)

                exhibit.owner = request.user
                exhibit.status = Exhibit.Status.DRAFT

                exhibit.save()

                ExhibitTag.objects.bulk_create(
                    [
                        ExhibitTag(
                            exhibit=exhibit,
                            tag=tag,
                        )
                        for tag in form.cleaned_data["tags"]
                    ]
                )

                ExhibitSource.objects.bulk_create(
                    [
                        ExhibitSource(
                            exhibit=exhibit,
                            source=source,
                        )
                        for source in form.cleaned_data["sources"]
                    ]
                )

                GalleryExhibit.objects.bulk_create(
                    [
                        GalleryExhibit(
                            gallery=gallery,
                            exhibit=exhibit,
                        )
                        for gallery in form.cleaned_data["galleries"]
                    ]
                )

            return redirect(
                "archive:exhibit_detail",
                pk=exhibit.pk,
            )

    else:
        form = ExhibitForm()

    return render(
        request,
        "archive/exhibit_form.html",
        {"form": form},
    )

def can_manage_exhibit(user, exhibit):
    if not user.is_authenticated:
        return False

    return (
        exhibit.owner_id == user.id
        or user.is_staff
        or user.role == "ADMIN"
    )

def can_manage_gallery(user, gallery):
    if not user.is_authenticated:
        return False

    return (
        gallery.owner_id == user.id
        or user.is_staff
        or user.is_superuser
        or user.role == "ADMIN"
    )

def can_manage_location(user, location):
    if not user.is_authenticated:
        return False

    if location.is_system:
        return False

    return (
        location.owner_id == user.id
        or user.is_staff
        or user.is_superuser
        or user.role == "ADMIN"
    )

@login_required
def exhibit_edit(request, pk):
    exhibit = get_object_or_404(
        Exhibit,
        pk=pk,
    )

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        form = ExhibitForm(
            request.POST,
            instance=exhibit,
        )

        if form.is_valid():
            with transaction.atomic():
                exhibit = form.save()

                ExhibitTag.objects.filter(
                    exhibit=exhibit,
                ).delete()

                ExhibitSource.objects.filter(
                    exhibit=exhibit,
                ).delete()

                GalleryExhibit.objects.filter(
                    exhibit=exhibit,
                ).delete()

                ExhibitTag.objects.bulk_create(
                    [
                        ExhibitTag(
                            exhibit=exhibit,
                            tag=tag,
                        )
                        for tag in form.cleaned_data["tags"]
                    ]
                )

                ExhibitSource.objects.bulk_create(
                    [
                        ExhibitSource(
                            exhibit=exhibit,
                            source=source,
                        )
                        for source in form.cleaned_data["sources"]
                    ]
                )

                GalleryExhibit.objects.bulk_create(
                    [
                        GalleryExhibit(
                            exhibit=exhibit,
                            gallery=gallery,
                        )
                        for gallery in form.cleaned_data["galleries"]
                    ]
                )

            return redirect(
                "archive:exhibit_detail",
                pk=exhibit.pk,
            )

    else:
        form = ExhibitForm(
            instance=exhibit,
            initial={
                "tags": exhibit.tags.all(),
                "sources": exhibit.sources.all(),
                "galleries": exhibit.galleries.all(),
            },
        )

    return render(
        request,
        "archive/exhibit_form.html",
        {
            "form": form,
            "exhibit": exhibit,
            "editing": True,
        },
    )

@login_required
def exhibit_delete(request, pk):
    exhibit = get_object_or_404(
        Exhibit,
        pk=pk,
    )

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        exhibit.delete()

        return redirect(
            "archive:exhibit_list",
        )

    return render(
        request,
        "archive/exhibit_confirm_delete.html",
        {"exhibit": exhibit},
    )

@login_required
def my_exhibits(request):
    exhibits = (
        Exhibit.objects
        .filter(owner=request.user)
        .select_related("category")
        .order_by("-updated_at")
    )

    return render(
        request,
        "archive/my_exhibits.html",
        {"exhibits": exhibits},
    )


@login_required
def exhibit_submit_for_review(request, pk):
    exhibit = get_object_or_404(
        Exhibit,
        pk=pk,
        owner=request.user,
    )

    if request.method != "POST":
        raise PermissionDenied

    if exhibit.status not in (
        Exhibit.Status.DRAFT,
        Exhibit.Status.REJECTED,
    ):
        raise PermissionDenied

    exhibit.status = Exhibit.Status.PENDING
    exhibit.save(update_fields=["status", "updated_at"])

    return redirect(
        "archive:exhibit_detail",
        pk=exhibit.pk,
    )

@login_required
def media_create(request, exhibit_pk):
    exhibit = get_object_or_404(
        Exhibit,
        pk=exhibit_pk,
    )

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        form = MediaForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            media = form.save(commit=False)
            media.exhibit = exhibit
            media.save()

            return redirect(
                "archive:exhibit_detail",
                pk=exhibit.pk,
            )

    else:
        form = MediaForm()

    return render(
        request,
        "archive/media_form.html",
        {
            "form": form,
            "exhibit": exhibit,
        },
    )

@login_required
def media_delete(request, pk):
    media = get_object_or_404(
        Media.objects.select_related("exhibit"),
        pk=pk,
    )

    exhibit = media.exhibit

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method != "POST":
        raise PermissionDenied

    media.file.delete(save=False)
    media.delete()

    return redirect(
        "archive:exhibit_detail",
        pk=exhibit.pk,
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
        form = GalleryForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.owner = request.user
            gallery.save()

            return redirect(
                "archive:gallery_detail",
                pk=gallery.pk,
            )

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

            return redirect(
                "archive:gallery_detail",
                pk=gallery.pk,
            )

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
    gallery = get_object_or_404(
        Gallery,
        pk=pk,
    )

    if not can_manage_gallery(request.user, gallery):
        raise PermissionDenied

    if request.method == "POST":
        gallery.delete()

        return redirect(
            "archive:my_galleries",
        )

    return render(
        request,
        "archive/gallery_confirm_delete.html",
        {"gallery": gallery},
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
        form = LocationForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            location = form.save(commit=False)

            location.owner = request.user
            location.is_system = False

            location.save()

            return redirect(
                "archive:location_detail",
                pk=location.pk,
            )

    else:
        form = LocationForm(
            user=request.user,
        )

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
        Location.objects.select_related(
            "owner",
            "parent",
        ),
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

            return redirect(
                "archive:location_detail",
                pk=location.pk,
            )

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
    location = get_object_or_404(
        Location,
        pk=pk,
    )

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

            return redirect(
                "archive:my_locations",
            )

    return render(
        request,
        "archive/location_confirm_delete.html",
        {
            "location": location,
            "error": error,
        },
    )


@login_required
def favorite_toggle(request, pk):
    if request.method != "POST":
        raise PermissionDenied

    exhibit = get_object_or_404(
        Exhibit,
        pk=pk,
    )

    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.role == "ADMIN"
    )

    is_owner = exhibit.owner_id == request.user.id

    if (
        exhibit.status != Exhibit.Status.PUBLISHED
        and not is_owner
        and not is_admin
    ):
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

    return redirect(
        "archive:exhibit_detail",
        pk=exhibit.pk,
    )

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

    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.role == "ADMIN"
    ):
        favorites = favorites.filter(
            Q(exhibit__status=Exhibit.Status.PUBLISHED)
            | Q(exhibit__owner=request.user)
        )

    return render(
        request,
        "archive/my_favorites.html",
        {"favorites": favorites},
    )
