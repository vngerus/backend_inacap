from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from cuentas.permissions import IsAdmin, IsStaff

from .models import Animal
from .serializers import AnimalSerializer


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    filterset_fields = ["especie", "sexo", "estado"]
    search_fields = ["nombre", "descripcion", "refugio"]
    ordering_fields = ["creado", "edad_meses", "nombre"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "destroy":
            return [IsAdmin()]
        return [IsStaff()]
