
def is_archive_admin(user):
    """Return whether the authenticated user can manage archive content globally."""
    if not user.is_authenticated:
        return False

    return (
        user.is_staff
        or user.is_superuser
        or user.role == "ADMIN"
    )


def can_manage_exhibit(user, exhibit):
    if not user.is_authenticated:
        return False

    return exhibit.owner_id == user.id or is_archive_admin(user)


def can_view_exhibit(user, exhibit):
    if exhibit.status == exhibit.Status.PUBLISHED:
        return True

    return (
        user.is_authenticated
        and (
            exhibit.owner_id == user.id
            or is_archive_admin(user)
        )
    )


def can_manage_gallery(user, gallery):
    if not user.is_authenticated:
        return False

    return gallery.owner_id == user.id or is_archive_admin(user)


def can_manage_location(user, location):
    if not user.is_authenticated or location.is_system:
        return False

    return location.owner_id == user.id or is_archive_admin(user)
