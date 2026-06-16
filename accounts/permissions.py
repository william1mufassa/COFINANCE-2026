from rest_framework.permissions import BasePermission

class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CLIENT'

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'AGENT'

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'

class IsAgentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.role in ['AGENT', 'ADMIN'] or request.user.is_staff)
