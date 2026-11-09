from django.db import migrations


def create_root_location(apps, schema_editor):
    Location = apps.get_model("archive", "Location")

    root_exists = Location.objects.filter(
        is_system=True,
        parent__isnull=True,
    ).exists()

    if not root_exists:
        Location.objects.create(
            name="Solemnace",
            description="Корневая системная локация цифрового архива.",
            is_system=True,
            owner=None,
            parent=None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("archive", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_root_location,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
