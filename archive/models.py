from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Location(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="locations",
        null=True,
        blank=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(is_system=True) | Q(owner__isnull=False),
                name="location_system_or_has_owner",
            ),
            models.CheckConstraint(
                condition=Q(parent__isnull=True) | ~Q(parent=F("id")),
                name="location_not_own_parent",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.is_system and self.parent_id is None:
            raise ValidationError({
                "parent": "Обычная локация должна иметь родительскую локацию."
            })

        if self.parent_id is None:
            return

        seen = set()
        current = self.parent

        while current is not None:
            if current.pk in seen:
                raise ValidationError({
                    "parent": "Обнаружен цикл в иерархии локаций."
                })
            seen.add(current.pk)

            if self.pk is not None and current.pk == self.pk:
                raise ValidationError({
                    "parent": (
                        "Нельзя переместить локацию внутрь самой себя "
                        "или одной из её дочерних локаций."
                    )
                })

            current = current.parent

    def __str__(self):
        return self.name


class Gallery(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="galleries",
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="galleries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    exhibits = models.ManyToManyField(
        "Exhibit",
        through="GalleryExhibit",
        related_name="galleries",
        blank=True,
    )

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Source(models.Model):
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, blank=True)
    author = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    url = models.URLField(max_length=1000, blank=True)

    def __str__(self):
        return self.title


class Exhibit(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        PENDING = "PENDING", "На модерации"
        PUBLISHED = "PUBLISHED", "Опубликован"
        REJECTED = "REJECTED", "Отклонён"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="exhibits",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="exhibits",
    )

    tags = models.ManyToManyField(
        Tag,
        through="ExhibitTag",
        related_name="exhibits",
        blank=True,
    )

    sources = models.ManyToManyField(
        Source,
        through="ExhibitSource",
        related_name="exhibits",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Media(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", "Изображение"
        GIF = "GIF", "GIF"

    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
        related_name="media",
    )

    file = models.FileField(upload_to="exhibits/")
    media_type = models.CharField(
        max_length=30,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )

    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.exhibit}: {self.file.name}"


class GalleryExhibit(models.Model):
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
    )

    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gallery", "exhibit"],
                name="unique_gallery_exhibit",
            ),
        ]


class ExhibitTag(models.Model):
    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exhibit", "tag"],
                name="unique_exhibit_tag",
            ),
        ]


class ExhibitSource(models.Model):
    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
    )

    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exhibit", "source"],
                name="unique_exhibit_source",
            ),
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "exhibit"],
                name="unique_user_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.exhibit}"


class ExhibitRelation(models.Model):
    exhibit_a = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
        related_name="relations_as_a",
    )

    exhibit_b = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
        related_name="relations_as_b",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exhibit_a", "exhibit_b"],
                name="unique_exhibit_relation",
            ),
            models.CheckConstraint(
                condition=Q(exhibit_a__lt=F("exhibit_b")),
                name="ordered_exhibit_relation",
            ),
        ]

    def clean(self):
        if (
            self.exhibit_a_id is not None
            and self.exhibit_b_id is not None
            and self.exhibit_a_id == self.exhibit_b_id
        ):
            raise ValidationError(
                "Экспонат нельзя связать с самим собой."
            )

    def save(self, *args, **kwargs):
        if (
            self.exhibit_a_id is not None
            and self.exhibit_b_id is not None
            and self.exhibit_a_id > self.exhibit_b_id
        ):
            self.exhibit_a_id, self.exhibit_b_id = (
                self.exhibit_b_id,
                self.exhibit_a_id,
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.exhibit_a} ↔ {self.exhibit_b}"
