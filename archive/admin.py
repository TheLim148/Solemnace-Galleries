from django.contrib import admin

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
    Source,
    Tag,
)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "owner", "is_system")
    list_filter = ("is_system",)
    search_fields = ("name",)


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "owner", "created_at")
    search_fields = ("name",)


@admin.register(Exhibit)
class ExhibitAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "owner", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "description")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "author", "year")
    search_fields = ("title", "author")


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("exhibit", "media_type", "position")


admin.site.register(GalleryExhibit)
admin.site.register(ExhibitTag)
admin.site.register(ExhibitSource)
admin.site.register(Favorite)
admin.site.register(ExhibitRelation)
