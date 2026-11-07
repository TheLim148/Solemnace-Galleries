from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth.decorators import login_required
from django.db import transaction

from django.core.exceptions import PermissionDenied

from .forms import ExhibitForm
from .models import (
    Exhibit,
    ExhibitRelation,
    ExhibitSource,
    ExhibitTag,
    Gallery,
    GalleryExhibit,
    Location,
)

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
    exhibits = (
        Exhibit.objects
        .select_related("category", "owner")
        .prefetch_related(
            "tags",
            "sources",
            "media",
            "galleries",
        )
    )

    if request.user.is_authenticated:
        is_admin = (
            request.user.is_staff
            or request.user.role == "ADMIN"
        )

        if not is_admin:
            exhibits = exhibits.filter(
                Q(status=Exhibit.Status.PUBLISHED)
                | Q(owner=request.user)
            )

    else:
        exhibits = exhibits.filter(
            status=Exhibit.Status.PUBLISHED,
        )

    exhibit = get_object_or_404(
        exhibits,
        pk=pk,
    )

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

    if request.user.is_authenticated:
        is_admin = (
            request.user.is_staff
            or request.user.role == "ADMIN"
        )

        if not is_admin:
            related_exhibits = related_exhibits.filter(
                Q(status=Exhibit.Status.PUBLISHED)
                | Q(owner=request.user)
            )

    else:
        related_exhibits = related_exhibits.filter(
            status=Exhibit.Status.PUBLISHED,
        )

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
