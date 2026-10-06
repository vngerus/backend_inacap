from rest_framework.permissions import BasePermission


class IsStaff(BasePermission):
    """Staff o admin: la jerarquía es adoptante < staff < admin."""

    message = "Se requiere rol staff."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsAdmin(BasePermission):
    message = "Se requiere rol admin."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
