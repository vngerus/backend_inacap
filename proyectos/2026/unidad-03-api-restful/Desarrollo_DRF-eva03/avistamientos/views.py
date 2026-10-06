from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from animales.serializers import AnimalSerializer
from cuentas.permissions import IsStaff

from .models import Avistamiento
from .serializers import AvistamientoSerializer, ConvertirSerializer


class AvistamientoViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = AvistamientoSerializer
    filterset_fields = ["estado", "especie"]
    ordering_fields = ["creado", "fecha_avistamiento"]

    def get_queryset(self):
        queryset = Avistamiento.objects.all()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        user = self.request.user
        return queryset if (user.is_staff or user.is_superuser) else queryset.filter(reportante=user)

    def perform_create(self, serializer):
        serializer.save(reportante=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def verificar(self, request, pk=None):
        avistamiento = self.get_object()
        avistamiento.verificar()
        return Response(self.get_serializer(avistamiento).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def descartar(self, request, pk=None):
        avistamiento = self.get_object()
        avistamiento.descartar()
        return Response(self.get_serializer(avistamiento).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff], serializer_class=ConvertirSerializer)
    def convertir(self, request, pk=None):
        avistamiento = self.get_object()
        entrada = ConvertirSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        animal = avistamiento.convertir(entrada.validated_data.get("nombre", ""))
        return Response(AnimalSerializer(animal, context={"request": request}).data, status=status.HTTP_201_CREATED)
