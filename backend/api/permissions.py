from rest_framework.permissions import BasePermission

from api.models import HRUser


class IsHRUser(BasePermission):
    """Allow access only to authenticated, active HR users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.user, HRUser)
            and request.user.is_active
        )
