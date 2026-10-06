from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from cuentas.permissions import IsStaff

from .models import SolicitudAdopcion
from .serializers import SolicitudSerializer


class SolicitudViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = SolicitudSerializer
    filterset_fields = ["estado", "animal"]
    ordering_fields = ["creada"]

    def get_queryset(self):
        queryset = SolicitudAdopcion.objects.select_related("animal")
        if getattr(self, "swagger_fake_view", False):  # drf-spectacular genera el schema sin usuario
            return queryset.none()
        user = self.request.user
        # un adoptante no ve solicitudes ajenas: devuelve 404, no 403
        return queryset if (user.is_staff or user.is_superuser) else queryset.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.aprobar(request.user)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.rechazar(request.user)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        solicitud = self.get_object()
        if solicitud.usuario_id != request.user.id:
            raise PermissionDenied("Solo quien creó la solicitud puede cancelarla.")
        solicitud.cancelar()
        return Response(self.get_serializer(solicitud).data)
