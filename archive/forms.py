from django import forms

from django.db.models import Q

from .models import (
    Category,
    Exhibit,
    Gallery,
    Location,
    Media,
    Source,
    Tag,
)


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
        queryset=Gallery.objects.order_by("name"),
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

        if user.is_staff or user.is_superuser or user.role == "ADMIN":
            self.fields["location"].queryset = Location.objects.order_by("name")
        else:
            self.fields["location"].queryset = (
                Location.objects
                .filter(
                    Q(owner=user)
                    | Q(is_system=True)
                )
                .order_by("name")
            )
