from .models import ExhibitSource, ExhibitTag, GalleryExhibit


def replace_exhibit_links(exhibit, *, tags, sources, galleries):
    """Replace the editable many-to-many links of an exhibit."""
    ExhibitTag.objects.filter(exhibit=exhibit).delete()
    ExhibitSource.objects.filter(exhibit=exhibit).delete()
    GalleryExhibit.objects.filter(exhibit=exhibit).delete()

    ExhibitTag.objects.bulk_create(
        [ExhibitTag(exhibit=exhibit, tag=tag) for tag in tags]
    )
    ExhibitSource.objects.bulk_create(
        [ExhibitSource(exhibit=exhibit, source=source) for source in sources]
    )
    GalleryExhibit.objects.bulk_create(
        [
            GalleryExhibit(exhibit=exhibit, gallery=gallery)
            for gallery in galleries
        ]
    )
