from rest_framework import serializers

from animales.models import Animal
from config.exceptions import Conflicto

from .models import SolicitudAdopcion


class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudAdopcion
        fields = ("id", "animal", "usuario", "mensaje", "estado", "creada", "resuelta", "resuelta_por")
        read_only_fields = ("id", "usuario", "estado", "creada", "resuelta", "resuelta_por")

    def validate_animal(self, animal):
        if animal.estado != Animal.Estado.ADOPTABLE:
            raise Conflicto("El animal ya fue adoptado.")
        return animal

    def validate(self, attrs):
        usuario = self.context["request"].user
        if SolicitudAdopcion.objects.filter(
            animal=attrs["animal"], usuario=usuario, estado=SolicitudAdopcion.Estado.PENDIENTE
        ).exists():
            raise serializers.ValidationError("Ya tienes una solicitud pendiente para este animal.")
        return attrs
