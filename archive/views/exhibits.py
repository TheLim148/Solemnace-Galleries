from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ExhibitForm, MediaForm
from ..models import (
    Category,
    Exhibit,
    ExhibitRelation,
    Favorite,
    Gallery,
    Media,
    Tag,
)
from ..permissions import can_manage_exhibit, can_view_exhibit, is_archive_admin
from ..services import replace_exhibit_links


def exhibit_list(request):
    published = Exhibit.objects.filter(status=Exhibit.Status.PUBLISHED)
    published_total = published.count()

    exhibits = (
        published
        .select_related("category", "owner")
        .prefetch_related(
            "tags",
            Prefetch(
                "media",
                queryset=Media.objects.order_by("position", "id"),
                to_attr="ordered_media",
            ),
        )
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
        exhibits = exhibits.filter(category_id=category_id)

    if tag_id:
        exhibits = exhibits.filter(tags__id=tag_id).distinct()

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
            "published_total": published_total,
            "result_count": exhibits.count(),
            "category_total": categories.count(),
            "tag_total": tags.count(),
        },
    )


def exhibit_detail(request, pk):
    exhibit = get_object_or_404(
        Exhibit.objects
        .select_related("category", "owner")
        .prefetch_related(
            "tags",
            "sources",
            Prefetch(
                "media",
                queryset=Media.objects.order_by("position", "id"),
            ),
            Prefetch(
                "galleries",
                queryset=Gallery.objects
                .select_related("location")
                .order_by("name"),
            ),
        ),
        pk=pk,
    )

    if not can_view_exhibit(request.user, exhibit):
        raise Http404

    relations = (
        ExhibitRelation.objects
        .filter(Q(exhibit_a=exhibit) | Q(exhibit_b=exhibit))
        .select_related("exhibit_a", "exhibit_b")
    )

    related_ids = [
        relation.exhibit_b_id
        if relation.exhibit_a_id == exhibit.id
        else relation.exhibit_a_id
        for relation in relations
    ]
    related_exhibits = (
        Exhibit.objects
        .filter(pk__in=related_ids)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "media",
                queryset=Media.objects.order_by("position", "id"),
            )
        )
    )

    if not is_archive_admin(request.user):
        if request.user.is_authenticated:
            related_exhibits = related_exhibits.filter(
                Q(status=Exhibit.Status.PUBLISHED)
                | Q(owner=request.user)
            )
        else:
            related_exhibits = related_exhibits.filter(
                status=Exhibit.Status.PUBLISHED
            )

    is_favorite = (
        request.user.is_authenticated
        and Favorite.objects.filter(
            user=request.user,
            exhibit=exhibit,
        ).exists()
    )

    return render(
        request,
        "archive/exhibit_detail.html",
        {
            "exhibit": exhibit,
            "related_exhibits": related_exhibits,
            "is_favorite": is_favorite,
            "can_manage": can_manage_exhibit(request.user, exhibit),
            "can_submit": (
                request.user.is_authenticated
                and exhibit.owner_id == request.user.id
                and exhibit.status in (
                    Exhibit.Status.DRAFT,
                    Exhibit.Status.REJECTED,
                )
            ),
        },
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
def exhibit_create(request):
    if request.method == "POST":
        form = ExhibitForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                exhibit = form.save(commit=False)
                exhibit.owner = request.user
                exhibit.status = Exhibit.Status.DRAFT
                exhibit.save()

                replace_exhibit_links(
                    exhibit,
                    tags=form.cleaned_data["tags"],
                    sources=form.cleaned_data["sources"],
                    galleries=form.cleaned_data["galleries"],
                )

            return redirect("archive:exhibit_detail", pk=exhibit.pk)
    else:
        form = ExhibitForm(user=request.user)

    return render(
        request,
        "archive/exhibit_form.html",
        {"form": form, "editing": False},
    )


@login_required
def exhibit_edit(request, pk):
    exhibit = get_object_or_404(Exhibit, pk=pk)

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        form = ExhibitForm(
            request.POST,
            instance=exhibit,
            user=request.user,
        )

        if form.is_valid():
            with transaction.atomic():
                exhibit = form.save()
                replace_exhibit_links(
                    exhibit,
                    tags=form.cleaned_data["tags"],
                    sources=form.cleaned_data["sources"],
                    galleries=form.cleaned_data["galleries"],
                )

            return redirect("archive:exhibit_detail", pk=exhibit.pk)
    else:
        form = ExhibitForm(
            instance=exhibit,
            user=request.user,
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
    exhibit = get_object_or_404(Exhibit, pk=pk)

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        exhibit.delete()
        return redirect("archive:exhibit_list")

    return render(
        request,
        "archive/exhibit_confirm_delete.html",
        {"exhibit": exhibit},
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

    return redirect("archive:exhibit_detail", pk=exhibit.pk)


@login_required
def media_create(request, exhibit_pk):
    exhibit = get_object_or_404(Exhibit, pk=exhibit_pk)

    if not can_manage_exhibit(request.user, exhibit):
        raise PermissionDenied

    if request.method == "POST":
        form = MediaForm(request.POST, request.FILES)

        if form.is_valid():
            media = form.save(commit=False)
            media.exhibit = exhibit
            media.save()
            return redirect("archive:exhibit_detail", pk=exhibit.pk)
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

    media.delete()

    return redirect("archive:exhibit_detail", pk=exhibit.pk)
