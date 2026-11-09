from django import forms
from django.db.models import Q

from .models import Exhibit, Gallery, Location, Media, Source, Tag
from .permissions import is_archive_admin


class ExhibitForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Теги",
    )
    sources = forms.ModelMultipleChoiceField(
        queryset=Source.objects.order_by("title"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Источники",
    )
    galleries = forms.ModelMultipleChoiceField(
        queryset=Gallery.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Галереи",
    )

    class Meta:
        model = Exhibit
        fields = (
            "title",
            "description",
            "category",
        )
        labels = {
            "title": "Название",
            "description": "Описание",
            "category": "Категория",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            return

        if is_archive_admin(user):
            galleries = Gallery.objects.all()
        else:
            galleries = Gallery.objects.filter(owner=user)

        self.fields["galleries"].queryset = galleries.order_by("name")


class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = (
            "file",
            "media_type",
            "caption",
            "alt_text",
            "position",
        )
        labels = {
            "file": "Файл",
            "media_type": "Тип",
            "caption": "Подпись",
            "alt_text": "Альтернативный текст",
            "position": "Позиция",
        }


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = (
            "name",
            "description",
            "location",
        )
        labels = {
            "name": "Название",
            "description": "Описание",
            "location": "Локация",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            self.fields["location"].queryset = Location.objects.none()
            return

        if is_archive_admin(user):
            locations = Location.objects.all()
        else:
            locations = Location.objects.filter(
                Q(owner=user) | Q(is_system=True)
            )

        self.fields["location"].queryset = locations.order_by("name")


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = (
            "name",
            "description",
            "parent",
        )
        labels = {
            "name": "Название",
            "description": "Описание",
            "parent": "Родительская локация",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            self.fields["parent"].queryset = Location.objects.none()
            return

        if is_archive_admin(user):
            locations = Location.objects.all()
        else:
            locations = Location.objects.filter(
                Q(owner=user) | Q(is_system=True)
            )

        if self.instance and self.instance.pk:
            locations = locations.exclude(pk=self.instance.pk)

        self.fields["parent"].queryset = locations.order_by("name")
        self.fields["parent"].required = True

        if not self.instance.pk:
            root = (
                Location.objects
                .filter(is_system=True, parent__isnull=True)
                .first()
            )
            if root:
                self.fields["parent"].initial = root

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")

        if parent is None:
            raise forms.ValidationError(
                "Обычная локация должна иметь родительскую локацию."
            )

        if not self.instance.pk:
            return parent

        current = parent
        while current is not None:
            if current.pk == self.instance.pk:
                raise forms.ValidationError(
                    "Нельзя переместить локацию внутрь самой себя "
                    "или одной из её дочерних локаций."
                )
            current = current.parent

        return parent
