import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User

from .forms import LocationForm, MediaForm
from .models import (
    Category,
    Exhibit,
    Favorite,
    Gallery,
    GalleryExhibit,
    Location,
    Media,
)


class ArchiveTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner",
            password="StrongPass123!",
        )
        cls.other = User.objects.create_user(
            username="other",
            password="StrongPass123!",
        )
        cls.archive_admin = User.objects.create_user(
            username="archive-admin",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )

        cls.root, _ = Location.objects.get_or_create(
            is_system=True,
            parent=None,
            defaults={
                "name": "Solemnace",
                "description": "System root",
                "owner": None,
            },
        )
        cls.category = Category.objects.create(name="Character")

    def make_exhibit(self, *, title="Trazyn", status=Exhibit.Status.DRAFT):
        return Exhibit.objects.create(
            title=title,
            description="Archive record",
            status=status,
            owner=self.owner,
            category=self.category,
        )

    def test_system_root_exists(self):
        self.assertTrue(
            Location.objects.filter(
                is_system=True,
                parent__isnull=True,
            ).exists()
        )

    def test_public_catalog_contains_only_published_exhibits(self):
        self.make_exhibit(title="Draft record")
        self.make_exhibit(
            title="Published record",
            status=Exhibit.Status.PUBLISHED,
        )

        response = self.client.get(reverse("archive:exhibit_list"))

        self.assertContains(response, "Published record")
        self.assertNotContains(response, "Draft record")

    def test_unpublished_exhibit_access_is_limited(self):
        exhibit = self.make_exhibit()
        url = reverse("archive:exhibit_detail", args=[exhibit.pk])

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(self.archive_admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_exhibit_can_belong_to_multiple_galleries(self):
        exhibit = self.make_exhibit()
        first = Gallery.objects.create(
            name="Prismatic Gallery",
            owner=self.owner,
            location=self.root,
        )
        second = Gallery.objects.create(
            name="Necron Dynasty",
            owner=self.owner,
            location=self.root,
        )

        GalleryExhibit.objects.create(gallery=first, exhibit=exhibit)
        GalleryExhibit.objects.create(gallery=second, exhibit=exhibit)

        self.assertEqual(exhibit.galleries.count(), 2)

    def test_deleting_gallery_does_not_delete_exhibit(self):
        exhibit = self.make_exhibit()
        gallery = Gallery.objects.create(
            name="Collection",
            owner=self.owner,
            location=self.root,
        )
        GalleryExhibit.objects.create(gallery=gallery, exhibit=exhibit)

        gallery.delete()

        self.assertTrue(Exhibit.objects.filter(pk=exhibit.pk).exists())
        self.assertFalse(GalleryExhibit.objects.filter(exhibit=exhibit).exists())

    def test_location_form_rejects_descendant_as_parent(self):
        parent = Location.objects.create(
            name="Parent",
            owner=self.owner,
            parent=self.root,
        )
        child = Location.objects.create(
            name="Child",
            owner=self.owner,
            parent=parent,
        )

        form = LocationForm(
            data={
                "name": parent.name,
                "description": parent.description,
                "parent": child.pk,
            },
            instance=parent,
            user=self.owner,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("parent", form.errors)

    def test_nonempty_location_cannot_be_deleted_through_ui(self):
        parent = Location.objects.create(
            name="Parent",
            owner=self.owner,
            parent=self.root,
        )
        Location.objects.create(
            name="Child",
            owner=self.owner,
            parent=parent,
        )

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("archive:location_delete", args=[parent.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нельзя удалить локацию")
        self.assertTrue(Location.objects.filter(pk=parent.pk).exists())

    def test_favorite_toggle_creates_and_removes_favorite(self):
        exhibit = self.make_exhibit(status=Exhibit.Status.PUBLISHED)
        url = reverse("archive:favorite_toggle", args=[exhibit.pk])

        self.client.force_login(self.other)
        self.client.post(url)
        self.assertTrue(
            Favorite.objects.filter(user=self.other, exhibit=exhibit).exists()
        )

        self.client.post(url)
        self.assertFalse(
            Favorite.objects.filter(user=self.other, exhibit=exhibit).exists()
        )

    def test_media_form_rejects_unsupported_extension(self):
        form = MediaForm(
            data={
                "media_type": Media.MediaType.IMAGE,
                "caption": "",
                "alt_text": "",
                "position": 0,
            },
            files={
                "file": SimpleUploadedFile(
                    "payload.txt",
                    b"not an image",
                    content_type="text/plain",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_deleting_media_removes_stored_file(self):
        exhibit = self.make_exhibit()

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                media = Media.objects.create(
                    exhibit=exhibit,
                    file=SimpleUploadedFile("image.png", b"image-data"),
                )
                file_path = Path(media.file.path)
                self.assertTrue(file_path.exists())

                with self.captureOnCommitCallbacks(execute=True):
                    media.delete()

                self.assertFalse(file_path.exists())
