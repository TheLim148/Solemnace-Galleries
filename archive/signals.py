from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Media


@receiver(post_delete, sender=Media)
def delete_media_file(sender, instance, **kwargs):
    """Remove the stored file after the database deletion is committed."""
    if not instance.file:
        return

    storage = instance.file.storage
    name = instance.file.name
    transaction.on_commit(lambda: storage.delete(name))
