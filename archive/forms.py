from django import forms

from .models import Category, Exhibit, Gallery, Media, Source, Tag


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
